# (DEPRECATED)

# How to run (Windows):
1. Install packages using conda
conda env create -f environmentALL.yml

    - note: environment.yml contains just the necessary packages **without** installing dependencies. environmentALL.yml has only been tested on Windows so far.

2. Ensure environment is now activated and installed properly
conda activate lipenv
conda env list

3. Run lip preprocessing
python RecordVideoAndCrop.py

# How to run (Mac):
[Instructions](https://docs.google.com/document/d/1Wr_Pq5GcMtT3JYjCo5KyYcI4_3sZE7bqeZrEZnSiahQ/edit)

# Commands to originally create the Anaconda package:
conda create -n lip_env_3.7.7 python=3.7.7
conda install -c conda-forge opencv=4.5.3 dlib=19.22.0 sk-video=1.1.10
