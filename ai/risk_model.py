"""
Risk Score Model Training and Prediction
Trains a machine learning model to predict patient risk based on lab values
"""

import pandas as pd
import numpy as np
import pickle
import os
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from database.db import get_connection as get_db
from datetime import datetime


MODEL_PATH = "ai/models/risk_model.pkl"
SCALER_PATH = "ai/models/scaler.pkl"
MODELS_DIR = "ai/models"


def ensure_models_dir():
    """Create models directory if it doesn't exist"""
    os.makedirs(MODELS_DIR, exist_ok=True)


def prepare_training_data():
    """
    Fetch lab data from database and prepare features for model training
    Returns: (X, y) where X is features and y is risk labels
    """
    conn = get_db()
    cur = conn.cursor()

    # Get all patient lab records with risk status
    cur.execute("""
        SELECT
            subject_id,
            test_name,
            value,
            status
        FROM lab_interpretations
        WHERE value IS NOT NULL AND status IS NOT NULL
    """)

    records = cur.fetchall()
    conn.close()

    if not records:
        raise ValueError("No training data available in database")

    # Convert to DataFrame
    df = pd.DataFrame([dict(r) for r in records])

    # Pivot to get features per patient
    pivot_data = []

    for subject_id in df['subject_id'].unique():
        patient_data = df[df['subject_id'] == subject_id]

        # Get patient features
        features = {'subject_id': subject_id}

        # Add lab test values as features
        for _, row in patient_data.iterrows():
            test_name = row['test_name'].lower().replace(' ', '_').replace('-', '_')
            features[f'{test_name}_value'] = row['value']

        # Determine risk label from status
        # CRITICAL = 2, ABNORMAL = 1, NORMAL = 0
        max_risk = 0
        if 'CRITICAL' in patient_data['status'].values:
            max_risk = 2
        elif 'ABNORMAL' in patient_data['status'].values:
            max_risk = 1

        features['risk_level'] = max_risk
        pivot_data.append(features)

    training_df = pd.DataFrame(pivot_data)

    # Fill missing values with median
    numeric_cols = training_df.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        if col != 'subject_id' and col != 'risk_level':
            training_df[col].fillna(training_df[col].median(), inplace=True)

    # Remove rows with missing values
    training_df = training_df.dropna()

    if len(training_df) < 2:
        raise ValueError("Insufficient training data after preprocessing")

    # Prepare X and y
    feature_cols = [col for col in training_df.columns
                    if col not in ['subject_id', 'risk_level']]
    X = training_df[feature_cols].values
    y = training_df['risk_level'].values

    return X, y, feature_cols, training_df


def train_risk_model():
    """
    Train the risk prediction model
    """
    ensure_models_dir()

    print("📊 Preparing training data...")
    try:
        X, y, feature_cols, training_df = prepare_training_data()
    except ValueError as e:
        print(f"❌ Error: {e}")
        return False

    print(f"✓ Training data prepared: {len(X)} samples, {len(feature_cols)} features")

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # Ensure all 3 classes are represented
    unique_classes = np.unique(y_train)
    if len(unique_classes) < 3:
        print(f"⚠️  Warning: Training data has only {len(unique_classes)} risk classes")
        print(f"   Classes found: {unique_classes}")
        print("   Using class_weight='balanced_subsample' for robustness")

    # Train Random Forest model
    print("🤖 Training Random Forest model...")
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        min_samples_split=5,
        random_state=42,
        n_jobs=-1,
        class_weight='balanced_subsample'
    )

    model.fit(X_train_scaled, y_train)

    # Evaluate
    train_score = model.score(X_train_scaled, y_train)
    test_score = model.score(X_test_scaled, y_test)

    print(f"✓ Training accuracy: {train_score:.2%}")
    print(f"✓ Testing accuracy: {test_score:.2%}")

    # Save model and scaler
    with open(MODEL_PATH, 'wb') as f:
        pickle.dump(model, f)

    with open(SCALER_PATH, 'wb') as f:
        pickle.dump(scaler, f)

    # Save feature names for later use
    with open('ai/models/feature_cols.pkl', 'wb') as f:
        pickle.dump(feature_cols, f)

    print(f"✓ Model saved to {MODEL_PATH}")
    print(f"✓ Scaler saved to {SCALER_PATH}")

    return True


def load_model():
    """Load trained model and scaler"""
    if not os.path.exists(MODEL_PATH) or not os.path.exists(SCALER_PATH):
        return None, None, None

    with open(MODEL_PATH, 'rb') as f:
        model = pickle.load(f)

    with open(SCALER_PATH, 'rb') as f:
        scaler = pickle.load(f)

    with open('ai/models/feature_cols.pkl', 'rb') as f:
        feature_cols = pickle.load(f)

    return model, scaler, feature_cols


def predict_patient_risk(subject_id: int):
    """
    Predict risk score for a patient
    Returns: {
        'subject_id': int,
        'risk_level': 0-2,
        'risk_label': 'NORMAL' | 'ABNORMAL' | 'CRITICAL',
        'confidence': float (0-100),
        'predicted_at': str
    }
    """
    model, scaler, feature_cols = load_model()

    if model is None:
        return {
            'subject_id': subject_id,
            'error': 'Model not trained. Please train the model first.'
        }

    # Fetch patient's lab data
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT test_name, value
        FROM lab_interpretations
        WHERE subject_id = ? AND value IS NOT NULL
    """, (subject_id,))

    records = cur.fetchall()
    conn.close()

    if not records:
        return {
            'subject_id': subject_id,
            'error': 'No lab data found for this patient'
        }

    # Prepare features for prediction
    patient_features = {}
    for record in records:
        test_name = record['test_name'].lower().replace(' ', '_').replace('-', '_')
        patient_features[f'{test_name}_value'] = record['value']

    # Create feature vector matching model's expected features
    X = []
    for col in feature_cols:
        X.append(patient_features.get(col, 0.0))  # Use 0 for missing features

    X = np.array([X])

    # Scale and predict
    X_scaled = scaler.transform(X)
    risk_level = model.predict(X_scaled)[0]
    probabilities = model.predict_proba(X_scaled)[0]
    
    # Handle case where model has fewer than 3 classes
    # Create proper probability mapping for all 3 classes
    prob_dict = {}
    for class_idx, class_label in enumerate(model.classes_):
        prob_dict[class_label] = probabilities[class_idx]
    
    # Ensure all 3 classes have a probability (0 if not present)
    full_probabilities = [
        prob_dict.get(0, 0.0),  # NORMAL
        prob_dict.get(1, 0.0),  # ABNORMAL
        prob_dict.get(2, 0.0)   # CRITICAL
    ]

    # Map risk level to label
    risk_labels = ['NORMAL', 'ABNORMAL', 'CRITICAL']
    risk_label = risk_labels[int(risk_level)]

    # Get confidence (probability of predicted class)
    confidence = float(max(probabilities)) * 100

    # Pad probabilities to always have 3 elements (normal, abnormal, critical)
    padded_probs = list(probabilities) + [0.0] * (3 - len(probabilities))
    padded_probs = padded_probs[:3]  # Ensure exactly 3 elements

    return {
        'subject_id': subject_id,
        'risk_level': int(risk_level),
        'risk_label': risk_label,
        'confidence': round(confidence, 2),
        'predicted_at': datetime.now().isoformat(),
        'probabilities': {
            'normal': round(float(full_probabilities[0]) * 100, 2),
            'abnormal': round(float(full_probabilities[1]) * 100, 2),
            'critical': round(float(full_probabilities[2]) * 100, 2)
        }
    }


if __name__ == '__main__':
    train_risk_model()
