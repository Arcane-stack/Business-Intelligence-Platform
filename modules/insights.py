# import pandas as pd
# import numpy as np


# # ==================================================
# # HELPERS
# # ==================================================

# def _insight(category, insight_type, text, recommendation, priority="Medium"):
#     return {
#         "Category": category,
#         "Type": insight_type,
#         "Priority": priority,
#         "Insight": text,
#         "Recommendation": recommendation,
#     }


# def _safe_float(value, default=0.0):
#     try:
#         value = float(value)
#         return value if np.isfinite(value) else default
#     except (TypeError, ValueError):
#         return default


# def _severity(percent, low=1, medium=5, high=15):
#     if percent <= low:
#         return "Low"
#     if percent <= medium:
#         return "Moderate"
#     if percent <= high:
#         return "High"
#     return "Critical"


# def _correlation_column(df):
#     for col in ["Correlation", "correlation", "Value", "Coefficient"]:
#         if col in df.columns:
#             return col
#     return None


# def _correlation_pair_columns(df):
#     first = second = None
#     for col in ["Column 1", "Column1", "Variable 1", "Variable1", "Feature 1", "Feature1", "X"]:
#         if col in df.columns:
#             first = col
#             break
#     for col in ["Column 2", "Column2", "Variable 2", "Variable2", "Feature 2", "Feature2", "Y"]:
#         if col in df.columns:
#             second = col
#             break
#     return first, second


# # ==================================================
# # DATA QUALITY INSIGHTS
# # ==================================================

# def generate_data_quality_insights(profile, df=None):
#     insights = []

#     missing_values = int(profile.get("missing_values", 0) or 0)
#     duplicate_rows = int(profile.get("duplicate_rows", 0) or 0)
#     rows = int(profile.get("rows", 0) or 0)
#     columns = int(profile.get("columns", 0) or 0)

#     total_cells = max(rows * columns, 1)
#     missing_percentage = (missing_values / total_cells) * 100
#     duplicate_percentage = (duplicate_rows / max(rows, 1)) * 100

#     missing_severity = _severity(missing_percentage, 1, 5, 15)
#     duplicate_severity = _severity(duplicate_percentage, 1, 5, 15)

#     # Missing-value severity
#     if missing_values == 0:
#         insights.append(_insight(
#             "Data Quality", "Positive",
#             "No missing values were detected. Data completeness is currently strong.",
#             "No missing-value treatment is required; continue monitoring new data loads.",
#             "Low"
#         ))
#     else:
#         insight_type = "Warning" if missing_severity in {"High", "Critical"} else "Information"
#         priority = "High" if missing_severity in {"High", "Critical"} else "Medium"
#         insights.append(_insight(
#             "Data Quality", insight_type,
#             f"The dataset contains {missing_values:,} missing cells ({missing_percentage:.2f}% of all cells), giving missing data a {missing_severity.lower()} severity.",
#             "Prioritize columns with the highest missingness and apply an appropriate imputation, exclusion, or data-collection fix.",
#             priority
#         ))

#     # Duplicate severity
#     if duplicate_rows == 0:
#         insights.append(_insight(
#             "Data Quality", "Positive",
#             "No duplicate rows were detected.",
#             "No duplicate-row removal is currently required.",
#             "Low"
#         ))
#     else:
#         insight_type = "Warning" if duplicate_severity in {"High", "Critical"} else "Information"
#         priority = "High" if duplicate_severity in {"High", "Critical"} else "Medium"
#         insights.append(_insight(
#             "Data Quality", insight_type,
#             f"{duplicate_rows:,} duplicate rows were detected ({duplicate_percentage:.2f}% of records), a {duplicate_severity.lower()} data-quality issue.",
#             "Review whether duplicates are legitimate repeated events; otherwise remove or prevent them before downstream analysis.",
#             priority
#         ))

#     # Columns with the most missing data
#     if df is not None and not df.empty:
#         missing_by_column = df.isna().sum()
#         missing_by_column = missing_by_column[missing_by_column > 0].sort_values(ascending=False)

#         if not missing_by_column.empty:
#             top_missing = missing_by_column.head(5)
#             details = []
#             for col, count in top_missing.items():
#                 pct = (count / len(df)) * 100
#                 details.append(f"{col}: {int(count):,} ({pct:.1f}%)")

#             top_column = str(top_missing.index[0])
#             top_pct = (top_missing.iloc[0] / len(df)) * 100
#             insights.append(_insight(
#                 "Data Quality", "Warning" if top_pct > 15 else "Information",
#                 "Columns with the most missing data: " + "; ".join(details) + ".",
#                 f"Investigate `{top_column}` first because it has the highest missing-value concentration.",
#                 "High" if top_pct > 15 else "Medium"
#             ))

#         # Overall risk
#         risk_score = 0
#         max_column_missing_pct = 0.0
#         if df is not None and not df.empty:
#             max_column_missing_pct = float((df.isna().sum() / len(df) * 100).max())

#         if missing_percentage > 15 or max_column_missing_pct > 25:
#             risk_score += 2
#         elif missing_percentage > 5 or max_column_missing_pct > 10:
#             risk_score += 1
#         if duplicate_percentage > 15:
#             risk_score += 2
#         elif duplicate_percentage > 5:
#             risk_score += 1

#         if risk_score >= 3:
#             risk = "High"
#             risk_type = "Warning"
#             priority = "High"
#         elif risk_score >= 1:
#             risk = "Moderate"
#             risk_type = "Information"
#             priority = "Medium"
#         else:
#             risk = "Low"
#             risk_type = "Positive"
#             priority = "Low"

#         insights.append(_insight(
#             "Data Quality", risk_type,
#             f"Overall data-quality risk is assessed as {risk.lower()} based on missingness and duplicate records.",
#             "Resolve high-impact quality issues before making sensitive business decisions from the dataset.",
#             priority
#         ))

#     return insights


# # ==================================================
# # TREND INSIGHTS
# # ==================================================

# def generate_trend_insights(trend_data, trend_direction, percentage_change, metric_column):
#     insights = []

#     if trend_data is None or trend_data.empty:
#         return insights

#     data = trend_data.copy()
#     if "Value" not in data.columns:
#         return insights

#     data["Value"] = pd.to_numeric(data["Value"], errors="coerce")
#     data = data.dropna(subset=["Value"]).reset_index(drop=True)
#     if data.empty:
#         return insights

#     # Direction and percentage change
#     if trend_direction == "Increasing":
#         insight_type, priority = "Positive", "Medium"
#     elif trend_direction == "Decreasing":
#         insight_type, priority = "Warning", "High"
#     else:
#         insight_type, priority = "Information", "Medium"

