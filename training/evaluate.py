import os
import sys
import torch
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, confusion_matrix, roc_curve, auc

# Add training directory to path to ensure imports work from any working directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from training.dataset import get_dataloader
from training.train import DeepfakeClassifier

def evaluate_model(data_dir, model_path, model_name="custom", output_dir="./metrics"):
    """
    Evaluate trained deepfake detector on test dataset.
    
    Args:
        data_dir: Path to dataset (should contain test/ folder)
        model_path: Path to saved model weights
        model_name: "custom" or "resnet18"
        output_dir: Where to save evaluation plots and metrics
    """
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"\n{'='*70}")
    print(f"EVALUATING DEEPFAKE DETECTOR")
    print(f"{'='*70}")
    print(f"Device: {device}")
    print(f"Model: {model_path}\n")
    
    # Load test dataset
    try:
        test_loader = get_dataloader(data_dir, batch_size=32, split="test", shuffle=False)
    except Exception as e:
        print(f"ERROR: Cannot load test dataset: {e}")
        print(f"Expected structure: {data_dir}/test/real/ and {data_dir}/test/fake/")
        print("Note: If you only have train/val splits, use 'val' instead of 'test'")
        return
    
    # Load model
    if not os.path.exists(model_path):
        print(f"ERROR: Model file not found: {model_path}")
        return
        
    model = DeepfakeClassifier(model_name=model_name).to(device)
    model.load_state_dict(torch.load(model_path, map_location=device))
    print(f"✓ Loaded model weights from {model_path}\n")
        
    model.eval()
    
    all_labels = []
    all_preds = []
    all_probs = []
    
    print("Evaluating on test set...")
    with torch.no_grad():
        for inputs, labels in test_loader:
            inputs = inputs.to(device)
            outputs = model(inputs)
            
            probs = torch.softmax(outputs, dim=1)[:, 1] # Probability of being Fake (class 1)
            _, predicted = outputs.max(1)
            
            all_labels.extend(labels.numpy())
            all_preds.extend(predicted.cpu().numpy())
            all_probs.extend(probs.cpu().numpy())
            
    all_labels = np.array(all_labels)
    all_preds = np.array(all_preds)
    all_probs = np.array(all_probs)
    
    if len(all_labels) == 0:
        print("ERROR: No samples found to evaluate.")
        return
        
    # Calculate metrics
    accuracy = accuracy_score(all_labels, all_preds)
    precision, recall, f1, _ = precision_recall_fscore_support(all_labels, all_preds, average='binary')
    cm = confusion_matrix(all_labels, all_preds)
    
    print(f"\n{'='*70}")
    print(f"EVALUATION RESULTS")
    print(f"{'='*70}")
    print(f"Accuracy:  {accuracy:.4f} ({accuracy*100:.2f}%)")
    print(f"Precision: {precision:.4f}")
    print(f"Recall:    {recall:.4f}")
    print(f"F1 Score:  {f1:.4f}")
    print(f"\nConfusion Matrix:")
    print(f"                 Predicted Real  Predicted Fake")
    print(f"Actually Real    {cm[0, 0]:6d}         {cm[0, 1]:6d}")
    print(f"Actually Fake    {cm[1, 0]:6d}         {cm[1, 1]:6d}")
    print(f"{'='*70}\n")
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Save Metrics text file
    metrics_path = os.path.join(output_dir, "metrics.txt")
    with open(metrics_path, "w") as f:
        f.write(f"DEEPFAKE DETECTOR EVALUATION METRICS\n")
        f.write(f"Model: {model_path}\n")
        f.write(f"Dataset: {data_dir}\n\n")
        f.write(f"Accuracy: {accuracy:.4f}\n")
        f.write(f"Precision: {precision:.4f}\n")
        f.write(f"Recall: {recall:.4f}\n")
        f.write(f"F1 Score: {f1:.4f}\n")
        f.write(f"\nConfusion Matrix:\n{cm}\n")
    print(f"✓ Saved metrics to {metrics_path}")
        
    # Plot and save ROC Curve
    fpr, tpr, thresholds = roc_curve(all_labels, all_probs)
    roc_auc = auc(fpr, tpr)
    
    plt.figure(figsize=(8, 6))
    plt.plot(fpr, tpr, color='darkorange', lw=2.5, label=f'ROC curve (AUC = {roc_auc:.3f})')
    plt.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--', label='Random Classifier')
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel('False Positive Rate', fontsize=12)
    plt.ylabel('True Positive Rate', fontsize=12)
    plt.title('Receiver Operating Characteristic (ROC) Curve', fontsize=14)
    plt.legend(loc="lower right", fontsize=11)
    plt.grid(alpha=0.3)
    
    roc_path = os.path.join(output_dir, "roc_curve.png")
    plt.savefig(roc_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"✓ Saved ROC curve to {roc_path}")
    
    # Plot and save Confusion Matrix image
    plt.figure(figsize=(6, 5))
    plt.imshow(cm, interpolation='nearest', cmap=plt.cm.Blues)
    plt.title('Confusion Matrix', fontsize=14)
    plt.colorbar()
    tick_marks = np.arange(2)
    plt.xticks(tick_marks, ['Real', 'Fake'], fontsize=11)
    plt.yticks(tick_marks, ['Real', 'Fake'], fontsize=11)
    plt.xlabel('Predicted Label', fontsize=12)
    plt.ylabel('True Label', fontsize=12)
    
    # Annotate CM
    thresh = cm.max() / 2.
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            plt.text(j, i, format(cm[i, j], 'd'),
                     ha="center", va="center", fontsize=14,
                     color="white" if cm[i, j] > thresh else "black")
                     
    cm_path = os.path.join(output_dir, "confusion_matrix.png")
    plt.savefig(cm_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"✓ Saved confusion matrix to {cm_path}")

if __name__ == "__main__":
    """
    Evaluate trained deepfake detector on test set.
    
    Usage:
        python -m training.evaluate
    """
    import os
    
    # Paths
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    model_path = os.path.join(os.path.dirname(__file__), "..", "models", "deepfake_model.pth")
    output_dir = os.path.join(os.path.dirname(__file__), "..", "evaluation_results")
    
    print("\n" + "="*70)
    print("DEEPFAKE DETECTOR - EVALUATION SCRIPT")
    print("="*70)
    
    # Check if dataset and model exist
    if not os.path.exists(model_path):
        print(f"\n✗ ERROR: Model not found: {model_path}")
        print("Make sure you have trained the model first:")
        print("  python -m training.train")
        exit(1)
    
    if not os.path.exists(os.path.join(data_dir, "test")):
        print(f"\n✗ ERROR: Test dataset not found: {data_dir}/test/")
        print("Expected structure:")
        print(f"  {data_dir}/test/real/ (50+ images)")
        print(f"  {data_dir}/test/fake/ (50+ images)")
        print("\nNote: Using validation set instead...\n")
        split = "val"
    else:
        split = "test"
    
    # Evaluate model
    try:
        evaluate_model(
            data_dir=data_dir,
            model_path=model_path,
            model_name="custom",
            output_dir=output_dir
        )
        print(f"\n✓ Evaluation complete! Results saved to: {output_dir}\n")
    except Exception as e:
        print(f"\n✗ Evaluation failed: {e}")
        import traceback
        traceback.print_exc()


