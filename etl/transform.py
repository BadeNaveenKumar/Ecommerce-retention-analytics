# etl/transform.py

import pandas as pd
import numpy as np

# ── CLEAN ──────────────────────────────────────────────────────────────────────

def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    original = len(df)
    df = df.copy()
    df.drop_duplicates(subset="transaction_id", inplace=True)
    df.dropna(subset=["customer_id", "product_id", "order_date"], inplace=True)
    df = df[df["return_flag"] == 0]
    df = df[df["revenue"] > 0]
    print(f"  Rows after cleaning: {len(df):,}  (removed {original - len(df):,})")
    return df

# ── DIMENSION TABLES ───────────────────────────────────────────────────────────

def build_dim_customer(df: pd.DataFrame) -> pd.DataFrame:
    dim = (df.groupby("customer_id")
             .agg(acquisition_date    =("order_date", "min"),
                  acquisition_channel =("channel",    "first"))
             .reset_index())
    dim["customer_key"] = range(1, len(dim) + 1)
    print(f"  dim_customer: {len(dim):,} rows")
    return dim

def build_dim_product(df: pd.DataFrame) -> pd.DataFrame:
    dim = (df[["product_id", "category", "unit_price"]]
             .drop_duplicates("product_id")
             .copy()
             .reset_index(drop=True))
    dim["product_key"] = range(1, len(dim) + 1)
    print(f"  dim_product: {len(dim):,} rows")
    return dim

def build_dim_date(df: pd.DataFrame) -> pd.DataFrame:
    dim = pd.DataFrame({"full_date": df["order_date"].unique()})
    dim["date_key"]    = dim["full_date"].dt.strftime("%Y%m%d").astype(int)
    dim["year"]        = dim["full_date"].dt.year
    dim["quarter"]     = dim["full_date"].dt.quarter
    dim["month"]       = dim["full_date"].dt.month
    dim["month_name"]  = dim["full_date"].dt.strftime("%B")
    dim["week"]        = dim["full_date"].dt.isocalendar().week.astype(int)
    dim["day_of_week"] = dim["full_date"].dt.day_name()
    dim["is_weekend"]  = dim["full_date"].dt.dayofweek >= 5
    dim = dim.sort_values("date_key").reset_index(drop=True)
    print(f"  dim_date: {len(dim):,} rows")
    return dim

def build_dim_channel(df: pd.DataFrame) -> pd.DataFrame:
    dim = pd.DataFrame({"channel_name": df["channel"].unique()})
    dim["channel_key"]  = range(1, len(dim) + 1)
    dim["channel_type"] = dim["channel_name"].map({
        "paid_search"    : "paid",
        "social_media"   : "paid",
        "organic_search" : "organic",
        "email"          : "owned",
        "referral"       : "organic",
    })
    print(f"  dim_channel: {len(dim):,} rows")
    return dim

# ── FACT TABLE ─────────────────────────────────────────────────────────────────

def build_fact_sales(df, dim_customer, dim_product,
                     dim_date, dim_channel) -> pd.DataFrame:
    fact = df.merge(dim_customer[["customer_id", "customer_key"]],
                    on="customer_id", how="left")
    fact = fact.merge(dim_product[["product_id", "product_key"]],
                      on="product_id", how="left")
    fact = fact.merge(dim_date[["full_date", "date_key"]],
                      left_on="order_date", right_on="full_date", how="left")
    fact = fact.merge(dim_channel[["channel_name", "channel_key"]],
                      left_on="channel", right_on="channel_name", how="left")
    fact = fact[[
        "transaction_id", "customer_key", "product_key",
        "date_key", "channel_key", "quantity",
        "unit_price", "discount_pct", "revenue", "marketing_cost"
    ]]
    print(f"  fact_sales: {len(fact):,} rows")
    return fact

# ── RFM SEGMENTATION ───────────────────────────────────────────────────────────

def run_rfm(df: pd.DataFrame) -> pd.DataFrame:
    snapshot = df["order_date"].max() + pd.Timedelta(days=1)

    rfm = df.groupby("customer_id").agg(
        recency   = ("order_date",     lambda x: (snapshot - x.max()).days),
        frequency = ("transaction_id", "count"),
        monetary  = ("revenue",        "sum")
    ).reset_index()

    rfm["R_score"] = pd.qcut(rfm["recency"],
                              5, labels=[5, 4, 3, 2, 1]).astype(int)
    rfm["F_score"] = pd.qcut(rfm["frequency"].rank(method="first"),
                              5, labels=[1, 2, 3, 4, 5]).astype(int)
    rfm["M_score"] = pd.qcut(rfm["monetary"],
                              5, labels=[1, 2, 3, 4, 5]).astype(int)

    rfm["rfm_total"] = rfm["R_score"] + rfm["F_score"] + rfm["M_score"]

    def label(score):
        if score >= 13: return "Champions"
        if score >= 10: return "Loyal"
        if score >= 7:  return "At Risk"
        return "Lost"

    rfm["segment"]  = rfm["rfm_total"].apply(label)
    rfm["monetary"] = rfm["monetary"].round(2)
    print(f"  RFM complete: {len(rfm):,} customers segmented")
    return rfm