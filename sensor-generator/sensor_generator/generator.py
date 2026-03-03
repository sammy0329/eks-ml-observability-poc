import numpy as np


def generate_normal(window_size: int, seed: int | None = None) -> list[float]:
    """정상 시계열 생성 — 사인파 + 가우시안 노이즈."""
    rng = np.random.default_rng(seed)
    t = np.linspace(0, 2 * np.pi, window_size)
    signal = np.sin(t) + rng.normal(0, 0.1, window_size)
    return signal.tolist()


def generate_spike(
    window_size: int,
    spike_magnitude: float = 10.0,
    seed: int | None = None,
) -> list[float]:
    """스파이크 포함 시계열 생성 — 임의 위치에 이상값 삽입."""
    rng = np.random.default_rng(seed)
    values = generate_normal(window_size, seed)
    spike_idx = int(rng.integers(0, window_size))
    values[spike_idx] += spike_magnitude
    return values


def generate_drift(
    window_size: int,
    drift_rate: float = 0.5,
    seed: int | None = None,
) -> list[float]:
    """드리프트 포함 시계열 생성 — 선형 평균 이동."""
    values = generate_normal(window_size, seed)
    drift = np.linspace(0, drift_rate * window_size * 0.1, window_size)
    return (np.array(values) + drift).tolist()


def generate_missing(
    window_size: int,
    missing_rate: float = 0.3,
    seed: int | None = None,
) -> tuple[list[float], list[bool]]:
    """결측 포함 시계열 생성 — missing_rate 비율로 결측 플래그 설정."""
    rng = np.random.default_rng(seed)
    values = generate_normal(window_size, seed)
    missing_flags = (rng.random(window_size) < missing_rate).tolist()
    return values, missing_flags
