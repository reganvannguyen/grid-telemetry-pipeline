from pathlib import Path
import time
import pandas as pd
import requests

#weather stations mapped to region (using Climate ID)
STATIONS = {
    "Calgary": 3031092,   # CALGARY INTL A
    "Edmonton": 3012216,  # EDMONTON INTL A
    "Central": 3025484,   # RED DEER REGIONAL A
    "South": 3034485,     # MEDICINE HAT RCS
}
YEARS = (2024, 2025)
BASE_URL = "https://climate.weather.gc.ca/climate_data/bulk_data_e.html"


def download_weather(dest_folder: Path, stations: dict[str, int] = STATIONS, years: tuple[int, ...] = YEARS) -> None:
    """Download monthly hourly weather CSVs from Environment Canada into dest_folder."""
    dest_folder.mkdir(parents=True, exist_ok=True)

    #loop through each station, year, and month
    for region, climate_id in stations.items():
        for year in years:
            for month in range(1, 13):
                out_file = dest_folder / f"weather_{climate_id}_{year}_{month:02d}.csv"

                #skip if already downloaded
                if out_file.exists():
                    continue

                url = f"{BASE_URL}?format=csv&climate_id={climate_id}&Year={year}&Month={month}&Day=14&timeframe=1&submit=Download+Data"
                print(f"Fetching {region} ({climate_id}) {year}-{month:02d} from Environment Canada...")

                try:
                    response = requests.get(url, timeout=30)
                    response.raise_for_status()
                    if response.text.lstrip().startswith("<"):
                        print(f"Skipping {region} ({climate_id}) {year}-{month:02d}: got HTML instead of CSV")
                        continue
                    out_file.write_bytes(response.content)

                    #polite delay for public api
                    time.sleep(0.3)

                except requests.RequestException as e:
                    print(f"Failed to fetch {region} ({climate_id}) {year}-{month:02d}: {e}")


def extract_weather(path: str | Path) -> pd.DataFrame:
    #read the csv file
    df = pd.read_csv(path)

    #get columns Station Name, Date/Time (LST), Temp (°C)
    df = df[['Station Name', 'Date/Time (LST)', 'Temp (°C)']]

    #rename columns to lowercase snake
    df = df.rename(columns={'Station Name': 'station_name', 'Date/Time (LST)': 'dt_lst', 'Temp (°C)': 'temp_celsius'})

    #change dt_lst to a datetime type
    df['dt_lst'] = pd.to_datetime(df['dt_lst'])

    #fill isolated sensor gaps in temp_celsius
    df['temp_celsius'] = pd.to_numeric(df['temp_celsius'], errors='coerce').ffill()

    return df
