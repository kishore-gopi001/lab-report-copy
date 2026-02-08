import pandas as pd

def join_labevents_with_metadata(
    labevents: pd.DataFrame,
    d_labitems: pd.DataFrame,
    patients: pd.DataFrame,
    admissions: pd.DataFrame
) -> pd.DataFrame:
    """
    Core joins to create a patient- and visit-aware lab dataset.
    """

    # Join lab names
    df = labevents.merge(
        d_labitems[["itemid", "label"]],
        on="itemid",
        how="left"
    )

    # Join patient demographics
    df = df.merge(
        patients[["subject_id", "gender", "anchor_age"]],
        on="subject_id",
        how="left"
    )

    # Join admission context
    df = df.merge(
        admissions[["hadm_id", "admittime", "dischtime"]],
        on="hadm_id",
        how="left"
    )

    # Rename for clarity
    df = df.rename(columns={
        "label": "test_name",
        "anchor_age": "age"
    })

    return df
