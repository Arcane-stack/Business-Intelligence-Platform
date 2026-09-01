import pandas as pd


def generate_statistical_summary(df):

    # ----------------------------------------------
    # Select numerical columns
    # ----------------------------------------------

    numerical_df = df.select_dtypes(
        include="number"
    )

    # No numerical columns
    if numerical_df.empty:
        return pd.DataFrame()

    results = []

    # ----------------------------------------------
    # Calculate statistics for each column
    # ----------------------------------------------

    for column in numerical_df.columns:

        series = numerical_df[column].dropna()

        # Avoid calculations on completely empty columns
        if series.empty:
            continue

        count = series.count()

        mean = series.mean()

        median = series.median()

        standard_deviation = series.std()

        variance = series.var()

        minimum = series.min()

        maximum = series.max()

        q1 = series.quantile(0.25)

        q3 = series.quantile(0.75)

        # ------------------------------------------
        # Coefficient of Variation
        # ------------------------------------------

        if mean != 0:

            coefficient_of_variation = (
                standard_deviation / abs(mean)
            ) * 100

        else:

            coefficient_of_variation = None

        # ------------------------------------------
        # Create result
        # ------------------------------------------

        results.append({

            "Column": column,

            "Count": count,

            "Unique Values": series.nunique(),

            "Mean": mean,

            "Median": median,

            "Standard Deviation": standard_deviation,

            "Variance": variance,

            "Minimum": minimum,

            "Q1": q1,

            "Q3": q3,

            "Maximum": maximum,

            "Range": maximum - minimum,

            "Skewness": series.skew(),

            "Kurtosis": series.kurt(),

            "Coefficient of Variation (%)":
                coefficient_of_variation,

            "Zero Values":
                (series == 0).sum(),

            "Negative Values":
                (series < 0).sum()
        })

    # ----------------------------------------------
    # Convert results to DataFrame
    # ----------------------------------------------

    summary = pd.DataFrame(results)

    # Round numerical values
    summary = summary.round(2)

    return summary