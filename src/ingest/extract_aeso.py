from pathlib import Path
import pandas as pd

def extract_aeso(path: str | Path) -> pd.DataFrame:
    #read the csv file 
    df = pd.read_csv(path)

    #remove/get the columns needed
    df = df.drop(columns=["DT_MPT","Month","BTFGen","CSDGen"])

    #rename to lower case snake
    df.columns = df.columns.str.strip().str.lower().str.replace(r'\s+', '_', regex=True)

    #normalize the timestamp
    df['dt_mst'] = pd.to_datetime(df['dt_mst'])

    #change all null values of sysgen to 0.0
    df['sysgen'] = df['sysgen'].fillna(0.0)

    #remove any duplicates 
    df = df.drop_duplicates()

    #sort based on date time if its not already
    if not df['dt_mst'].is_monotonic_increasing:
        df = df.sort_values(by='dt_mst').reset_index(drop=True)

    return df


   



