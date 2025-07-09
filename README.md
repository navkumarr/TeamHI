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
