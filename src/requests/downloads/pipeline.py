from pathlib import Path
import sqlite3
import sys
import zipfile
import pandas as pd

#let the path work anywhere and allow imports from project root
PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.ingest.extract_aeso import extract_aeso
from src.ingest.extract_weather import download_weather, extract_weather

DB_PATH = PROJECT_ROOT / "data/grid_telemetry.db"


def run_ingest(folder: Path, extract_fn, table_name: str, sort_col: str | None = None, db_path: Path = DB_PATH) -> None:
    """Unzip any .zip files in folder, run extract_fn on each CSV, combine, and load into SQLite."""
    #find any zip files in the folder
    zip_files = []
    for item in folder.iterdir():
        if item.is_file() and item.suffix == ".zip":
            zip_files.append(item)

    #unzip files into unzipped/ if zips exist, otherwise read CSVs straight from folder
    if zip_files:
        csv_dir = folder / "unzipped"
        for item in zip_files:
            with zipfile.ZipFile(item, "r") as zip_ref:
                zip_ref.extractall(csv_dir)
            print(f"Unzipped {item.name} into {csv_dir}")
    else:
        csv_dir = folder

    #read and clean each csv file
    csv_files = sorted(csv_dir.glob("*.csv"))
    dfs = []
    for f in csv_files:
        dfs.append(extract_fn(f))

    #combine all files, remove duplicates, and sort if a sort column was given
    df = pd.concat(dfs, ignore_index=True).drop_duplicates()
    if sort_col:
        df = df.sort_values(by=sort_col)
    df = df.reset_index(drop=True)

    #write the combined table to sqlite
    with sqlite3.connect(db_path) as conn:
        df.to_sql(name=table_name, con=conn, if_exists="replace", index=False, chunksize=10000)

    print(f"Loaded {len(df)} rows into {db_path} (table: {table_name})")


#run the pipeline for aeso (and weather later)
if __name__ == "__main__":
    run_ingest(
        folder=PROJECT_ROOT / "data/raw/aeso",
        extract_fn=extract_aeso,
        table_name="raw_aeso_load",
        sort_col="dt_mst",
    )

    weather_dir = PROJECT_ROOT / "data/raw/weather"
    download_weather(weather_dir)
    run_ingest(
        folder=weather_dir,
        extract_fn=extract_weather,
        table_name="raw_weather",
        sort_col="dt_lst",
    )
