#!/usr/bin/env python
"""Find correct MediaPipe import paths"""
import sys
sys.path.insert(0, '.')

print('\n' + '='*70)
print('MEDIAPIPE 0.10.35 API INSPECTION')
print('='*70)

import mediapipe as mp

# Check tasks module structure
print('\n[1] mp.tasks attributes:')
print('  ' + ', '.join([x for x in dir(mp.tasks) if not x.startswith('_')]))

# Check vision module
print('\n[2] mp.tasks.python attributes:')
try:
    from mediapipe.tasks import python
    print('  ' + ', '.join([x for x in dir(python) if not x.startswith('_')]))
except:
    print('  (not available)')

# Check vision module
print('\n[3] mp.tasks.python.vision attributes:')
try:
    from mediapipe.tasks.python import vision
    attrs = [x for x in dir(vision) if not x.startswith('_')]
    print('  ' + ', '.join(attrs[:10]) + '...')
except Exception as e:
    print(f'  Error: {e}')

# Check for BaseOptions
print('\n[4] Looking for BaseOptions:')
try:
    from mediapipe.tasks.python import BaseOptions
    print('  Found at: mediapipe.tasks.python.BaseOptions')
except:
    try:
        from mediapipe.tasks.core import BaseOptions
        print('  Found at: mediapipe.tasks.core.BaseOptions')
    except:
        print('  Not found - checking all options')
        from mediapipe.tasks.python import vision
        for attr in dir(vision):
            if 'Option' in attr:
                print(f'    - {attr}')

print('\n' + '='*70)
