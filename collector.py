"""Collect current weather from Open-Meteo for multiple sample locations."""
from pathlib import Path
from datetime import datetime
import requests
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
DATA_FILE = DATA_DIR / "weather_data.csv"

# Approximate sample coordinates. Replace/add locations approved by your team.
LOCATIONS = {
    "Pune": (18.5204, 73.8567),
    "Pimpri-Chinchwad": (18.6298, 73.7997),
    "Hinjawadi": (18.5912, 73.7389),
    "Hadapsar": (18.5089, 73.9260),
    "Kothrud": (18.5074, 73.8077),
}

API_URL = "https://api.open-meteo.com/v1/forecast"
CURRENT_FIELDS = (
    "temperature_2m,relative_humidity_2m,precipitation,"
    "wind_speed_10m,cloud_cover,weather_code"
)

WEATHER_CODES = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    71: "Slight snow",
    73: "Moderate snow",
    75: "Heavy snow",
    80: "Rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    95: "Thunderstorm",
    96: "Thunderstorm with hail",
    99: "Thunderstorm with heavy hail",
}

def fetch_location_weather(name: str, latitude: float, longitude: float) -> dict:
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": CURRENT_FIELDS,
        "timezone": "Asia/Kolkata",
        "wind_speed_unit": "kmh",
    }
    response = requests.get(API_URL, params=params, timeout=30)
    response.raise_for_status()
    payload = response.json()
    current = payload.get("current")
    if not current:
        raise ValueError(f"No current weather returned for {name}")

    code = int(current.get("weather_code", -1))
    return {
        "location": name,
        "latitude": latitude,
        "longitude": longitude,
        "time": current.get("time"),
        "temperature": current.get("temperature_2m"),
        "humidity": current.get("relative_humidity_2m"),
        "precipitation": current.get("precipitation"),
        "wind_speed": current.get("wind_speed_10m"),
        "cloud_cover": current.get("cloud_cover"),
        "weather_code": code,
        "weather_description": WEATHER_CODES.get(code, "Unknown"),
        "collected_at": datetime.now().astimezone().isoformat(timespec="seconds"),
    }

def collect_weather(locations: dict | None = None) -> pd.DataFrame:
    """Fetch all locations; save successful records by appending to CSV."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    locations = locations or LOCATIONS
    records = []
    errors = []

    for name, coords in locations.items():
        try:
            records.append(fetch_location_weather(name, coords[0], coords[1]))
            print(f"Collected: {name}")
        except (requests.RequestException, ValueError, KeyError) as exc:
            errors.append(f"{name}: {exc}")
            print(f"ERROR: {name}: {exc}")

    if not records:
        raise RuntimeError("No locations could be collected. Check internet/API connection.")

    new_data = pd.DataFrame(records)
    if DATA_FILE.exists():
        old_data = pd.read_csv(DATA_FILE)
        combined = pd.concat([old_data, new_data], ignore_index=True)
    else:
        combined = new_data

    combined.to_csv(DATA_FILE, index=False)
    print(f"\nSaved {len(records)} new records to: {DATA_FILE}")
    if errors:
        print("\nSome locations failed:")
        print("\n".join(errors))
    return new_data

if __name__ == "__main__":
    collect_weather()
