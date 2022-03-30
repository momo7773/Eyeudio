# Lip Reading Module for Outputting Basic Computer Commands

## Setup environment

### Step 1: Install Anaconda: https://docs.anaconda.com/anaconda/install/index.html

### Step 2: Create and activate a Python 3.7.7 environment, install packages
```bash
conda create -n lip_env_3.7.7 python=3.7.7
conda activate lip_env_3.7.7

# For Lip Preprocessing
conda install -c conda-forge opencv=4.5.3 dlib=19.22.0 sk-video=1.1.10

# For Deep Lip Reading
python -m pip install tensorflow-gpu
python -m pip install numpy
python -m pip install av
python -m pip install editdistance
python -m pip install configargparse
python -m pip install six
python -m pip install moviepy==0.2.3.5
python -m pip install opencv-python
python -m pip install imageio-ffmpeg
python -m pip install tensorflow_addons
```

**Note:** We need to activate this environment by running `conda activate lip_env_3.7.7` every time opening up a new terminal.

### Step 3 (one-time): Download the Deep Lip Reading's pretrained models
You may need to download/install `wget` for the following to work. 
Here is one tutorial for Windows: https://builtvisible.com/download-your-website-with-wget/
```bash
cd Eyeudio/lip_reading/
./download_models.sh
```

### Step 4: Call the Lip Reading module in GUI or as a module
In `gui.py`, add:
```python
from lip_reading.start_lip_reading import start_lip_reading

# Then call this in a thread
start_lip_reading()
```
or run from terminal:
```bash
cd Eyeudio/
python -m lip_reading.start_lip_reading
```

**Note:** `gui.py` should be in the root directory (`Eyeudio/`)
**Note:** calling from terminal runs it as a **module** instead of a **top-level script**. This allows for the relative imports within `start_lip_reading`.

## Module Dependency Tree:

```
config.py

start_lip_reading.py
|___data/list_generator.py
	|___data/label_vectorization.py
	|___data/load_video.py

|___language_model/char_rnn_lm.py

|___lip_model/training_graph.py
	|___config.py
	|___lip_model/losses.py
	|___lip_model/modules.py
	|___lip_model/visual_frontend.py
		|___config.py
		|___lip_model/prepoc_and_aug.py
			|___util/tf_util.py
		|___lip_model/resnet.py
			|___util/tf_util.py
		|___util/tf_util.py
	|___util/tf_util.py
	|___util/tb_util.py

|___lip_model/inference_graph.py
	|___config.py
	|___language_model/char_rnn_lm.py
	|___lip_model/beam_search.py
		|___util/tf_util.py
	|___lip_model.training_graph.py
		|___*
	|___lip_model.modules.py
	|___util/tf_util.py
```

## Credits:

T. Afouras, Deep Lip Reading. 2022. Accessed: Mar. 10, 2022. [Online]. Available: https://github.com/afourast/deep_lip_reading

