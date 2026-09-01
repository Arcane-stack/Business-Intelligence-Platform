import pandas as pd


def generate_correlation_matrix(df):

    # Select numerical columns
    numerical_df = df.select_dtypes(
        include="number"
    )

    # Need at least 2 numerical columns
    if numerical_df.shape[1] < 2:
        return pd.DataFrame()

    # Generate correlation matrix
    correlation_matrix = numerical_df.corr()

    return correlation_matrix


def find_strong_correlations(
    correlation_matrix,
    threshold=0.7
):

    strong_correlations = []

    columns = correlation_matrix.columns

    # Compare every pair of columns
    for i in range(len(columns)):

        for j in range(i + 1, len(columns)):

            column_1 = columns[i]
            column_2 = columns[j]

            correlation = correlation_matrix.loc[
                column_1,
                column_2
            ]

            # Ignore missing correlations
            if pd.isna(correlation):
                continue

            # Check absolute correlation
            if abs(correlation) >= threshold:

                if correlation > 0:
                    relationship = "Positive"
                else:
                    relationship = "Negative"

                strong_correlations.append({

                    "Column 1": column_1,

                    "Column 2": column_2,

                    "Correlation": round(
                        correlation,
                        2
                    ),

                    "Relationship": relationship

                })

    return pd.DataFrame(
        strong_correlations
    )