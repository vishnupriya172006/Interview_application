# Real Dataset Setup Guide for Deepfake Detection Training

## Overview
Your code was configured to train with **dummy/synthetic data**. This guide shows how to switch to **real deepfake datasets**.

---

## Step 1: Create Dataset Folder Structure

Create this folder structure inside your `training/` directory:

```
training/
├── data/                    ← CREATE THIS FOLDER
│   ├── train/
│   │   ├── real/           ← Real face images (100+ images)
│   │   │   ├── frame_001.jpg
│   │   │   ├── frame_002.jpg
│   │   │   └── ... (more real faces)
│   │   └── fake/           ← Deepfake images (100+ images)
│   │       ├── frame_001.jpg
│   │       ├── frame_002.jpg
│   │       └── ... (more deepfakes)
│   └── val/                ← Validation set (optional but recommended)
│       ├── real/           ← 50+ real face images
│       └── fake/           ← 50+ deepfake images
├── dataset.py
├── train.py
└── (other files)
```

**On Windows PowerShell:**
```powershell
cd training
mkdir data\train\real, data\train\fake, data\val\real, data\val\fake
```

---

## Step 2: Get Real Datasets

Download deepfake datasets from:

### Option 1: **FaceForensics++ (Recommended for beginners)**
- **Download**: https://github.com/ondyari/FaceForensics++
- **Size**: 50-300GB (choose compressed low-quality version first)
- **Content**: Real videos + AI-generated deepfakes
- **How to use**: Extract frames from videos using provided script

### Option 2: **Celeb-DF (Celebrity Deepfakes)**
- **Download**: https://github.com/yuezunli/celeb-df
- **Size**: 120GB
- **Content**: High-quality celebrity deepfakes
- **Already has frames**: Extract real/ and fake/ folders

### Option 3: **DFDC Dataset (Deepfake Detection Challenge)**
- **Download**: https://www.kaggle.com/competitions/deepfake-detection-challenge
- **Size**: 470GB+
- **Content**: Real-world deepfakes

### Option 4: **Quick Start - Use Pre-extracted Dataset**
If you just want to test the pipeline quickly:
- Download FaceForensics++ "Compressed (MP4 format)" - ~15GB instead of 500GB
- Extract 200-300 frames manually into your folders

---

## Step 3: Extract Frames from Videos

If you downloaded video files, extract frames:

### Python Script to Extract Frames:
```python
import cv2
import os
from pathlib import Path

def extract_frames(video_path, output_dir, frame_interval=30):
    """Extract every Nth frame from video"""
    os.makedirs(output_dir, exist_ok=True)
    
    cap = cv2.VideoCapture(video_path)
    frame_count = 0
    saved_count = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        if frame_count % frame_interval == 0:
            frame_path = os.path.join(output_dir, f"frame_{saved_count:06d}.jpg")
            cv2.imwrite(frame_path, frame)
            saved_count += 1
        
        frame_count += 1
    
    cap.release()
    print(f"Extracted {saved_count} frames to {output_dir}")

# Example usage:
extract_frames("real_video.mp4", "training/data/train/real/", frame_interval=30)
extract_frames("deepfake_video.mp4", "training/data/train/fake/", frame_interval=30)
```

---

## Step 4: Verify Dataset is Correct

Check that your dataset is properly organized:

```python
import os

data_dir = "training/data"
for split in ["train", "val"]:
    real_count = len(os.listdir(f"{data_dir}/{split}/real/"))
    fake_count = len(os.listdir(f"{data_dir}/{split}/fake/"))
    print(f"{split.upper()} - Real: {real_count}, Fake: {fake_count}")
```

**Expected output:**
```
TRAIN - Real: 150, Fake: 150
VAL - Real: 50, Fake: 50
```

---

## Step 5: Train with Real Data

Now run training with real dataset:

```bash
cd Interview_application
python -m training.train
```

**What to expect:**
- ✓ Dataset loading should show actual image counts (not "generating synthetic samples")
- ✓ Training should take minutes (not seconds)
- ✓ Model accuracy should improve with each epoch

---

## Code Changes Made

### Changes to `dataset.py`:
- ✅ **Removed**: `_generate_synthetic_samples()` method
- ✅ **Removed**: `synthetic_count` parameter
- ✅ **Kept**: `_load_dataset()` - loads real images from folders
- ✅ **Added**: Better logging showing real image counts

### Changes to `train.py`:
- ✅ **Removed**: `synthetic_count=0` parameter from `train_model()`
- ✅ **Removed**: Conditional dummy data generation
- ✅ **Updated**: `__main__` section now checks for real dataset
- ✅ **Added**: Setup instructions if dataset not found
- ✅ **Improved**: Better logging and error messages

---

## Troubleshooting

### "No images found in" error
**Problem**: Dataset folder exists but is empty
**Solution**:
```bash
# Check what's in your folders
dir training\data\train\real
dir training\data\train\fake
```
Make sure you have at least 50 images in each folder.

### "JPEG data is truncated" error
**Problem**: Some images are corrupted
**Solution**: Remove corrupted images:
```python
from PIL import Image
import os

def remove_corrupted_images(folder_path):
    for filename in os.listdir(folder_path):
        if filename.endswith(('.jpg', '.jpeg', '.png')):
            try:
                img = Image.open(os.path.join(folder_path, filename))
                img.verify()
            except:
                os.remove(os.path.join(folder_path, filename))
                print(f"Removed corrupted: {filename}")
```

### Out of Memory (OOM) error
**Problem**: GPU doesn't have enough memory
**Solution**: Reduce batch size in `train.py`:
```python
train_model(
    ...
    batch_size=8,  # Reduce from 32
    ...
)
```

### Very slow training
**Problem**: Using CPU instead of GPU
**Solution**: Check GPU availability:
```python
import torch
print(torch.cuda.is_available())  # Should print True
print(torch.cuda.get_device_name(0))  # GPU name
```

---

## Advanced: Using Pre-trained Models

For better accuracy without training from scratch:

```python
# In train.py __main__ section:
train_model(
    data_dir=data_dir,
    model_save_path=model_save_path,
    epochs=5,           # Fewer epochs needed
    batch_size=32,
    lr=0.0001,          # Lower learning rate
    model_name="resnet18"  # Pre-trained model
)
```

---

## Next Steps

1. **Create** the `training/data/` folder structure
2. **Download** a dataset from FaceForensics++ or Celeb-DF
3. **Extract** frames into real/ and fake/ folders (100+ each)
4. **Run** `python -m training.train`
5. **Monitor** training progress - validation accuracy should improve

Your model will be saved to: `models/deepfake_model.pth`

---

## Questions?

If you have questions about:
- **Dataset download**: Check the official GitHub repos (links above)
- **Frame extraction**: The Python script in Step 3 works for any video format
- **Training issues**: Check the Troubleshooting section
