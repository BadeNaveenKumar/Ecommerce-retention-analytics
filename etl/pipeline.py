# etl/pipeline.py  ── the main runner
# Run with: python etl/pipeline.py

from etl.extract import extract_raw
from etl.transform import (clean_data, build_dim_customer, build_dim_product,
                            build_dim_date, build_dim_channel,
                            build_fact_sales, run_rfm)
from etl.load import load_to_csv

def run():
    print("\n── STEP 1: EXTRACT ──────────────────────────────────")
    raw = extract_raw("data/raw/transactions_raw.csv")

    print("\n── STEP 2: CLEAN & TRANSFORM ────────────────────────")
    clean    = clean_data(raw)

    dim_cust = build_dim_customer(clean)
    dim_prod = build_dim_product(clean)
    dim_date = build_dim_date(clean)
    dim_chan = build_dim_channel(clean)
    fact     = build_fact_sales(clean, dim_cust, dim_prod, dim_date, dim_chan)

    print("\n── STEP 3: RFM SEGMENTATION ─────────────────────────")
    rfm      = run_rfm(clean)

    print("\n  Segment breakdown:")
    print(rfm["segment"].value_counts().to_string())

    champions_rev = clean.merge(rfm[["customer_id","segment"]], on="customer_id")
    champ_pct = (champions_rev[champions_rev["segment"]=="Champions"]["revenue"].sum()
                 / champions_rev["revenue"].sum() * 100)
    print(f"\n  Champions drive {champ_pct:.1f}% of total revenue")

    dim_cust = dim_cust.merge(
        rfm[["customer_id","recency","frequency","monetary","segment"]],
        on="customer_id", how="left")

    print("\n── STEP 4: LOAD TO CSV ──────────────────────────────")
    load_to_csv({
        "dim_customer" : dim_cust,
        "dim_product"  : dim_prod,
        "dim_date"     : dim_date,
        "dim_channel"  : dim_chan,
        "fact_sales"   : fact,
        "rfm_segments" : rfm,
    })

    print("\n✓ Pipeline complete! Check your data/processed/ folder.")

if __name__ == "__main__":
    run()