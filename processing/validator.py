def validate_schema(df, expected_columns: set, table_name: str):
    missing = expected_columns - set(df.columns)
    if missing:
        raise ValueError(
            f"{table_name} missing required columns: {missing}"
        )

