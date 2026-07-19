#!/usr/bin/env python
"""Test MediaPipe import paths"""
import sys
sys.path.insert(0, '.')

print('\n' + '='*70)
print('TESTING MEDIAPIPE IMPORT')
print('='*70)

# Test 1: Direct mediapipe import
print('\n[TEST 1] Direct mediapipe import...')
try:
    import mediapipe as mp
    version = mp.__version__ if hasattr(mp, '__version__') else 'unknown'
    print(f'  OK mediapipe version: {version}')
    print(f'  OK Has solutions: {hasattr(mp, "solutions")}')
    attrs = [x for x in dir(mp) if not x.startswith('_')]
    print(f'  OK Public attributes: {attrs[:5]}...')
except Exception as e:
    print(f'  FAIL: {e}')

# Test 2: Try to import tasks
print('\n[TEST 2] Try tasks.python.vision...')
try:
    from mediapipe.tasks.python import vision
    print(f'  OK vision module imported')
except Exception as e:
    print(f'  FAIL: {e}')

# Test 3: Try legacy solutions
print('\n[TEST 3] Try solutions.face_mesh...')
try:
    import mediapipe as mp
    fm = mp.solutions.face_mesh
    print(f'  OK face_mesh imported')
    print(f'  OK FaceMesh class available: {hasattr(fm, "FaceMesh")}')
except Exception as e:
    print(f'  FAIL: {e}')

print('\n' + '='*70)
