#!/usr/bin/env python

# This is a comment
from __future__ import print_function

import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3' 

import editdistance
import numpy as np
import tensorflow as tf
from tensorflow.keras.utils import Progbar

from .config import load_args
from .data.list_generator import ListGenerator
from .language_model.char_rnn_lm import CharRnnLmWrapperSingleton
from .lip_model.training_graph import TransformerTrainGraph
from .lip_model.inference_graph import TransformerInferenceGraph
from .lip_preprocessing.record_and_crop_video import record_and_crop

tf.compat.v1.disable_eager_execution()

config = load_args()

graph_dict = {
    'train': TransformerTrainGraph,
    'infer': TransformerInferenceGraph,
}


def predict(sess, g, n_batches, chars=None, val_gen=None):
    '''
        Take in the recorded video and return the prediction sentence
    '''

    for i in range(n_batches):
        x, y =  val_gen.next()
        if len(x) == 1: x = x[0]
        if len(y) == 1: y = y[0]

        # -- Autoregressive inference
        preds = np.zeros((config.batch_size, config.maxlen), np.int32)

        tile_preds = config.test_aug_times
        # -- For train graph feed in the previous step's predictions manually for the next
        if not 'infer' in config.graph_type:
            prev_inp = np.tile(preds, [config.test_aug_times,1]) if tile_preds else preds
            feed_dict = {g.x: x, g.prev: prev_inp, g.y: y}

            enc = sess.run( g.enc, feed_dict)
            if type(enc) is list:
                for enc_tens, enc_val in zip(g.enc, enc): feed_dict[enc_tens] = enc_val
            else:
                feed_dict[g.enc] = enc
            for j in range(config.maxlen):
                _preds, loss, cer = sess.run([g.preds, g.mean_loss, g.cer], feed_dict)
                preds[:, j] = _preds[:, j]
                prev_inp = np.tile(preds, [config.test_aug_times,1]) if tile_preds else preds
                feed_dict[g.prev] = prev_inp
                # if all samples in batch predict the pad symbol (char_id==0)
                if np.sign(preds[:,j]).sum() == 0:
                    if g.tb_sum is not None:
                        tb_sum = sess.run( g.tb_sum, {g.x: x, g.prev: prev_inp, g.y: y})
                    break

        # -- Autoregression loop is built into the beam search graph
        else:
            feed_dict = {g.x: x, g.y: y}
            enc = sess.run( g.enc, feed_dict)
            if type(enc) is list:
                for enc_tens, enc_val in zip(g.enc, enc): feed_dict[enc_tens] = enc_val
            else:
                feed_dict[g.enc] = enc
            _preds, loss, cer = sess.run([g.preds, g.mean_loss, g.cer], feed_dict)
            preds = _preds

        decode_preds_to_chars = lambda decoding: ''.join([ chars[cid] for cid in decoding]).strip()
        pred_sentences = [decode_preds_to_chars(prr).replace('-', ' ') for prr in preds]
        pred_words = [sent.split(' ') for sent in  pred_sentences]

    return pred_sentences, pred_words


def init_models_and_data(istrain):
    '''
        Initialize the Deep Lip Reading model and run lip preprocessing to record and crop video
    '''

    print ('Loading data generators')
    val_gen = ListGenerator(data_list=config.data_list)
    val_epoch_size = val_gen.calc_nbatches_per_epoch()
    print ('Done')
  
    os.environ["CUDA_VISIBLE_DEVICES"] = str(config.gpu_id)
    gpu_options = tf.compat.v1.GPUOptions(allow_growth=True)
    sess_config = tf.compat.v1.ConfigProto(gpu_options=gpu_options)
    sess = tf.compat.v1.Session(config=sess_config)
  
    if config.lm_path:
        # initialize singleton rnn so that RNN tf graph is created first
        beam_batch_size = 1
        lm_handle = CharRnnLmWrapperSingleton(batch_size=beam_batch_size,
                                              sess=sess,
                                              checkpoint_path=config.lm_path)
  
    TransformerGraphClass = graph_dict[config.graph_type]
  
    (shapes_in, dtypes_in), (shapes_out, dtypes_out) = TransformerGraphClass.get_model_input_target_shapes_and_types()
  
    go_idx = val_gen.label_vectorizer.char_indices[val_gen.label_vectorizer.go_token]
    x_val = tf.compat.v1.placeholder(dtypes_in[0], shape=shapes_in[0])
    prev_shape = list(shapes_out[0])

    if config.test_aug_times:
        prev_shape[0] *= config.test_aug_times

    prev_ph = tf.compat.v1.placeholder(dtypes_out[0], shape=prev_shape)
    y_ph = tf.compat.v1.placeholder(dtypes_out[0], shape=shapes_out[0])
    y_val = [prev_ph, y_ph]
  
    chars = val_gen.label_vectorizer.chars
    val_g = TransformerGraphClass(x_val,
                                  y_val,
                                  is_training=False,
                                  reuse=tf.compat.v1.AUTO_REUSE,
                                  go_token_index=go_idx,
                                  chars=chars)
    print("Validation Graph loaded")
  
    sess.run(tf.compat.v1.tables_initializer())
  
    load_checkpoints(sess)
  
    return val_g, val_epoch_size, chars, sess, val_gen


def load_checkpoints(sess, var_scopes = ('encoder', 'decoder', 'dense')):
    '''
        Load the pretrained model checkpoint
    '''
    checkpoint_path =  config.lip_model_path
    if checkpoint_path:
        if os.path.isdir(checkpoint_path):
            checkpoint = tf.train.latest_checkpoint(checkpoint_path)
        else:
            checkpoint = checkpoint_path
  
    if config.featurizer:

        if checkpoint_path:
            from tensorflow.python.training import checkpoint_utils
            var_list = checkpoint_utils.list_variables(checkpoint)
            for var in var_list:
                if 'visual_frontend' in var[0]:
                    var_scopes = var_scopes + ('visual_frontend',)
                    break

        if not 'visual_frontend' in var_scopes:
            featurizer_vars = tf.compat.v1.global_variables(scope='visual_frontend')
            featurizer_ckpt = tf.train.get_checkpoint_state(config.featurizer_model_path)
            featurizer_vars = [var for var in featurizer_vars if not 'Adam' in var.name]
            tf.train.Saver(featurizer_vars).restore(sess, featurizer_ckpt.model_checkpoint_path)

    all_variables = []
    for scope in var_scopes:
        all_variables += [var for var in tf.compat.v1.global_variables(scope=scope)
                          if not 'Adam' in var.name ]
    if checkpoint_path:
        tf.compat.v1.train.Saver(all_variables).restore(sess, checkpoint)

        print("Restored saved model {}!".format(checkpoint))


def start_lip_reading():
    '''
        Run Lip Preprocessing and Deep Lip Reading
    '''
    # begin reading in camera input data
    record_and_crop()

    np.random.seed(config.seed)
    tf.random.set_seed(config.seed)

    val_g, val_epoch_size, chars, sess, val_gen = init_models_and_data(istrain=0)

    with sess.as_default():
        pred_sentences, pred_words = predict(sess=sess, g=val_g, n_batches=val_epoch_size, chars=chars, val_gen=val_gen)

    return pred_sentences[0], pred_words[0] # Assume batch size is always 1


if __name__ == '__main__':
    lip_command, lip_words = start_lip_reading()
    print('lip command: ', lip_command)
    print('lip words: ', lip_words)

