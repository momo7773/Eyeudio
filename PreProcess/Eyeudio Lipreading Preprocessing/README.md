# How to run:
1) Install packages using conda
conda env create -f environment.yml

2) Ensure environment is now activated and installed properly
conda activate lipenv
conda env list

3) Run lip preprocessing
python RecordVideoAndCrop.py

# Commands to originally create the Anaconda package:
conda create -n lipenv python=3.6.8
conda install -c conda-forge opencv=4.5.3 dlib=19.22.0 sk-video=1.1.10