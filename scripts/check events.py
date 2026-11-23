"""
Cross-check of the Python model against CSM_model.xlsx (base case and Event B).
Run from the project folder:  python scripts/check_events.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from csm_model import run_model

base = run_model()
ev = run_model(event_year=5, shift=0.10)

excel = {
    "premium": 428.34,
    "day-one CSM": 469523,
    "year-10 closing CSM (base)": 0,
    "change in FCF (Event B)": 193233,
    "closing CSM by year (Event B)": [438472, 404381, 367075, 326373, 121329, 100639, 78247, 54069, 28016, 0],
}
python = {
    "premium": round(base["premium"], 2),
    "day-one CSM": round(base["csm0"]),
    "year-10 closing CSM (base)": round(base["closing"][-1], 6),
    "change in FCF (Event B)": round(ev["delta_fcf"]),
    "closing CSM by year (Event B)": [round(x) for x in ev["closing"]],
}
for k in excel:
    ok = "PASS" if excel[k] == python[k] else "FAIL"
    print(f"{ok}  {k}\n      Excel:  {excel[k]}\n      Python: {python[k]}")
