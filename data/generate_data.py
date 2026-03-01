import pandas as pd
import numpy as np
import uuid
import os

np.random.seed(42)
N = 500_000

print("Generating data... please wait ~30 seconds")

customer_ids = [f"CUST_{i:05d}" for i in range(1, 50_001)]
product_ids  = [f"PROD_{i:04d}" for i in range(1, 1_001)]
channels     = ["organic_search","paid_search","email","social_media","referral"]
categories   = ["Electronics","Apparel","Home Garden","Beauty","Sports"]

cust_arr  = np.random.choice(customer_ids, N)
prod_arr  = np.random.choice(product_ids, N)
chan_arr  = np.random.choice(channels, N, p=[0.30,0.25,0.20,0.15,0.10])
cat_arr   = np.random.choice(categories, N, p=[0.25,0.30,0.20,0.15,0.10])
qty_arr   = np.random.randint(1, 6, N)
price_arr = np.round(np.random.uniform(5, 500, N), 2)
disc_arr  = np.random.choice([0,0,0,5,10,15,20], N)
rev_arr   = np.round(qty_arr * price_arr * (1 - disc_arr/100), 2)
cost_arr  = np.round(np.random.uniform(0, 30, N), 2)
ret_arr   = np.random.choice([0,0,0,0,1], N)

base     = pd.Timestamp("2022-01-01")
days_arr = np.random.randint(0, 730, N)
date_arr = [(base + pd.Timedelta(days=int(d))).strftime("%Y-%m-%d") for d in days_arr]

print("Building dataframe...")

df = pd.DataFrame({
    "transaction_id" : [str(uuid.uuid4())[:12] for _ in range(N)],
    "customer_id"    : cust_arr,
    "product_id"     : prod_arr,
    "order_date"     : date_arr,
    "quantity"       : qty_arr,
    "unit_price"     : price_arr,
    "discount_pct"   : disc_arr,
    "revenue"        : rev_arr,
    "channel"        : chan_arr,
    "category"       : cat_arr,
    "marketing_cost" : cost_arr,
    "return_flag"    : ret_arr,
})

os.makedirs("data/raw", exist_ok=True)
df.to_csv("data/raw/transactions_raw.csv", index=False)
print(f"Done! Saved {len(df):,} rows to data/raw/transactions_raw.csv")