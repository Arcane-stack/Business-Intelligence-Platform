import pandas as pd


# ==================================================
# DATE RANGE DETECTION
# ==================================================

def is_date_range_column(series):

    values = (
        series
        .dropna()
        .astype(str)
        .str.strip()
    )

    if values.empty:
        return False

    pattern = (
        r"^\d{4}-\d{2}-\d{2}"
        r"/"
        r"\d{4}-\d{2}-\d{2}$"
    )

    matches = values.str.match(
        pattern,
        na=False
    )

    return matches.mean() >= 0.8


# ==================================================
# NORMAL DATE DETECTION
# ==================================================

def is_date_column(series):

    # --------------------------------------------------
    # Already a datetime column
    # --------------------------------------------------

    if pd.api.types.is_datetime64_any_dtype(series):
        return True

    # --------------------------------------------------
    # Check whether the column contains strings
    #
    # This works for:
    # object dtype
    # pandas StringDtype
    # normal Python strings
    # --------------------------------------------------

    if not (
        pd.api.types.is_object_dtype(series)
        or
        pd.api.types.is_string_dtype(series)
    ):
        return False

    values = (
        series
        .dropna()
        .astype(str)
        .str.strip()
    )

    if values.empty:
        return False

    # --------------------------------------------------
    # FIRST: Check common date formats directly
    #
    # Example:
    # 2019-12-10
    # 2020-01-25
    # --------------------------------------------------

    iso_pattern = r"^\d{4}-\d{2}-\d{2}$"

    iso_matches = values.str.match(
        iso_pattern,
        na=False
    )

    if iso_matches.mean() >= 0.8:
        return True

    # --------------------------------------------------
    # SECOND: Try general datetime conversion
    # --------------------------------------------------

    converted = pd.to_datetime(
        values,
        errors="coerce",
        utc=True
    )

    valid_percentage = (
        converted.notna().mean()
    )

    return valid_percentage >= 0.8


# ==================================================
# NORMALIZE DATE COLUMNS
# ==================================================

def normalize_date_columns(df):

    df = df.copy()

    for column in df.columns:

        series = df[column]

        # --------------------------------------------------
        # DATE RANGE
        #
        # Example:
        # 2009-06-29/2009-07-05
        # --------------------------------------------------

        if is_date_range_column(series):

            print(
                f"Date range detected: {column}"
            )

            start_dates = (
                series
                .astype(str)
                .str.strip()
                .str.split("/")
                .str[0]
            )

            df[column] = pd.to_datetime(
                start_dates,
                errors="coerce",
                utc=True
            )

            continue

        # --------------------------------------------------
        # NORMAL DATE
        # --------------------------------------------------

        if is_date_column(series):

            print(
                f"Date detected: {column}"
            )

            df[column] = pd.to_datetime(
                series,
                errors="coerce",
                utc=True
            )

    return df


# ==================================================
# LOAD DATA
# ==================================================

def load_data(uploaded_file):

    file_name = uploaded_file.name.lower()

    # --------------------------------------------------
    # CSV
    # --------------------------------------------------

    if file_name.endswith(".csv"):

        df = pd.read_csv(
            uploaded_file
        )

    # --------------------------------------------------
    # JSON
    # --------------------------------------------------

    elif file_name.endswith(".json"):

        df = pd.read_json(
            uploaded_file
        )

    # --------------------------------------------------
    # TXT
    # --------------------------------------------------

    elif file_name.endswith(".txt"):

        df = pd.read_csv(
            uploaded_file,
            sep=None,
            engine="python"
        )

    else:

        raise ValueError(
            "Unsupported file format."
        )

    # --------------------------------------------------
    # CLEAN COLUMN NAMES
    # --------------------------------------------------

    df.columns = (
        df.columns
        .astype(str)
        .str.strip()
    )

    # --------------------------------------------------
    # REMOVE COMPLETELY EMPTY COLUMNS
    # --------------------------------------------------

    df = df.dropna(
        axis=1,
        how="all"
    )

    # --------------------------------------------------
    # AUTOMATIC DATE NORMALIZATION
    # --------------------------------------------------

    df = normalize_date_columns(
        df
    )

    return df