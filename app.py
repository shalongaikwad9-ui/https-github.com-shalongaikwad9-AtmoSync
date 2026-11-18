"""AtmoSync interactive Streamlit dashboard."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st
import pandas as pd
import plotly.express as px

from src.analysis import load_weather_data, location_summary, pairwise_comparison
from src.collector import collect_weather

st.set_page_config(page_title="AtmoSync | Micro-Climate Analytics",
                   page_icon="🌦️", layout="wide")

st.title("🌦️ AtmoSync")
st.subheader("Micro-Climate Arbitrage Analytics")
st.caption("Compare model-based current weather estimates across locations.")

with st.sidebar:
    st.header("Controls")
    if st.button("Collect latest weather data", use_container_width=True):
        with st.spinner("Fetching weather from Open-Meteo..."):
            try:
                collect_weather()
                st.success("Weather data collected.")
                st.rerun()
            except Exception as exc:
                st.error(f"Collection failed: {exc}")
    st.markdown("---")
    st.write("Data source: Open-Meteo")
    st.write("Use the button above to append a fresh snapshot.")

try:
    df = load_weather_data()
except Exception as exc:
    st.error(f"Could not read the weather CSV: {exc}")
    st.stop()

if df.empty:
    st.warning("No data available yet. Run `python -m src.collector` or use the sidebar button.")
    st.code("python -m src.collector")
    st.stop()

summary = location_summary(df)
comparisons = pairwise_comparison(summary)

# Optional location filter
all_locations = sorted(df["location"].dropna().unique().tolist())
selected = st.sidebar.multiselect("Locations", all_locations, default=all_locations)
view = df[df["location"].isin(selected)]
summary_view = location_summary(view)

if view.empty:
    st.info("Select at least one location.")
    st.stop()

latest = view.sort_values("collected_at").groupby("location", as_index=False).tail(1)
c1, c2, c3, c4 = st.columns(4)
c1.metric("Locations", latest["location"].nunique())
c2.metric("Average temperature", f"{view['temperature'].mean():.1f} °C")
c3.metric("Average humidity", f"{view['humidity'].mean():.1f} %")
c4.metric("Temperature range",
          f"{view['temperature'].max() - view['temperature'].min():.1f} °C")

st.markdown("### Location-wise weather")
left, right = st.columns(2)

with left:
    fig_temp = px.bar(summary_view, x="location", y="avg_temperature",
                      title="Average temperature by location",
                      labels={"location": "Location", "avg_temperature": "Temperature (°C)"},
                      text_auto=".1f")
    st.plotly_chart(fig_temp, use_container_width=True)

with right:
    fig_humidity = px.bar(summary_view, x="location", y="avg_humidity",
                          title="Average humidity by location",
                          labels={"location": "Location", "avg_humidity": "Humidity (%)"},
                          text_auto=".1f")
    st.plotly_chart(fig_humidity, use_container_width=True)

st.markdown("### Weather trends over collection time")
if "collected_at" in view.columns:
    trend = view.copy()
    trend["collected_at"] = pd.to_datetime(trend["collected_at"], errors="coerce")
    trend = trend.dropna(subset=["collected_at"])
    if not trend.empty:
        fig_line = px.line(
            trend.sort_values("collected_at"),
            x="collected_at", y="temperature", color="location",
            markers=True, title="Temperature snapshots over time",
            labels={"collected_at": "Collection time", "temperature": "Temperature (°C)"}
        )
        st.plotly_chart(fig_line, use_container_width=True)
    else:
        st.info("Trend chart will appear after valid collection timestamps are available.")

st.markdown("### Location comparison")
if len(selected) >= 2:
    comp = pairwise_comparison(summary_view)
    st.dataframe(comp, use_container_width=True, hide_index=True)
else:
    st.info("Select at least two locations to compare them.")

st.markdown("### Micro-climate heatmap")
heat_cols = [c for c in ["avg_temperature", "avg_humidity",
                         "avg_precipitation", "avg_wind_speed", "avg_cloud_cover"]
             if c in summary_view.columns]
if len(summary_view) >= 1 and heat_cols:
    heat = summary_view.set_index("location")[heat_cols]
    # Normalize each metric to 0–1 so different units can be viewed together.
    normalized = heat.copy()
    for col in normalized.columns:
        minimum, maximum = normalized[col].min(), normalized[col].max()
        normalized[col] = 0.0 if maximum == minimum else (
            (normalized[col] - minimum) / (maximum - minimum)
        )
    fig_heat = px.imshow(
        normalized, text_auto=".2f", aspect="auto",
        color_continuous_scale="RdYlBu_r",
        title="Normalized weather metric heatmap (0 = lowest, 1 = highest)"
    )
    st.plotly_chart(fig_heat, use_container_width=True)
else:
    st.info("Heatmap requires location data.")

st.markdown("### Location summary")
st.dataframe(summary_view, use_container_width=True, hide_index=True)

with st.expander("View collected raw records"):
    st.dataframe(view.sort_values("collected_at", ascending=False),
                 use_container_width=True, hide_index=True)

st.caption("Weather data by Open-Meteo.com. Values are model-based estimates, not street-level sensor measurements.")
