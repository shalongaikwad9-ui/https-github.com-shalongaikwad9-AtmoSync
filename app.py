"""AtmoSync modern Streamlit dashboard.

Uses the existing Open-Meteo collector and Week 2 analysis functions.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.analysis import (
    DATA_FILE,
    clean_weather_data,
    load_weather_data,
    location_summary,
    pairwise_comparison,
    overall_statistics,
    data_quality_report,
    save_reports,
)
from src.collector import collect_weather

st.set_page_config(
    page_title="AtmoSync | Weather Intelligence",
    page_icon="🌦️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------- Styling ----------
st.markdown("""
<style>
:root { --teal: #0f9d9a; }
.block-container {padding-top: 1.7rem; padding-bottom: 2.5rem; max-width: 1450px;}
[data-testid="stSidebar"] {background: linear-gradient(180deg,#102a43 0%,#163f59 100%);}
[data-testid="stSidebar"] * {color: #f3f8fb !important;}
[data-testid="stSidebar"] [data-baseweb="tag"] {background-color:#087e80 !important;}
.hero {
  padding: 1.35rem 1.55rem; border-radius: 18px;
  background: linear-gradient(115deg,#073b4c 0%,#087e8b 55%,#25a6a1 100%);
  color: white; margin-bottom: 1.2rem;
}
.hero h1 {color:white; margin:0; font-size:2.15rem;}
.hero p {color:#e1f6f4; margin:.35rem 0 0 0; font-size:1rem;}
.section-note {color:#64748b; font-size:.9rem; margin-top:-.5rem;}
div[data-testid="stMetric"] {
  background:#ffffff; border:1px solid #e5edf2; padding:15px 17px;
  border-radius:14px; box-shadow:0 3px 12px rgba(15,45,65,.05);
}
div[data-testid="stMetricLabel"] p {color:#587083; font-weight:600;}
div[data-testid="stMetricValue"] {color:#123047;}
.card-title {font-size:1.12rem; font-weight:700; color:#173b50; margin:.25rem 0 .7rem;}
</style>
""", unsafe_allow_html=True)

# ---------- Sidebar ----------
with st.sidebar:
    st.markdown("## 🌦️ AtmoSync")
    st.caption("Micro-climate intelligence")
    st.markdown("---")
    st.markdown("### Data controls")
    if st.button("↻ Collect latest weather", use_container_width=True, type="primary"):
        with st.spinner("Collecting current weather from Open-Meteo..."):
            try:
                new_rows = collect_weather()
                st.success(f"Collected {len(new_rows)} location snapshots.")
                st.rerun()
            except Exception as exc:
                st.error(f"Collection failed: {exc}")
    st.markdown("---")
    st.markdown("### Filters")
    st.caption("Choose locations to include in the dashboard.")

# ---------- Load data ----------
try:
    df = load_weather_data()
except Exception as exc:
    st.error(f"Could not read weather data: {exc}")
    st.stop()

st.markdown("""
<div class="hero">
  <h1>🌦️ AtmoSync Weather Intelligence</h1>
  <p>Understand local weather patterns, compare micro-climates, and explore collected observations.</p>
</div>
""", unsafe_allow_html=True)

if df.empty:
    st.warning("No weather data is available yet. Use the sidebar button or run `python -m src.collector`.")
    st.code("python -m src.collector")
    st.stop()

all_locations = sorted(df["location"].dropna().astype(str).unique().tolist())
with st.sidebar:
    selected = st.multiselect("Locations", all_locations, default=all_locations)
    if not selected:
        st.info("Select at least one location to display analytics.")

view = df[df["location"].isin(selected)].copy()
if view.empty:
    st.info("Select at least one location from the sidebar.")
    st.stop()

summary = location_summary(view)
latest = view.copy()
if "collected_at" in latest.columns:
    latest["collected_at"] = pd.to_datetime(latest["collected_at"], errors="coerce")
    latest = latest.sort_values("collected_at").groupby("location", as_index=False).tail(1)

# Latest readings for headline cards; use latest record per location.
temp_avg = latest["temperature"].mean()
humidity_avg = latest["humidity"].mean()
wind_avg = latest["wind_speed"].mean() if "wind_speed" in latest.columns else float("nan")
temp_range = latest["temperature"].max() - latest["temperature"].min()
latest_stamp = ""
if "collected_at" in latest.columns and latest["collected_at"].notna().any():
    latest_stamp = latest["collected_at"].max().strftime("%d %b %Y, %I:%M %p")

st.markdown("### Live snapshot")
st.markdown(f'<p class="section-note">Latest available record per selected location · {latest_stamp or "collection time unavailable"}</p>', unsafe_allow_html=True)
m1, m2, m3, m4 = st.columns(4)
m1.metric("🌡️ Avg temperature", f"{temp_avg:.1f} °C" if pd.notna(temp_avg) else "—")
m2.metric("💧 Avg humidity", f"{humidity_avg:.1f}%" if pd.notna(humidity_avg) else "—")
m3.metric("💨 Avg wind speed", f"{wind_avg:.1f} km/h" if pd.notna(wind_avg) else "—")
m4.metric("↕️ Temperature spread", f"{temp_range:.1f} °C" if pd.notna(temp_range) else "—")

overview_tab, compare_tab, records_tab = st.tabs(["📊 Overview", "📍 Location comparison", "🧾 Data & reports"])

with overview_tab:
    st.markdown("### Weather at a glance")
    left, right = st.columns([1.55, 1])
    with left:
        st.markdown('<div class="card-title">Micro-climate heatmap</div>', unsafe_allow_html=True)
        heat_cols = [c for c in ["avg_temperature", "avg_humidity", "avg_wind_speed",
                                 "avg_precipitation", "avg_cloud_cover"] if c in summary.columns]
        if len(summary) and heat_cols:
            heat = summary.set_index("location")[heat_cols].copy()
            normalized = heat.copy()
            for col in normalized.columns:
                lo, hi = normalized[col].min(), normalized[col].max()
                normalized[col] = 0 if pd.isna(lo) or pd.isna(hi) or hi == lo else (normalized[col] - lo) / (hi - lo)
            labels = {
                "avg_temperature": "Temperature", "avg_humidity": "Humidity",
                "avg_wind_speed": "Wind", "avg_precipitation": "Precipitation",
                "avg_cloud_cover": "Cloud cover",
            }
            normalized.columns = [labels.get(c, c) for c in normalized.columns]
            fig_heat = px.imshow(
                normalized, text_auto=".2f", aspect="auto",
                color_continuous_scale="Tealrose", zmin=0, zmax=1,
                labels={"x": "Weather metric", "y": "Location", "color": "Relative level"},
            )
            fig_heat.update_layout(margin=dict(l=5,r=5,t=10,b=5), height=340,
                                   coloraxis_colorbar_title="Relative<br>level")
            st.plotly_chart(fig_heat, use_container_width=True)
        else:
            st.info("Heatmap needs location summary data.")
    with right:
        st.markdown('<div class="card-title">Weather condition mix</div>', unsafe_allow_html=True)
        if "weather_description" in latest.columns and latest["weather_description"].notna().any():
            condition_counts = latest["weather_description"].fillna("Unknown").value_counts().rename_axis("Condition").reset_index(name="Locations")
            names, values = condition_counts["Condition"], condition_counts["Locations"]
        else:
            condition_counts = latest[["location"]].copy()
            condition_counts["Locations"] = 1
            names, values = condition_counts["location"], condition_counts["Locations"]
        fig_donut = go.Figure(data=[go.Pie(
            labels=names, values=values, hole=.62,
            textinfo="label+percent", sort=False,
            marker=dict(line=dict(color="white", width=2)),
        )])
        fig_donut.update_layout(showlegend=False, height=340, margin=dict(l=5,r=5,t=10,b=5),
                                annotations=[dict(text=f"{len(latest)}<br>places", x=.5, y=.5,
                                                  font_size=18, showarrow=False)])
        st.plotly_chart(fig_donut, use_container_width=True)

    st.markdown("### Weather trends")
    trend = view.copy()
    if "collected_at" in trend.columns:
        trend["collected_at"] = pd.to_datetime(trend["collected_at"], errors="coerce")
        trend = trend.dropna(subset=["collected_at"]).sort_values("collected_at")
    if not trend.empty:
        metric_options = [c for c in ["temperature", "humidity", "wind_speed", "precipitation", "cloud_cover"] if c in trend.columns]
        metric_labels = {"temperature":"Temperature (°C)", "humidity":"Humidity (%)",
                         "wind_speed":"Wind speed (km/h)", "precipitation":"Precipitation (mm)",
                         "cloud_cover":"Cloud cover (%)"}
        chosen_metric = st.selectbox("Chart metric", metric_options, format_func=lambda x: metric_labels.get(x,x))
        fig_line = px.line(trend, x="collected_at", y=chosen_metric, color="location",
                           markers=True, title=metric_labels.get(chosen_metric, chosen_metric))
        fig_line.update_layout(height=360, margin=dict(l=5,r=5,t=50,b=5),
                               legend_title_text="Location", hovermode="x unified")
        st.plotly_chart(fig_line, use_container_width=True)
        if trend.groupby("location").size().max() < 2:
            st.caption("Only one snapshot per location is currently available. Collect weather data again over time to build meaningful trend lines.")
    else:
        st.info("Trend chart will appear when valid collection timestamps are available.")

with compare_tab:
    st.markdown("### Compare selected locations")
    c1, c2 = st.columns(2)
    with c1:
        fig_temp = px.bar(summary, x="location", y="avg_temperature", text_auto=".1f",
                          title="Average temperature by location",
                          labels={"location":"Location","avg_temperature":"Temperature (°C)"},
                          color="avg_temperature", color_continuous_scale="Teal")
        fig_temp.update_layout(height=360, showlegend=False, coloraxis_showscale=False,
                               margin=dict(l=5,r=5,t=55,b=5))
        st.plotly_chart(fig_temp, use_container_width=True)
    with c2:
        fig_hum = px.bar(summary, x="location", y="avg_humidity", text_auto=".1f",
                         title="Average humidity by location",
                         labels={"location":"Location","avg_humidity":"Humidity (%)"},
                         color="avg_humidity", color_continuous_scale="Blues")
        fig_hum.update_layout(height=360, showlegend=False, coloraxis_showscale=False,
                              margin=dict(l=5,r=5,t=55,b=5))
        st.plotly_chart(fig_hum, use_container_width=True)

    if len(selected) >= 2:
        st.markdown("#### Pairwise micro-climate differences")
        comparison = pairwise_comparison(summary)
        st.dataframe(comparison, use_container_width=True, hide_index=True)
    else:
        st.info("Select at least two locations to compare them.")
    st.markdown("#### Full location statistics")
    st.dataframe(summary, use_container_width=True, hide_index=True)

with records_tab:
    st.markdown("### Data quality and exports")
    cleaned = clean_weather_data(view)
    quality = data_quality_report(view, cleaned)
    q1, q2, q3 = st.columns(3)
    q1.metric("Records", len(view))
    q2.metric("Valid records", len(cleaned))
    q3.metric("Removed during cleaning", max(0, len(view)-len(cleaned)))
    st.dataframe(quality, use_container_width=True, hide_index=True)
    st.markdown("#### Download current data")
    st.download_button("⬇️ Download filtered weather CSV",
                       data=cleaned.to_csv(index=False).encode("utf-8"),
                       file_name="atmosync_filtered_weather.csv", mime="text/csv")
    if st.button("Generate Week 2 analysis reports", type="primary"):
        try:
            report_paths = save_reports(view)
            st.success("Week 2 reports generated in the data folder.")
            for label, path in report_paths.items():
                p = Path(path)
                if p.exists():
                    st.download_button(
                        f"Download {p.name}", data=p.read_bytes(),
                        file_name=p.name, mime="text/csv", key=f"report_{label}"
                    )
        except Exception as exc:
            st.error(f"Could not generate reports: {exc}")
    with st.expander("View collected raw records"):
        st.dataframe(view.sort_values("collected_at", ascending=False) if "collected_at" in view.columns else view,
                     use_container_width=True, hide_index=True)

st.markdown("---")
st.caption("Weather estimates are provided by Open-Meteo. They are model-based estimates, not street-level sensor measurements.")

with st.sidebar:
    st.markdown("## 🌦️ AtmoSync")
    st.caption("Weather Intelligence System")

    st.divider()

    st.subheader("Navigation")

    page = st.radio(
        "Choose Dashboard",
        [
            "🏠 Home",
            "📊 Weather Analytics",
            "🌡️ Temperature Analysis",
            "💧 Humidity Analysis",
            "📍 Location Management",
            "📥 Download Reports",
            "ℹ️ About AtmoSync"
        ]
    )

    st.divider()

    st.subheader("Quick Information")
    st.info("Weather Data: Open-Meteo")
    st.success("System Status: Active")