#     insights.append(_insight(
#         "Trend", insight_type,
#         f"{metric_column} is {str(trend_direction).lower()} with an overall change of {percentage_change:+.2f}%.",
#         "Sustain the drivers of growth if positive; if declining, investigate the underlying causes and corrective actions.",
#         priority
#     ))

#     # Period-to-period changes
#     changes = data["Value"].pct_change().replace([np.inf, -np.inf], np.nan).dropna()
#     if not changes.empty:
#         max_growth_idx = changes.idxmax()
#         max_decline_idx = changes.idxmin()
#         growth_pct = changes.loc[max_growth_idx] * 100
#         decline_pct = changes.loc[max_decline_idx] * 100

#         def period_label(idx):
#             if "Date" in data.columns:
#                 return str(data.loc[idx, "Date"])
#             return f"period {idx + 1}"

#         insights.append(_insight(
#             "Trend", "Positive" if growth_pct > 0 else "Information",
#             f"Strongest growth period: {period_label(max_growth_idx)} with a {growth_pct:+.2f}% period-over-period change.",
#             "Investigate what changed during this period and determine whether the conditions can be replicated.",
#             "Medium"
#         ))

#         insights.append(_insight(
#             "Trend", "Warning" if decline_pct < 0 else "Information",
#             f"Strongest decline period: {period_label(max_decline_idx)} with a {decline_pct:+.2f}% period-over-period change.",
#             "Review operational, market, or data factors associated with this period before assuming the decline is structural.",
#             "High" if decline_pct < -10 else "Medium"
#         ))

#         volatility = changes.std() * 100
#         if np.isnan(volatility):
#             volatility = 0

#         if volatility >= 20:
#             volatility_label = "high"
#             volatility_type = "Warning"
#             volatility_priority = "High"
#         elif volatility >= 10:
#             volatility_label = "moderate"
#             volatility_type = "Information"
#             volatility_priority = "Medium"
#         else:
#             volatility_label = "low"
#             volatility_type = "Positive"
#             volatility_priority = "Low"

#         insights.append(_insight(
#             "Trend", volatility_type,
#             f"Trend volatility is {volatility_label}, with a period-to-period change standard deviation of {volatility:.2f}%.",
#             "Use shorter monitoring intervals when volatility is high and investigate unusually large period-to-period movements.",
#             volatility_priority
#         ))

#     # Recent vs overall performance
#     recent_n = min(3, len(data))
#     recent_mean = data["Value"].tail(recent_n).mean()
#     overall_mean = data["Value"].mean()
#     if overall_mean != 0:
#         recent_difference = ((recent_mean - overall_mean) / abs(overall_mean)) * 100
#     else:
#         recent_difference = 0

#     recent_type = "Positive" if recent_difference > 5 else "Warning" if recent_difference < -5 else "Information"
#     insights.append(_insight(
#         "Trend", recent_type,
#         f"The most recent {recent_n} periods are {recent_difference:+.2f}% versus the overall average level.",
#         "Compare recent conditions with the historical baseline to determine whether the latest movement is temporary or a sustained shift.",
#         "Medium" if abs(recent_difference) > 5 else "Low"
#     ))

#     return insights


# # ==================================================
# # PERFORMANCE INSIGHTS
# # ==================================================

# def generate_performance_insights(performance_data, summary, dimension_column, metric_column):
#     insights = []

#     if performance_data is None or performance_data.empty or not summary:
#         return insights

#     data = performance_data.copy()
#     if "Performance" not in data.columns:
#         return insights

#     data["Performance"] = pd.to_numeric(data["Performance"], errors="coerce")
#     data = data.dropna(subset=["Performance"])
#     if data.empty:
#         return insights

#     average = _safe_float(summary.get("average_performance"), data["Performance"].mean())
#     highest = _safe_float(summary.get("highest_performance"), data["Performance"].max())
#     lowest = _safe_float(summary.get("lowest_performance"), data["Performance"].min())
#     top = summary.get("top_performer", data.iloc[data["Performance"].idxmax()][dimension_column])
#     bottom = summary.get("bottom_performer", data.iloc[data["Performance"].idxmin()][dimension_column])

#     # Top / bottom performer
#     insights.append(_insight(
#         "Performance", "Positive",
#         f"{top} is the top-performing {dimension_column} based on {metric_column} ({highest:,.2f}).",
#         f"Study the factors associated with {top} and identify practices that can be replicated elsewhere.",
#         "Medium"
#     ))

#     insights.append(_insight(
#         "Performance", "Warning",
#         f"{bottom} is the lowest-performing {dimension_column} based on {metric_column} ({lowest:,.2f}).",
#         f"Investigate the drivers of {bottom}'s performance and prioritize targeted corrective action.",
#         "High"
#     ))

#     # Gap
#     gap = highest - lowest
#     gap_pct = (gap / abs(average) * 100) if average != 0 else 0
#     insights.append(_insight(
#         "Performance", "Warning" if gap_pct > 50 else "Information",
#         f"The performance gap is {gap:,.2f}, equivalent to {gap_pct:.2f}% of the average performance.",
#         "Investigate why performance varies so widely and determine whether the gap reflects structural differences or improvement opportunities.",
#         "High" if gap_pct > 50 else "Medium"
#     ))

#     # Above/below average entities
#     above = int((data["Performance"] > average).sum())
#     below = int((data["Performance"] < average).sum())
#     total = len(data)
#     insights.append(_insight(
#         "Performance", "Information",
#         f"{above} of {total} entities ({above / total * 100:.1f}%) are above average, while {below} ({below / total * 100:.1f}%) are below average.",
#         "Use the above-average group as a benchmark and prioritize support for consistently below-average entities.",
#         "Medium"
#     ))

#     # Concentration and top contribution
#     total_performance = data["Performance"].sum()
#     top_n = max(1, min(5, int(np.ceil(len(data) * 0.20))))
#     top_n_total = data.nlargest(top_n, "Performance")["Performance"].sum()
#     contribution = (top_n_total / total_performance * 100) if total_performance != 0 else 0
#     concentration_type = "Warning" if contribution >= 60 else "Information"
#     insights.append(_insight(
#         "Performance", concentration_type,
#         f"The top {top_n} entities contribute {contribution:.2f}% of total aggregated performance.",
#         "If concentration is high, reduce dependency on a small number of entities and identify ways to lift the broader group.",
#         "High" if contribution >= 60 else "Medium"
#     ))

#     return insights


# # ==================================================
# # OUTLIER INSIGHTS
# # ==================================================

# def generate_outlier_insights(outlier_summary):
#     insights = []

#     if outlier_summary is None or outlier_summary.empty or "Outliers" not in outlier_summary.columns:
#         return insights

#     data = outlier_summary.copy()
#     data["Outliers"] = pd.to_numeric(data["Outliers"], errors="coerce").fillna(0)
#     if "Outlier %" in data.columns:
#         data["Outlier %"] = pd.to_numeric(data["Outlier %"], errors="coerce").fillna(0)
#     else:
#         data["Outlier %"] = 0.0

