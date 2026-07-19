import os
import sys
import torch
import torch.nn as nn
import torch.optim as optim
from torchvision import models

# Add training directory to path to ensure imports work from any working directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from training.dataset import get_dataloader

class DeepfakeClassifier(nn.Module):
    """
    A custom, robust CNN architecture for Deepfake Face Classification.
    Designed for fast processing and high accuracy on face patches.
    Can also wrap torchvision models like ResNet or EfficientNet.
    """
    def __init__(self, model_name="custom", num_classes=2):
        super(DeepfakeClassifier, self).__init__()
        self.model_name = model_name
        
        if model_name == "resnet18":
            try:
                # Try to load pre-trained ResNet18
                self.backbone = models.resnet18(weights=models.ResNet18_Weights.DEFAULT)
                num_ftrs = self.backbone.fc.in_features
                self.backbone.fc = nn.Linear(num_ftrs, num_classes)
            except Exception as e:
                print(f"Warning: Failed to load pretrained resnet18 weights ({e}). Initializing random weights.")
                self.backbone = models.resnet18(weights=None)
                num_ftrs = self.backbone.fc.in_features
                self.backbone.fc = nn.Linear(num_ftrs, num_classes)
        else:
            # Custom CNN architecture
            self.backbone = nn.Sequential(
                nn.Conv2d(3, 32, kernel_size=3, padding=1),
                nn.BatchNorm2d(32),
                nn.ReLU(),
                nn.MaxPool2d(2, 2), # 112x112
                
                nn.Conv2d(32, 64, kernel_size=3, padding=1),
                nn.BatchNorm2d(64),
                nn.ReLU(),
                nn.MaxPool2d(2, 2), # 56x56
                
                nn.Conv2d(64, 128, kernel_size=3, padding=1),
                nn.BatchNorm2d(128),
                nn.ReLU(),
                nn.MaxPool2d(2, 2), # 28x28
                
                nn.Conv2d(128, 256, kernel_size=3, padding=1),
                nn.BatchNorm2d(256),
                nn.ReLU(),
                nn.AdaptiveAvgPool2d((1, 1)), # 256x1x1
                
                nn.Flatten(),
                nn.Linear(256, 128),
                nn.ReLU(),
                nn.Dropout(0.5),
                nn.Linear(128, num_classes)
            )

    def forward(self, x):
        return self.backbone(x)

