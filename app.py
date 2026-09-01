
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px

from modules.data_loader import load_data

from modules.data_profiler import (
    generate_profile,
    column_profile,
    classify_columns
)

from modules.data_cleaner import (
    remove_duplicate_rows,
    fill_missing_numeric,
    fill_missing_categorical,
    generate_cleaning_report
)

from modules.statistics import generate_statistical_summary

from modules.correlation import (
    generate_correlation_matrix,
    find_strong_correlations
)

from modules.outlier_detection import (
    detect_iqr_outliers,
    detect_zscore_outliers,
    get_outlier_rows
)

from modules.trends_analysis import (
    convert_date_columns,
    get_date_columns,
    get_numerical_columns,
    generate_trend_data,
    calculate_trend_direction,
    calculate_percentage_change
)

from modules.performance import (
    get_dimension_columns,
    get_metric_columns,
    generate_performance_data,
    get_top_performers,
    get_bottom_performers,
    generate_performance_summary
)

from modules.insights import generate_all_insights


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Business Intelligence Platform",
    page_icon="📊",
    layout="wide"
)


# ============================================================
# HEADER
# ============================================================

st.title("📊 Business Intelligence Platform")
st.caption(
    "Upload your dataset and transform raw data into "
    "actionable business insights."
)


# ============================================================
# DATE NORMALIZATION
# ============================================================