#     total_outliers = int(data["Outliers"].sum())
#     if total_outliers == 0:
#         insights.append(_insight(
#             "Outliers", "Positive",
#             "No statistical outliers were detected using the selected method.",
#             "Continue monitoring numerical variables for unusual future changes.",
#             "Low"
#         ))
#         return insights

#     highest = data.loc[data["Outliers"].idxmax()]
#     highest_column = str(highest.get("Column", "Unknown"))
#     highest_count = int(highest["Outliers"])
#     highest_pct = float(highest["Outlier %"])

#     insights.append(_insight(
#         "Outliers", "Warning",
#         f"A total of {total_outliers:,} outlier values were detected. {highest_column} is the most affected column with {highest_count:,} outliers ({highest_pct:.2f}%).",
#         f"Investigate {highest_column} first to determine whether these values are errors, rare legitimate events, or important exceptions.",
#         "High"
#     ))

#     # Unusually high outlier percentages
#     high_pct = data[data["Outlier %"] >= 10].sort_values("Outlier %", ascending=False)
#     if not high_pct.empty:
#         columns = ", ".join(
#             f"{row['Column']} ({row['Outlier %']:.1f}%)"
#             for _, row in high_pct.head(5).iterrows()
#         )
#         insights.append(_insight(
#             "Outliers", "Warning",
#             f"The following columns have unusually high outlier percentages: {columns}.",
#             "Validate these variables for data-entry problems, inconsistent units, or genuine high-variance business events.",
#             "High"
#         ))

#     # Severity
#     max_pct = float(data["Outlier %"].max())
#     if max_pct >= 20:
#         severity = "critical"
#         priority = "High"
#     elif max_pct >= 10:
#         severity = "high"
#         priority = "High"
#     elif max_pct >= 5:
#         severity = "moderate"
#         priority = "Medium"
#     else:
#         severity = "low"
#         priority = "Low"

#     insights.append(_insight(
#         "Outliers", "Warning" if severity in {"high", "critical"} else "Information",
#         f"Overall outlier severity is {severity}, based on the highest detected outlier percentage of {max_pct:.2f}%.",
#         "Do not automatically remove outliers; validate their business meaning before changing the dataset.",
#         priority
#     ))

#     return insights


# # ==================================================
# # CORRELATION INSIGHTS
# # ==================================================

# def generate_correlation_insights(strong_correlations, correlation_matrix=None, performance_metric=None):
#     insights = []

#     if strong_correlations is None:
#         strong_correlations = pd.DataFrame()

#     corr_col = _correlation_column(strong_correlations)

#     if strong_correlations.empty or corr_col is None:
#         insights.append(_insight(
#             "Correlation", "Information",
#             "No strong correlation relationships were detected using the selected threshold.",
#             "Consider reviewing weaker relationships and combining correlation results with domain knowledge.",
#             "Low"
#         ))
#     else:
#         corr = pd.to_numeric(strong_correlations[corr_col], errors="coerce").dropna()
#         positive = corr[corr > 0]
#         negative = corr[corr < 0]

#         if not positive.empty:
#             idx = positive.idxmax()
#             row = strong_correlations.loc[idx]
#             first, second = _correlation_pair_columns(strong_correlations)
#             pair = f"{row[first]} and {row[second]}" if first and second else "the strongest positive pair"
#             value = float(row[corr_col])
#             insights.append(_insight(
#                 "Correlation", "Information",
#                 f"Strongest positive correlation: {pair} ({value:.2f}).",
#                 "Investigate whether the relationship reflects a meaningful business driver; correlation does not prove causation.",
#                 "Medium"
#             ))

#         if not negative.empty:
#             idx = negative.idxmin()
#             row = strong_correlations.loc[idx]
#             first, second = _correlation_pair_columns(strong_correlations)
#             pair = f"{row[first]} and {row[second]}" if first and second else "the strongest negative pair"
#             value = float(row[corr_col])
#             insights.append(_insight(
#                 "Correlation", "Information",
#                 f"Strongest negative correlation: {pair} ({value:.2f}).",
#                 "Investigate whether the inverse relationship could indicate a trade-off, constraint, or confounding factor.",
#                 "Medium"
#             ))

#         insights.append(_insight(
#             "Correlation", "Information",
#             f"{len(strong_correlations)} strong correlation relationship(s) were detected.",
#             "Prioritize relationships that involve the selected performance metric or other key business measures.",
#             "Medium"
#         ))

#     # Potential drivers of selected performance metric
#     if correlation_matrix is not None and performance_metric in getattr(correlation_matrix, "columns", []):
#         series = pd.to_numeric(correlation_matrix[performance_metric], errors="coerce").drop(labels=[performance_metric], errors="ignore").dropna()
#         if not series.empty:
#             top_drivers = series.abs().sort_values(ascending=False).head(3).index.tolist()
#             driver_text = ", ".join(
#                 f"{col} ({series[col]:+.2f})" for col in top_drivers
#             )
#             insights.append(_insight(
#                 "Correlation", "Information",
#                 f"Potential business drivers associated with {performance_metric}: {driver_text}.",
#                 "Investigate these variables as candidate drivers of performance, while validating the relationships with business context or further analysis.",
#                 "High" if top_drivers else "Medium"
#             ))

#     return insights


# # ==================================================
# # CROSS-ANALYSIS INSIGHTS
# # ==================================================

# def generate_cross_analysis_insights(
#     analysis_df=None,
#     performance_data=None,
#     performance_summary=None,
#     dimension_column=None,
#     performance_metric=None,
#     trend_data=None,
#     trend_direction=None,
#     percentage_change=0,
#     correlation_matrix=None,
#     strong_correlations=None,
#     outlier_summary=None,
#     profile=None,
#     outlier_method="IQR",
#     outlier_multiplier=1.5,
#     zscore_threshold=3.0,
# ):
#     insights = []

#     # --------------------------------------------------
#     # Performance + Outliers
#     # --------------------------------------------------
#     if (
#         analysis_df is not None
#         and not analysis_df.empty
#         and performance_data is not None
#         and not performance_data.empty
#         and performance_summary
#         and dimension_column in analysis_df.columns
#         and performance_metric in analysis_df.columns
#     ):
#         temp = analysis_df[[dimension_column, performance_metric]].copy()
#         temp[performance_metric] = pd.to_numeric(temp[performance_metric], errors="coerce")
#         temp = temp.dropna(subset=[performance_metric])

