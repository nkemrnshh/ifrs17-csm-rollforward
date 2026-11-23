"""
Python version of the CSM roll-forward model (cross-check for CSM_model.xlsx).

Product: 10-year level term, one cohort; premiums and expenses at the start of each
policy year, claims at the end. See data/README_data.md for the mortality source.
"""
import numpy as np

TERM = 10
DEFAULTS = dict(
    n=1000, sa=100_000, exp_pp=50.0, i=0.039, ra_pct=0.05, loading=1.20, scaling=1.0,
    q5_4044=0.01168, q5_4549=0.02081,   # DOSM 5q, Selangor male 2024
    premium=None,                         # None = solve from loading; number = fixed premium
)

def smoothed_q(q5_4044, q5_4549, ages=range(40, 50)):
    """Convert 5q to annual q, then straight-line ln(q) through band midpoints 42 and 47."""
    q42 = 1 - (1 - q5_4044) ** (1 / 5)
    q47 = 1 - (1 - q5_4549) ** (1 / 5)
    slope = np.log(q47 / q42) / 5
    return np.array([q42 * np.exp(slope * (a - 42)) for a in ages])

def _lives(q, n):
    l = np.empty(TERM + 1); l[0] = n
    for k in range(TERM):
        l[k + 1] = l[k] * (1 - q[k])
    return l

def run_model(**overrides):
    """Initial recognition and CSM roll-forward. Optional event B via event_year/shift."""
    p = {**DEFAULTS, **overrides}
    event_year = p.pop("event_year", None)      # end of policy year (1-9) when estimates change
    shift = p.pop("shift", 0.0)                 # increase in future mortality
    i, n, sa = p["i"], p["n"], p["sa"]
    q = smoothed_q(p["q5_4044"], p["q5_4549"]) * p["scaling"]
    v = 1 / (1 + i); t = np.arange(TERM)
    lives = _lives(q, n); deaths = lives[:TERM] * q
    pv_c = (deaths * sa * v ** (t + 1)).sum()
    pv_e = (lives[:TERM] * p["exp_pp"] * v ** t).sum()
    ann = (lives[:TERM] * v ** t).sum()
    prem = p["premium"] if p["premium"] is not None else p["loading"] * (pv_c + pv_e) / ann
    pv_p = (lives[:TERM] * prem * v ** t).sum()
    ra = p["ra_pct"] * pv_c
    fcf = pv_c + pv_e - pv_p + ra
    csm0, loss0 = max(-fcf, 0.0), max(fcf, 0.0)

    # roll-forward (with optional event B)
    cu_b = lives[:TERM] * sa
    dF = 0.0; cu_r = cu_b
    if event_year:
        Y = event_year
        qr = np.where(t >= Y, q * (1 + shift), q); lr = _lives(qr, n); dr = lr[:TERM] * qr
        fut = t >= Y
        dfs = np.where(fut, v ** (t - Y), 0.0); dfe = np.where(fut, v ** (t + 1 - Y), 0.0)
        def f_future(l, d):
            pc = (d * sa * dfe).sum(); pe = (l[:TERM] * p["exp_pp"] * dfs).sum(); pp = (l[:TERM] * prem * dfs).sum()
            return pc + pe - pp + p["ra_pct"] * pc
        dF = f_future(lr, dr) - f_future(lives, deaths)
        cu_r = lr[:TERM] * sa
    csm = csm0; rel = []; clo = []; loss_adj = 0.0
    for k in range(TERM):
        op = csm; acc = op * i; adj = 0.0
        if event_year and k + 1 == event_year:
            adj = -min(dF, op + acc) if dF > 0 else -dF
            loss_adj = max(dF - (op + acc), 0.0)
        use_r = bool(event_year) and (k + 1 >= event_year)
        cu = cu_r if use_r else cu_b
        pre = op + acc + adj; r = pre * cu[k] / cu[k:].sum(); csm = pre - r
        rel.append(r); clo.append(csm)
    return dict(premium=prem, pv_claims=pv_c, pv_expenses=pv_e, pv_premiums=pv_p, ra=ra, fcf=fcf,
                csm0=csm0, day_one_loss=loss0, status="Profitable" if fcf < 0 else ("Onerous" if fcf > 0 else "Break-even"),
                release=rel, closing=clo, delta_fcf=dF, loss_from_adjustment=loss_adj)

if __name__ == "__main__":
    r = run_model()
    print({k: (round(v, 2) if isinstance(v, float) else v) for k, v in r.items() if k not in ("release", "closing")})
