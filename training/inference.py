import os
import sys
import cv2
from torchvision import transforms
from PIL import Image

# Add training directory to path to ensure imports work from any working directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class DeepfakeDetector:
    """
    Inference helper that loads the deepfake classifier and runs prediction on frames.
    Integrates OpenCV Haar Cascade to crop faces from full video frames automatically.
    """
    def __init__(self, model_path, model_name="custom"):
        import torch
        from training.train import DeepfakeClassifier

        self.torch = torch
        self.device = self.torch.device("cuda" if self.torch.cuda.is_available() else "cpu")
        self.model = DeepfakeClassifier(model_name=model_name)
        
        if os.path.exists(model_path):
            self.model.load_state_dict(torch.load(model_path, map_location=self.device))
            print(f"Loaded Deepfake Detector weights from: {model_path}")
        else:
            print(f"Warning: Deepfake model weights file not found at: {model_path}. Model will run with random weights.")
            
        self.model.to(self.device)
        self.model.eval()
        
        # Load OpenCV Haar cascade face detector
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
        # Transform pipeline
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])

    def detect_face_and_predict(self, frame):
        """
        Processes a full BGR camera frame (OpenCV format).
        1. Detects face.
        2. Crops and pre-processes.
        3. Predicts fake probability.
        Returns: (probability_fake, face_coords)
        - probability_fake: Float (0.0 to 1.0)
        - face_coords: (x, y, w, h) of the detected face, or None
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60))
        
        if len(faces) == 0:
            return 0.0, None
            
        # Take the largest face
        faces = sorted(faces, key=lambda f: f[2] * f[3], reverse=True)
        (x, y, w, h) = faces[0]
        
        # Crop face
        face_img = frame[y:y+h, x:x+w]
        
        # Convert BGR to RGB
        face_img_rgb = cv2.cvtColor(face_img, cv2.COLOR_BGR2RGB)
        
        # Run inference
        prob_fake = self.predict_face(face_img_rgb)
        
        return prob_fake, (int(x), int(y), int(w), int(h))

    def predict_face(self, face_rgb_image):
        """
        Accepts a cropped face image (numpy array RGB) and outputs the probability of being fake.
        """
        pil_img = Image.fromarray(face_rgb_image)
        input_tensor = self.transform(pil_img).unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            outputs = self.model(input_tensor)
            probs = torch.softmax(outputs, dim=1)
            fake_prob = probs[0, 1].item() # Class 1 is Fake
            
        return fake_prob

if __name__ == "__main__":
    # Quick visual check / mock
    detector = DeepfakeDetector("../models/deepfake_model.pth")
    # Make a dummy face frame (random face)
    import numpy as np
    dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    # Draw a mock square where the "face" would be
    cv2.rectangle(dummy_frame, (200, 100), (400, 300), (0, 255, 0), -1)
    
    score, bbox = detector.detect_face_and_predict(dummy_frame)
    print(f"Pred Score: {score}, Bounding box: {bbox}")
