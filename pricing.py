"""Core pricing functions for European options under Black--Scholes."""

from dataclasses import dataclass
from typing import Literal

import numpy as np
import scipy
from scipy.stats import norm

OptionType = Literal["call", "put"]


@dataclass(frozen=True)
class OptionParameters:
    """Market and contract parameters for a European option."""
    spot: float
    strike: float
    maturity: float
    rate: float
    volatility: float

    def __post_init__(self) -> None:
        if self.spot <= 0:
            raise ValueError("spot must be positive")
        if self.strike <= 0:
            raise ValueError("strike must be positive")
        if self.maturity <= 0:
            raise ValueError("maturity must be positive")
        if self.volatility <= 0:
            raise ValueError("volatility must be positive")


@dataclass(frozen=True)
class MonteCarloResult:
    """Monte Carlo estimate with its sampling uncertainty."""

    price: float
    standard_error: float
    confidence_interval: tuple[float, float]
    n_simulations: int
    seed: int | None


def _validate_option_type(option_type: OptionType) -> None:
    if option_type not in ("call", "put"):
        raise ValueError("option_type must be 'call' or 'put'")


def black_scholes_price(
    params: OptionParameters, option_type: OptionType = "call"
) -> float:
    """Return the analytical Black--Scholes price.

    The model assumes a non-dividend-paying stock and a constant continuously
    compounded risk-free rate and volatility.
    """

    _validate_option_type(option_type)
    s0, k, t, r, sigma = (
        params.spot,
        params.strike,
        params.maturity,
        params.rate,
        params.volatility,
    )
    sqrt_t = np.sqrt(t)
    d1 = (np.log(s0 / k) + (r + 0.5 * sigma**2) * t) / (sigma * sqrt_t)
    d2 = d1 - sigma * sqrt_t

    if option_type == "call":
        return float(s0 * norm.cdf(d1) - k * np.exp(-r * t) * norm.cdf(d2))
    return float(k * np.exp(-r * t) * norm.cdf(-d2) - s0 * norm.cdf(-d1))


def simulate_gbm_paths(
    params: OptionParameters,
    n_paths: int,
    n_steps: int,
    *,
    seed: int | None = None,
) -> np.ndarray:
    """Simulate full risk-neutral GBM paths using the exact transition law.

    Returns an array with shape ``(n_paths, n_steps + 1)``.
    """

    if n_paths < 1:
        raise ValueError("n_paths must be at least 1")
    if n_steps < 1:
        raise ValueError("n_steps must be at least 1")

    rng = np.random.default_rng(seed)
    dt = params.maturity / n_steps
    shocks = rng.standard_normal((n_paths, n_steps))
    log_returns = (
        (params.rate - 0.5 * params.volatility**2) * dt
        + params.volatility * np.sqrt(dt) * shocks
    )
    log_paths = np.cumsum(log_returns, axis=1)
    paths = np.empty((n_paths, n_steps + 1), dtype=float)
    paths[:, 0] = params.spot
    paths[:, 1:] = params.spot * np.exp(log_paths)
    return paths


def monte_carlo_price(
    params: OptionParameters,
    option_type: OptionType = "call",
    *,
    n_simulations: int = 100_000,
    seed: int | None = 42,
    confidence_level: float = 0.95,
    antithetic: bool = False,
) -> MonteCarloResult:
    """Price a European option by simulating its terminal stock price.

    When ``antithetic`` is true, each observation is the average payoff from
    shocks ``Z`` and ``-Z``. This keeps the estimator unbiased and usually
    reduces its variance. ``n_simulations`` is the total number of terminal
    prices, and therefore must be even in antithetic mode.
    """

    _validate_option_type(option_type)
    if n_simulations < 2:
        raise ValueError("n_simulations must be at least 2")
    if not 0 < confidence_level < 1:
        raise ValueError("confidence_level must lie between 0 and 1")
    if antithetic and n_simulations % 2:
        raise ValueError("n_simulations must be even with antithetic sampling")

    rng = np.random.default_rng(seed)
    drift = (params.rate - 0.5 * params.volatility**2) * params.maturity
    diffusion_scale = params.volatility * np.sqrt(params.maturity)

    if antithetic:
        z = rng.standard_normal(n_simulations // 2)
        terminal_plus = params.spot * np.exp(drift + diffusion_scale * z)
        terminal_minus = params.spot * np.exp(drift - diffusion_scale * z)
        if option_type == "call":
            payoffs = 0.5 * (
                np.maximum(terminal_plus - params.strike, 0.0)
                + np.maximum(terminal_minus - params.strike, 0.0)
            )
        else:
            payoffs = 0.5 * (
                np.maximum(params.strike - terminal_plus, 0.0)
                + np.maximum(params.strike - terminal_minus, 0.0)
            )
    else:
        z = rng.standard_normal(n_simulations)
        terminal_prices = params.spot * np.exp(drift + diffusion_scale * z)
        if option_type == "call":
            payoffs = np.maximum(terminal_prices - params.strike, 0.0)
        else:
            payoffs = np.maximum(params.strike - terminal_prices, 0.0)

    discounted_payoffs = np.exp(-params.rate * params.maturity) * payoffs
    price = float(np.mean(discounted_payoffs))
    standard_error = float(
        np.std(discounted_payoffs, ddof=1) / np.sqrt(discounted_payoffs.size)
    )
    critical_value = float(norm.ppf(0.5 + confidence_level / 2))
    half_width = critical_value * standard_error

    return MonteCarloResult(
        price=price,
        standard_error=standard_error,
        confidence_interval=(price - half_width, price + half_width),
        n_simulations=n_simulations,
        seed=seed,
    )

