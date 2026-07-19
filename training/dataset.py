import os
import torch
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms
from PIL import Image

class DeepfakeDataset(Dataset):
    """
    PyTorch Dataset for Deepfake Detection.
    Loads real and fake face images from organized folder structure.
    
    Expected directory structure:
        data/
        ├── train/
        │   ├── real/ (real face images)
        │   └── fake/ (deepfake/manipulated images)
        ├── val/
        │   ├── real/
        │   └── fake/
        └── test/
            ├── real/
            └── fake/
    """
    def __init__(self, data_dir, split="train", transform=None):
        self.data_dir = data_dir
        self.split = split
        self.samples = []
        
        # Image preprocessing pipeline
        self.transform = transform or transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
        
        self._load_dataset()
            
    def _load_dataset(self):
        """
        Scans data_dir for real and fake face frames.
        Labels: 0 = Real, 1 = Fake/Deepfake
        """
        real_dir = os.path.join(self.data_dir, self.split, "real")
        fake_dir = os.path.join(self.data_dir, self.split, "fake")
        
        # Load real images
        if os.path.exists(real_dir):
            for filename in os.listdir(real_dir):
                if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                    self.samples.append((os.path.join(real_dir, filename), 0))  # 0 = Real
            print(f"[{self.split.upper()}] Loaded {len([s for s in self.samples if s[1]==0])} real images")
        else:
            print(f"[WARNING] Real directory not found: {real_dir}")
                    
        # Load fake images
        if os.path.exists(fake_dir):
            fake_count_before = len([s for s in self.samples if s[1]==1])
            for filename in os.listdir(fake_dir):
                if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                    self.samples.append((os.path.join(fake_dir, filename), 1))  # 1 = Fake
            fake_count_after = len([s for s in self.samples if s[1]==1])
            print(f"[{self.split.upper()}] Loaded {fake_count_after - fake_count_before} fake images")
        else:
            print(f"[WARNING] Fake directory not found: {fake_dir}")
        
        total = len(self.samples)
        real_count = len([s for s in self.samples if s[1]==0])
        fake_count = len([s for s in self.samples if s[1]==1])
        print(f"[{self.split.upper()}] TOTAL: {total} samples (Real: {real_count}, Fake: {fake_count})")
        
        if total == 0:
            raise ValueError(f"No images found in {self.data_dir}/{self.split}/. Please check your dataset path.")

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        img_path, label = self.samples[idx]
        
        try:
            image = Image.open(img_path).convert("RGB")
        except Exception as e:
            print(f"Error loading image {img_path}: {e}")
            # Return black image as fallback
            image = Image.new("RGB", (224, 224), color=(0, 0, 0))
            
        if self.transform:
            image = self.transform(image)
            
        return image, torch.tensor(label, dtype=torch.long)


def get_dataloader(data_dir, batch_size=32, split="train", shuffle=True, num_workers=0):
    """
    Create a DataLoader for the specified dataset split.
    
    Args:
        data_dir: Path to dataset root (containing train/val/test folders)
        batch_size: Batch size for training
        split: "train", "val", or "test"
        shuffle: Whether to shuffle the data
        num_workers: Number of CPU workers for data loading
    """
    dataset = DeepfakeDataset(data_dir, split=split)
    return DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=shuffle,
        num_workers=num_workers
    )


if __name__ == "__main__":
    # Test script - requires actual dataset
    print("Testing dataset loader...")
    
    # Update path to your actual dataset
    data_path = os.path.join(os.path.dirname(__file__), "data")
    
    if os.path.exists(data_path):
        loader = get_dataloader(data_path, batch_size=4, split="train")
        for imgs, labels in loader:
            print(f"✓ Batch loaded successfully!")
            print(f"  Image shape: {imgs.shape}")
            print(f"  Labels: {labels}")
            break
    else:
        print(f"[ERROR] Dataset not found at {data_path}")
        print(f"[INFO] Create the dataset structure:")
        print(f"  {data_path}/train/real/")
        print(f"  {data_path}/train/fake/")
        print(f"  {data_path}/val/real/")
        print(f"  {data_path}/val/fake/")
