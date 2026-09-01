import pandas as pd


# ==================================================
# CONVERT DATE-LIKE COLUMNS
# ==================================================

def convert_date_columns(df):

    result = df.copy()

    detected_date_columns = []

    for column in result.columns:

        # --------------------------------------------------
        # Already a datetime column
        # --------------------------------------------------

        if pd.api.types.is_datetime64_any_dtype(
            result[column]
        ):
            detected_date_columns.append(column)
            continue

        # --------------------------------------------------
        # Only inspect string/object columns
        # --------------------------------------------------

        if result[column].dtype != "object":
            continue

        values = result[column].dropna()

        if values.empty:
            continue

        # --------------------------------------------------
        # Try converting strings to datetime
        # --------------------------------------------------

        try:

            converted = pd.to_datetime(
                values,
                errors="coerce",
                format="mixed",
                utc=True
            )

            valid_ratio = (
                converted.notna().sum()
                / len(values)
            )

            # --------------------------------------------------
            # If 80% or more values are valid dates
            # --------------------------------------------------

            if valid_ratio >= 0.80:

                full_converted = pd.to_datetime(
                    result[column],
                    errors="coerce",
                    format="mixed",
                    utc=True
                )

                result[column] = full_converted

                detected_date_columns.append(
                    column
                )

        except Exception:
            continue

    return result, detected_date_columns
# ==================================================
# GET DATE COLUMNS
# ==================================================

def get_date_columns(df):

    return df.select_dtypes(
        include=["datetime", "datetimetz"]
    ).columns.tolist()

# ==================================================
# GET NUMERICAL COLUMNS
# ==================================================

def get_numerical_columns(df):

    return df.select_dtypes(
        include="number"
    ).columns.tolist()


# ==================================================
# PREPARE DATE COLUMN
# ==================================================
def prepare_date_column(df, date_column):

    result = df.copy()

    series = result[date_column].astype(str)

    # ----------------------------------------------
    # HANDLE DATE RANGE
    # ----------------------------------------------
    #
    # Example:
    # 2009-06-29/2009-07-05
    #
    # We use the START date as the representative
    # date for trend analysis.
    # ----------------------------------------------

    date_range_mask = series.str.match(
        r"^\d{4}-\d{2}-\d{2}/\d{4}-\d{2}-\d{2}$",
        na=False
    )

    if date_range_mask.any():

        result.loc[date_range_mask, date_column] = (
            result.loc[date_range_mask, date_column]
            .str.split("/")
            .str[0]
        )

    # ----------------------------------------------
    # CONVERT TO DATETIME
    # ----------------------------------------------

    result[date_column] = pd.to_datetime(
        result[date_column],
        errors="coerce",
        utc=True
    )

    # Remove invalid dates
    result = result.dropna(
        subset=[date_column]
    )

    return result

# ==================================================
# AGGREGATE TREND DATA
# ==================================================

def generate_trend_data(
    df,
    date_column,
    metric_column,
    aggregation="sum",
    frequency="Monthly"
):

    result = prepare_date_column(
        df,
        date_column
    )

    if result.empty:
        return pd.DataFrame()

    # --------------------------------------------------
    # FREQUENCY MAPPING
    # --------------------------------------------------

    frequency_mapping = {

        "Daily": "D",

        "Weekly": "W",

        "Monthly": "ME",

        "Quarterly": "QE",

        "Yearly": "YE"
    }

    if frequency not in frequency_mapping:

        raise ValueError(
            "Invalid frequency selected."
        )

    pandas_frequency = frequency_mapping[
        frequency
    ]

    # --------------------------------------------------
    # GROUP BY DATE
    # --------------------------------------------------

    result = result.set_index(
        date_column
    )

    # --------------------------------------------------
    # AGGREGATION
    # --------------------------------------------------

    if aggregation == "sum":

        trend = result[
            metric_column
        ].resample(
            pandas_frequency
        ).sum()

    elif aggregation == "mean":

        trend = result[
            metric_column
        ].resample(
            pandas_frequency
        ).mean()

    elif aggregation == "median":

        trend = result[
            metric_column
        ].resample(
            pandas_frequency
        ).median()

    elif aggregation == "count":

        trend = result[
            metric_column
        ].resample(
            pandas_frequency
        ).count()

    elif aggregation == "min":

        trend = result[
            metric_column
        ].resample(
            pandas_frequency
        ).min()

    elif aggregation == "max":

        trend = result[
            metric_column
        ].resample(
            pandas_frequency
        ).max()

    else:

        raise ValueError(
            "Invalid aggregation selected."
        )

    # --------------------------------------------------
    # CONVERT TO DATAFRAME
    # --------------------------------------------------

    trend = trend.reset_index()

    trend.columns = [
        "Date",
        "Value"
    ]

    return trend


# ==================================================
# CALCULATE TREND DIRECTION
# ==================================================

def calculate_trend_direction(
    trend_data
):

    if trend_data.empty:
        return "No Data"

    if len(trend_data) < 2:
        return "Insufficient Data"

    first_value = trend_data[
        "Value"
    ].iloc[0]

    last_value = trend_data[
        "Value"
    ].iloc[-1]

    if pd.isna(first_value) or pd.isna(last_value):
        return "Insufficient Data"

    if last_value > first_value:
        return "Increasing"

    elif last_value < first_value:
        return "Decreasing"

    else:
        return "Stable"


# ==================================================
# CALCULATE PERCENTAGE CHANGE
# ==================================================

def calculate_percentage_change(
    trend_data
):

    if trend_data.empty:
        return 0

    if len(trend_data) < 2:
        return 0

    first_value = trend_data[
        "Value"
    ].iloc[0]

    last_value = trend_data[
        "Value"
    ].iloc[-1]

    if pd.isna(first_value) or pd.isna(last_value):
        return 0

    if first_value == 0:
        return 0

    change = (
        (last_value - first_value)
        / abs(first_value)
    ) * 100

    return round(change, 2)