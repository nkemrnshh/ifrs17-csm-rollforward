Mortality inputs

1. Source
* Department of Statistics Malaysia (DOSM), OpenDOSM data catalogue, abridged life tables by state ("lifetables_state").
* File used: `lifetables_state.csv` (downloaded: 22/11/2026).
* Licence: Creative Commons Attribution 4.0 International (CC BY 4.0), as stated on the dataset's OpenDOSM page: https://creativecommons.org/licenses/by/4.0/
* Attribution: Life Tables by State & Sex, Department of Statistics Malaysia (DOSM), via OpenDOSM (https://open.dosm.gov.my/data-catalogue/lifetables_state). Changes made extracted one state, sex, year and two age bands; converted 5-year death probabilities to annual rates; smoothed to single ages.

2. Selection
* State: Selangor | Sex: male | Year: 2024 (the latest year not labelled provisional or estimate on DOSM's release page) | Ages 40-49.
* Why: large population (less noisy than small states). Results are specific to this choice, not "Malaysian mortality".

3. Method
1. Take the 5-year death probability (`prob_death`, 5q) for bands 40-44 and 45-49.
2. Convert to a one-year rate: q = 1 - (1 - 5q) ^ (1/5). Check: matches the file's `mortality_rate` within about 0.5%.
3. Treat each converted rate as applying at the band midpoint (age 42 and age 47).
4. Smooth with a straight line through log(q) at the two midpoints and read off ages 40 to 49 (`mortality_ages_40_49.csv`).

4. Files
* `mortality_bands.csv`: raw and converted band rates, with the check ratio.
* `mortality_ages_40_49.csv`: smoothed annual rates used by the model.
* Reproduce with `python scripts/extract_mortality.py lifetables_state.csv`.

5. Limitations
* Population mortality, not insured-lives mortality (insured lives are usually lighter).
* Abridged 5-year bands, so single-age rates are an interpolation assumption.
* State-level data; rates differ a lot between states (about 3x between the lowest and highest at ages 40-44).
* Smoothing is a modelling assumption, not part of the DOSM data.

