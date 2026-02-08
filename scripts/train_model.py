"""
Script to train the risk prediction model
Run this from the project root: python scripts/train_model.py
"""

import sys
sys.path.insert(0, '.')

from ai.risk_model import train_risk_model

if __name__ == '__main__':
    print("=" * 50)
    print("PATIENT RISK PREDICTION MODEL TRAINING")
    print("=" * 50)
    success = train_risk_model()
    print("=" * 50)
    if success:
        print("✅ Model training completed successfully!")
    else:
        print("❌ Model training failed!")
    print("=" * 50)
