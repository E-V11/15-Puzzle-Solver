import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import scipy.stats as stats
import statsmodels.api as sm
from statsmodels.stats.diagnostic import het_breuschpagan
import warnings
warnings.filterwarnings("ignore")

df = pd.read_csv("benchmark.csv")

print("=" * 60)
print("  15-Puzzle Solver — Empirical Analysis")
print("=" * 60)
print(f"\nTotal observations loaded: {len(df)}")

# Timed-out runs are right-censored, naive exclusion biases runtime estimates downward
print(f"Timed out: {df['timed_out'].sum()} ({100 * df['timed_out'].mean():.1f}%)")
print(f"Solved:    {(~df['timed_out']).sum()} ({100 * (~df['timed_out']).mean():.1f}%)")

print("\n" + "=" * 60)
print(" Descriptive Statistics (solved boards only)")
print("=" * 60)

# Restrict to uncensored observations. timed-out boards cannot contribute valid outcome measures
solved = df[df["timed_out"] == False].copy()

desc_vars = ["solve_time", "moves", "states_explored", "log_states", "initial_manhattan", "initial_conflicts", "initial_heuristic"]
desc = solved[desc_vars].describe().T
desc = desc[["mean", "std", "min", "25%", "50%", "75%", "max"]]
desc.columns = ["Mean", "Std", "Min", "Q1", "Median", "Q3", "Max"]
print(desc.round(4).to_string())