#         if not temp.empty:
#             if outlier_method == "Z-Score":
#                 mean = temp[performance_metric].mean()
#                 std = temp[performance_metric].std()
#                 if std and not np.isnan(std):
#                     outlier_mask = ((temp[performance_metric] - mean) / std).abs() > zscore_threshold
#                 else:
#                     outlier_mask = pd.Series(False, index=temp.index)
#             else:
#                 q1 = temp[performance_metric].quantile(0.25)
#                 q3 = temp[performance_metric].quantile(0.75)
#                 iqr = q3 - q1
#                 outlier_mask = (
#                     (temp[performance_metric] < q1 - outlier_multiplier * iqr)
#                     | (temp[performance_metric] > q3 + outlier_multiplier * iqr)
#                 )

#             outlier_entities = set(temp.loc[outlier_mask, dimension_column].astype(str))
#             top = str(performance_summary.get("top_performer"))
#             bottom = str(performance_summary.get("bottom_performer"))

#             top_outlier = top in outlier_entities
#             bottom_outlier = bottom in outlier_entities

#             if top_outlier or bottom_outlier:
#                 affected = []
#                 if top_outlier:
#                     affected.append(f"top performer {top}")
#                 if bottom_outlier:
#                     affected.append(f"bottom performer {bottom}")
#                 insights.append(_insight(
#                     "Cross-analysis", "Warning",
#                     f"Unusual {performance_metric} values are associated with the {' and '.join(affected)}.",
#                     "Investigate whether the unusual values represent genuine exceptional performance or data-quality issues before drawing conclusions.",
#                     "High"
#                 ))
#             else:
#                 insights.append(_insight(
#                     "Cross-analysis", "Positive",
#                     "Neither the top nor bottom performer is associated with an unusual value in the selected performance metric under the current outlier method.",
#                     "Continue monitoring extreme performers for future anomalies.",
#                     "Low"
#                 ))

#     # --------------------------------------------------
#     # Performance + Trends
#     # --------------------------------------------------
#     if trend_data is not None and not trend_data.empty and performance_metric:
#         direction = str(trend_direction or "Unknown").lower()
#         if direction == "decreasing":
#             text_type = "Warning"
#             priority = "High"
#         elif direction == "increasing":
#             text_type = "Positive"
#             priority = "Medium"
#         else:
#             text_type = "Information"
#             priority = "Medium"

#         insights.append(_insight(
#             "Cross-analysis", text_type,
#             f"The selected performance metric {performance_metric} is {direction}, with an overall change of {percentage_change:+.2f}%.",
#             "Connect the observed trend to operational or business events and determine whether the movement requires intervention or scaling.",
#             priority
#         ))

#     # --------------------------------------------------
#     # Correlation + Performance
#     # --------------------------------------------------
#     if correlation_matrix is not None and performance_metric in getattr(correlation_matrix, "columns", []):
#         series = pd.to_numeric(correlation_matrix[performance_metric], errors="coerce").drop(labels=[performance_metric], errors="ignore").dropna()
#         if not series.empty:
#             strongest = series.abs().sort_values(ascending=False).head(3)
#             driver_text = ", ".join(f"{idx} ({series[idx]:+.2f})" for idx in strongest.index)
#             insights.append(_insight(
#                 "Cross-analysis", "Information",
#                 f"Variables most associated with {performance_metric}: {driver_text}.",
#                 "Treat these variables as candidate business drivers and validate them with experiments, domain knowledge, or causal analysis.",
#                 "High"
#             ))

#     # --------------------------------------------------
#     # Data Quality + Performance
#     # --------------------------------------------------
#     if analysis_df is not None and not analysis_df.empty and performance_metric in analysis_df.columns:
#         metric_missing = int(analysis_df[performance_metric].isna().sum())
#         metric_missing_pct = metric_missing / len(analysis_df) * 100
#         duplicates = int(analysis_df.duplicated().sum())

#         if metric_missing > 0 or duplicates > 0:
#             parts = []
#             if metric_missing > 0:
#                 parts.append(f"{metric_missing:,} missing {performance_metric} values ({metric_missing_pct:.2f}%)")
#             if duplicates > 0:
#                 parts.append(f"{duplicates:,} duplicate rows")
#             insights.append(_insight(
#                 "Cross-analysis", "Warning",
#                 "Data-quality issues may affect conclusions about performance: " + " and ".join(parts) + ".",
#                 f"Resolve or assess these issues before treating {performance_metric} differences as reliable business signals.",
#                 "High"
#             ))
#         else:
#             insights.append(_insight(
#                 "Cross-analysis", "Positive",
#                 f"No missing values were detected in the selected performance metric {performance_metric}, and no duplicate rows were detected.",
#                 "Performance comparisons can proceed with relatively low data-quality risk from these checks.",
#                 "Low"
#             ))

#     return insights


# # ==================================================
# # PRIORITIZED BUSINESS RECOMMENDATIONS
# # ==================================================

# def generate_business_recommendations(insights):
#     if not insights:
#         return []

#     recommendations = []
#     seen = set()

#     priority_order = {"High": 0, "Medium": 1, "Low": 2}
#     ranked = sorted(
#         insights,
#         key=lambda x: priority_order.get(x.get("Priority", "Medium"), 1)
#     )

#     for item in ranked:
#         rec = item.get("Recommendation", "").strip()
#         if not rec or rec in seen:
#             continue
#         seen.add(rec)
#         recommendations.append(_insight(
#             "Business Recommendation",
#             "Action",
#             f"[{item.get('Priority', 'Medium')} priority] {item.get('Insight', '')}",
#             rec,
#             item.get("Priority", "Medium")
#         ))

#         if len(recommendations) >= 7:
#             break

#     return recommendations


# # ==================================================
# # COMBINE ALL INSIGHTS
# # ==================================================

# def generate_all_insights(
#     profile=None,
#     df=None,
#     trend_data=None,
#     trend_direction=None,
#     percentage_change=0,
#     metric_column=None,
#     performance_data=None,
#     performance_summary=None,
#     dimension_column=None,
#     performance_metric=None,
#     outlier_summary=None,
#     strong_correlations=None,
#     correlation_matrix=None,
#     outlier_method="IQR",
#     outlier_multiplier=1.5,
#     zscore_threshold=3.0,
# ):
#     insights = []

#     if profile is not None:
#         insights.extend(generate_data_quality_insights(profile, df=df))

#     if trend_data is not None and metric_column is not None:
#         insights.extend(generate_trend_insights(
#             trend_data,
#             trend_direction,
#             percentage_change,
#             metric_column
#         ))

#     if (
#         performance_data is not None
#         and performance_summary is not None
#         and dimension_column is not None
#         and performance_metric is not None
#     ):
#         insights.extend(generate_performance_insights(
#             performance_data,
#             performance_summary,
#             dimension_column,
#             performance_metric
#         ))

#     if outlier_summary is not None:
#         insights.extend(generate_outlier_insights(outlier_summary))

#     insights.extend(generate_correlation_insights(
#         strong_correlations,
#         correlation_matrix=correlation_matrix,
#         performance_metric=performance_metric
#     ))

