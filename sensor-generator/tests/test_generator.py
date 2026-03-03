import math

import numpy as np
import pytest

from sensor_generator.generator import (
    generate_drift,
    generate_missing,
    generate_normal,
    generate_spike,
)


class TestGenerateNormal:
    def test_returns_correct_length(self):
        assert len(generate_normal(30)) == 30

    def test_values_are_floats(self):
        values = generate_normal(10)
        assert all(isinstance(v, float) for v in values)

    def test_values_within_reasonable_range(self):
        # 정상 시계열: 사인파 + 노이즈, 대부분 -3 ~ 3 이내
        values = generate_normal(100, seed=42)
        assert all(-5.0 < v < 5.0 for v in values)

    def test_reproducible_with_seed(self):
        assert generate_normal(10, seed=0) == generate_normal(10, seed=0)

    def test_different_seed_gives_different_values(self):
        assert generate_normal(10, seed=0) != generate_normal(10, seed=1)


class TestGenerateSpike:
    def test_returns_correct_length(self):
        assert len(generate_spike(30)) == 30

    def test_spike_increases_max_value(self):
        normal = generate_normal(30, seed=42)
        spiked = generate_spike(30, spike_magnitude=50.0, seed=42)
        assert max(spiked) > max(normal)

    def test_spike_magnitude_affects_max(self):
        small = generate_spike(30, spike_magnitude=5.0, seed=42)
        large = generate_spike(30, spike_magnitude=100.0, seed=42)
        assert max(large) > max(small)

    def test_spike_detected_by_zscore(self):
        values = generate_spike(30, spike_magnitude=50.0, seed=42)
        arr = np.array(values)
        zscores = np.abs((arr - arr.mean()) / (arr.std() + 1e-9))
        assert zscores.max() > 3.0


class TestGenerateDrift:
    def test_returns_correct_length(self):
        assert len(generate_drift(30)) == 30

    def test_second_half_mean_greater_than_first(self):
        values = generate_drift(100, drift_rate=1.0, seed=42)
        first_half_mean = sum(values[:50]) / 50
        second_half_mean = sum(values[50:]) / 50
        assert second_half_mean > first_half_mean

    def test_larger_drift_rate_gives_bigger_shift(self):
        slow = generate_drift(50, drift_rate=0.1, seed=42)
        fast = generate_drift(50, drift_rate=5.0, seed=42)
        assert max(fast) > max(slow)


class TestGenerateMissing:
    def test_returns_values_and_flags(self):
        values, flags = generate_missing(30)
        assert len(values) == 30
        assert len(flags) == 30

    def test_flags_are_bools(self):
        _, flags = generate_missing(20)
        assert all(isinstance(f, bool) for f in flags)

    def test_missing_rate_respected(self):
        _, flags = generate_missing(1000, missing_rate=0.4, seed=42)
        actual_rate = sum(flags) / len(flags)
        assert 0.35 < actual_rate < 0.45

    def test_zero_missing_rate(self):
        _, flags = generate_missing(30, missing_rate=0.0, seed=42)
        assert not any(flags)