def train_model(data_dir, model_save_path, epochs=5, batch_size=32, lr=0.001, model_name="custom"):
    """
    Train the Deepfake Classifier on real dataset.
    
    Args:
        data_dir: Path to dataset (should contain train/ and val/ folders)
        model_save_path: Where to save the trained model
        epochs: Number of training epochs
        batch_size: Batch size for training
        lr: Learning rate
        model_name: "custom" or "resnet18"
    """
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"\n{'='*70}")
    print(f"DEEPFAKE DETECTOR TRAINING")
    print(f"{'='*70}")
    print(f"Device: {device}")
    print(f"Dataset: {data_dir}")
    print(f"Model: {model_name}")
    print(f"Epochs: {epochs}, Batch Size: {batch_size}, LR: {lr}\n")
    
    # Dataloaders - load from real dataset
    try:
        train_loader = get_dataloader(data_dir, batch_size=batch_size, split="train", shuffle=True)
        val_loader = get_dataloader(data_dir, batch_size=batch_size, split="val", shuffle=False)
    except Exception as e:
        print(f"ERROR: Failed to load dataset: {e}")
        print(f"\nMake sure your dataset is organized as:")
        print(f"  {data_dir}/")
        print(f"  ├── train/")
        print(f"  │   ├── real/   (100+ real face images)")
        print(f"  │   └── fake/   (100+ deepfake images)")
        print(f"  ├── val/")
        print(f"  │   ├── real/   (50+ real face images)")
        print(f"  │   └── fake/   (50+ deepfake images)")
        return None
    
    # Initialize model
    model = DeepfakeClassifier(model_name=model_name).to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=lr)
    
    best_val_acc = 0.0
    
    for epoch in range(epochs):
        # ============ TRAINING PHASE ============
        model.train()
        running_loss = 0.0
        correct = 0
        total = 0
        
        for batch_idx, (inputs, labels) in enumerate(train_loader):
            inputs, labels = inputs.to(device), labels.to(device)
            
            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            
            running_loss += loss.item() * inputs.size(0)
            _, predicted = outputs.max(1)
            total += labels.size(0)
            correct += predicted.eq(labels).sum().item()
        
        train_loss = running_loss / total
        train_acc = correct / total
        
        # ============ VALIDATION PHASE ============
        val_loss = 0.0
        val_correct = 0
        val_total = 0
        
        model.eval()
        with torch.no_grad():
            for inputs, labels in val_loader:
                inputs, labels = inputs.to(device), labels.to(device)
                outputs = model(inputs)
                loss = criterion(outputs, labels)
                
                val_loss += loss.item() * inputs.size(0)
                _, predicted = outputs.max(1)
                val_total += labels.size(0)
                val_correct += predicted.eq(labels).sum().item()
        
        val_loss = val_loss / max(val_total, 1)
        val_acc = val_correct / max(val_total, 1)
        
        print(f"Epoch {epoch+1:2d}/{epochs} | "
              f"Train Loss: {train_loss:.4f} Acc: {train_acc:.2%} | "
              f"Val Loss: {val_loss:.4f} Acc: {val_acc:.2%}", end="")
        
        # Save best model
        if val_acc >= best_val_acc:
            best_val_acc = val_acc
            os.makedirs(os.path.dirname(model_save_path), exist_ok=True)
            torch.save(model.state_dict(), model_save_path)
            print(f" ✓ SAVED")
        else:
            print()
    
    print(f"\n{'='*70}")
    print(f"Training Complete! Best validation accuracy: {best_val_acc:.2%}")
    print(f"Model saved to: {model_save_path}")
    print(f"{'='*70}\n")
    
    return model

if __name__ == "__main__":
    """
    Train Deepfake Detector with real dataset.
    
    SETUP INSTRUCTIONS:
    1. Create dataset folder: training/data/
    2. Organize as:
       data/
       ├── train/
       │   ├── real/ (100+ real face images)
       │   └── fake/ (100+ deepfake images)
       └── val/
           ├── real/ (50+ real face images)
           └── fake/ (50+ deepfake images)
    3. Run this script
    """
    
    import os
    
    # Dataset path
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    model_save_path = os.path.join(os.path.dirname(__file__), "..", "models", "deepfake_model.pth")
    
    print("\n" + "="*70)
    print("DEEPFAKE DETECTOR - TRAINING SCRIPT")
    print("="*70)
    
    # Check if dataset exists
    if not os.path.exists(data_dir):
        print(f"\n✗ ERROR: Dataset directory not found: {data_dir}")
        print("\nSetup Instructions:")
        print("1. Create the data folder:")
        print(f"   mkdir -p '{data_dir}/train/real'")
        print(f"   mkdir -p '{data_dir}/train/fake'")
        print(f"   mkdir -p '{data_dir}/val/real'")
        print(f"   mkdir -p '{data_dir}/val/fake'")
        print("\n2. Download a dataset from:")
        print("   - FaceForensics++: https://github.com/ondyari/FaceForensics++")
        print("   - DFDC: https://www.kaggle.com/competitions/deepfake-detection-challenge")
        print("   - Celeb-DF: https://github.com/yuezunli/celeb-df")
        print("\n3. Extract face frames and place them in the directories above")
        print("\n4. Run training again")
        exit(1)
    
    # Train model with real data
    train_model(
        data_dir=data_dir,
        model_save_path=model_save_path,
        epochs=10,              # Increase as needed
        batch_size=32,          # Adjust based on GPU memory
        lr=0.001,               # Learning rate
        model_name="custom"     # or "resnet18" for better accuracy
    )