#     insights.extend(generate_cross_analysis_insights(
#         analysis_df=df,
#         performance_data=performance_data,
#         performance_summary=performance_summary,
#         dimension_column=dimension_column,
#         performance_metric=performance_metric,
#         trend_data=trend_data,
#         trend_direction=trend_direction,
#         percentage_change=percentage_change,
#         correlation_matrix=correlation_matrix,
#         strong_correlations=strong_correlations,
#         outlier_summary=outlier_summary,
#         profile=profile,
#         outlier_method=outlier_method,
#         outlier_multiplier=outlier_multiplier,
#         zscore_threshold=zscore_threshold,
#     ))

#     # Prioritized recommendations are intentionally included as a separate
#     # category so the UI can distinguish actions from analytical findings.
#     recommendations = generate_business_recommendations(insights)
#     insights.extend(recommendations)

#     return pd.DataFrame(insights)

import pandas as pd
import numpy as np


# ==================================================
# HELPERS
# ==================================================

def _insight(category, insight_type, text, recommendation, priority="Medium"):
    return {
        "Category": category,
        "Type": insight_type,
        "Priority": priority,
        "Insight": text,
        "Recommendation": recommendation,
    }


def _safe_float(value, default=0.0):
    try:
        value = float(value)
        return value if np.isfinite(value) else default
    except (TypeError, ValueError):
        return default


def _severity(percent, low=1, medium=5, high=15):
    if percent <= low:
        return "Low"
    if percent <= medium:
        return "Moderate"
    if percent <= high:
        return "High"
    return "Critical"


def _correlation_column(df):
    for col in ["Correlation", "correlation", "Value", "Coefficient"]:
        if col in df.columns:
            return col
    return None


def _correlation_pair_columns(df):
    first = second = None
    for col in ["Column 1", "Column1", "Variable 1", "Variable1", "Feature 1", "Feature1", "X"]:
        if col in df.columns:
            first = col
            break
    for col in ["Column 2", "Column2", "Variable 2", "Variable2", "Feature 2", "Feature2", "Y"]:
        if col in df.columns:
            second = col
            break
    return first, second


# ==================================================
# DATA QUALITY INSIGHTS
# ==================================================

def generate_data_quality_insights(profile, df=None):
    insights = []

    missing_values = int(profile.get("missing_values", 0) or 0)
    duplicate_rows = int(profile.get("duplicate_rows", 0) or 0)
    rows = int(profile.get("rows", 0) or 0)
    columns = int(profile.get("columns", 0) or 0)

    total_cells = max(rows * columns, 1)
    missing_percentage = (missing_values / total_cells) * 100
    duplicate_percentage = (duplicate_rows / max(rows, 1)) * 100

    missing_severity = _severity(missing_percentage, 1, 5, 15)
    duplicate_severity = _severity(duplicate_percentage, 1, 5, 15)

    # Missing-value severity
    if missing_values == 0:
        insights.append(_insight(
            "Data Quality", "Positive",
            "No missing values were detected. Data completeness is currently strong.",
            "No missing-value treatment is required; continue monitoring new data loads.",
            "Low"
        ))
    else:
        insight_type = "Warning" if missing_severity in {"High", "Critical"} else "Information"
        priority = "High" if missing_severity in {"High", "Critical"} else "Medium"
        insights.append(_insight(
            "Data Quality", insight_type,
            f"The dataset contains {missing_values:,} missing cells ({missing_percentage:.2f}% of all cells), giving missing data a {missing_severity.lower()} severity.",
            "Prioritize columns with the highest missingness and apply an appropriate imputation, exclusion, or data-collection fix.",
            priority
        ))

    # Duplicate severity
    if duplicate_rows == 0:
        insights.append(_insight(
            "Data Quality", "Positive",
            "No duplicate rows were detected.",
            "No duplicate-row removal is currently required.",
            "Low"
        ))
    else:
        insight_type = "Warning" if duplicate_severity in {"High", "Critical"} else "Information"
        priority = "High" if duplicate_severity in {"High", "Critical"} else "Medium"
        insights.append(_insight(
            "Data Quality", insight_type,
            f"{duplicate_rows:,} duplicate rows were detected ({duplicate_percentage:.2f}% of records), a {duplicate_severity.lower()} data-quality issue.",
            "Review whether duplicates are legitimate repeated events; otherwise remove or prevent them before downstream analysis.",
            priority
        ))

    # Columns with the most missing data
    if df is not None and not df.empty:
        missing_by_column = df.isna().sum()
        missing_by_column = missing_by_column[missing_by_column > 0].sort_values(ascending=False)

        if not missing_by_column.empty:
            top_missing = missing_by_column.head(5)
            details = []
            for col, count in top_missing.items():
                pct = (count / len(df)) * 100
                details.append(f"{col}: {int(count):,} ({pct:.1f}%)")

            top_column = str(top_missing.index[0])
            top_pct = (top_missing.iloc[0] / len(df)) * 100
            insights.append(_insight(
                "Data Quality", "Warning" if top_pct > 15 else "Information",
                "Columns with the most missing data: " + "; ".join(details) + ".",
                f"Investigate `{top_column}` first because it has the highest missing-value concentration.",
                "High" if top_pct > 15 else "Medium"
            ))

        # Overall risk
        risk_score = 0
        max_column_missing_pct = 0.0
        if df is not None and not df.empty:
            max_column_missing_pct = float((df.isna().sum() / len(df) * 100).max())

        if missing_percentage > 15 or max_column_missing_pct > 25:
            risk_score += 2
        elif missing_percentage > 5 or max_column_missing_pct > 10:
            risk_score += 1
        if duplicate_percentage > 15:
            risk_score += 2
        elif duplicate_percentage > 5:
            risk_score += 1

        if risk_score >= 3:
            risk = "High"
            risk_type = "Warning"
            priority = "High"
        elif risk_score >= 1:
            risk = "Moderate"
            risk_type = "Information"
            priority = "Medium"
        else:
            risk = "Low"
            risk_type = "Positive"
            priority = "Low"

        insights.append(_insight(
            "Data Quality", risk_type,
            f"Overall data-quality risk is assessed as {risk.lower()} based on missingness and duplicate records.",
            "Resolve high-impact quality issues before making sensitive business decisions from the dataset.",
            priority
        ))

    return insights


# ==================================================
# TREND INSIGHTS
# ==================================================

