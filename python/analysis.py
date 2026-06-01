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

#OLS 
print("\n" + "=" * 60)
print("  OLS Regression: log(states explored) ~ board features")
print("=" * 60)
# log_states is the dependent variable — states explored is heavily right-skewed
# so log transformation is standard practice before running OLS
X_ols = solved[["initial_manhattan", "initial_conflicts", "initial_heuristic",
                 "blank_position", "tiles_in_place"]].copy()
X_ols = sm.add_constant(X_ols)
y_ols = solved["log_states"]

ols_model = sm.OLS(y_ols, X_ols).fit()
print(ols_model.summary())

print("\n" + "=" * 60)
print("  Breusch-Pagan Test for Heteroskedasticity")
print("=" * 60)

# OLS assumes constant error variance, BP test checks whether this holds
bp_test = het_breuschpagan(ols_model.resid, ols_model.model.exog)
bp_labels = ["LM Statistic", "LM p-value", "F Statistic", "F p-value"]
for label, val in zip(bp_labels, bp_test):
    print(f"  {label}: {val:.4f}")

if bp_test[1] < 0.05:
    # Heteroskedasticity present, HC3 robust SEs correct for non-constant variance
    print("\n  Heteroskedasticity detected (p < 0.05), re-estimating with HC3 robust standard errors.")
    ols_robust = sm.OLS(y_ols, X_ols).fit(cov_type="HC3")
    print(ols_robust.summary())
else:
    print("\n  No significant heteroskedasticity detected.")

#Log-lin model
print("\n" + "=" * 60)
print("  Log-Linear Model: log(solve_time) ~ initial_heuristic")
print("=" * 60)

# log(1 + solve_time) avoids log(0) for near-instant solves
solved["log_solve_time"] = np.log1p(solved["solve_time"])

X_log = sm.add_constant(solved[["initial_heuristic"]])
y_log = solved["log_solve_time"]

log_model = sm.OLS(y_log, X_log).fit()
print(log_model.summary())

#Model Comp 
print("\n" + "=" * 60)
print("  Model Comparison: AIC / BIC")
print("=" * 60)

# Lower AIC/BIC indicates better model fit penalised for complexity
models = {
    "OLS (all features)"     : ols_model,
    "Log-linear (heuristic)" : log_model,
}

for name, model in models.items():
    print(f"  {name}")
    print(f"    R²:  {model.rsquared:.4f}")
    print(f"    AIC: {model.aic:.2f}")
    print(f"    BIC: {model.bic:.2f}\n")

#Tobit Mod 
print("=" * 60)
print("  Tobit Model: censored regression on solve_time")
print("=" * 60)

# Timed-out boards are right-censored at the timeout value
# Dropping them would bias coefficient estimates downward — Tobit corrects for this
from scipy.optimize import minimize
from scipy.stats import norm

timeout_val = df["solve_time"].max()

X_tobit = df[["initial_heuristic"]].copy()
X_tobit.insert(0, "const", 1.0)
X_tobit = X_tobit.values
y_tobit = df["solve_time"].values
censored = df["timed_out"].values

def tobit_loglik(params):
    beta = params[:-1]
    sigma = np.exp(params[-1])        # exponentiated to enforce sigma > 0
    mu = X_tobit @ beta
    ll = np.where(
        censored,
        np.log(1 - norm.cdf((timeout_val - mu) / sigma) + 1e-10),
        norm.logpdf(y_tobit, mu, sigma)
    )
    return -ll.sum()

init_params = np.zeros(X_tobit.shape[1] + 1)
result = minimize(tobit_loglik, init_params, method="L-BFGS-B")

tobit_beta  = result.x[:-1]
tobit_sigma = np.exp(result.x[-1])

print(f"  Intercept:         {tobit_beta[0]:.4f}")
print(f"  initial_heuristic: {tobit_beta[1]:.4f}")
print(f"  Sigma:             {tobit_sigma:.4f}")
print(f"  Log-likelihood:    {-result.fun:.4f}")
print(f"\n  A one-unit increase in initial heuristic is associated")
print(f"  with a {tobit_beta[1]:.4f}s increase in solve time,")
print(f"  accounting for censored observations.")

#Plots 

print("\n" + "=" * 60)
print("  Generating plots...")
print("=" * 60)

fig, axes = plt.subplots(2, 2, figsize=(12, 10))
fig.suptitle("15-Puzzle Solver: Empirical Analysis", fontsize=14, fontweight="bold")

#solution depth distribution across solved boards
axes[0, 0].hist(solved["moves"], bins=20, color="steelblue", edgecolor="black", alpha=0.8)
axes[0, 0].set_title("Distribution of Solution Depths")
axes[0, 0].set_xlabel("Moves to Solve")
axes[0, 0].set_ylabel("Frequency")
axes[0, 0].axvline(solved["moves"].mean(), color="red", linestyle="--",
                   label=f"Mean: {solved['moves'].mean():.1f}")
axes[0, 0].legend()

#heuristic vs log states, key predictor relationship
axes[0, 1].scatter(solved["initial_heuristic"], solved["log_states"],
                   alpha=0.6, color="steelblue", edgecolors="black", linewidths=0.5)
m, b = np.polyfit(solved["initial_heuristic"], solved["log_states"], 1)
x_line = np.linspace(solved["initial_heuristic"].min(), solved["initial_heuristic"].max(), 100)
axes[0, 1].plot(x_line, m * x_line + b, color="red", linewidth=2, label="OLS fit")
axes[0, 1].set_title("Heuristic Value vs log(States Explored)")
axes[0, 1].set_xlabel("Initial Heuristic Value")
axes[0, 1].set_ylabel("log(States Explored)")
axes[0, 1].legend()

#censored observations shown as red crosses at the timeout ceiling
axes[1, 0].scatter(solved["initial_heuristic"], solved["solve_time"],
                   alpha=0.6, color="steelblue", edgecolors="black", linewidths=0.5)
axes[1, 0].scatter(df[df["timed_out"]]["initial_heuristic"],
                   [timeout_val] * df["timed_out"].sum(),
                   color="red", marker="x", s=80, label="Censored (timeout)")
axes[1, 0].set_title("Heuristic Value vs Solve Time")
axes[1, 0].set_xlabel("Initial Heuristic Value")
axes[1, 0].set_ylabel("Solve Time (s)")
axes[1, 0].legend()

#residuals should scatter randomly around zero if OLS assumptions hold
fitted    = ols_model.fittedvalues
residuals = ols_model.resid
axes[1, 1].scatter(fitted, residuals, alpha=0.6, color="steelblue",
                   edgecolors="black", linewidths=0.5)
axes[1, 1].axhline(0, color="red", linestyle="--")
axes[1, 1].set_title("OLS Residual Plot")
axes[1, 1].set_xlabel("Fitted Values")
axes[1, 1].set_ylabel("Residuals")

plt.tight_layout()
plt.savefig("analysis_plots.png", dpi=150, bbox_inches="tight")
plt.show()
print("  Plots saved to analysis_plots.png")

print("\n" + "=" * 60)
print("  Analysis complete.")
print("=" * 60)
