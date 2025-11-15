from __future__ import annotations


class Stage:
    """
    Abstract focus stage interface.

    I use this as the common base class for all motion backends
    (mock, VISA-controlled, Kinesis, etc.).

    Every concrete stage class must implement:
      - move_to(pos_um): absolute move in micrometers
      - step(dz_um): relative move in micrometers
      - position(): current position in micrometers
    """

    def move_to(self, pos_um: float) -> None:  # pragma: no cover - interface
        raise NotImplementedError

    def step(self, dz_um: float) -> None:  # pragma: no cover - interface
        raise NotImplementedError

    def position(self) -> float:  # pragma: no cover - interface
        raise NotImplementedError


class MockStage(Stage):
    """
    Simple in-memory stage for testing autofocus logic without hardware.

    I use this whenever I want to exercise autofocus code or hardware
    workflows (e.g. in unit tests or simulations) without touching a real
    motion controller.
    """

    def __init__(self, z0_um: float = 0.0) -> None:
        self._z = float(z0_um)

    def move_to(self, pos_um: float) -> None:
        self._z = float(pos_um)

    def step(self, dz_um: float) -> None:
        self._z += float(dz_um)

    def position(self) -> float:
        return self._z