def generate_trend_insights(trend_data, trend_direction, percentage_change, metric_column):
    insights = []

    if trend_data is None or trend_data.empty:
        return insights

    data = trend_data.copy()
    if "Value" not in data.columns:
        return insights

    data["Value"] = pd.to_numeric(data["Value"], errors="coerce")
    data = data.dropna(subset=["Value"]).reset_index(drop=True)
    if data.empty:
        return insights

    # Direction and percentage change
    if trend_direction == "Increasing":
        insight_type, priority = "Positive", "Medium"
    elif trend_direction == "Decreasing":
        insight_type, priority = "Warning", "High"
    else:
        insight_type, priority = "Information", "Medium"

    insights.append(_insight(
        "Trend", insight_type,
        f"{metric_column} is {str(trend_direction).lower()} with an overall change of {percentage_change:+.2f}%.",
        "Sustain the drivers of growth if positive; if declining, investigate the underlying causes and corrective actions.",
        priority
    ))

    # Period-to-period changes
    changes = data["Value"].pct_change().replace([np.inf, -np.inf], np.nan).dropna()
    if not changes.empty:
        max_growth_idx = changes.idxmax()
        max_decline_idx = changes.idxmin()
        growth_pct = changes.loc[max_growth_idx] * 100
        decline_pct = changes.loc[max_decline_idx] * 100

        def period_label(idx):
            if "Date" in data.columns:
                return str(data.loc[idx, "Date"])
            return f"period {idx + 1}"

        insights.append(_insight(
            "Trend", "Positive" if growth_pct > 0 else "Information",
            f"Strongest growth period: {period_label(max_growth_idx)} with a {growth_pct:+.2f}% period-over-period change.",
            "Investigate what changed during this period and determine whether the conditions can be replicated.",
            "Medium"
        ))

        insights.append(_insight(
            "Trend", "Warning" if decline_pct < 0 else "Information",
            f"Strongest decline period: {period_label(max_decline_idx)} with a {decline_pct:+.2f}% period-over-period change.",
            "Review operational, market, or data factors associated with this period before assuming the decline is structural.",
            "High" if decline_pct < -10 else "Medium"
        ))

        volatility = changes.std() * 100
        if np.isnan(volatility):
            volatility = 0

        if volatility >= 20:
            volatility_label = "high"
            volatility_type = "Warning"
            volatility_priority = "High"
        elif volatility >= 10:
            volatility_label = "moderate"
            volatility_type = "Information"
            volatility_priority = "Medium"
        else:
            volatility_label = "low"
            volatility_type = "Positive"
            volatility_priority = "Low"

        insights.append(_insight(
            "Trend", volatility_type,
            f"Trend volatility is {volatility_label}, with a period-to-period change standard deviation of {volatility:.2f}%.",
            "Use shorter monitoring intervals when volatility is high and investigate unusually large period-to-period movements.",
            volatility_priority
        ))

    # Recent vs overall performance
    recent_n = min(3, len(data))
    recent_mean = data["Value"].tail(recent_n).mean()
    overall_mean = data["Value"].mean()
    if overall_mean != 0:
        recent_difference = ((recent_mean - overall_mean) / abs(overall_mean)) * 100
    else:
        recent_difference = 0

    recent_type = "Positive" if recent_difference > 5 else "Warning" if recent_difference < -5 else "Information"
    insights.append(_insight(
        "Trend", recent_type,
        f"The most recent {recent_n} periods are {recent_difference:+.2f}% versus the overall average level.",
        "Compare recent conditions with the historical baseline to determine whether the latest movement is temporary or a sustained shift.",
        "Medium" if abs(recent_difference) > 5 else "Low"
    ))

    return insights


# ==================================================
# PERFORMANCE INSIGHTS
# ==================================================

def generate_performance_insights(performance_data, summary, dimension_column, metric_column):
    insights = []

    if performance_data is None or performance_data.empty or not summary:
        return insights

    data = performance_data.copy()
    if "Performance" not in data.columns:
        return insights

    data["Performance"] = pd.to_numeric(data["Performance"], errors="coerce")
    data = data.dropna(subset=["Performance"])
    if data.empty:
        return insights

    average = _safe_float(summary.get("average_performance"), data["Performance"].mean())
    highest = _safe_float(summary.get("highest_performance"), data["Performance"].max())
    lowest = _safe_float(summary.get("lowest_performance"), data["Performance"].min())
    top = summary.get("top_performer", data.iloc[data["Performance"].idxmax()][dimension_column])
    bottom = summary.get("bottom_performer", data.iloc[data["Performance"].idxmin()][dimension_column])

    # Top / bottom performer
    insights.append(_insight(
        "Performance", "Positive",
        f"{top} is the top-performing {dimension_column} based on {metric_column} ({highest:,.2f}).",
        f"Study the factors associated with {top} and identify practices that can be replicated elsewhere.",
        "Medium"
    ))

    insights.append(_insight(
        "Performance", "Warning",
        f"{bottom} is the lowest-performing {dimension_column} based on {metric_column} ({lowest:,.2f}).",
        f"Investigate the drivers of {bottom}'s performance and prioritize targeted corrective action.",
        "High"
    ))

    # Gap
    gap = highest - lowest
    gap_pct = (gap / abs(average) * 100) if average != 0 else 0
    insights.append(_insight(
        "Performance", "Warning" if gap_pct > 50 else "Information",
        f"The performance gap is {gap:,.2f}, equivalent to {gap_pct:.2f}% of the average performance.",
        "Investigate why performance varies so widely and determine whether the gap reflects structural differences or improvement opportunities.",
        "High" if gap_pct > 50 else "Medium"
    ))

    # Above/below average entities
    above = int((data["Performance"] > average).sum())
    below = int((data["Performance"] < average).sum())
    total = len(data)
    insights.append(_insight(
        "Performance", "Information",
        f"{above} of {total} entities ({above / total * 100:.1f}%) are above average, while {below} ({below / total * 100:.1f}%) are below average.",
        "Use the above-average group as a benchmark and prioritize support for consistently below-average entities.",
        "Medium"
    ))

    # Concentration and top contribution
    total_performance = data["Performance"].sum()
    top_n = max(1, min(5, int(np.ceil(len(data) * 0.20))))
    top_n_total = data.nlargest(top_n, "Performance")["Performance"].sum()
    contribution = (top_n_total / total_performance * 100) if total_performance != 0 else 0
    concentration_type = "Warning" if contribution >= 60 else "Information"
    insights.append(_insight(
        "Performance", concentration_type,
        f"The top {top_n} entities contribute {contribution:.2f}% of total aggregated performance.",
        "If concentration is high, reduce dependency on a small number of entities and identify ways to lift the broader group.",
        "High" if contribution >= 60 else "Medium"
    ))

    return insights


# ==================================================
# OUTLIER INSIGHTS
# ==================================================

