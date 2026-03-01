# analysis/cohort_analysis.py
# Run with: python analysis/cohort_analysis.py

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import seaborn as sns
import os

os.makedirs("outputs", exist_ok=True)

# ── LOAD DATA ──────────────────────────────────────────────
print("Loading data...")
raw = pd.read_csv("data/raw/transactions_raw.csv", parse_dates=["order_date"])
raw = raw[raw["return_flag"] == 0]
raw = raw[raw["revenue"] > 0]
print(f"  Rows loaded: {len(raw):,}")

# ── BUILD COHORT TABLE ─────────────────────────────────────
print("Building cohort table...")
raw["order_month"] = raw["order_date"].dt.to_period("M")

# Each customer's first purchase month = their cohort
first_purchase = (raw.groupby("customer_id")["order_date"]
                     .min()
                     .dt.to_period("M")
                     .rename("cohort_month"))

raw = raw.merge(first_purchase, on="customer_id")

# How many months after first purchase is this order?
raw["cohort_index"] = (raw["order_month"] - raw["cohort_month"]).apply(lambda x: x.n)

# Count unique customers per cohort per month
cohort_data = (raw.groupby(["cohort_month", "cohort_index"])
                  ["customer_id"].nunique()
                  .reset_index(name="customers"))

pivot = cohort_data.pivot(index="cohort_month",
                           columns="cohort_index",
                           values="customers")

# Retention = customers in month N / customers in month 0
cohort_size = pivot[0]
retention   = pivot.divide(cohort_size, axis=0).round(3)

# ── PRINT KEY NUMBERS ──────────────────────────────────────
print("\n── RETENTION INSIGHTS ───────────────────────────────")
print(f"  Month-1  avg retention: {retention[1].mean():.1%}")
print(f"  Month-3  avg retention: {retention[3].mean():.1%}")
print(f"  Month-6  avg retention: {retention[6].mean():.1%}")
if 12 in retention.columns:
    print(f"  Month-12 avg retention: {retention[12].mean():.1%}")

# Channel retention comparison
print("\n── RETENTION BY CHANNEL ─────────────────────────────")
channel_map = (raw[["customer_id","channel"]]
               .drop_duplicates("customer_id"))
cohort_channel = (raw.merge(channel_map, on="customer_id", suffixes=("","_first"))
                     .groupby(["channel","cohort_index"])["customer_id"]
                     .nunique().reset_index(name="customers"))

for ch in raw["channel"].unique():
    ch_data = cohort_channel[cohort_channel["channel"]==ch]
    ch_pivot = ch_data.pivot(index="channel", columns="cohort_index", values="customers")
    if 0 in ch_pivot.columns and 1 in ch_pivot.columns:
        m1 = (ch_pivot[1] / ch_pivot[0]).values[0]
        print(f"  {ch:<20} Month-1 retention: {m1:.1%}")

# ── DARK THEME COLORS ──────────────────────────────────────
BG_COLOR    = "#0D1117"   # Dark navy background
CARD_COLOR  = "#161B22"   # Slightly lighter dark
BLUE_ACCENT = "#1F6FEB"   # Blue accent
TEXT_WHITE  = "#FFFFFF"   # White text
TEXT_LIGHT  = "#8B949E"   # Light gray text

# ── PLOT HEATMAP ───────────────────────────────────────────
print("\nGenerating dark theme heatmap...")
window = retention.iloc[:, :13]   # show months 0 to 12

# ── SET DARK STYLE ─────────────────────────────────────────
plt.style.use("dark_background")

fig, ax = plt.subplots(figsize=(18, 10))

# Dark backgrounds
fig.patch.set_facecolor(BG_COLOR)
ax.set_facecolor(BG_COLOR)

# ── HEATMAP ────────────────────────────────────────────────
heatmap = sns.heatmap(
    window,
    annot      = True,
    fmt        = ".0%",
    cmap       = "Blues",
    linewidths = 0.5,
    linecolor  = "#1a2744",        # Dark blue grid lines
    vmin       = 0,
    vmax       = 0.5,
    ax         = ax,
    annot_kws  = {
        "size"   : 9,
        "weight" : "bold",
        "color"  : "white"
    },
    cbar_kws   = {
        "label"  : "Retention Rate",
        "shrink" : 0.8
    }
)

# ── COLORBAR STYLING ───────────────────────────────────────
cbar = heatmap.collections[0].colorbar
cbar.ax.yaxis.label.set_color(TEXT_WHITE)
cbar.ax.yaxis.label.set_fontsize(11)
cbar.ax.tick_params(colors=TEXT_WHITE, labelsize=9)
cbar.outline.set_edgecolor(BLUE_ACCENT)

# ── AXIS LABELS ────────────────────────────────────────────
ax.set_xlabel(
    "Months Since First Purchase",
    fontsize   = 12,
    color      = TEXT_WHITE,
    labelpad   = 10
)
ax.set_ylabel(
    "Acquisition Cohort (Month)",
    fontsize   = 12,
    color      = TEXT_WHITE,
    labelpad   = 10
)

# ── TICK LABELS ────────────────────────────────────────────
ax.tick_params(
    axis   = "both",
    colors = TEXT_WHITE,
    labelsize = 9
)
ax.set_xticklabels(
    ax.get_xticklabels(),
    color = TEXT_WHITE,
    fontsize = 9
)
ax.set_yticklabels(
    ax.get_yticklabels(),
    color    = TEXT_WHITE,
    fontsize = 9,
    rotation = 0
)

# ── BORDER / SPINE STYLING ─────────────────────────────────
for spine in ax.spines.values():
    spine.set_edgecolor(BLUE_ACCENT)
    spine.set_linewidth(1.5)

# ── KEY FINDINGS ANNOTATION ────────────────────────────────
m1  = retention[1].mean()
m6  = retention[6].mean() if 6  in retention.columns else 0
m12 = retention[12].mean() if 12 in retention.columns else 0

findings_text = (
    f"Key Retention Findings:   "
    f"Month-1: {m1:.1%}   |   "
    f"Month-6: {m6:.1%}   |   "
    f"Month-12: {m12:.1%}"
)

fig.text(
    0.5, 0.01,
    findings_text,
    ha        = "center",
    fontsize  = 10,
    color     = TEXT_WHITE,
    style     = "italic",
    bbox      = dict(
        boxstyle    = "round,pad=0.4",
        facecolor   = CARD_COLOR,
        edgecolor   = BLUE_ACCENT,
        linewidth   = 1.2
    )
)

plt.tight_layout(rect=[0, 0.04, 1, 1])

# ── SAVE WITH DARK BACKGROUND ──────────────────────────────
plt.savefig(
    "outputs/cohort_heatmap.png",
    dpi         = 150,
    facecolor   = BG_COLOR,      # ← Dark background in saved PNG
    bbox_inches = "tight"
)
print("✓ Saved: outputs/cohort_heatmap.png")
plt.show()