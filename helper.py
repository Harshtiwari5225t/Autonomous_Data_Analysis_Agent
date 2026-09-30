import pandas as pd
import numpy as np
import os
import re
import warnings

# Suppress pandas migration warnings if any
warnings.filterwarnings("ignore", category=UserWarning)


# --------------------------------------------------
# LOAD DATA
# --------------------------------------------------

def load_data(file_path):
    """
    Load CSV, Excel or JSON file.
    """

    extension = os.path.splitext(file_path)[1].lower()

    if extension == ".csv":
        df = pd.read_csv(file_path)

    elif extension in [".xlsx", ".xls"]:
        df = pd.read_excel(file_path)

    elif extension == ".json":
        df = pd.read_json(file_path)

    else:
        raise ValueError(
            "Unsupported file format. "
            "Use CSV, Excel or JSON."
        )

    return df


# --------------------------------------------------
# NUMERIC CLEANING HELPER
# --------------------------------------------------

def _clean_numeric_series(series):
    """
    Attempt to convert a string series containing currency symbols (₹, $),
    commas, percentages, or non-numeric tokens into numbers.
    """
    if not (pd.api.types.is_object_dtype(series) or pd.api.types.is_string_dtype(series)):
        return series

    s = series.astype(str).str.strip()

    # Remove currency symbols, commas, percentage signs, and whitespace
    cleaned = s.str.replace(r"[₹$,%\s]", "", regex=True)

    # Coerce to numeric (invalid characters like '|' will become NaN)
    numeric_s = pd.to_numeric(cleaned, errors="coerce")

    # Check if majority of valid values converted to numbers
    non_empty = s[~s.isin(["nan", "None", "", "NaN", "null"]) & s.notnull()]
    if len(non_empty) > 0:
        valid_converted = numeric_s[non_empty.index].notnull().sum()
        ratio = valid_converted / len(non_empty)
        if ratio >= 0.5:
            return numeric_s

    return series


# --------------------------------------------------
# PROFILE DATA
# --------------------------------------------------

def profile_data(df):
    """
    Generate basic information about the dataset.
    """

    profile = {
        "rows": int(df.shape[0]),
        "columns": int(df.shape[1]),
        "column_names": df.columns.tolist(),
        "data_types": {
            column: str(dtype)
            for column, dtype in df.dtypes.items()
        },
        "missing_values": {
            column: int(value)
            for column, value in df.isnull().sum().items()
            if value > 0
        },
        "duplicate_rows": int(df.duplicated().sum())
    }

    return profile


# --------------------------------------------------
# CLEAN DATA
# --------------------------------------------------

def clean_data(df):
    """
    Clean and refine dataset.
    """
    df = df.copy()

    original_rows = len(df)

    # Remove duplicate rows
    duplicates_removed = int(df.duplicated().sum())
    df = df.drop_duplicates()

    # Strip spaces from column names
    df.columns = df.columns.str.strip()

    # Clean numeric-like text columns (e.g. ₹399 -> 399, 64% -> 64)
    for col in df.columns:
        df[col] = _clean_numeric_series(df[col])

    # Handle missing values
    missing_before = int(df.isnull().sum().sum())

    numeric_columns = df.select_dtypes(
        include=np.number
    ).columns

    categorical_columns = df.select_dtypes(
        include=["object", "category", "string"]
    ).columns

    # Numeric columns -> median
    for column in numeric_columns:
        median_val = df[column].median()
        if pd.notnull(median_val):
            df[column] = df[column].fillna(median_val)
        else:
            df[column] = df[column].fillna(0)

    # Categorical columns -> mode
    for column in categorical_columns:
        if not df[column].mode().empty:
            df[column] = df[column].fillna(
                df[column].mode()[0]
            )
        else:
            df[column] = df[column].fillna("Unknown")

    missing_after = int(df.isnull().sum().sum())

    cleaning_report = {
        "rows_before": original_rows,
        "rows_after": len(df),
        "duplicates_removed": duplicates_removed,
        "missing_values_before": missing_before,
        "missing_values_after": missing_after
    }

    return df, cleaning_report


# --------------------------------------------------
# BASIC STATISTICS
# --------------------------------------------------

def get_statistics(df):
    """
    Generate descriptive statistics.
    """

    numeric_df = df.select_dtypes(
        include=np.number
    )

    if numeric_df.empty:
        return {}

    desc = numeric_df.describe().to_dict()

    # Convert all metrics to standard python floats/ints for JSON serialization
    clean_stats = {}
    for col, metrics in desc.items():
        clean_stats[col] = {
            k: (float(v) if pd.notnull(v) else None)
            for k, v in metrics.items()
        }

    return clean_stats


# --------------------------------------------------
# COLUMN INFORMATION
# --------------------------------------------------

def get_column_information(df):
    """
    Return useful information about each column.
    """

    information = {}

    for column in df.columns:

        information[column] = {
            "data_type": str(df[column].dtype),
            "unique_values": int(
                df[column].nunique()
            ),
            "missing_values": int(
                df[column].isnull().sum()
            )
        }

    return information