"""
Maps MIMIC-IV lab labels (d_labitems.label)
to canonical lab concepts used by the rule engine.
"""

LAB_CANONICAL_MAP = {
    # Hematology
    "Hemoglobin": "Hemoglobin",
    "Hematocrit": "Hematocrit",
    "Red Blood Cells": "RBC",
    "White Blood Cells": "WBC",
    "Platelet Count": "Platelets",

    # Electrolytes
    "Sodium": "Sodium",
    "Potassium": "Potassium",
    "Chloride": "Chloride",
    "Bicarbonate": "Bicarbonate",

    # Renal
    "Creatinine": "Creatinine",
    "Blood Urea Nitrogen": "Blood Urea Nitrogen",

    # Metabolic
    "Glucose": "Glucose"
}
