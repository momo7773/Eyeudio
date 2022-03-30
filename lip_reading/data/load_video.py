import numpy as np
from ..lip_preprocessing.record_and_crop_video import get_copy_of_output_frames

def load_video_frames(path, maxlen, pad_mode, grayscale=True):
    mat = np.array(get_copy_of_output_frames())

    if grayscale:
        mat = np.expand_dims(mat,axis=3)

    mat = mat.astype('float')/255.
  
    if pad_mode:
        if len(mat) > maxlen:
            return None
        mat = pad_seq(mat, mode = pad_mode, maxlen = maxlen)
  
    return mat

def pad_seq(mat, mode, maxlen):
    dat = np.zeros( ( maxlen ,)  + mat.shape[1:], dtype=mat.dtype )
    if mode == 'end':
        dat[ :mat.shape[0] ] = mat
        mat = dat
    elif mode == 'mid':
        assert maxlen >= mat.shape[0]
        padlen = (maxlen - mat.shape[0])//2
        dat[ padlen:padlen + mat.shape[0] ] = mat
        mat = dat

    return mat
