# Eyeudio

## Team Members:
* Frank Cai    (frank_cai@berkeley.edu)
* Yiqing Tao   (yiqingtao73@berkeley.edu)
* Jordan Wong  (jotywong@berkeley.edu)
* Ananth Goyal (ananthgoyal@berkeley.edu)
* Kanglan Tang (kanglan_tang@berkeley.edu)
* Vincent Wang (vincent-wang@berkeley.edu)
* Yaowei Ma    (yaowei_ma@berkeley.edu)
* Hoang Nguyen (hoang_nguyen@berkeley.edu)

## Setup environment (Windows 10)

### Step 1: Install Anaconda: https://docs.anaconda.com/anaconda/install/index.html

### Step 2: Create and activate a Python 3.7.7 environment, install packages
```bash
conda create -n eyeudio_env_3.7.7 python=3.7.7
conda activate eyeudio_env_3.7.7

# For Lip Preprocessing/Deep Lip Reading
conda install -c conda-forge opencv=4.5.3 dlib=19.22.0 sk-video=1.1.10
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

# For Kivy (GUI)
python -m pip install "kivy[base]" kivy_examples

# For Speech Recognition/Syntax Checker
python -m pip install SpeechRecognition
python -m pip install pyautogui
python -m pip install osascript
python -m pip install fuzzywuzzy
conda install -c conda-forge python-levenshtein
python -m pip install ./PyAudio-0.2.11-cp37-cp37m-win_amd64.whl

# For Eye Tracking
conda install pytorch torchvision torchaudio cpuonly -c pytorch
python -m pip install omegaconf
python -m pip install face-alignment
python -m pip install fvcore
python -m pip install pandas
python -m pip install pyyaml
python -m pip install scipy
python -m pip install tensorboardX
python -m pip install yacs
python -m pip install mediapipe
python -m pip install timm
python -m pip install playsound==1.2.2
# pip install -r requirements.txt
```

**Note:** We need to activate this environment by running `conda activate eyeudio_env_3.7.7` every time opening up a new terminal.

**Note:** This is the installation guide for Windows 10.

## Credits:

[1] Shinji Watanabe, Takaaki Hori, Shigeki Karita, Tomoki Hayashi, Jiro Nishitoba, Yuya
Unno, Nelson Enrique Yalta Soplin, Jahn Heymann, Matthew Wiesner, Nanxin Chen,
Adithya Renduchintala, and Tsubasa Ochiai. ESPnet: End-to-end speech processing
toolkit. In Interspeech 2018. ISCA, sep 2018. doi: 10.21437/interspeech.2018-1456.
URL https://doi.org/10.21437%2Finterspeech.2018-1456.

[2] Siddhant Arora, Siddharth Dalmia, Pavel Denisov, Xuankai Chang, Yushi Ueda, Yifan
Peng, Yuekai Zhang, Sujay Kumar, Karthik Ganesan, Brian Yan, et al. Espnet-
slu: Advancing spoken language understanding through espnet. arXiv preprint
arXiv:2111.14706, 2021.

[3] Xucong Zhang, Yusuke Sugano, Mario Fritz, and Andreas Bulling. Mpiigaze: Real-
world dataset and deep appearance-based gaze estimation. IEEE transactions on
pattern analysis and machine intelligence, 41(1):162–175, 2017.

[4] Xucong Zhang, Seonwook Park, Thabo Beeler, Derek Bradley, Siyu Tang, and Otmar
Hilliges. Eth-xgaze: A large scale dataset for gaze estimation under extreme head
pose and gaze variation. In European Conference on Computer Vision, pages 365–381.
Springer, 2020.

[5] Grace Tilton. Computer vision lip reading. Dec 2019. URL http://cs229.
stanford.edu/proj2019aut/data/assignment_308832_raw/26646023.pdf.

[6] T. Afouras, J. S. Chung, and A. Zisserman. Deep lip reading: a comparison of models
and an online application. In INTERSPEECH, 2018.

[7] J. S. Chung and A. Zisserman. Lip reading in the wild. In Asian Conference on
Computer Vision, 2016.

[8] J. S. Chung, A. Senior, O. Vinyals, and A. Zisserman. Lip reading sentences in the
wild. In IEEE Conference on Computer Vision and Pattern Recognition, 2017

