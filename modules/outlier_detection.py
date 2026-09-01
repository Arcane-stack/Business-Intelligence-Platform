import pandas as pd
import numpy as np


# ==================================================
# GET NUMERICAL COLUMNS
# ==================================================

def get_numerical_columns(df):

    return df.select_dtypes(
        include="number"
    ).columns.tolist()


# ==================================================
# IQR OUTLIER DETECTION
# ==================================================

def detect_iqr_outliers(df, multiplier=1.5):

    numerical_columns = get_numerical_columns(df)

    results = []

    for column in numerical_columns:

        series = df[column].dropna()

        if series.empty:
            continue

        # ------------------------------------------
        # QUARTILES
        # ------------------------------------------

        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)

        iqr = q3 - q1

        # ------------------------------------------
        # LOWER AND UPPER LIMITS
        # ------------------------------------------

        lower_bound = q1 - (
            multiplier * iqr
        )

        upper_bound = q3 + (
            multiplier * iqr
        )

        # ------------------------------------------
        # FIND OUTLIERS
        # ------------------------------------------

        outlier_mask = (
            (df[column] < lower_bound) |
            (df[column] > upper_bound)
        )

        outlier_count = outlier_mask.sum()

        total_values = df[column].notna().sum()

        outlier_percentage = (
            outlier_count / total_values * 100
            if total_values > 0
            else 0
        )

        results.append({

            "Column": column,

            "Q1": round(q1, 2),

            "Q3": round(q3, 2),

            "IQR": round(iqr, 2),

            "Lower Bound": round(
                lower_bound, 2
            ),

            "Upper Bound": round(
                upper_bound, 2
            ),

            "Outliers": int(
                outlier_count
            ),

            "Outlier %": round(
                outlier_percentage, 2
            )
        })

    return pd.DataFrame(results)


# ==================================================
# Z-SCORE OUTLIER DETECTION
# ==================================================

def detect_zscore_outliers(
    df,
    threshold=3.0
):

    numerical_columns = get_numerical_columns(df)

    results = []

    for column in numerical_columns:

        series = df[column].dropna()

        if series.empty:
            continue

        mean = series.mean()

        std = series.std()

        # Avoid division by zero
        if std == 0 or pd.isna(std):

            outlier_count = 0

        else:

            z_scores = (
                (series - mean) / std
            )

            outlier_count = (
                np.abs(z_scores) > threshold
            ).sum()

        total_values = len(series)

        outlier_percentage = (
            outlier_count / total_values * 100
            if total_values > 0
            else 0
        )

        results.append({

            "Column": column,

            "Mean": round(
                mean, 2
            ),

            "Std Dev": round(
                std, 2
            ),

            "Threshold": threshold,

            "Outliers": int(
                outlier_count
            ),

            "Outlier %": round(
                outlier_percentage, 2
            )
        })

    return pd.DataFrame(results)


# ==================================================
# GET OUTLIER ROWS
# ==================================================

def get_outlier_rows(
    df,
    column,
    method="IQR",
    multiplier=1.5,
    threshold=3.0
):

    series = df[column]

    # ----------------------------------------------
    # IQR
    # ----------------------------------------------

    if method == "IQR":

        q1 = series.quantile(0.25)

        q3 = series.quantile(0.75)

        iqr = q3 - q1

        lower_bound = (
            q1 - multiplier * iqr
        )

        upper_bound = (
            q3 + multiplier * iqr
        )

        mask = (
            (series < lower_bound) |
            (series > upper_bound)
        )

    # ----------------------------------------------
    # Z-SCORE
    # ----------------------------------------------

    else:

        mean = series.mean()

        std = series.std()

        if std == 0 or pd.isna(std):

            mask = pd.Series(
                False,
                index=df.index
            )

        else:

            z_scores = (
                (series - mean) / std
            )

            mask = (
                np.abs(z_scores) > threshold
            )

    return df[mask]