def generate_outlier_insights(outlier_summary):
    insights = []

    if outlier_summary is None or outlier_summary.empty or "Outliers" not in outlier_summary.columns:
        return insights

    data = outlier_summary.copy()
    data["Outliers"] = pd.to_numeric(data["Outliers"], errors="coerce").fillna(0)
    if "Outlier %" in data.columns:
        data["Outlier %"] = pd.to_numeric(data["Outlier %"], errors="coerce").fillna(0)
    else:
        data["Outlier %"] = 0.0

    total_outliers = int(data["Outliers"].sum())
    if total_outliers == 0:
        insights.append(_insight(
            "Outliers", "Positive",
            "No statistical outliers were detected using the selected method.",
            "Continue monitoring numerical variables for unusual future changes.",
            "Low"
        ))
        return insights

    highest = data.loc[data["Outliers"].idxmax()]
    highest_column = str(highest.get("Column", "Unknown"))
    highest_count = int(highest["Outliers"])
    highest_pct = float(highest["Outlier %"])

    insights.append(_insight(
        "Outliers", "Warning",
        f"A total of {total_outliers:,} outlier values were detected. {highest_column} is the most affected column with {highest_count:,} outliers ({highest_pct:.2f}%).",
        f"Investigate {highest_column} first to determine whether these values are errors, rare legitimate events, or important exceptions.",
        "High"
    ))

    # Unusually high outlier percentages
    high_pct = data[data["Outlier %"] >= 10].sort_values("Outlier %", ascending=False)
    if not high_pct.empty:
        columns = ", ".join(
            f"{row['Column']} ({row['Outlier %']:.1f}%)"
            for _, row in high_pct.head(5).iterrows()
        )
        insights.append(_insight(
            "Outliers", "Warning",
            f"The following columns have unusually high outlier percentages: {columns}.",
            "Validate these variables for data-entry problems, inconsistent units, or genuine high-variance business events.",
            "High"
        ))

    # Severity
    max_pct = float(data["Outlier %"].max())
    if max_pct >= 20:
        severity = "critical"
        priority = "High"
    elif max_pct >= 10:
        severity = "high"
        priority = "High"
    elif max_pct >= 5:
        severity = "moderate"
        priority = "Medium"
    else:
        severity = "low"
        priority = "Low"

    insights.append(_insight(
        "Outliers", "Warning" if severity in {"high", "critical"} else "Information",
        f"Overall outlier severity is {severity}, based on the highest detected outlier percentage of {max_pct:.2f}%.",
        "Do not automatically remove outliers; validate their business meaning before changing the dataset.",
        priority
    ))

    return insights


# ==================================================
# CORRELATION INSIGHTS
# ==================================================

def generate_correlation_insights(strong_correlations, correlation_matrix=None, performance_metric=None):
    insights = []

    if strong_correlations is None:
        strong_correlations = pd.DataFrame()

    corr_col = _correlation_column(strong_correlations)

    if strong_correlations.empty or corr_col is None:
        insights.append(_insight(
            "Correlation", "Information",
            "No strong correlation relationships were detected using the selected threshold.",
            "Consider reviewing weaker relationships and combining correlation results with domain knowledge.",
            "Low"
        ))
    else:
        corr = pd.to_numeric(strong_correlations[corr_col], errors="coerce").dropna()
        positive = corr[corr > 0]
        negative = corr[corr < 0]

        if not positive.empty:
            idx = positive.idxmax()
            row = strong_correlations.loc[idx]
            first, second = _correlation_pair_columns(strong_correlations)
            pair = f"{row[first]} and {row[second]}" if first and second else "the strongest positive pair"
            value = float(row[corr_col])
            insights.append(_insight(
                "Correlation", "Information",
                f"Strongest positive correlation: {pair} ({value:.2f}).",
                "Investigate whether the relationship reflects a meaningful business driver; correlation does not prove causation.",
                "Medium"
            ))

        if not negative.empty:
            idx = negative.idxmin()
            row = strong_correlations.loc[idx]
            first, second = _correlation_pair_columns(strong_correlations)
            pair = f"{row[first]} and {row[second]}" if first and second else "the strongest negative pair"
            value = float(row[corr_col])
            insights.append(_insight(
                "Correlation", "Information",
                f"Strongest negative correlation: {pair} ({value:.2f}).",
                "Investigate whether the inverse relationship could indicate a trade-off, constraint, or confounding factor.",
                "Medium"
            ))

        insights.append(_insight(
            "Correlation", "Information",
            f"{len(strong_correlations)} strong correlation relationship(s) were detected.",
            "Prioritize relationships that involve the selected performance metric or other key business measures.",
            "Medium"
        ))

    # Potential drivers of selected performance metric
    if correlation_matrix is not None and performance_metric in getattr(correlation_matrix, "columns", []):
        series = pd.to_numeric(correlation_matrix[performance_metric], errors="coerce").drop(labels=[performance_metric], errors="ignore").dropna()
        if not series.empty:
            top_drivers = series.abs().sort_values(ascending=False).head(3).index.tolist()
            driver_text = ", ".join(
                f"{col} ({series[col]:+.2f})" for col in top_drivers
            )
            insights.append(_insight(
                "Correlation", "Information",
                f"Potential business drivers associated with {performance_metric}: {driver_text}.",
                "Investigate these variables as candidate drivers of performance, while validating the relationships with business context or further analysis.",
                "High" if top_drivers else "Medium"
            ))

    return insights


# ==================================================
# CROSS-ANALYSIS INSIGHTS
# ==================================================

