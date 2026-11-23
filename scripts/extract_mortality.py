"""
Step 1 of the CSM roll-forward project:
extract the mortality inputs from the OpenDOSM state life table file and
save them as small, reproducible CSVs in /data.

Run from the project folder:
    python scripts/extract_mortality.py path/to/lifetables_state.csv
"""
import sys
import numpy as np
import pandas as pd

# ---- Choices (change these and re-run; record any change in data/README_data.md)
STATE = "Selangor"
SEX = "male"
DATE = "2024-01-01"          # latest year not labelled provisional/estimate by DOSM
BANDS = ["40-44", "45-49"]   # 5-year age bands; midpoints are ages 42 and 47
MIDPOINTS = {"40-44": 42, "45-49": 47}
AGES = list(range(40, 50))   # ages used by the 10-year term product (age 40 at entry)

src = sys.argv[1] if len(sys.argv) > 1 else "lifetables_state.csv"
df = pd.read_csv(src)

sel = df[(df.state == STATE) & (df.sex == SEX) & (df.date == DATE) & (df.age.isin(BANDS))].copy()
assert len(sel) == len(BANDS), f"Expected {len(BANDS)} rows, found {len(sel)}. Check STATE/SEX/DATE."

# Convert the 5-year death probability (5q) to a one-year rate: q = 1 - (1 - 5q)^(1/5)
sel["q_annual_converted"] = 1 - (1 - sel["prob_death"]) ** (1 / 5)
sel["midpoint_age"] = sel["age"].map(MIDPOINTS)
sel["check_ratio_vs_file_rate"] = sel["q_annual_converted"] / sel["mortality_rate"]

bands = sel[["state", "sex", "date", "age", "midpoint_age",
             "prob_death", "q_annual_converted", "mortality_rate",
             "check_ratio_vs_file_rate"]].rename(columns={"age": "age_band", "prob_death": "prob_death_5q",
                                                         "mortality_rate": "mortality_rate_in_file"})
bands.to_csv("data/mortality_bands.csv", index=False, float_format="%.6f")

# Smooth: straight line through log(q) at the two band midpoints (Gompertz-style)
sel = sel.sort_values("midpoint_age")
(m1, m2), (q1, q2) = sel["midpoint_age"].to_list(), sel["q_annual_converted"].to_list()
slope = np.log(q2 / q1) / (m2 - m1)
q_x = [q1 * np.exp(slope * (a - m1)) for a in AGES]
out = pd.DataFrame({"age": AGES, "q_smoothed": q_x})
out.to_csv("data/mortality_ages_40_49.csv", index=False, float_format="%.6f")

print(bands.to_string(index=False))
print(f"\nlog-slope = {slope:.5f}")
print(out.to_string(index=False))
