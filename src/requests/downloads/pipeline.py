from pathlib import Path
import sqlite3
import sys
import zipfile
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[3] #this lets the path of the file work anywhere
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.ingest.extract_aeso import extract_aeso

folder = PROJECT_ROOT / "data/raw/aeso"
extract_to = folder / "unzipped"

for item in folder.iterdir():
    # Check if it's a file and ends with .zip
    if item.is_file() and item.suffix == ".zip":
        with zipfile.ZipFile(item, "r") as zip_ref:
            zip_ref.extractall(extract_to)
        print(f"Unzipped {item.name} into {extract_to}")

csv_files = sorted(extract_to.glob("*.csv"))
dfs = []
for f in csv_files:
    dfs.append(extract_aeso(f))

df = pd.concat(dfs, ignore_index=True).drop_duplicates().sort_values(by="dt_mst").reset_index(drop=True)

#sqlite
db_path = PROJECT_ROOT / "data/grid_telemetry.db"
with sqlite3.connect(db_path) as conn:
    df.to_sql(name='raw_aeso_load', con=conn, if_exists='replace', index=False, chunksize=10000)

print(f"Loaded {len(df)} rows into {db_path} (table: planning_Area_Load_hourly)")
