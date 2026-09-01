import pandas as pd


def generate_profile(df):

    profile = {}

    profile["rows"] = df.shape[0]

    profile["columns"] = df.shape[1]

    profile["missing_values"] = df.isnull().sum().sum()

    profile["duplicate_rows"] = df.duplicated().sum()

    profile["numeric_columns"] = df.select_dtypes(
        include="number"
    ).columns.tolist()

    profile["categorical_columns"] = df.select_dtypes(
        include="object"
    ).columns.tolist()

    return profile


def column_profile(df):

    report = pd.DataFrame({
        "Column": df.columns,

        "Data Type": [
            str(df[column].dtype)
            for column in df.columns
        ],

        "Unique Values": [
            df[column].nunique(dropna=True)
            for column in df.columns
        ],

        "Missing Values": [
            df[column].isnull().sum()
            for column in df.columns
        ]
    })

    report["Missing Percentage"] = (
        report["Missing Values"] / len(df) * 100
    ).round(2)

    return report
def classify_columns(df):

    classification = []

    for column in df.columns:

        series = df[column]

        # ==================================================
        # DATE / TIME
        # ==================================================

        if pd.api.types.is_datetime64_any_dtype(series):

            role = "Date / Time"

        # ==================================================
        # NUMERICAL
        # ==================================================

        elif pd.api.types.is_numeric_dtype(series):

            unique_count = series.nunique(
                dropna=True
            )

            total_count = len(
                series.dropna()
            )

            # Identifier detection
            if (
                total_count > 0
                and unique_count == total_count
            ):
                role = "Identifier"

            else:
                role = "Numerical"

        # ==================================================
        # CATEGORICAL
        # ==================================================

        else:

            role = "Categorical"

        classification.append({

            "Column": column,

            "Data Type": str(
                series.dtype
            ),

            "Unique Values": series.nunique(
                dropna=True
            ),

            "Role": role

        })

    return pd.DataFrame(
        classification
    )