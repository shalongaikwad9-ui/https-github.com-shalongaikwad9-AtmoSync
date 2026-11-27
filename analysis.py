"""Data cleaning, statistical analysis, comparisons, and CSV reports for AtmoSync."""
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = PROJECT_ROOT / "data" / "weather_data.csv"
DATA_DIR = PROJECT_ROOT / "data"

NUMERIC_COLUMNS = [
    "temperature", "humidity", "precipitation",
    "wind_speed", "cloud_cover"
]
REQUIRED_COLUMNS = {"location", "temperature", "humidity"}


def clean_weather_data(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize columns and values; discard rows without essential measurements."""
    if df.empty:
        return df.copy()

    cleaned = df.copy()
    cleaned.columns = cleaned.columns.astype(str).str.strip()
    missing = REQUIRED_COLUMNS - set(cleaned.columns)
    if missing:
        raise ValueError(f"CSV is missing required columns: {sorted(missing)}")

    cleaned["location"] = cleaned["location"].astype("string").str.strip()
    cleaned["location"] = cleaned["location"].replace("", pd.NA)

    for column in NUMERIC_COLUMNS:
        if column in cleaned.columns:
            cleaned[column] = pd.to_numeric(cleaned[column], errors="coerce")

    # Keep only rows with the fields needed for the core analysis.
    cleaned = cleaned.dropna(subset=["location", "temperature", "humidity"])

    if "time" in cleaned.columns:
        cleaned["time"] = pd.to_datetime(cleaned["time"], errors="coerce")
    if "collected_at" in cleaned.columns:
        cleaned["collected_at"] = pd.to_datetime(
            cleaned["collected_at"], errors="coerce"
        )

    # Remove exact duplicate records without discarding separate snapshots.
    cleaned = cleaned.drop_duplicates().reset_index(drop=True)
    return cleaned


def load_weather_data(path=DATA_FILE) -> pd.DataFrame:
    """Load and clean the collected weather CSV; return empty if it is absent."""
    path = Path(path)
    if not path.exists():
        return pd.DataFrame()
    raw = pd.read_csv(path)
    return clean_weather_data(raw)


def location_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate average, minimum, maximum, and record count per location."""
    if df.empty:
        return pd.DataFrame()

    aggregations = {
        "avg_temperature": ("temperature", "mean"),
        "min_temperature": ("temperature", "min"),
        "max_temperature": ("temperature", "max"),
        "avg_humidity": ("humidity", "mean"),
        "min_humidity": ("humidity", "min"),
        "max_humidity": ("humidity", "max"),
        "records": ("location", "count"),
    }
    optional_metrics = [
        ("precipitation", "avg_precipitation"),
        ("wind_speed", "avg_wind_speed"),
        ("cloud_cover", "avg_cloud_cover"),
    ]
    for source, target in optional_metrics:
        if source in df.columns:
            aggregations[target] = (source, "mean")

    return df.groupby("location").agg(**aggregations).round(2).reset_index()


def pairwise_comparison(summary: pd.DataFrame) -> pd.DataFrame:
    """Compare absolute average temperature and humidity gaps for each pair."""
    columns = [
        "location_1", "location_2",
        "temperature_difference", "humidity_difference",
    ]
    rows = []
    if summary.empty:
        return pd.DataFrame(columns=columns)

    for i in range(len(summary)):
        for j in range(i + 1, len(summary)):
            first, second = summary.iloc[i], summary.iloc[j]
            rows.append({
                "location_1": first["location"],
                "location_2": second["location"],
                "temperature_difference": round(
                    abs(first["avg_temperature"] - second["avg_temperature"]),  2
                ),
                "humidity_difference": round(
                    abs(first["avg_humidity"] - second["avg_humidity"]), 2
                ),
            })
    return pd.DataFrame(rows, columns=columns)


def overall_statistics(df: pd.DataFrame) -> pd.DataFrame:
    """Return mean, minimum, maximum, and standard deviation for measurements."""
    available = [c for c in NUMERIC_COLUMNS if c in df.columns]
    if df.empty or not available:
        return pd.DataFrame()
    return df[available].agg(["count", "mean", "min", "max", "std"]).round(2)


def data_quality_report(raw_df: pd.DataFrame, cleaned_df: pd.DataFrame) -> pd.DataFrame:
    """Summarize input row counts and missing values for the core measurements."""
    fields = [c for c in ["location", "temperature", "humidity"] if c in raw_df.columns]
    rows = [{
        "metric": "input_rows",
        "value": int(len(raw_df)),
    }, {
        "metric": "valid_rows_after_cleaning",
        "value": int(len(cleaned_df)),
    }, {
        "metric": "removed_rows",
        "value": int(len(raw_df) - len(cleaned_df)),
    }]
    for field in fields:
        rows.append({"metric": f"missing_{field}", "value": int(raw_df[field].isna().sum())})
    return pd.DataFrame(rows)


def save_reports(df: pd.DataFrame, output_dir=DATA_DIR) -> dict:
    """Clean data and save Week 2 analysis reports as CSV files."""
    if df.empty:
        raise ValueError("No valid data available to analyse. Run the collector first.")

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    cleaned = clean_weather_data(df)
    if cleaned.empty:
        raise ValueError("No valid weather rows remain after cleaning.")

    summary = location_summary(cleaned)
    comparisons = pairwise_comparison(summary)
    overall = overall_statistics(cleaned)
    quality = data_quality_report(df, cleaned)

    paths = {
        "cleaned": output_dir / "cleaned_weather_data.csv",
        "summary": output_dir / "location_analysis.csv",
        "comparison": output_dir / "location_comparison.csv",
        "overall": output_dir / "overall_statistics.csv",
        "quality": output_dir / "data_quality_report.csv",
    }
    cleaned.to_csv(paths["cleaned"], index=False)
    summary.to_csv(paths["summary"], index=False)
    comparisons.to_csv(paths["comparison"], index=False)
    overall.to_csv(paths["overall"])
    quality.to_csv(paths["quality"], index=False)
    return paths


if __name__ == "__main__":
    raw_data = pd.read_csv(DATA_FILE) if DATA_FILE.exists() else pd.DataFrame()
    if raw_data.empty:
        raise SystemExit("No data found. Run: python -m src.collector")

    data = clean_weather_data(raw_data)
    if data.empty:
        raise SystemExit("No valid weather rows found. Check the source CSV.")

    summary = location_summary(data)
    reports = save_reports(raw_data)
    print("\nLOCATION ANALYSIS")
    print(summary.to_string(index=False))
    print("\nPAIRWISE LOCATION COMPARISON")
    comparison = pairwise_comparison(summary)
    print(comparison.to_string(index=False) if not comparison.empty else "Only one location is available.")
    print("\nOVERALL STATISTICS")
    print(overall_statistics(data).to_string())
    print("\nReports saved:")
    for label, path in reports.items():
        print(f"- {label}: {path}")
