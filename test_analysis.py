import pandas as pd
import pytest

from src.analysis import (
    clean_weather_data,
    data_quality_report,
    location_summary,
    overall_statistics,
    pairwise_comparison,
    save_reports,
)


def sample_data():
    return pd.DataFrame({
        "location": ["Pune", "Pune", "Hinjawadi"],
        "temperature": [30, 32, 28],
        "humidity": [60, 64, 70],
        "precipitation": [0, 1, 0],
    })


def test_location_summary():
    result = location_summary(sample_data())
    pune = result[result["location"] == "Pune"].iloc[0]
    assert pune["avg_temperature"] == 31
    assert pune["avg_humidity"] == 62
    assert pune["records"] == 2
    assert pune["min_temperature"] == 30
    assert pune["max_temperature"] == 32


def test_pairwise_comparison():
    result = pairwise_comparison(location_summary(sample_data()))
    assert len(result) == 1
    assert result.iloc[0]["temperature_difference"] == 3
    assert result.iloc[0]["humidity_difference"] == 8


def test_cleaning_coerces_bad_numbers_and_drops_invalid_rows():
    raw = pd.DataFrame({
        " location ": [" Pune ", "", "Mumbai"],
        "temperature": ["31", "29", "not-a-number"],
        "humidity": ["60", "55", "70"],
    })
    result = clean_weather_data(raw)
    assert len(result) == 1
    assert result.iloc[0]["location"] == "Pune"
    assert result.iloc[0]["temperature"] == 31


def test_cleaning_requires_core_columns():
    with pytest.raises(ValueError, match="missing required columns"):
        clean_weather_data(pd.DataFrame({"location": ["Pune"]}))


def test_overall_statistics():
    result = overall_statistics(sample_data())
    assert result.loc["mean", "temperature"] == 30
    assert result.loc["min", "humidity"] == 60
    assert result.loc["max", "humidity"] == 70


def test_quality_report_counts_removed_rows():
    raw = pd.DataFrame({
        "location": ["Pune", ""],
        "temperature": [30, 29],
        "humidity": [60, 55],
    })
    cleaned = clean_weather_data(raw)
    report = data_quality_report(raw, cleaned)
    removed = report.loc[report["metric"] == "removed_rows", "value"].iloc[0]
    assert removed == 1


def test_save_reports_creates_five_csv_files(tmp_path):
    paths = save_reports(sample_data(), output_dir=tmp_path)
    assert len(paths) == 5
    assert all(path.exists() for path in paths.values())
    assert "avg_temperature" in pd.read_csv(paths["summary"]).columns
