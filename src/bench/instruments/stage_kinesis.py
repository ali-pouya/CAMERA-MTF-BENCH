from __future__ import annotations

from typing import Optional


class ThorlabsKMTS50Stage:
    """
    Thorlabs KMTS50E/M motorized translation stage driven via the Kinesis API.

    This is a *skeleton* implementation intended for integration with the
    Thorlabs Kinesis motion-control software. It matches the interface used
    elsewhere in this repo (move_to() and position()), so I can swap it in
    place of MockStage or any other Stage-like backend.

    Notes
    -----
    - I assume the existence of a Python wrapper for Kinesis, imported as
      `thorlabs_kinesis`. I will adjust the import and API calls once I have
      a real environment and SDK to test against.
    - I do not perform any unit conversion beyond µm ↔ mm.
    - I expect callers to invoke `shutdown()` before exiting to cleanly
      disconnect from the hardware.
    """

    def __init__(self, serial_number: str, axis_um_per_mm: float = 1000.0):
        """
        Parameters
        ----------
        serial_number : str
            The Thorlabs device serial number for the Kinesis controller
            associated with the KMTS50E/M stage.

        axis_um_per_mm : float
            Conversion factor from controller units (mm) to µm. For linear
            stages, this is typically 1000 µm/mm.
        """
        self._serial = serial_number
        self._axis_um_per_mm = float(axis_um_per_mm)

        # I import the Kinesis wrapper lazily so the rest of the repo can
        # still be used without the hardware SDK installed.
        try:
            import thorlabs_kinesis as tk  # type: ignore[import]
        except ImportError as exc:  # pragma: no cover - hardware-only path
            raise RuntimeError(
                "thorlabs_kinesis package is required for ThorlabsKMTS50Stage. "
                "Install the appropriate Kinesis Python wrapper and try again."
            ) from exc

        self._tk = tk

        # Example API usage — I will adjust this to match my actual wrapper.
        # Here I assume a KCubeDCServo motor object controlling the stage.
        self._motor = tk.KCubeDCServo(serial_number)
        self._motor.connect()
        self._motor.enable()
        self._motor.wait_until_ready()

        # Optionally: home the stage on startup
        # self._motor.home(wait=True)

        # Cache of last known position in µm (optional)
        self._last_pos_um: Optional[float] = None

    # ------------------------------------------------------------------ #
    # Public interface matching MockStage / Stage                         #
    # ------------------------------------------------------------------ #

    def move_to(self, z_um: float) -> None:
        """
        Move the stage to the requested z position in micrometers.

        Parameters
        ----------
        z_um : float
            Target position in µm.
        """
        z_mm = z_um / self._axis_um_per_mm
        # I do a blocking move so that callers get a simple, deterministic API.
        self._motor.move_to(z_mm, wait=True)
        self._last_pos_um = z_um

    def position(self) -> float:
        """
        Return the current stage position in micrometers.
        """
        z_mm = self._motor.get_position()
        z_um = z_mm * self._axis_um_per_mm
        self._last_pos_um = z_um
        return z_um

    def shutdown(self) -> None:
        """
        Disable and disconnect the Kinesis motor.

        I call this before exiting the application to cleanly release USB resources.
        """
        # Best-effort cleanup; ignore errors on shutdown.
        try:
            self._motor.disable()
        except Exception:
            pass
        try:
            self._motor.disconnect()
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Alias used by workflows_hardware
# ---------------------------------------------------------------------------

class KinesisStage(ThorlabsKMTS50Stage):
    """
    Thin alias around ThorlabsKMTS50Stage to match the name I use in
    workflows_hardware. This keeps the intent obvious without forcing
    me to rename the underlying implementation class.
    """
    pass
