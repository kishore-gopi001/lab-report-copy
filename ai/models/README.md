# Patient Risk Prediction Model

This directory contains the trained machine learning models for patient risk prediction.

## Files

- `risk_model.pkl` - Trained Random Forest classifier for risk prediction
- `scaler.pkl` - StandardScaler for feature normalization
- `feature_cols.pkl` - List of feature names used during training

## Training

To train a new model, run:

```bash
python scripts/train_model.py
```

**Requirements:**
- Python 3.7+
- scikit-learn
- pandas
- numpy

The model will be trained on lab data from the database and saved to this directory.

## Model Details

**Algorithm:** Random Forest Classifier
- 100 estimators
- Max depth: 10
- Min samples split: 5

**Risk Levels:**
- 0 = NORMAL (only normal labs)
- 1 = ABNORMAL (has abnormal labs but no critical)
- 2 = CRITICAL (has at least one critical lab)

**Features:**
- Patient lab test values (automatically extracted from database)
- Missing values are filled with median values
- Features are standardized using StandardScaler

## API Usage

### Predict Risk for Single Patient

```
GET /predict/patient/{subject_id}/risk
```

Response:
```json
{
  "subject_id": 123,
  "risk_level": 2,
  "risk_label": "CRITICAL",
  "confidence": 95.5,
  "predicted_at": "2026-01-24T10:30:00",
  "probabilities": {
    "normal": 2.5,
    "abnormal": 2.0,
    "critical": 95.5
  }
}
```

### Get Risk Distribution

```
GET /predict/risk-distribution
```

Returns counts of patients in each risk category.

### Get High Risk Patients

```
GET /predict/high-risk?risk_level=2&limit=50
```

Returns paginated list of high-risk patients with confidence scores.

## Performance Notes

- Training requires sufficient lab data in the database
- Prediction is fast (~1ms per patient)
- Model retrains from scratch each time (no incremental learning)
