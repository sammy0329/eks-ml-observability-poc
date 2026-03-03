import pytest

from app.detector import detect_anomaly


class TestNormalData:
    def test_normal_data_is_not_anomaly(self):
        values = [1.0, 1.1, 0.9, 1.05, 0.95, 1.02, 0.98, 1.0, 1.01, 0.99]
        result = detect_anomaly(values)
        assert result.is_anomaly is False
        assert result.reason == "ok"
        assert 0.0 <= result.anomaly_score < 1.0


class TestVarianceSpike:
    def test_spike_is_detected(self):
        # 정상 값 중 극단적 스파이크 삽입
        values = [1.0] * 9 + [100.0]
        result = detect_anomaly(values)
        assert result.is_anomaly is True
        assert result.reason == "variance_spike"
        assert result.anomaly_score >= 1.0

    def test_large_spike_in_long_baseline_detected(self):
        # 베이스라인이 충분히 길면 스파이크의 Z-score가 명확하게 높아짐
        values = [1.0] * 20 + [50.0]
        result = detect_anomaly(values)
        assert result.is_anomaly is True
        assert result.reason == "variance_spike"


class TestMissingRate:
    def test_high_missing_rate_detected(self):
        values = [1.0] * 10
        missing_flags = [True] * 4 + [False] * 6  # 40% 결측
        result = detect_anomaly(values, missing_flags)
        assert result.is_anomaly is True
        assert result.reason == "missing_rate_high"

    def test_low_missing_rate_not_anomaly(self):
        values = [1.0] * 10
        missing_flags = [True, False, False, False, False, False, False, False, False, False]  # 10%
        result = detect_anomaly(values, missing_flags)
        assert result.is_anomaly is False

    def test_no_missing_flags_defaults_to_none(self):
        values = [1.0, 1.1, 0.9]
        result = detect_anomaly(values, missing_flags=None)
        assert result.is_anomaly is False


class TestEdgeCases:
    def test_single_value_returns_ok(self):
        # 유효값 1개 — 판단 불가, ok 반환 (line 38 커버)
        result = detect_anomaly([1.0])
        assert result.is_anomaly is False
        assert result.anomaly_score == 0.0

    def test_constant_values_returns_ok(self):
        # std == 0 — Z-score 계산 불가 (line 44 커버)
        result = detect_anomaly([5.0, 5.0, 5.0, 5.0])
        assert result.is_anomaly is False
        assert result.reason == "ok"

    def test_two_values_no_drift(self):
        # 최소 유효값 케이스 (mid==1)
        result = detect_anomaly([1.0, 1.0])
        assert result.is_anomaly is False


class TestDrift:
    def test_drift_detected(self):
        # 전반부 평균 ~1.0, 후반부 평균 ~20.0 — 반쪽 std 기준으로 drift_score >> threshold
        first_half = [1.0 + 0.05 * i for i in range(10)]   # 1.0 ~ 1.45
        second_half = [20.0 + 0.05 * i for i in range(10)]  # 20.0 ~ 20.45
        result = detect_anomaly(first_half + second_half)
        assert result.is_anomaly is True
        assert result.reason == "drift_detected"

    def test_no_drift_in_normal_data(self):
        import math
        values = [1.0 + 0.1 * math.sin(i) for i in range(20)]
        result = detect_anomaly(values)
        assert result.is_anomaly is False
