import pandas as pd


# ==================================================
# GET DIMENSION COLUMNS
# ==================================================

def get_dimension_columns(df, classification_table=None):
    """
    Return columns suitable for grouping/performance analysis.

    Uses the existing column classification when available.
    """

    if classification_table is not None:

        dimensions = classification_table[
            classification_table["Role"].isin(
                ["Categorical", "Identifier"]
            )
        ]["Column"].tolist()

        return dimensions

    # Fallback if classification table isn't supplied

    dimension_columns = []

    for column in df.columns:

        if pd.api.types.is_object_dtype(df[column]):

            dimension_columns.append(column)

        elif pd.api.types.is_string_dtype(df[column]):

            dimension_columns.append(column)

        elif (
            "id" in column.lower()
            or "code" in column.lower()
        ):

            dimension_columns.append(column)

    return dimension_columns


# ==================================================
# GET METRIC COLUMNS
# ==================================================

def get_metric_columns(df, classification_table=None):
    """
    Return columns suitable for numerical metrics.

    Only columns classified as Numerical are returned.
    """

    if classification_table is not None:

        metrics = classification_table[
            classification_table["Role"] == "Numerical"
        ]["Column"].tolist()

        return metrics

    # Fallback

    return df.select_dtypes(
        include="number"
    ).columns.tolist()
# ==================================================
# GENERATE PERFORMANCE DATA
# ==================================================

def generate_performance_data(
    df,
    dimension_column,
    metric_column,
    aggregation="sum"
):
    """
    Group the dataset by a dimension and calculate
    an aggregated performance metric.
    """

    if dimension_column not in df.columns:
        raise ValueError(
            f"Dimension column '{dimension_column}' "
            "does not exist."
        )

    if metric_column not in df.columns:
        raise ValueError(
            f"Metric column '{metric_column}' "
            "does not exist."
        )

    # --------------------------------------------------
    # SELECT REQUIRED COLUMNS
    # --------------------------------------------------

    data = df[
        [
            dimension_column,
            metric_column
        ]
    ].copy()

    # --------------------------------------------------
    # REMOVE MISSING DIMENSIONS
    # --------------------------------------------------

    data = data.dropna(
        subset=[dimension_column]
    )

    # --------------------------------------------------
    # CONVERT METRIC TO NUMERIC
    # --------------------------------------------------

    data[metric_column] = pd.to_numeric(
        data[metric_column],
        errors="coerce"
    )

    data = data.dropna(
        subset=[metric_column]
    )

    if data.empty:
        return pd.DataFrame()

    # --------------------------------------------------
    # AGGREGATION
    # --------------------------------------------------

    if aggregation == "sum":

        result = data.groupby(
            dimension_column
        )[metric_column].sum()

    elif aggregation == "mean":

        result = data.groupby(
            dimension_column
        )[metric_column].mean()

    elif aggregation == "median":

        result = data.groupby(
            dimension_column
        )[metric_column].median()

    elif aggregation == "count":

        result = data.groupby(
            dimension_column
        )[metric_column].count()

    elif aggregation == "min":

        result = data.groupby(
            dimension_column
        )[metric_column].min()

    elif aggregation == "max":

        result = data.groupby(
            dimension_column
        )[metric_column].max()

    else:

        raise ValueError(
            "Invalid aggregation selected."
        )

    # --------------------------------------------------
    # CONVERT TO DATAFRAME
    # --------------------------------------------------

    result = result.reset_index()

    result.columns = [
        dimension_column,
        "Performance"
    ]

    # --------------------------------------------------
    # SORT BY PERFORMANCE
    # --------------------------------------------------

    result = result.sort_values(
        "Performance",
        ascending=False
    ).reset_index(
        drop=True
    )

    return result


# ==================================================
# TOP PERFORMERS
# ==================================================

def get_top_performers(
    performance_data,
    n=5
):
    """
    Return the top N performers.
    """

    if performance_data.empty:
        return pd.DataFrame()

    return performance_data.head(
        n
    ).copy()


# ==================================================
# BOTTOM PERFORMERS
# ==================================================

def get_bottom_performers(
    performance_data,
    n=5
):
    """
    Return the bottom N performers.
    """

    if performance_data.empty:
        return pd.DataFrame()

    return (
        performance_data
        .sort_values(
            "Performance",
            ascending=True
        )
        .head(n)
        .copy()
    )


# ==================================================
# PERFORMANCE SUMMARY
# ==================================================

def generate_performance_summary(
    performance_data
):
    """
    Generate high-level performance statistics.
    """

    if performance_data.empty:
        return {}

    values = performance_data[
        "Performance"
    ]

    highest = values.max()
    lowest = values.min()
    average = values.mean()

    highest_row = performance_data.loc[
        values.idxmax()
    ]

    lowest_row = performance_data.loc[
        values.idxmin()
    ]

    dimension_column = performance_data.columns[0]

    return {

        "total_entities":
            int(len(performance_data)),

        "highest_performance":
            float(highest),

        "lowest_performance":
            float(lowest),

        "average_performance":
            float(average),

        "top_performer":
            highest_row[dimension_column],

        "bottom_performer":
            lowest_row[dimension_column]
    }