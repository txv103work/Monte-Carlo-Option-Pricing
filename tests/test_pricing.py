"""Unit tests using only Python's standard-library test runner."""

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from option_pricing import (  # noqa: E402
    OptionParameters,
    black_scholes_price,
    monte_carlo_price,
    simulate_gbm_paths,
)


class TestOptionPricing(unittest.TestCase):
    def setUp(self) -> None:
        self.params = OptionParameters(100, 100, 1, 0.05, 0.20)

    def test_known_black_scholes_prices(self) -> None:
        self.assertAlmostEqual(
            black_scholes_price(self.params, "call"), 10.4506, places=4
        )
        self.assertAlmostEqual(
            black_scholes_price(self.params, "put"), 5.5735, places=4
        )

    def test_put_call_parity(self) -> None:
        call = black_scholes_price(self.params, "call")
        put = black_scholes_price(self.params, "put")
        parity_rhs = self.params.spot - self.params.strike * (
            2.718281828459045 ** (-self.params.rate * self.params.maturity)
        )
        self.assertAlmostEqual(call - put, parity_rhs, places=10)

    def test_simulated_paths_shape_and_initial_value(self) -> None:
        paths = simulate_gbm_paths(self.params, n_paths=12, n_steps=20, seed=1)
        self.assertEqual(paths.shape, (12, 21))
        self.assertTrue((paths[:, 0] == self.params.spot).all())
        self.assertTrue((paths > 0).all())

    def test_monte_carlo_call_contains_analytical_price(self) -> None:
        analytical = black_scholes_price(self.params, "call")
        result = monte_carlo_price(
            self.params, "call", n_simulations=300_000, seed=123
        )
        self.assertLess(result.confidence_interval[0], analytical)
        self.assertGreater(result.confidence_interval[1], analytical)

    def test_reproducibility(self) -> None:
        first = monte_carlo_price(
            self.params, "put", n_simulations=10_000, seed=8
        )
        second = monte_carlo_price(
            self.params, "put", n_simulations=10_000, seed=8
        )
        self.assertEqual(first, second)

    def test_invalid_parameters(self) -> None:
        with self.assertRaises(ValueError):
            OptionParameters(0, 100, 1, 0.05, 0.20)
        with self.assertRaises(ValueError):
            monte_carlo_price(self.params, "invalid")  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()

