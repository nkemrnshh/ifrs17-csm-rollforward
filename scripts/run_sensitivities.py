"""
Step 7: sensitivities and stress scenarios, holding the contract premium fixed at the base case.
Run from the project folder:  python scripts/run_sensitivities.py
Writes results/sensitivities.csv and results/two_way_csm.csv.
"""
import sys, os
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
from csm_model import run_model

base = run_model()
P = base["premium"]                       # contract premium held fixed in every scenario
b0 = run_model(premium=P)

# 2021 and 2022 Selangor male 5q (DOSM lifetables_state.csv)
STRESS = {"DOSM 2021 mortality (Selangor male)": (0.01529, 0.02533),
          "DOSM 2022 mortality (Selangor male)": (0.01502, 0.02567)}

scen = [("Base case", {})]
scen += [(f"Mortality x{int(s*100)}%", dict(scaling=s)) for s in (0.8, 0.9, 1.1, 1.2)]
scen += [("Discount rate 2.9% (-1%)", dict(i=0.029)), ("Discount rate 4.9% (+1%)", dict(i=0.049))]
scen += [("Risk adjustment 3%", dict(ra_pct=0.03)), ("Risk adjustment 8%", dict(ra_pct=0.08))]
scen += [("Expenses RM40 per policy", dict(exp_pp=40.0)), ("Expenses RM60 per policy", dict(exp_pp=60.0))]
scen += [(k, dict(q5_4044=a, q5_4549=b)) for k, (a, b) in STRESS.items()]
scen += [("Combined adverse: mortality x120%, expenses RM60, RA 8%", dict(scaling=1.2, exp_pp=60.0, ra_pct=0.08))]

rows = []
for name, kw in scen:
    r = run_model(premium=P, **kw)
    rows.append(dict(scenario=name, premium=P, pv_claims=r["pv_claims"], pv_expenses=r["pv_expenses"],
                     pv_premiums=r["pv_premiums"], ra=r["ra"], fcf=r["fcf"], day_one_csm=r["csm0"],
                     day_one_loss=r["day_one_loss"], status=r["status"], year1_release=r["release"][0]))
df = pd.DataFrame(rows)
df["csm_change"] = df["day_one_csm"] - b0["csm0"]
df["csm_change_pct"] = df["csm_change"] / b0["csm0"]
df.to_csv("results/sensitivities.csv", index=False, float_format="%.4f")

# Two-way: mortality scaling x discount rate -> day-one CSM
sc = [0.8, 0.9, 1.0, 1.1, 1.2]; dr = [0.029, 0.034, 0.039, 0.044, 0.049]
grid = pd.DataFrame([[run_model(premium=P, scaling=s, i=d)["csm0"] for d in dr] for s in sc],
                    index=[f"x{int(s*100)}%" for s in sc], columns=[f"{d:.1%}" for d in dr])
grid.to_csv("results/two_way_csm.csv", float_format="%.2f")

# Break-even mortality multiplier (fixed premium): bisection on FCF = 0
lo, hi = 1.0, 6.0
for _ in range(60):
    mid = (lo + hi) / 2
    if run_model(premium=P, scaling=mid)["fcf"] < 0: lo = mid
    else: hi = mid
print(f"premium held at {P:.4f}; break-even mortality multiplier = {lo:.4f}")
print(df[["scenario","fcf","day_one_csm","csm_change","csm_change_pct","status","year1_release"]].round(4).to_string(index=False))
print(grid.round(0).to_string())
