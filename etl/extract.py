# etl/extract.py

import pandas as pd

def extract_raw(filepath: str) -> pd.DataFrame:
    print(f"  Loading: {filepath}")
    df = pd.read_csv(filepath, parse_dates=["order_date"])
    print(f"  Rows loaded: {len(df):,}")
    return df