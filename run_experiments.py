"""Reproduce all numerical results and figures for the project."""

import csv
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from option_pricing import (  # noqa: E402
    OptionParameters,
    black_scholes_price,
    monte_carlo_price,
    simulate_gbm_paths,
)

RESULTS_DIR = ROOT / "results"
FIGURES_DIR = RESULTS_DIR / "figures"


def convergence_experiment(
    params: OptionParameters,
    option_type: str,
    simulation_counts: list[int],
    base_seed: int,
) -> list[dict[str, float | int | str]]:
    """Run independent Monte Carlo estimates over increasing sample sizes."""

    analytical = black_scholes_price(params, option_type)
    rows: list[dict[str, float | int | str]] = []
    for index, n_simulations in enumerate(simulation_counts):
        result = monte_carlo_price(
            params,
            option_type,
            n_simulations=n_simulations,
            seed=base_seed + index,
        )
        rows.append(
            {
                "option_type": option_type,
                "n_simulations": n_simulations,
                "mc_price": result.price,
                "standard_error": result.standard_error,
                "ci_lower": result.confidence_interval[0],
                "ci_upper": result.confidence_interval[1],
                "black_scholes_price": analytical,
                "absolute_error": abs(result.price - analytical),
            }
        )
    return rows


def save_csv(rows: list[dict[str, float | int | str]]) -> None:
    with (RESULTS_DIR / "convergence_results.csv").open(
        "w", newline="", encoding="utf-8"
    ) as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def plot_sample_paths(params: OptionParameters) -> None:
    paths = simulate_gbm_paths(params, n_paths=30, n_steps=252, seed=7)
    times = np.linspace(0, params.maturity, paths.shape[1])
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(times, paths.T, linewidth=0.9, alpha=0.7)
    ax.axhline(params.strike, color="black", linestyle="--", label="Strike")
    ax.set(
        title="Risk-neutral geometric Brownian motion paths",
        xlabel="Time (years)",
        ylabel="Stock price",
    )
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "gbm_paths.png", dpi=180)
    plt.close(fig)


def plot_convergence(rows: list[dict[str, float | int | str]]) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    for ax, option_type in zip(axes, ("call", "put")):
        selected = [row for row in rows if row["option_type"] == option_type]
        n = np.array([row["n_simulations"] for row in selected], dtype=int)
        estimates = np.array([row["mc_price"] for row in selected], dtype=float)
        lower = np.array([row["ci_lower"] for row in selected], dtype=float)
        upper = np.array([row["ci_upper"] for row in selected], dtype=float)
        analytical = float(selected[0]["black_scholes_price"])

        ax.plot(n, estimates, "o-", label="Monte Carlo")
        ax.fill_between(n, lower, upper, alpha=0.2, label="95% CI")
        ax.axhline(
            analytical, color="black", linestyle="--", label="Black–Scholes"
        )
        ax.set_xscale("log")
        ax.set(
            title=f"European {option_type.capitalize()}",
            xlabel="Number of simulations (log scale)",
            ylabel="Option price",
        )
        ax.legend()
    fig.suptitle("Monte Carlo convergence to the analytical price")
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "convergence.png", dpi=180)
    plt.close(fig)


def plot_error_rate(
    params: OptionParameters, simulation_counts: list[int], n_replications: int = 40
) -> None:
    analytical = black_scholes_price(params, "call")
    rmse_values = []
    for n_simulations in simulation_counts:
        estimates = [
            monte_carlo_price(
                params,
                "call",
                n_simulations=n_simulations,
                seed=10_000 + replication,
            ).price
            for replication in range(n_replications)
        ]
        rmse_values.append(
            np.sqrt(np.mean((np.asarray(estimates) - analytical) ** 2))
        )

    reference = rmse_values[0] * np.sqrt(
        simulation_counts[0] / np.asarray(simulation_counts)
    )
    fig, ax = plt.subplots(figsize=(7.5, 5))
    ax.loglog(simulation_counts, rmse_values, "o-", label="Empirical RMSE")
    ax.loglog(
        simulation_counts,
        reference,
        "--",
        label=r"Reference rate $N^{-1/2}$",
    )
    ax.set(
        title="Monte Carlo error rate for a European call",
        xlabel="Number of simulations",
        ylabel="Root mean squared error",
    )
    ax.grid(True, which="both", alpha=0.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "error_rate.png", dpi=180)
    plt.close(fig)


def main() -> None:
    RESULTS_DIR.mkdir(exist_ok=True)
    FIGURES_DIR.mkdir(exist_ok=True)
    params = OptionParameters(
        spot=100.0,
        strike=100.0,
        maturity=1.0,
        rate=0.05,
        volatility=0.20,
    )
    simulation_counts = [1_000, 5_000, 10_000, 50_000, 100_000, 500_000]

    rows = convergence_experiment(params, "call", simulation_counts, base_seed=42)
    rows += convergence_experiment(params, "put", simulation_counts, base_seed=142)
    save_csv(rows)
    plot_sample_paths(params)
    plot_convergence(rows)
    plot_error_rate(params, simulation_counts[:-1])

    for option_type in ("call", "put"):
        analytical = black_scholes_price(params, option_type)
        estimate = monte_carlo_price(
            params, option_type, n_simulations=500_000, seed=2026
        )
        print(
            f"{option_type.capitalize():4s} | "
            f"MC={estimate.price:.4f} | BS={analytical:.4f} | "
            f"SE={estimate.standard_error:.4f} | "
            f"95% CI=({estimate.confidence_interval[0]:.4f}, "
            f"{estimate.confidence_interval[1]:.4f})"
        )
    print(f"\nResults saved to {RESULTS_DIR}")


if __name__ == "__main__":
    main()

