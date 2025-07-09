## Installation Guide: CUDA-enabled PyTorch, Torchaudio, Torchvision & PySide6

SAMURAI builds on top of **SAM 2**, and to leverage GPU acceleration and the GUI demo components, you’ll need to install compatible versions of `torch`, `torchaudio`, `torchvision` with CUDA support, along with `PySide6` for Qt-based UIs.

This guide assumes you already have `python >= 3.10` and a CUDA-capable NVIDIA GPU.

### 1️⃣ Install CUDA-enabled PyTorch + TorchVision + TorchAudio

Visit the official [PyTorch Get Started page](https://pytorch.org/get-started/locally/) to determine the exact command matching your OS, Python, CUDA version.

Here’s an example for **CUDA 12.1** (recommended if you have CUDA 12.1 installed):

```bash
pip install torch==2.3.1 torchvision==0.18.1 torchaudio==2.3.1 --index-url https://download.pytorch.org/whl/cu121
```

For other CUDA versions:

* CUDA 12.0: use `cu120`
* CUDA 11.8: use `cu118`

Example for CUDA 11.8:

```bash
pip install torch==2.3.1 torchvision==0.18.1 torchaudio==2.3.1 --index-url https://download.pytorch.org/whl/cu118
```

> ⚠️ Check your local CUDA version with:
>
> ```bash
> nvcc --version
> ```

You can also install the CPU-only version if you don’t have a GPU:

```bash
pip install torch==2.3.1 torchvision==0.18.1 torchaudio==2.3.1
```

---

### 2️⃣ Install PySide6

For the Qt-based UI components, install `PySide6`:

```bash
pip install PySide6
```

---

### 3️⃣ Install SAMURAI & Dependencies

Then follow the repository’s own install instructions:

```bash
cd sam2
pip install -e .
pip install -e ".[notebooks]"
```

And the additional Python packages required:

```bash
pip install matplotlib==3.7 tikzplotlib jpeg4py opencv-python lmdb pandas scipy loguru
```

---

### 4️⃣ Download SAM 2.1 Checkpoints

```bash
cd checkpoints
./download_ckpts.sh
cd ..
```

---

✅ After these steps, you’ll have:

* CUDA-enabled `torch`, `torchvision`, `torchaudio`
* `PySide6` installed
* All SAMURAI dependencies installed and ready to run

Continue with the [Getting Started](#getting-started) section of this README for data preparation and running inference.

## Getting Started

#### SAMURAI Installation 

SAM 2 needs to be installed first before use. The code requires python>=3.10, as well as torch>=2.3.1 and torchvision>=0.18.1. Please follow the instructions [here](https://github.com/facebookresearch/sam2?tab=readme-ov-file) to install both PyTorch and TorchVision dependencies. You can install **the SAMURAI version** of SAM 2 on a GPU machine using:

cd sam2
pip install -e .
pip install -e ".[notebooks]"



Please see [INSTALL.md](https://github.com/facebookresearch/sam2/blob/main/INSTALL.md) from the original SAM 2 repository for FAQs on potential issues and solutions.

Install other requirements:

pip install matplotlib==3.7 tikzplotlib jpeg4py opencv-python lmdb pandas scipy loguru



#### SAM 2.1 Checkpoint Download

cd checkpoints && \
./download_ckpts.sh && \
cd ..



#### Data Preparation

Please prepare the data in the following format:

data/LaSOT
├── airplane/
│   ├── airplane-1/
│   │   ├── full_occlusion.txt
│   │   ├── groundtruth.txt
│   │   ├── img
│   │   ├── nlp.txt
│   │   └── out_of_view.txt
│   ├── airplane-2/
│   ├── airplane-3/
│   ├── ...
├── basketball
├── bear
├── bicycle
...
├── training_set.txt
└── testing_set.txt



#### Main Inference

python scripts/main_inference.py



## Demo on Custom Video

To run the demo with your custom video or frame directory, use the following examples:

**Note:** The .txt file contains a single line with the bounding box of the first frame in x,y,w,h format while the SAM 2 takes x1,y1,x2,y2 format as bbox input.

### Input is Video File

python scripts/demo.py --video_path <your_video.mp4> --txt_path <path_to_first_frame_bbox.txt>



### Input is Frame Folder

# Only JPG images are supported
python scripts/demo.py --video_path <your_frame_directory> --txt_path <path_to_first_frame_bbox.txt>



## FAQs
**Question 1:** Does SAMURAI need training? [issue 34](https://github.com/yangchris11/samurai/issues/34)

**Answer 1:** Unlike real-life samurai, the proposed samurai do not require additional training. It is a zero-shot method, we directly use the weights from SAM 2.1 to conduct VOT experiments. The Kalman filter is used to estimate the current and future state (bounding box location and scale in our case) of a moving object based on measurements over time, it is a common approach that had been adopted in the field of tracking for a long time, which does not require any training. Please refer to code for more detail.

**Question 2:** Does SAMURAI support streaming input (e.g. webcam)?

**Answer 2:** Not yet. The existing code doesn't support live/streaming video as we inherit most of the codebase from the amazing SAM 2. Some discussion that you might be interested in: facebookresearch/sam2#90, facebookresearch/sam2#388 (comment).

**Question 3:** How to use SAMURAI in longer video?

**Answer 3:** See the discussion from sam2 https://github.com/facebookresearch/sam2/issues/264.

**Question 4:** How do you run the evaluation on the VOT benchmarks?

**Answer 4:** For LaSOT, LaSOT-ext, OTB, NFS please refer to the [issue 74](https://github.com/yangchris11/samurai/issues/74) for more details. For GOT-10k-test and TrackingNet, please refer to the official portal for submission.

## Acknowledgment

SAMURAI is built on top of [SAM 2](https://github.com/facebookresearch/sam2?tab=readme-ov-file) by Meta FAIR.

The VOT evaluation code is modifed from [VOT Toolkit](https://github.com/votchallenge/toolkit) by Luka Čehovin Zajc.
