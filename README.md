## Pytorch implementation of Learning-based Video Motion Magnification
### 2021 / 02 / 16 / winter_internship

Most of the source code was referenced and copied in the materials.
1. https://github.com/12dmodel/deep_motion_mag
2. https://github.com/Fangyh09/Image2LMDB
3. https://pytorch.org/tutorials/

## Installation
    conda create -n name python==3.6.9
    pip install ffmpeg==1.4
    pip install -r requirements.txt
This code has been tested with torch 1.7.1, torchvision 0.8.2, CUDA 10.2, conda 4.6.9, python 3.6.9, Ubuntu 16.04.

## Inference
Train

        python main.py --phase="train" --checkpoint_path="/home/urp1/model/epoch1_64_iter_22000.tar" --data_path="/home/urp1/train/data"

Inference

        python main.py --phase="play" --checkpoint_path="/home/urp1/model/epoch1_64_iter_22000.tar" --vid_dir="/home/urp1/test/video" --out_dir="/home/urp1/test/video/result" --velocity_mag

Inference with temporal filtered

        python main.py --phase="play_temporal" --checkpoint_path="/home/urp1/model/epoch1_64_iter_22000.tar" --vid_dir="/home/urp1/test/video" --out_dir="/home/urp1/test/video/temporal" --amplification_factor=20 --fl=0.04 --fh=0.4 --flss=30 --n_filter_tap=2 --filter_type="differenceOfIIR"

## Citation
        @article{oh2018learning,
          title={Learning-based Video Motion Magnification},
          author={Oh, Tae-Hyun and Jaroensri, Ronnachai and Kim, Changil and Elgharib, Mohamed and Durand, Fr{\'e}do and Freeman, William T and Matusik, Wojciech},
          journal={arXiv preprint arXiv:1804.02684},
          year={2018}
        }
