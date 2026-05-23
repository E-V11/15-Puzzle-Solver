import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import scipy.stats as stats
import statsmodels.api as sm
from statsmodels.stats.diagnostic import het_breuschpagan
import warnings
warnings.filterwarnings("ignore")

#Data loading perimeters
df = pd.read_csv("benchmark.csv")

print("=" * 60)
print("  15-Puzzle Solver — Empirical Analysis")
print("=" * 60)
print(f"\nTotal observations loaded: {len(df)}")
print(f"Timed out: {df['timed_out'].sum()} ({100 * df['timed_out'].mean():.1f}%)")
print(f"Solved:    {(~df['timed_out']).sum()} ({100 * (~df['timed_out']).mean():.1f}%)")

