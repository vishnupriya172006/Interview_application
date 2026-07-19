#!/usr/bin/env python
"""Find MediaPipe model path"""
import sys
sys.path.insert(0, '.')

print('\n' + '='*70)
print('MEDIAPIPE MODEL PATH DETECTION')
print('='*70)

import mediapipe as mp

# Check if there's a bundled model
print('\n[1] Checking MediaPipe package structure...')
import mediapipe
mp_path = mediapipe.__path__[0] if hasattr(mediapipe, '__path__') else 'unknown'
print(f'  MediaPipe package path: {mp_path}')

# List face_landmarker models
import os
model_path = os.path.join(mp_path, 'tasks', 'python', 'vision', 'face_landmarker_models')
print(f'\n[2] Checking for bundled models at: {model_path}')
if os.path.exists(model_path):
    print(f'  Models found:')
    for f in os.listdir(model_path):
        if f.endswith('.tflite'):
            full_path = os.path.join(model_path, f)
            print(f'    - {f}')
else:
    print(f'  No bundled models found')

# Check alternative paths
print(f'\n[3] Checking alternative paths...')
alt_paths = [
    os.path.join(mp_path, 'tasks', 'face_landmarker_models'),
    os.path.join(mp_path, 'models'),
]
for path in alt_paths:
    if os.path.exists(path):
        print(f'  Found at: {path}')
        for f in os.listdir(path):
            print(f'    - {f}')

print('\n' + '='*70)
