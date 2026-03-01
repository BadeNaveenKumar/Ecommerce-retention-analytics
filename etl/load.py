# etl/load.py

import os
import pandas as pd

OUTPUT_DIR = "data/processed"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def load_to_csv(tables: dict):
    for name, df in tables.items():
        path = f"{OUTPUT_DIR}/{name}.csv"
        df.to_csv(path, index=False)
        print(f"  ✓ {name}.csv  →  {len(df):,} rows saved")