def normalize_dates(df):
    """Detect and normalize date-like object columns."""
    df = df.copy()

    for column in df.columns:

        if pd.api.types.is_datetime64_any_dtype(df[column]):
            continue

        if df[column].dtype != "object":
            continue

        series = (
            df[column]
            .dropna()
            .astype(str)
            .str.strip()
        )

        if series.empty:
            continue

        date_range_pattern = (
            r"^\d{4}-\d{2}-\d{2}/"
            r"\d{4}-\d{2}-\d{2}$"
        )

        range_matches = series.str.match(
            date_range_pattern,
            na=False
        )

        if range_matches.mean() >= 0.8:

            start_dates = (
                df[column]
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

        converted = pd.to_datetime(
            series,
            errors="coerce",
            utc=True
        )

        valid_percentage = converted.notna().mean()

        if valid_percentage >= 0.8:

            df[column] = pd.to_datetime(
                df[column],
                errors="coerce",
                utc=True
            )

    return df


# ============================================================
# SESSION STATE INITIALIZATION
# ============================================================

def initialize_session_state():

    defaults = {
        "cleaned_df": None,
        "cleaned": False,
        "uploaded_filename": None,

        "performance_data": pd.DataFrame(),
        "top_performers": pd.DataFrame(),
        "bottom_performers": pd.DataFrame(),
        "performance_summary": {},
        "performance_config": {},

        "trend_data": pd.DataFrame(),
        "trend_config": {},

        "business_insights": pd.DataFrame(),
        "insights_config": {}
    }

    for key, value in defaults.items():

        if key not in st.session_state:

            if isinstance(value, pd.DataFrame):
                st.session_state[key] = value.copy()

            elif isinstance(value, dict):
                st.session_state[key] = value.copy()

            else:
                st.session_state[key] = value


initialize_session_state()


# ============================================================
# FILE UPLOAD
# ============================================================

uploaded_file = st.file_uploader(
    "Upload your dataset",
    type=["csv", "json", "txt"]
)


# ============================================================
# PROCESS DATASET
# ============================================================

if uploaded_file is not None:

    try:

        # ----------------------------------------------------
        # LOAD DATA
        # ----------------------------------------------------

        df = load_data(uploaded_file)

        # ----------------------------------------------------
        # DATE CONVERSION
        # ----------------------------------------------------

        try:
            df, detected_date_columns = convert_date_columns(df)
        except Exception:
            detected_date_columns = []

        df = normalize_dates(df)

        st.success(
            f"Dataset loaded successfully: "
            f"{uploaded_file.name}"
        )

        # ----------------------------------------------------
        # RESET STATE WHEN A NEW FILE IS UPLOADED
        # ----------------------------------------------------

        if (
            st.session_state.get("uploaded_filename")
            != uploaded_file.name
        ):

            st.session_state.cleaned_df = df.copy()
            st.session_state.cleaned = False
            st.session_state.uploaded_filename = uploaded_file.name

            st.session_state.performance_data = pd.DataFrame()
            st.session_state.top_performers = pd.DataFrame()
            st.session_state.bottom_performers = pd.DataFrame()
            st.session_state.performance_summary = {}
            st.session_state.performance_config = {}

            st.session_state.trend_data = pd.DataFrame()
            st.session_state.trend_config = {}

            st.session_state.business_insights = pd.DataFrame()
            st.session_state.insights_config = {}

        elif st.session_state.cleaned_df is None:

            st.session_state.cleaned_df = df.copy()

        # ----------------------------------------------------
        # BASIC PROFILE
        # ----------------------------------------------------

        profile = generate_profile(df)

        classification_table = classify_columns(df)

        # ====================================================
        # ANALYSIS SETTINGS
        # ====================================================

        st.divider()

        st.subheader("⚙️ Analysis Settings")

        if st.session_state.cleaned:

            analysis_options = [
                "Original Dataset",
                "Cleaned Dataset"
            ]

        else:

            analysis_options = [
                "Original Dataset"
            ]

        analysis_source = st.radio(
            "Dataset to use for analysis",
            analysis_options,
            horizontal=True,
            help=(
                "Choose whether Statistics, Correlation, "
                "Outliers, Trends, Performance and Insights "
                "should use the raw or cleaned dataset."
            )
        )

        if analysis_source == "Cleaned Dataset":

            analysis_df = st.session_state.cleaned_df

        else:

            analysis_df = df

        st.caption(
            f"Current analysis source: **{analysis_source}**"
        )

        # ====================================================
        # NAVIGATION TABS
        # ====================================================

        (
            overview_tab,
            cleaning_tab,
            statistics_tab,
            correlation_tab,
            outlier_tab,
            trend_tab,
            performance_tab,
            insights_tab
        ) = st.tabs(
            [
                "📊 Overview",
                "🧹 Cleaning",
                "📈 Statistics",
                "🔗 Correlation",
                "⚠️ Outliers",
                "📉 Trends",
                "🏆 Performance",
                "🤖 Insights"
            ]
        )

        # ====================================================
        # OVERVIEW TAB
        # ====================================================

        with overview_tab:

            st.header("📊 Dataset Overview")

            st.caption(
                "A quick summary of your uploaded dataset."
            )

            col1, col2, col3, col4 = st.columns(4)

            col1.metric("Rows", profile["rows"])
            col2.metric("Columns", profile["columns"])
            col3.metric(
                "Missing Values",
                profile["missing_values"]
            )
            col4.metric(
                "Duplicate Rows",
                profile["duplicate_rows"]
            )

            st.divider()

            st.subheader("🧠 Column Classification")

            numerical_count = (
                classification_table["Role"] == "Numerical"
            ).sum()

            categorical_count = (
                classification_table["Role"] == "Categorical"
            ).sum()

            date_count = (
                classification_table["Role"] == "Date / Time"
            ).sum()

            identifier_count = (
                classification_table["Role"] == "Identifier"
            ).sum()

            col1, col2, col3, col4 = st.columns(4)

            col1.metric("Numerical", numerical_count)
            col2.metric("Categorical", categorical_count)
            col3.metric("Date / Time", date_count)
            col4.metric("Identifiers", identifier_count)

            st.subheader("✅ Data Quality")

            col1, col2 = st.columns(2)

            with col1:

                if profile["missing_values"] == 0:

                    st.success(
                        "No missing values detected."
                    )

                else:

                    st.warning(
                        f"{profile['missing_values']} "
                        "missing values detected."
                    )

            with col2:

                if profile["duplicate_rows"] == 0:

                    st.success(
                        "No duplicate rows detected."
                    )

                else:

                    st.warning(
                        f"{profile['duplicate_rows']} "
                        "duplicate rows detected."
                    )

            with st.expander("📄 View Dataset Preview"):

                st.dataframe(
                    df.head(10),
                    use_container_width=True,
                    hide_index=True
                )

            with st.expander("🔍 View Column Profile"):

                profile_report = column_profile(df)

                st.dataframe(
                    profile_report,
                    use_container_width=True,
                    hide_index=True
                )

            with st.expander("🧠 View Classification Details"):

                st.dataframe(
                    classification_table,
                    use_container_width=True,
                    hide_index=True
                )

            with st.expander("🔧 View Detected Data Types"):

                dtype_report = pd.DataFrame({
                    "Column": df.columns,
                    "Data Type": [
                        str(df[column].dtype)
                        for column in df.columns
                    ]
                })

                st.dataframe(
                    dtype_report,
                    use_container_width=True,
                    hide_index=True
                )

        # ====================================================
        # CLEANING TAB
        # ====================================================

        with cleaning_tab:

            st.header("🧹 Data Cleaning")

            st.caption(
                "Clean missing values and duplicate records "
                "before performing advanced analysis."
            )

            st.subheader("Cleaning Options")

            remove_duplicates = st.checkbox(
                "Remove duplicate rows"
            )

            fill_numeric = st.checkbox(
                "Fill missing numerical values"
            )

            fill_categorical = st.checkbox(
                "Fill missing categorical values"
            )

            numeric_method = "Median"

            if fill_numeric:

                numeric_method = st.selectbox(
                    "Numerical missing-value method",
                    ["Median", "Mean"],
                    key="numeric_cleaning_method"
                )

            categorical_method = "Mode"

            if fill_categorical:

                categorical_method = st.selectbox(
                    "Categorical missing-value method",
                    ["Mode", "Unknown"],
                    key="categorical_cleaning_method"
                )

            clean_button = st.button(
                "🧹 Clean Dataset",
                type="primary",
                key="clean_dataset_button"
            )

            if clean_button:

                cleaned_df = df.copy()

                if remove_duplicates:

                    (
                        cleaned_df,
                        duplicates_removed
                    ) = remove_duplicate_rows(cleaned_df)

                else:

                    duplicates_removed = 0

                if fill_numeric:

                    (
                        cleaned_df,
                        numeric_values_filled
                    ) = fill_missing_numeric(
                        cleaned_df,
                        method=numeric_method.lower()
                    )

                else:

                    numeric_values_filled = 0

                if fill_categorical:

                    (
                        cleaned_df,
                        categorical_values_filled
                    ) = fill_missing_categorical(
                        cleaned_df,
                        method=categorical_method.lower()
                    )

                else:

                    categorical_values_filled = 0

                st.session_state.cleaned_df = cleaned_df.copy()
                st.session_state.cleaned = True

                # A new cleaned dataset invalidates old analyses.
                st.session_state.performance_data = pd.DataFrame()
                st.session_state.top_performers = pd.DataFrame()
                st.session_state.bottom_performers = pd.DataFrame()
                st.session_state.performance_summary = {}
                st.session_state.performance_config = {}

                st.session_state.trend_data = pd.DataFrame()
                st.session_state.trend_config = {}

                st.session_state.business_insights = pd.DataFrame()
                st.session_state.insights_config = {}

                cleaning_report = generate_cleaning_report(
                    df,
                    cleaned_df
                )

                st.success(
                    "Dataset cleaned successfully."
                )

                st.subheader("📊 Cleaning Summary")

                col1, col2, col3, col4 = st.columns(4)

                col1.metric(
                    "Missing Values Fixed",
                    cleaning_report["missing_fixed"]
                )

                col2.metric(
                    "Duplicates Removed",
                    cleaning_report["duplicates_removed"]
                )

                col3.metric(
                    "Rows Removed",
                    cleaning_report["rows_removed"]
                )

                col4.metric(
                    "Remaining Missing",
                    cleaning_report["missing_after"]
                )

                with st.expander("📋 Detailed Cleaning Report"):

                    report_df = pd.DataFrame({
                        "Metric": [
                            "Missing Values Before",
                            "Missing Values After",
                            "Missing Values Fixed",
                            "Duplicates Before",
                            "Duplicates After",
                            "Duplicates Removed",
                            "Rows Before",
                            "Rows After",
                            "Rows Removed"
                        ],
                        "Value": [
                            cleaning_report["missing_before"],
                            cleaning_report["missing_after"],
                            cleaning_report["missing_fixed"],
                            cleaning_report["duplicates_before"],
                            cleaning_report["duplicates_after"],
                            cleaning_report["duplicates_removed"],
                            cleaning_report["rows_before"],
                            cleaning_report["rows_after"],
                            cleaning_report["rows_removed"]
                        ]
                    })

                    st.dataframe(
                        report_df,
                        use_container_width=True,
                        hide_index=True
                    )

                with st.expander("📄 View Cleaned Dataset"):

                    st.dataframe(
                        cleaned_df.head(10),
                        use_container_width=True,
                        hide_index=True
                    )

                csv_data = (
                    cleaned_df
                    .to_csv(index=False)
                    .encode("utf-8")
                )

                st.download_button(
                    label="⬇️ Download Cleaned Dataset",
                    data=csv_data,
                    file_name="cleaned_dataset.csv",
                    mime="text/csv",
                    key="download_cleaned_dataset"
                )

            else:

                if st.session_state.cleaned:

                    st.info(
                        "A cleaned dataset is available. "
                        "Run cleaning again if you want to "
                        "change the cleaning options."
                    )

                else:

                    st.info(
                        "Choose your cleaning options and "
                        "click 'Clean Dataset' to create "
                        "the cleaned version."
                    )

        # ====================================================
        # STATISTICS TAB
        # ====================================================

        with statistics_tab:

            st.header("📈 Statistical Analysis")

            st.caption(
                f"Analysis based on: **{analysis_source}**"
            )

            statistical_summary = (
                generate_statistical_summary(
                    analysis_df
                )
            )

            if statistical_summary.empty:

                st.info(
                    "No numerical columns are available "
                    "for statistical analysis."
                )

            else:

                st.dataframe(
                    statistical_summary,
                    use_container_width=True,
                    hide_index=True
                )

                with st.expander(
                    "ℹ️ What do these statistics mean?"
                ):

                    st.write(
                        """
                        **Mean** – Average value of the column.

                        **Median** – Middle value of the dataset.

                        **Standard Deviation** – Measures how spread
                        out values are around the mean.

                        **Variance** – Square of the standard deviation.

                        **Skewness** – Measures asymmetry in the distribution.

                        **Kurtosis** – Indicates the heaviness of
                        distribution tails.

                        **Coefficient of Variation** – Measures
                        relative variability.

                        **Zero Values** – Number of values equal to zero.

                        **Negative Values** – Number of values below zero.

                        **Unique Values** – Number of distinct non-null values.
                        """
                    )

        # ====================================================
        # CORRELATION TAB
        # ====================================================

        with correlation_tab:

            st.header("🔗 Correlation Analysis")

            st.caption(
                f"Analysis based on: **{analysis_source}**"
            )

            correlation_matrix = (
                generate_correlation_matrix(
                    analysis_df
                )
            )

            if correlation_matrix.empty:

                st.info(
                    "At least two numerical columns are "
                    "required for correlation analysis."
                )

            else:

                correlation_threshold = st.slider(
                    "🎚️ Correlation strength threshold",
                    min_value=0.0,
                    max_value=1.0,
                    value=0.7,
                    step=0.05,
                    key="correlation_threshold"
                )

                st.caption(
                    f"Showing strong relationships with "
                    f"|correlation| ≥ "
                    f"{correlation_threshold:.2f}"
                )

                max_heatmap_columns = 20

                if len(correlation_matrix.columns) > max_heatmap_columns:

                    st.warning(
                        f"The dataset contains "
                        f"{len(correlation_matrix.columns)} "
                        "numerical columns. Only the first "
                        f"{max_heatmap_columns} are displayed "
                        "in the heatmap to keep the visualization readable."
                    )

                    heatmap_matrix = correlation_matrix.iloc[
                        :max_heatmap_columns,
                        :max_heatmap_columns
                    ]

                else:

                    heatmap_matrix = correlation_matrix

                col1, col2 = st.columns([2, 1])

                with col1:

                    st.subheader("🔥 Correlation Heatmap")

                    heatmap_size = max(
                        6,
                        min(
                            12,
                            len(heatmap_matrix.columns) * 0.6
                        )
                    )

                    fig, ax = plt.subplots(
                        figsize=(
                            heatmap_size,
                            heatmap_size
                        )
                    )

                    sns.heatmap(
                        heatmap_matrix,
                        annot=(
                            len(
                                heatmap_matrix.columns
                            ) <= 12
                        ),
                        fmt=".2f",
                        cmap="coolwarm",
                        center=0,
                        linewidths=0.5,
                        ax=ax,
                        cbar=True
                    )

                    ax.set_title("Correlation Heatmap")

                    plt.xticks(
                        rotation=45,
                        ha="right"
                    )

                    plt.yticks(rotation=0)

                    st.pyplot(
                        fig,
                        use_container_width=True
                    )

                    plt.close(fig)

                with col2:

                    st.subheader("💡 Strong Correlations")

                    strong_correlations = (
                        find_strong_correlations(
                            correlation_matrix,
                            threshold=correlation_threshold
                        )
                    )

                    if strong_correlations.empty:

                        st.info(
                            "No correlations meet "
                            "the selected threshold."
                        )

                    else:

                        st.dataframe(
                            strong_correlations,
                            use_container_width=True,
                            hide_index=True
                        )

                with st.expander(
                    "📋 View Full Correlation Matrix"
                ):

                    st.dataframe(
                        correlation_matrix.round(2),
                        use_container_width=True
                    )

        # ====================================================
        # OUTLIER TAB
        # ====================================================

        with outlier_tab:

            st.header("⚠️ Outlier Detection")

            st.caption(
                f"Analysis based on: **{analysis_source}**"
            )

            detection_method = st.radio(
                "Choose an outlier detection method:",
                ["IQR", "Z-Score"],
                horizontal=True,
                key="outlier_detection_method"
            )

            if detection_method == "IQR":

                iqr_multiplier = st.slider(
                    "IQR Multiplier",
                    min_value=1.0,
                    max_value=3.0,
                    value=1.5,
                    step=0.1,
                    key="iqr_multiplier"
                )

                st.caption(
                    f"Values below Q1 − {iqr_multiplier:.1f} × IQR "
                    f"or above Q3 + {iqr_multiplier:.1f} × IQR "
                    "will be considered outliers."
                )

                outlier_summary = detect_iqr_outliers(
                    analysis_df,
                    multiplier=iqr_multiplier
                )

            else:

                zscore_threshold = st.slider(
                    "Z-Score Threshold",
                    min_value=1.0,
                    max_value=5.0,
                    value=3.0,
                    step=0.1,
                    key="zscore_threshold"
                )

                st.caption(
                    f"Values with an absolute Z-score greater than "
                    f"{zscore_threshold:.1f} will be considered outliers."
                )

                outlier_summary = detect_zscore_outliers(
                    analysis_df,
                    threshold=zscore_threshold
                )

            if outlier_summary.empty:

                st.info(
                    "No numerical columns are available "
                    "for outlier detection."
                )

            else:

                total_outliers = int(
                    outlier_summary["Outliers"].sum()
                )

                columns_with_outliers = int(
                    (
                        outlier_summary["Outliers"] > 0
                    ).sum()
                )

                highest_outlier_column = (
                    outlier_summary
                    .loc[
                        outlier_summary["Outliers"].idxmax(),
                        "Column"
                    ]
                )

                col1, col2, col3 = st.columns(3)

                col1.metric(
                    "Total Outliers",
                    total_outliers
                )

                col2.metric(
                    "Columns Affected",
                    columns_with_outliers
                )

                col3.metric(
                    "Most Affected Column",
                    highest_outlier_column
                )

                st.divider()

                st.subheader("📊 Outlier Summary")

                st.dataframe(
                    outlier_summary,
                    use_container_width=True,
                    hide_index=True
                )

                st.subheader("🔎 Investigate a Column")

                available_columns = (
                    outlier_summary["Column"].tolist()
                )

                selected_column = st.selectbox(
                    "Select a numerical column:",
                    available_columns,
                    key="outlier_selected_column"
                )

                if detection_method == "IQR":

                    selected_outliers = get_outlier_rows(
                        analysis_df,
                        selected_column,
                        method="IQR",
                        multiplier=iqr_multiplier
                    )

                else:

                    selected_outliers = get_outlier_rows(
                        analysis_df,
                        selected_column,
                        method="Z-Score",
                        threshold=zscore_threshold
                    )

                st.write(
                    f"**{len(selected_outliers)} outlier rows "
                    f"detected in `{selected_column}`**"
                )

                if selected_outliers.empty:

                    st.success(
                        "No outlier rows were detected "
                        "for this column."
                    )

                else:

                    st.dataframe(
                        selected_outliers,
                        use_container_width=True,
                        hide_index=True
                    )

                st.subheader("📦 Outlier Visualization")

                fig, ax = plt.subplots(
                    figsize=(10, 4)
                )

                sns.boxplot(
                    x=analysis_df[selected_column],
                    ax=ax
                )

                ax.set_title(
                    f"Distribution of {selected_column}"
                )

                ax.set_xlabel(selected_column)

                st.pyplot(
                    fig,
                    use_container_width=True
                )

                plt.close(fig)

        # ====================================================
        # TRENDS TAB
        # ====================================================

        with trend_tab:

            st.header("📉 Trends Analysis")

            st.caption(
                f"Analysis based on: **{analysis_source}**"
            )

            date_columns = get_date_columns(
                analysis_df
            )

            numerical_columns = get_numerical_columns(
                analysis_df
            )

            if not date_columns:

                st.warning(
                    "No date/time columns were detected "
                    "in the selected dataset."
                )

                st.info(
                    "A date column is required to generate "
                    "trend analysis."
                )

            elif not numerical_columns:

                st.warning(
                    "No numerical columns were detected "
                    "in the selected dataset."
                )

                st.info(
                    "At least one numerical column is "
                    "required for trend analysis."
                )

            else:

                st.subheader("⚙️ Trend Configuration")

                col1, col2, col3, col4 = st.columns(4)

                with col1:

                    date_column = st.selectbox(
                        "Date Column",
                        date_columns,
                        key="trend_date_column"
                    )

                with col2:

                    metric_column = st.selectbox(
                        "Metric",
                        numerical_columns,
                        key="trend_metric_column"
                    )

                with col3:

                    aggregation = st.selectbox(
                        "Aggregation",
                        [
                            "sum",
                            "mean",
                            "median",
                            "count",
                            "min",
                            "max"
                        ],
                        key="trend_aggregation"
                    )

                with col4:

                    frequency = st.selectbox(
                        "Frequency",
                        [
                            "Daily",
                            "Weekly",
                            "Monthly",
                            "Quarterly",
                            "Yearly"
                        ],
                        index=2,
                        key="trend_frequency"
                    )


                # Automatically generate on first load,
                # or when the user explicitly clicks the button.
                trend_needs_generation = (
                     st.session_state.trend_data.empty
                    or st.session_state.trend_config.get(
                        "analysis_source"
                    ) != analysis_source
                    or st.session_state.trend_config.get(
                        "date_column"
                    ) != date_column
                    or st.session_state.trend_config.get(
                        "metric_column"
                    ) != metric_column
                    or st.session_state.trend_config.get(
                        "aggregation"
                    ) != aggregation
                    or st.session_state.trend_config.get(
                        "frequency"
                    ) != frequency
                )

                if trend_needs_generation:

                    try:

                        trend_data = generate_trend_data(
                            analysis_df,
                            date_column=date_column,
                            metric_column=metric_column,
                            aggregation=aggregation,
                            frequency=frequency
                        )

                        st.session_state.trend_data = (
                            trend_data.copy()
                        )

                        st.session_state.trend_config = {
                            "date_column": date_column,
                            "metric_column": metric_column,
                            "aggregation": aggregation,
                            "frequency": frequency,
                            "analysis_source": analysis_source
                        }

                    except Exception as e:

                        st.session_state.trend_data = pd.DataFrame()

                        st.error(
                            f"Could not generate trend analysis: {e}"
                        )

                trend_data = st.session_state.trend_data

                if trend_data.empty:

                    st.warning(
                        "No valid trend data could be generated "
                        "using the selected configuration."
                    )

                else:

                    trend_direction = (
                        calculate_trend_direction(
                            trend_data
                        )
                    )

                    percentage_change = (
                        calculate_percentage_change(
                            trend_data
                        )
                    )

                    first_value = trend_data["Value"].iloc[0]
                    last_value = trend_data["Value"].iloc[-1]

                    st.subheader("📊 Trend Summary")

                    kpi1, kpi2, kpi3, kpi4 = st.columns(4)

                    kpi1.metric(
                        "Starting Value",
                        f"{first_value:,.2f}"
                    )

                    kpi2.metric(
                        "Latest Value",
                        f"{last_value:,.2f}"
                    )

                    kpi3.metric(
                        "Change",
                        f"{percentage_change:+.2f}%"
                    )

                    kpi4.metric(
                        "Trend",
                        trend_direction
                    )

                    st.divider()

                    st.subheader(
                        f"📈 {metric_column} Trend"
                    )

                    fig = px.line(
                        trend_data,
                        x="Date",
                        y="Value",
                        markers=True,
                        title=(
                            f"{aggregation.title()} "
                            f"{metric_column} — "
                            f"{frequency}"
                        )
                    )

                    fig.update_layout(
                        xaxis_title="Date",
                        yaxis_title=metric_column,
                        hovermode="x unified",
                        height=450,
                        margin=dict(
                            l=20,
                            r=20,
                            t=60,
                            b=20
                        )
                    )

                    fig.update_traces(
                        line_width=3
                    )

                    st.plotly_chart(
                        fig,
                        use_container_width=True
                    )

                    with st.expander("📋 View Trend Data"):

                        display_trend_data = trend_data.copy()

                        display_trend_data["Value"] = (
                            display_trend_data["Value"].round(2)
                        )

                        st.dataframe(
                            display_trend_data,
                            use_container_width=True,
                            hide_index=True
                        )

        # ====================================================
        # PERFORMANCE TAB
        # ====================================================

        with performance_tab:

            st.header("🏆 Performance Analysis")

            st.caption(
                f"Analysis based on: **{analysis_source}**"
            )

            # ------------------------------------------------
            # GET AVAILABLE DIMENSIONS AND METRICS
            # ------------------------------------------------

            dimension_columns = get_dimension_columns(
                analysis_df,
                classification_table
            )

            metric_columns = get_metric_columns(
                analysis_df,
                classification_table
            )

            if not dimension_columns:

                st.warning(
                    "No categorical or identifier columns are "
                    "available for performance analysis."
                )

            elif not metric_columns:

                st.warning(
                    "No numerical columns are available "
                    "for performance analysis."
                )

            else:

                st.subheader(
                    "⚙️ Performance Configuration"
                )

                col1, col2, col3 = st.columns(3)

                with col1:

                    selected_dimension = st.selectbox(
                        "Dimension",
                        dimension_columns,
                        key="performance_dimension",
                        help=(
                            "Choose the column used to group "
                            "and compare entities."
                        )
                    )

                with col2:

                    selected_metric = st.selectbox(
                        "Metric",
                        metric_columns,
                        key="performance_metric",
                        help=(
                            "Choose the numerical column used "
                            "to measure performance."
                        )
                    )

                with col3:

                    selected_aggregation = st.selectbox(
                        "Aggregation",
                        [
                            "sum",
                            "mean",
                            "median",
                            "count",
                            "min",
                            "max"
                        ],
                        key="performance_aggregation"
                    )

                top_n = st.slider(
                    "Number of Top / Bottom Performers",
                    min_value=1,
                    max_value=20,
                    value=5,
                    step=1,
                    key="performance_top_n"
                )

                analyze_performance = st.button(
                    "🏆 Analyze Performance",
                    type="primary",
                    key="analyze_performance_button"
                )

                # ------------------------------------------------
                # CONFIGURATION CHANGE DETECTION
                # ------------------------------------------------

                current_performance_config = {
                    "dimension": selected_dimension,
                    "metric": selected_metric,
                    "aggregation": selected_aggregation,
                    "top_n": top_n,
                    "analysis_source": analysis_source
                }

                if analyze_performance:

                    try:

                        performance_data = (
                            generate_performance_data(
                                analysis_df,
                                dimension_column=selected_dimension,
                                metric_column=selected_metric,
                                aggregation=selected_aggregation
                            )
                        )

                        if performance_data.empty:

                            st.session_state.performance_data = (
                                pd.DataFrame()
                            )

                            st.session_state.top_performers = (
                                pd.DataFrame()
                            )

                            st.session_state.bottom_performers = (
                                pd.DataFrame()
                            )

                            st.session_state.performance_summary = {}

                            st.session_state.performance_config = (
                                current_performance_config
                            )

                            st.warning(
                                "No performance data could be "
                                "generated using the selected "
                                "configuration."
                            )

                        else:

                            top_performers = get_top_performers(
                                performance_data,
                                n=top_n
                            )

                            bottom_performers = (
                                get_bottom_performers(
                                    performance_data,
                                    n=top_n
                                )
                            )

                            summary = (
                                generate_performance_summary(
                                    performance_data
                                )
                            )

                            # ------------------------------------
                            # SAVE ALL RESULTS
                            # ------------------------------------

                            st.session_state.performance_data = (
                                performance_data.copy()
                            )

                            st.session_state.top_performers = (
                                top_performers.copy()
                            )

                            st.session_state.bottom_performers = (
                                bottom_performers.copy()
                            )

                            st.session_state.performance_summary = (
                                summary.copy()
                            )

                            st.session_state.performance_config = (
                                current_performance_config.copy()
                            )

                            st.success(
                                "Performance analysis completed."
                            )

                    except Exception as e:

                        st.error(
                            f"Could not generate performance "
                            f"analysis: {e}"
                        )

                # ------------------------------------------------
                # READ SAVED RESULTS
                # ------------------------------------------------

                performance_data = st.session_state.get(
                    "performance_data",
                    pd.DataFrame()
                )

                top_performers = st.session_state.get(
                    "top_performers",
                    pd.DataFrame()
                )

                bottom_performers = st.session_state.get(
                    "bottom_performers",
                    pd.DataFrame()
                )

                summary = st.session_state.get(
                    "performance_summary",
                    {}
                )

                # ------------------------------------------------
                # DISPLAY RESULTS
                # ------------------------------------------------

                if not performance_data.empty:

                    st.subheader(
                        "📊 Performance Summary"
                    )

                    kpi1, kpi2, kpi3, kpi4 = st.columns(4)

                    kpi1.metric(
                        "Total Entities",
                        summary.get(
                            "total_entities",
                            0
                        )
                    )

                    kpi2.metric(
                        "Top Performer",
                        str(
                            summary.get(
                                "top_performer",
                                "-"
                            )
                        )
                    )

                    kpi3.metric(
                        "Bottom Performer",
                        str(
                            summary.get(
                                "bottom_performer",
                                "-"
                            )
                        )
                    )

                    kpi4.metric(
                        "Average Performance",
                        f"{summary.get(
                            'average_performance',
                            0
                        ):,.2f}"
                    )

                    st.divider()

                    col1, col2 = st.columns(2)

                    with col1:

                        st.subheader(
                            "🥇 Top Performers"
                        )

                        top_display = (
                            top_performers
                            .reset_index(drop=True)
                            .copy()
                        )

                        top_display.insert(
                            0,
                            "Rank",
                            range(
                                1,
                                len(top_display) + 1
                            )
                        )

                        st.dataframe(
                            top_display,
                            use_container_width=True,
                            hide_index=True
                        )

                    with col2:

                        st.subheader(
                            "📉 Bottom Performers"
                        )

                        bottom_display = (
                            bottom_performers
                            .reset_index(drop=True)
                            .copy()
                        )

                        bottom_display.insert(
                            0,
                            "Rank",
                            range(
                                1,
                                len(bottom_display) + 1
                            )
                        )

                        st.dataframe(
                            bottom_display,
                            use_container_width=True,
                            hide_index=True
                        )

                    st.divider()

                    st.subheader(
                        "📊 Top Performer Visualization"
                    )

                    chart_data = (
                        top_performers
                        .sort_values(
                            "Performance",
                            ascending=True
                        )
                    )

                    fig, ax = plt.subplots(
                        figsize=(10, 5)
                    )

                    ax.barh(
                        chart_data[
                            selected_dimension
                        ].astype(str),
                        chart_data[
                            "Performance"
                        ]
                    )

                    ax.set_xlabel(
                        selected_metric
                    )

                    ax.set_ylabel(
                        selected_dimension
                    )

                    ax.set_title(
                        f"Top {top_n} "
                        f"{selected_dimension} by "
                        f"{selected_metric}"
                    )

                    plt.tight_layout()

                    st.pyplot(
                        fig,
                        use_container_width=True
                    )

                    plt.close(fig)

                    with st.expander(
                        "📋 View Complete Performance Data"
                    ):

                        st.dataframe(
                            performance_data,
                            use_container_width=True,
                            hide_index=True
                        )

                    with st.expander(
                        "⚙️ Performance Analysis Configuration"
                    ):

                        config = st.session_state.performance_config

                        config_df = pd.DataFrame({
                            "Setting": [
                                "Dimension",
                                "Metric",
                                "Aggregation",
                                "Top / Bottom N",
                                "Dataset"
                            ],
                            "Value": [
                                config.get(
                                    "dimension",
                                    "-"
                                ),
                                config.get(
                                    "metric",
                                    "-"
                                ),
                                config.get(
                                    "aggregation",
                                    "-"
                                ),
                                config.get(
                                    "top_n",
                                    "-"
                                ),
                                config.get(
                                    "analysis_source",
                                    "-"
                                )
                            ]
                        })

                        st.dataframe(
                            config_df,
                            use_container_width=True,
                            hide_index=True
                        )

                else:

                    st.info(
                        "Configure Performance Analysis above "
                        "to generate top performers, bottom "
                        "performers and performance insights."
                    )

                # ====================================================
                # INSIGHTS TAB
                # ====================================================

                with insights_tab:

                    st.header("🤖 Business Insights")

                    st.caption(
                        f"Analysis source: **{analysis_source}**"
                    )

                    st.write(
                        "Transform your dataset analysis into actionable business "
                        "findings, risks, trends and recommendations."
                    )

                    st.caption(
                        "Insights are generated from completed Performance Analytics "
                        "and supporting trend, correlation, outlier and data-quality analysis."
                    )

                    # ============================================================
                    # READ SAVED ANALYSIS RESULTS
                    # ============================================================

                    performance_data = st.session_state.get(
                        "performance_data",
                        pd.DataFrame()
                    )

                    performance_summary = st.session_state.get(
                        "performance_summary",
                        {}
                    )

                    performance_config = st.session_state.get(
                        "performance_config",
                        {}
                    )

                    trend_data_for_insights = st.session_state.get(
                        "trend_data",
                        pd.DataFrame()
                    )

                    trend_config_for_insights = st.session_state.get(
                        "trend_config",
                        {}
                    )

                    # ============================================================
                    # SUPPORTING ANALYSIS
                    # These are used by insights.py but are NOT displayed as
                    # duplicate analysis sections.
                    # ============================================================

                    try:

                        insight_correlation_matrix = (
                            generate_correlation_matrix(
                                analysis_df
                            )
                        )

                    except Exception:

                        insight_correlation_matrix = pd.DataFrame()


                    insight_correlation_threshold = st.session_state.get(
                        "correlation_threshold",
                        0.7
                    )


                    try:

                        if not insight_correlation_matrix.empty:

                            insight_strong_correlations = (
                                find_strong_correlations(
                                    insight_correlation_matrix,
                                    threshold=insight_correlation_threshold
                                )
                            )

                        else:

                            insight_strong_correlations = pd.DataFrame()

                    except Exception:

                        insight_strong_correlations = pd.DataFrame()


                    # ============================================================
                    # OUTLIER SUPPORTING ANALYSIS
                    # ============================================================

                    insight_detection_method = st.session_state.get(
                        "outlier_detection_method",
                        "IQR"
                    )

                    insight_iqr_multiplier = st.session_state.get(
                        "iqr_multiplier",
                        1.5
                    )

                    insight_zscore_threshold = st.session_state.get(
                        "zscore_threshold",
                        3.0
                    )


                    try:

                        if insight_detection_method == "IQR":

                            insight_outlier_summary = (
                                detect_iqr_outliers(
                                    analysis_df,
                                    multiplier=insight_iqr_multiplier
                                )
                            )

                        else:

                            insight_outlier_summary = (
                                detect_zscore_outliers(
                                    analysis_df,
                                    threshold=insight_zscore_threshold
                                )
                            )

                    except Exception:

                        insight_outlier_summary = pd.DataFrame()


                    # ============================================================
                    # PERFORMANCE PREREQUISITE
                    # ============================================================

                    performance_analysis_ready = (
                        isinstance(performance_data, pd.DataFrame)
                        and not performance_data.empty
                        and isinstance(performance_summary, dict)
                        and bool(performance_summary)
                        and isinstance(performance_config, dict)
                        and bool(performance_config)
                    )

                    if performance_analysis_ready:

                        st.success(
                            "✓ Performance Analytics completed — "
                            "Insights are ready to be generated."
                        )

                    else:

                        st.warning(
                            "⚠️ Performance Analytics is required before "
                            "Business Insights can be generated."
                        )

                        st.info(
                            "Go to the **Performance** tab, configure your "
                            "dimension, metric and aggregation, and click "
                            "**Analyze Performance** first."
                        )

                    # ============================================================
                    # INSIGHT COVERAGE
                    # ============================================================

                    coverage = {

                        "Data Quality": True,

                        "Trend": (
                            not trend_data_for_insights.empty
                        ),

                        "Performance": (
                            not performance_data.empty
                        ),

                        "Correlation": (
                            not insight_correlation_matrix.empty
                        ),

                        "Outliers": (
                            not insight_outlier_summary.empty
                        )
                    }


                    st.subheader("🔎 Insight Coverage")


                    coverage_cols = st.columns(5)


                    for col, (label, available) in zip(
                        coverage_cols,
                        coverage.items()
                    ):

                        if available:

                            col.success(
                                f"✓ {label}"
                            )

                        else:

                            col.warning(
                                f"○ {label}"
                            )


                    unavailable = [
                        name
                        for name, available in coverage.items()
                        if not available
                    ]


                    if unavailable:

                        st.caption(
                            "Additional insight categories can be generated after "
                            "their corresponding analysis is completed: "
                            + ", ".join(unavailable)
                            + "."
                        )


                    st.divider()


                    # ============================================================
                    # GENERATE / CLEAR BUTTONS
                    # ============================================================

                    button_col1, button_col2 = st.columns(
                        [3, 1]
                    )


                    with button_col1:

                        generate_insights_button = st.button(
                            "🤖 Generate Business Insights",
                            type="primary",
                            use_container_width=True,
                            disabled=not performance_analysis_ready,
                            key="generate_business_insights_button_v2"
                        )


                    with button_col2:

                        clear_insights_button = st.button(
                            "🗑️ Clear",
                            use_container_width=True,
                            key="clear_business_insights_button_v2"
                        )


                    # ============================================================
                    # CLEAR INSIGHTS
                    # ============================================================

                    if clear_insights_button:

                        st.session_state.business_insights = (
                            pd.DataFrame()
                        )

                        st.session_state.insights_config = {}

                        # Remove old filter state so a future generation starts
                        # with "All Categories".
                        if "insight_category_filter_v2" in st.session_state:

                            del st.session_state[
                                "insight_category_filter_v2"
                            ]

                        st.rerun()


                    # ============================================================
                    # GENERATE INSIGHTS
                    #
                    # IMPORTANT:
                    # Only generation is inside this button block.
                    # DISPLAYING SAVED INSIGHTS happens BELOW this block.
                    # ============================================================

                    if generate_insights_button:

                        try:

                            if not performance_analysis_ready:

                                raise ValueError(
                                    "Performance Analytics must be completed "
                                    "before Business Insights can be generated."
                                )

                            # ----------------------------------------------------
                            # PROFILE
                            # ----------------------------------------------------

                            insight_profile = generate_profile(
                                analysis_df
                            )


                            # ----------------------------------------------------
                            # TREND INFORMATION
                            # ----------------------------------------------------

                            trend_direction_for_insights = None

                            percentage_change_for_insights = 0.0

                            trend_metric_for_insights = (
                                trend_config_for_insights.get(
                                    "metric_column"
                                )
                            )


                            if (
                                not trend_data_for_insights.empty
                                and trend_metric_for_insights
                            ):

                                trend_direction_for_insights = (
                                    calculate_trend_direction(
                                        trend_data_for_insights
                                    )
                                )

                                percentage_change_for_insights = (
                                    calculate_percentage_change(
                                        trend_data_for_insights
                                    )
                                )


                            # ----------------------------------------------------
                            # PERFORMANCE INFORMATION
                            # ----------------------------------------------------

                            dimension_for_insights = (
                                performance_config.get(
                                    "dimension"
                                )
                            )

                            metric_for_insights = (
                                performance_config.get(
                                    "metric"
                                )
                            )


                            # ----------------------------------------------------
                            # GENERATE ALL INSIGHTS
                            # ----------------------------------------------------

                            generated_insights = generate_all_insights(

                                profile=insight_profile,

                                df=analysis_df,

                                trend_data=(
                                    trend_data_for_insights
                                    if not trend_data_for_insights.empty
                                    else None
                                ),

                                trend_direction=(
                                    trend_direction_for_insights
                                ),

                                percentage_change=(
                                    percentage_change_for_insights
                                ),

                                metric_column=(
                                    trend_metric_for_insights
                                ),

                                performance_data=(
                                    performance_data
                                    if not performance_data.empty
                                    else None
                                ),

                                performance_summary=(
                                    performance_summary
                                    if performance_summary
                                    else None
                                ),

                                dimension_column=(
                                    dimension_for_insights
                                ),

                                performance_metric=(
                                    metric_for_insights
                                ),

                                outlier_summary=(
                                    insight_outlier_summary
                                    if not insight_outlier_summary.empty
                                    else None
                                ),

                                strong_correlations=(
                                    insight_strong_correlations
                                    if not insight_strong_correlations.empty
                                    else None
                                ),

                                correlation_matrix=(
                                    insight_correlation_matrix
                                    if not insight_correlation_matrix.empty
                                    else None
                                ),

                                outlier_method=(
                                    insight_detection_method
                                ),

                                outlier_multiplier=(
                                    insight_iqr_multiplier
                                ),

                                zscore_threshold=(
                                    insight_zscore_threshold
                                )
                            )


                            # ----------------------------------------------------
                            # SAVE INSIGHTS
                            # ----------------------------------------------------

                            st.session_state.business_insights = (
                                generated_insights.copy()
                            )


                            st.session_state.insights_config = {

                                "analysis_source": analysis_source,

                                "trend_config":
                                    trend_config_for_insights.copy(),

                                "performance_config":
                                    performance_config.copy(),

                                "outlier_method":
                                    insight_detection_method,

                                "iqr_multiplier":
                                    insight_iqr_multiplier,

                                "zscore_threshold":
                                    insight_zscore_threshold,

                                "correlation_threshold":
                                    insight_correlation_threshold
                            }


                            # Reset filter after generating a completely new
                            # insight collection.

                            if "insight_category_filter_v2" in st.session_state:

                                del st.session_state[
                                    "insight_category_filter_v2"
                                ]


                            st.success(
                                f"Generated "
                                f"{len(generated_insights)} "
                                f"actionable insight(s)."
                            )


                        except Exception as e:

                            st.error(
                                f"Could not generate business insights: {e}"
                            )


                    # ============================================================
                    # IMPORTANT:
                    # ALWAYS READ SAVED INSIGHTS AFTER THE GENERATION BLOCK
                    #
                    # This is what makes the insights survive Streamlit reruns.
                    # ============================================================

                    saved_insights = st.session_state.get(
                        "business_insights",
                        pd.DataFrame()
                    )


                    # ============================================================
                    # NO INSIGHTS YET
                    # ============================================================

                    if saved_insights.empty:

                        st.info(
                            "No business insights have been generated yet. "
                            "Run the analyses you want to include and click "
                            "'Generate Business Insights'."
                        )


                    # ============================================================
                    # DISPLAY GENERATED INSIGHTS
                    # ============================================================

                    else:

                        # ========================================================
                        # NORMALIZE DATA
                        # ========================================================

                        display_insights = saved_insights.copy()


                        if "Category" not in display_insights.columns:

                            display_insights["Category"] = (
                                "Other"
                            )


                        if "Type" not in display_insights.columns:

                            display_insights["Type"] = (
                                "Information"
                            )


                        if "Priority" not in display_insights.columns:

                            display_insights["Priority"] = (
                                "Medium"
                            )


                        if "Insight" not in display_insights.columns:

                            display_insights["Insight"] = ""


                        if "Recommendation" not in display_insights.columns:

                            display_insights["Recommendation"] = ""


                        # ========================================================
                        # SUMMARY METRICS
                        # ========================================================

                        total_insights = len(
                            display_insights
                        )


                        warning_count = int(
                            (
                                display_insights["Type"]
                                .astype(str)
                                .str.lower()
                                == "warning"
                            ).sum()
                        )


                        positive_count = int(
                            (
                                display_insights["Type"]
                                .astype(str)
                                .str.lower()
                                == "positive"
                            ).sum()
                        )


                        high_priority_count = int(
                            (
                                display_insights["Priority"]
                                .astype(str)
                                .str.lower()
                                == "high"
                            ).sum()
                        )


                        recommendation_count = int(
                            (
                                display_insights["Category"]
                                .astype(str)
                                .str.lower()
                                == "business recommendation"
                            ).sum()
                        )


                        st.subheader(
                            "📊 Business Insight Summary"
                        )


                        kpi1, kpi2, kpi3, kpi4 = st.columns(4)


                        kpi1.metric(
                            "Total Insights",
                            total_insights
                        )


                        kpi2.metric(
                            "⚠️ Warnings",
                            warning_count
                        )


                        kpi3.metric(
                            "🔥 High Priority",
                            high_priority_count
                        )


                        kpi4.metric(
                            "🎯 Actions",
                            recommendation_count
                        )


                        # ========================================================
                        # EXECUTIVE INSIGHT SUMMARY
                        # ========================================================

                        st.subheader(
                            "🧠 Executive Insight Summary"
                        )

                        summary_col1, summary_col2 = st.columns(2)

                        with summary_col1:

                            if high_priority_count > 0:
                                st.warning(
                                    f"**{high_priority_count} high-priority "
                                    f"finding(s)** require attention."
                                )
                            else:
                                st.success(
                                    "No high-priority risks were identified "
                                    "in the current analysis."
                                )

                            if warning_count > 0:
                                st.warning(
                                    f"The analysis identified "
                                    f"**{warning_count} warning(s)** that may "
                                    f"require investigation."
                                )
                            else:
                                st.success(
                                    "No major warning signals were identified."
                                )

                        with summary_col2:

                            if positive_count > 0:
                                st.success(
                                    f"**{positive_count} positive finding(s)** "
                                    f"indicate areas of strength."
                                )

                            if recommendation_count > 0:
                                st.info(
                                    f"**{recommendation_count} actionable "
                                    f"recommendation(s)** were generated from "
                                    f"the combined analysis."
                                )

                            st.caption(
                                "These findings combine data quality, trend, "
                                "performance, outlier and correlation analysis "
                                "where available."
                            )


                        # ========================================================
                        # PRIORITY DISTRIBUTION
                        # ========================================================

                        st.subheader(
                            "🎯 Insight Priority Distribution"
                        )

                        priority_counts = (
                            display_insights["Priority"]
                            .astype(str)
                            .str.title()
                            .value_counts()
                        )

                        priority_df = pd.DataFrame({
                            "Priority": [
                                "High",
                                "Medium",
                                "Low"
                            ],
                            "Count": [
                                int(priority_counts.get("High", 0)),
                                int(priority_counts.get("Medium", 0)),
                                int(priority_counts.get("Low", 0))
                            ]
                        })

                        priority_col1, priority_col2 = st.columns([1, 2])

                        with priority_col1:
                            st.dataframe(
                                priority_df,
                                use_container_width=True,
                                hide_index=True
                            )

                        with priority_col2:
                            priority_fig = px.bar(
                                priority_df,
                                x="Priority",
                                y="Count",
                                title="Insights by Priority"
                            )

                            priority_fig.update_layout(
                                height=300,
                                margin=dict(
                                    l=20,
                                    r=20,
                                    t=50,
                                    b=20
                                ),
                                xaxis_title="Priority",
                                yaxis_title="Number of Insights"
                            )

                            st.plotly_chart(
                                priority_fig,
                                use_container_width=True
                            )


                        st.divider()


                        # ========================================================
                        # PRIORITY ACTIONS
                        # ========================================================

                        recommendations = display_insights[
                            display_insights["Category"]
                            .astype(str)
                            .str.lower()
                            == "business recommendation"
                        ].copy()


                        if not recommendations.empty:

                            st.subheader(
                                "🎯 Priority Actions"
                            )

                            st.caption(
                                "Recommended actions generated from the combined "
                                "analysis of your dataset."
                            )


                            priority_order = {
                                "High": 0,
                                "Medium": 1,
                                "Low": 2
                            }


                            recommendations["_priority_order"] = (
                                recommendations["Priority"]
                                .map(priority_order)
                                .fillna(3)
                            )


                            recommendations = (
                                recommendations
                                .sort_values(
                                    "_priority_order"
                                )
                                .drop(
                                    columns=["_priority_order"]
                                )
                            )


                            for _, row in recommendations.iterrows():

                                priority = str(
                                    row.get(
                                        "Priority",
                                        "Medium"
                                    )
                                )

                                insight_text = str(
                                    row.get(
                                        "Insight",
                                        ""
                                    )
                                )

                                recommendation = str(
                                    row.get(
                                        "Recommendation",
                                        ""
                                    )
                                )


                                with st.container(
                                    border=True
                                ):

                                    if priority == "High":

                                        st.markdown(
                                            f"### 🔴 High Priority"
                                        )

                                    elif priority == "Medium":

                                        st.markdown(
                                            f"### 🟠 Medium Priority"
                                        )

                                    else:

                                        st.markdown(
                                            f"### 🟢 Low Priority"
                                        )


                                    st.markdown(
                                        insight_text
                                    )


                                    st.markdown(
                                        "**Recommended Action**"
                                    )

                                    st.write(
                                        recommendation
                                    )


                        # ========================================================
                        # EXPLORE INSIGHTS
                        # ========================================================

                        st.divider()


                        st.subheader(
                            "🔎 Explore Insights"
                        )


                        analytical_insights = display_insights[
                            display_insights["Category"]
                            .astype(str)
                            .str.lower()
                            != "business recommendation"
                        ].copy()


                        if not analytical_insights.empty:

                            available_categories = []


                            category_order = [

                                "Data Quality",

                                "Trend",

                                "Performance",

                                "Outliers",

                                "Correlation",

                                "Cross-analysis"
                            ]


                            for category in category_order:

                                if category in (
                                    analytical_insights["Category"]
                                    .astype(str)
                                    .unique()
                                ):

                                    available_categories.append(
                                        category
                                    )


                            # Add any categories that the insight engine may
                            # produce in the future.

                            for category in (
                                analytical_insights["Category"]
                                .astype(str)
                                .unique()
                            ):

                                if category not in available_categories:

                                    available_categories.append(
                                        category
                                    )


                            category_options = [
                                "All Categories"
                            ] + available_categories


                            selected_insight_category = st.selectbox(

                                "Filter insights by category",

                                category_options,

                                key="insight_category_filter_v2"
                            )


                            # ----------------------------------------------------
                            # FILTER ONLY DISPLAYED INSIGHTS
                            #
                            # The saved DataFrame is NEVER modified.
                            # ----------------------------------------------------

                            if (
                                selected_insight_category
                                == "All Categories"
                            ):

                                filtered_insights = (
                                    analytical_insights.copy()
                                )

                            else:

                                filtered_insights = (
                                    analytical_insights[
                                        analytical_insights[
                                            "Category"
                                        ].astype(str)
                                        == selected_insight_category
                                    ].copy()
                                )


                            # ====================================================
                            # DISPLAY FILTERED FINDINGS
                            # ====================================================

                            if filtered_insights.empty:

                                st.info(
                                    "No analytical findings are available "
                                    "for this category."
                                )

                            else:

                                for category in category_order:

                                    category_rows = (
                                        filtered_insights[
                                            filtered_insights[
                                                "Category"
                                            ].astype(str)
                                            == category
                                        ]
                                    )


                                    if category_rows.empty:

                                        continue


                                    st.markdown(
                                        f"## {category}"
                                    )


                                    for _, row in (
                                        category_rows.iterrows()
                                    ):

                                        insight_type = str(
                                            row.get(
                                                "Type",
                                                "Information"
                                            )
                                        )

                                        priority = str(
                                            row.get(
                                                "Priority",
                                                "Medium"
                                            )
                                        )

                                        insight_text = str(
                                            row.get(
                                                "Insight",
                                                ""
                                            )
                                        )

                                        recommendation = str(
                                            row.get(
                                                "Recommendation",
                                                ""
                                            )
                                        )


                                        # ----------------------------------------
                                        # WARNING
                                        # ----------------------------------------

                                        if insight_type == "Warning":

                                            with st.container(
                                                border=True
                                            ):

                                                st.markdown(
                                                    f"### ⚠️ {insight_text}"
                                                )

                                                st.caption(
                                                    f"Priority: **{priority}**"
                                                )

                                                st.markdown(
                                                    "**Recommended Action**"
                                                )

                                                st.write(
                                                    recommendation
                                                )


                                        # ----------------------------------------
                                        # POSITIVE
                                        # ----------------------------------------

                                        elif insight_type == "Positive":

                                            with st.container(
                                                border=True
                                            ):

                                                st.markdown(
                                                    f"### ✅ {insight_text}"
                                                )

                                                st.caption(
                                                    f"Priority: **{priority}**"
                                                )

                                                st.markdown(
                                                    "**Recommended Action**"
                                                )

                                                st.write(
                                                    recommendation
                                                )


                                        # ----------------------------------------
                                        # INFORMATION
                                        # ----------------------------------------

                                        else:

                                            with st.container(
                                                border=True
                                            ):

                                                st.markdown(
                                                    f"### ℹ️ {insight_text}"
                                                )

                                                st.caption(
                                                    f"Priority: **{priority}**"
                                                )

                                                st.markdown(
                                                    "**Recommended Action**"
                                                )

                                                st.write(
                                                    recommendation
                                                )


                        else:

                            st.info(
                                "No analytical findings are available."
                            )


                        # ========================================================
                        # INSIGHT DISTRIBUTION
                        # ========================================================

                        st.divider()


                        st.subheader(
                            "📈 Insight Distribution"
                        )


                        distribution_cols = st.columns(3)


                        category_counts = (
                            analytical_insights[
                                "Category"
                            ]
                            .value_counts()
                            .to_dict()
                        )


                        distribution_cols[0].metric(
                            "Data Quality",
                            category_counts.get(
                                "Data Quality",
                                0
                            )
                        )


                        distribution_cols[1].metric(
                            "Cross-analysis",
                            category_counts.get(
                                "Cross-analysis",
                                0
                            )
                        )


                        distribution_cols[2].metric(
                            "Other Analytical",
                            sum(
                                value
                                for key, value
                                in category_counts.items()
                                if key not in [
                                    "Data Quality",
                                    "Cross-analysis"
                                ]
                            )
                        )


                        # ========================================================
                        # COMPLETE REPORT
                        # ========================================================

                        st.divider()


                        with st.expander(
                            "📋 View Complete Insight Report"
                        ):

                            complete_report = (
                                display_insights.copy()
                            )


                            if "_priority_order" in complete_report.columns:

                                complete_report = (
                                    complete_report.drop(
                                        columns=["_priority_order"]
                                    )
                                )


                            st.dataframe(
                                complete_report,
                                use_container_width=True,
                                hide_index=True
                            )


                            insights_csv = (
                                complete_report
                                .to_csv(index=False)
                                .encode("utf-8")
                            )

                            st.download_button(
                                label="⬇️ Download Insights CSV",
                                data=insights_csv,
                                file_name="business_insights.csv",
                                mime="text/csv",
                                key="download_business_insights_csv"
                            )


                        # ========================================================
                        # GENERATION CONFIGURATION
                        # ========================================================

                        saved_insight_config = (
                            st.session_state.get(
                                "insights_config",
                                {}
                            )
                        )


                        if saved_insight_config:

                            with st.expander(
                                "⚙️ Insight Generation Configuration"
                            ):

                                trend_cfg = (
                                    saved_insight_config.get(
                                        "trend_config",
                                        {}
                                    )
                                )


                                performance_cfg = (
                                    saved_insight_config.get(
                                        "performance_config",
                                        {}
                                    )
                                )


                                config_rows = {

                                    "Analysis Dataset":
                                        saved_insight_config.get(
                                            "analysis_source",
                                            "-"
                                        ),

                                    "Trend Metric":
                                        trend_cfg.get(
                                            "metric_column",
                                            "Not generated"
                                        ),

                                    "Performance Dimension":
                                        performance_cfg.get(
                                            "dimension",
                                            "Not analyzed"
                                        ),

                                    "Performance Metric":
                                        performance_cfg.get(
                                            "metric",
                                            "Not analyzed"
                                        ),

                                    "Performance Aggregation":
                                        performance_cfg.get(
                                            "aggregation",
                                            "Not analyzed"
                                        ),

                                    "Outlier Method":
                                        saved_insight_config.get(
                                            "outlier_method",
                                            "-"
                                        ),

                                    "Correlation Threshold":
                                        saved_insight_config.get(
                                            "correlation_threshold",
                                            "-"
                                        )
                                }


                                config_df = pd.DataFrame({

                                    "Setting":
                                        list(
                                            config_rows.keys()
                                        ),

                                    "Value":
                                        list(
                                            config_rows.values()
                                        )
                                })


                                st.dataframe(
                                    config_df,
                                    use_container_width=True,
                                    hide_index=True
                                )

    except Exception as e:

        st.error(
            f"Could not process the file: {e}"
        )
