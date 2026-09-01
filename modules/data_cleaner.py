import pandas as pd


# --------------------------------------------------
# REMOVE DUPLICATE ROWS
# --------------------------------------------------

def remove_duplicate_rows(df):

    cleaned_df = df.drop_duplicates()

    removed = len(df) - len(cleaned_df)

    return cleaned_df, removed


# --------------------------------------------------
# FILL NUMERICAL MISSING VALUES
# --------------------------------------------------

def fill_missing_numeric(df, method="median"):

    cleaned_df = df.copy()

    numeric_columns = cleaned_df.select_dtypes(
        include="number"
    ).columns

    filled_values = 0

    for column in numeric_columns:

        missing_before = cleaned_df[column].isnull().sum()

        if missing_before == 0:
            continue

        if method == "median":

            cleaned_df[column] = cleaned_df[column].fillna(
                cleaned_df[column].median()
            )

        elif method == "mean":

            cleaned_df[column] = cleaned_df[column].fillna(
                cleaned_df[column].mean()
            )

        filled_values += missing_before

    return cleaned_df, filled_values


# --------------------------------------------------
# FILL CATEGORICAL MISSING VALUES
# --------------------------------------------------

def fill_missing_categorical(df, method="mode"):

    cleaned_df = df.copy()

    categorical_columns = cleaned_df.select_dtypes(
        include="object"
    ).columns

    filled_values = 0

    for column in categorical_columns:

        missing_before = cleaned_df[column].isnull().sum()

        if missing_before == 0:
            continue

        if method == "mode":

            mode = cleaned_df[column].mode()

            if not mode.empty:

                cleaned_df[column] = cleaned_df[column].fillna(
                    mode[0]
                )

                filled_values += missing_before

        elif method == "unknown":

            cleaned_df[column] = cleaned_df[column].fillna(
                "Unknown"
            )

            filled_values += missing_before

    return cleaned_df, filled_values


# --------------------------------------------------
# CLEANING SUMMARY
# --------------------------------------------------

def generate_cleaning_report(original_df, cleaned_df):

    report = {

        "missing_before":
            int(original_df.isnull().sum().sum()),

        "missing_after":
            int(cleaned_df.isnull().sum().sum()),

        "duplicates_before":
            int(original_df.duplicated().sum()),

        "duplicates_after":
            int(cleaned_df.duplicated().sum()),

        "rows_before":
            len(original_df),

        "rows_after":
            len(cleaned_df)
    }

    report["missing_fixed"] = (
        report["missing_before"]
        - report["missing_after"]
    )

    report["duplicates_removed"] = (
        report["duplicates_before"]
        - report["duplicates_after"]
    )

    report["rows_removed"] = (
        report["rows_before"]
        - report["rows_after"]
    )

    return report