# AtmoSync – Micro-Climate Arbitrage Analytics

A beginner-friendly Python project that collects current weather estimates for multiple locations, analyses differences with Pandas, and displays results in a Streamlit + Plotly dashboard.

## Project weeks

- **Week 1 – Data Collection:** Python setup, Open-Meteo API connection, collect weather snapshots for multiple locations.
- **Week 2 – Data Analysis:** Clean data, calculate temperature/humidity statistics, compare locations and export CSV reports.
- **Week 3 – Dashboard:** Streamlit dashboard with Plotly bar charts, trend chart, pairwise comparisons and normalized heatmap.
- **Week 4 – Finalization:** Test, commit to GitHub, deploy on Streamlit Community Cloud and prepare presentation.

## 1. Requirements

Install Python 3.10 or newer. On Windows, open PowerShell or VS Code terminal in this folder.

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

If PowerShell blocks activation, use Command Prompt:

```cmd
venv\Scripts\activate.bat
```

## 2. Week 1 – Collect weather data

```bash
python -m src.collector
```

The collector requests current weather from Open-Meteo for sample Pune-area coordinates and appends records to `data/weather_data.csv`. Run it more than once (for example, morning, afternoon and evening) to build a history for the trend chart.

The coordinates in `src/collector.py` are approximate sample coordinates. Verify or replace them with team-approved locations.

## 3. Week 2 – Analyse data

```bash
python -m src.analysis
```

Generated reports:
- `data/cleaned_weather_data.csv`
- `data/location_analysis.csv`
- `data/location_comparison.csv`
- `data/overall_statistics.csv`

## 4. Week 3 – Launch dashboard

```bash
streamlit run app.py
```

Open the local URL printed in the terminal. Use **Collect latest weather data** in the sidebar to append a fresh snapshot. Select locations to filter the dashboard.

## 5. Week 4 – Test

```bash
python -m pytest -q
```

Manual checks:
1. Run collection and verify that the CSV is created.
2. Run collection again and confirm that new rows are appended.
3. Run analysis and verify all four report CSVs.
4. Launch the dashboard and test location filters, charts and heatmap.
5. Try the dashboard with no CSV present; it should show a helpful message.
6. Check that missing numeric values are ignored during analysis.

## 6. GitHub workflow

Create a repository on GitHub, then in the project folder:

```bash
git init
git add .
git commit -m "Initial AtmoSync project setup"
git branch -M main
git remote add origin YOUR_GITHUB_REPOSITORY_URL
git push -u origin main
```

For team work, agree on branch names with the team lead. Example:

```bash
git switch -c week1-data-collection
git add src/collector.py README.md requirements.txt
git commit -m "Add multi-location weather collection"
git push -u origin week1-data-collection
```

Create pull requests to merge branches. Do not commit your virtual environment. Data CSV files are ignored by `.gitignore`; if your team needs sample data in GitHub, add a small anonymized/sample CSV intentionally and coordinate with the team.

## 7. Week 4 – Deploy to Streamlit Community Cloud

1. Push the project to GitHub.
2. Sign in to Streamlit Community Cloud using your GitHub account.
3. Create a new app and select your repository, branch (`main`) and main file (`app.py`).
4. Deploy the app.
5. Check app logs if deployment fails; ensure `requirements.txt` is in the repository root.

**Important:** Streamlit Community Cloud uses an ephemeral filesystem. Data collected while the app is running may not be permanently retained across restarts/redeployments. For a persistent production project, connect a database or persistent storage. For a student demo, collect data locally and optionally commit a small sample CSV if permitted.

## 8. Project limitations and attribution

- Open-Meteo current conditions are weather-model estimates, not direct street-level sensor readings.
- The sample coordinates are approximate; verify them before final analysis.
- “Arbitrage” in this project means identifying differences/insights between micro-climates. It does not perform financial trading.
- Include attribution: **Weather data by Open-Meteo.com**.

## 9. Presentation outline

1. Title: AtmoSync – Micro-Climate Arbitrage Analytics
2. Problem statement: weather can vary across nearby locations.
3. Objective: collect, compare and visualize local weather estimates.
4. Tech stack: Python, Open-Meteo, Pandas, Streamlit, Plotly.
5. Data collection: locations, API fields and CSV storage.
6. Analysis: average/min/max temperature and humidity; pairwise differences.
7. Dashboard: charts, comparison table and heatmap.
8. Testing: test commands and validation checks.
9. Results: show actual screenshots and actual measured output from your run.
10. Limitations and future scope: sensors, longer time series, database, improved spatial coverage.
11. Team contributions and GitHub repository.
12. Conclusion.

## Suggested team division

- Member 1: API/data collection and location verification.
- Member 2: data cleaning and Pandas analysis.
- Member 3: Streamlit dashboard and Plotly charts.
- Member 4 (or shared): testing, GitHub integration, deployment and presentation.

Everyone should understand the complete project and contribute meaningful commits. Adjust division to your actual team size.