def generate_cross_analysis_insights(
    analysis_df=None,
    performance_data=None,
    performance_summary=None,
    dimension_column=None,
    performance_metric=None,
    trend_data=None,
    trend_direction=None,
    percentage_change=0,
    correlation_matrix=None,
    strong_correlations=None,
    outlier_summary=None,
    profile=None,
    outlier_method="IQR",
    outlier_multiplier=1.5,
    zscore_threshold=3.0,
):
    insights = []

    # --------------------------------------------------
    # Performance + Outliers
    # --------------------------------------------------
    if (
        analysis_df is not None
        and not analysis_df.empty
        and performance_data is not None
        and not performance_data.empty
        and performance_summary
        and dimension_column in analysis_df.columns
        and performance_metric in analysis_df.columns
    ):
        temp = analysis_df[[dimension_column, performance_metric]].copy()
        temp[performance_metric] = pd.to_numeric(temp[performance_metric], errors="coerce")
        temp = temp.dropna(subset=[performance_metric])

        if not temp.empty:
            if outlier_method == "Z-Score":
                mean = temp[performance_metric].mean()
                std = temp[performance_metric].std()
                if std and not np.isnan(std):
                    outlier_mask = ((temp[performance_metric] - mean) / std).abs() > zscore_threshold
                else:
                    outlier_mask = pd.Series(False, index=temp.index)
            else:
                q1 = temp[performance_metric].quantile(0.25)
                q3 = temp[performance_metric].quantile(0.75)
                iqr = q3 - q1
                outlier_mask = (
                    (temp[performance_metric] < q1 - outlier_multiplier * iqr)
                    | (temp[performance_metric] > q3 + outlier_multiplier * iqr)
                )

            outlier_entities = set(temp.loc[outlier_mask, dimension_column].astype(str))
            top = str(performance_summary.get("top_performer"))
            bottom = str(performance_summary.get("bottom_performer"))

            top_outlier = top in outlier_entities
            bottom_outlier = bottom in outlier_entities

            if top_outlier or bottom_outlier:
                affected = []
                if top_outlier:
                    affected.append(f"top performer {top}")
                if bottom_outlier:
                    affected.append(f"bottom performer {bottom}")
                insights.append(_insight(
                    "Cross-analysis", "Warning",
                    f"Unusual {performance_metric} values are associated with the {' and '.join(affected)}.",
                    "Investigate whether the unusual values represent genuine exceptional performance or data-quality issues before drawing conclusions.",
                    "High"
                ))
            else:
                insights.append(_insight(
                    "Cross-analysis", "Positive",
                    "Neither the top nor bottom performer is associated with an unusual value in the selected performance metric under the current outlier method.",
                    "Continue monitoring extreme performers for future anomalies.",
                    "Low"
                ))

    # --------------------------------------------------
    # Performance + Trends
    # --------------------------------------------------
    if trend_data is not None and not trend_data.empty and performance_metric:
        direction = str(trend_direction or "Unknown").lower()
        if direction == "decreasing":
            text_type = "Warning"
            priority = "High"
        elif direction == "increasing":
            text_type = "Positive"
            priority = "Medium"
        else:
            text_type = "Information"
            priority = "Medium"

        insights.append(_insight(
            "Cross-analysis", text_type,
            f"The selected performance metric {performance_metric} is {direction}, with an overall change of {percentage_change:+.2f}%.",
            "Connect the observed trend to operational or business events and determine whether the movement requires intervention or scaling.",
            priority
        ))

    # --------------------------------------------------
    # Correlation + Performance
    # --------------------------------------------------
    if correlation_matrix is not None and performance_metric in getattr(correlation_matrix, "columns", []):
        series = pd.to_numeric(correlation_matrix[performance_metric], errors="coerce").drop(labels=[performance_metric], errors="ignore").dropna()
        if not series.empty:
            strongest = series.abs().sort_values(ascending=False).head(3)
            driver_text = ", ".join(f"{idx} ({series[idx]:+.2f})" for idx in strongest.index)
            insights.append(_insight(
                "Cross-analysis", "Information",
                f"Variables most associated with {performance_metric}: {driver_text}.",
                "Treat these variables as candidate business drivers and validate them with experiments, domain knowledge, or causal analysis.",
                "High"
            ))

    # --------------------------------------------------
    # Data Quality + Performance
    # --------------------------------------------------
    if analysis_df is not None and not analysis_df.empty and performance_metric in analysis_df.columns:
        metric_missing = int(analysis_df[performance_metric].isna().sum())
        metric_missing_pct = metric_missing / len(analysis_df) * 100
        duplicates = int(analysis_df.duplicated().sum())

        if metric_missing > 0 or duplicates > 0:
            parts = []
            if metric_missing > 0:
                parts.append(f"{metric_missing:,} missing {performance_metric} values ({metric_missing_pct:.2f}%)")
            if duplicates > 0:
                parts.append(f"{duplicates:,} duplicate rows")
            insights.append(_insight(
                "Cross-analysis", "Warning",
                "Data-quality issues may affect conclusions about performance: " + " and ".join(parts) + ".",
                f"Resolve or assess these issues before treating {performance_metric} differences as reliable business signals.",
                "High"
            ))
        else:
            insights.append(_insight(
                "Cross-analysis", "Positive",
                f"No missing values were detected in the selected performance metric {performance_metric}, and no duplicate rows were detected.",
                "Performance comparisons can proceed with relatively low data-quality risk from these checks.",
                "Low"
            ))

    return insights


# ==================================================
# PRIORITIZED BUSINESS RECOMMENDATIONS
# ==================================================

def generate_business_recommendations(insights):
    if not insights:
        return []

    recommendations = []
    seen = set()

    priority_order = {"High": 0, "Medium": 1, "Low": 2}
    ranked = sorted(
        insights,
        key=lambda x: priority_order.get(x.get("Priority", "Medium"), 1)
    )

    for item in ranked:
        rec = item.get("Recommendation", "").strip()
        if not rec or rec in seen:
            continue
        seen.add(rec)
        recommendations.append(_insight(
            "Business Recommendation",
            "Action",
            f"[{item.get('Priority', 'Medium')} priority] {item.get('Insight', '')}",
            rec,
            item.get("Priority", "Medium")
        ))

        if len(recommendations) >= 7:
            break

    return recommendations


# ==================================================
# COMBINE ALL INSIGHTS
# ==================================================

def generate_all_insights(
    profile=None,
    df=None,
    trend_data=None,
    trend_direction=None,
    percentage_change=0,
    metric_column=None,
    performance_data=None,
    performance_summary=None,
    dimension_column=None,
    performance_metric=None,
    outlier_summary=None,
    strong_correlations=None,
    correlation_matrix=None,
    outlier_method="IQR",
    outlier_multiplier=1.5,
    zscore_threshold=3.0,
):
    insights = []

    if profile is not None:
        insights.extend(generate_data_quality_insights(profile, df=df))

    if trend_data is not None and metric_column is not None:
        insights.extend(generate_trend_insights(
            trend_data,
            trend_direction,
            percentage_change,
            metric_column
        ))

    if (
        performance_data is not None
        and performance_summary is not None
        and dimension_column is not None
        and performance_metric is not None
    ):
        insights.extend(generate_performance_insights(
            performance_data,
            performance_summary,
            dimension_column,
            performance_metric
        ))

    if outlier_summary is not None:
        insights.extend(generate_outlier_insights(outlier_summary))

    insights.extend(generate_correlation_insights(
        strong_correlations,
        correlation_matrix=correlation_matrix,
        performance_metric=performance_metric
    ))

    insights.extend(generate_cross_analysis_insights(
        analysis_df=df,
        performance_data=performance_data,
        performance_summary=performance_summary,
        dimension_column=dimension_column,
        performance_metric=performance_metric,
        trend_data=trend_data,
        trend_direction=trend_direction,
        percentage_change=percentage_change,
        correlation_matrix=correlation_matrix,
        strong_correlations=strong_correlations,
        outlier_summary=outlier_summary,
        profile=profile,
        outlier_method=outlier_method,
        outlier_multiplier=outlier_multiplier,
        zscore_threshold=zscore_threshold,
    ))

    # Prioritized recommendations are intentionally included as a separate
    # category so the UI can distinguish actions from analytical findings.
    recommendations = generate_business_recommendations(insights)
    insights.extend(recommendations)

    return pd.DataFrame(insights)
