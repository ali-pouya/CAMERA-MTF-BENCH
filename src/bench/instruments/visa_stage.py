from __future__ import annotations

import pyvisa

from bench.instruments.stage import Stage


class VisaStage(Stage):
    """
    VISA-controlled stage.

    This is a skeleton for a motion controller that speaks SCPI-style
    commands over VISA (for example, an Aerotech controller).

    For my v1 repo I treat this as a placeholder: the exact SCPI commands
    (`MOV`, `POS?`, units, axis names) will depend on the actual hardware.
    Once I have a real controller on the bench, I will adjust the strings
    here to match its manual.
    """

    def __init__(self, resource: str, axis: str = "Z"):
        """
        Parameters
        ----------
        resource : str
            VISA resource string, e.g. 'TCPIP0::192.168.0.10::INSTR'.

        axis : str
            Axis identifier understood by the controller (e.g. 'X', 'Y', 'Z').
        """
        # I open the VISA resource manager once per instance.
        self.rm = pyvisa.ResourceManager()
        self.inst = self.rm.open_resource(resource)
        self.axis = axis

    def move_to(self, z_um: float) -> None:
        """
        Move the stage to the requested z position in micrometers.

        For now I assume the controller expects millimeters in a simple
        'MOV <axis>,<pos_mm>' format. I will update this once I lock in a
        specific controller and SCPI dialect.
        """
        z_mm = z_um / 1000.0
        cmd = f"MOV {self.axis},{z_mm:.6f}"
        self.inst.write(cmd)

    def step(self, dz_um: float) -> None:
        """
        Relative move by dz_um micrometers.

        I implement this using position() + move_to() so I don't depend on
        the existence of an incremental move command in the controller.
        """
        current = self.position()
        self.move_to(current + dz_um)

    def position(self) -> float:
        """
        Return the current stage position in micrometers.

        For now I assume the controller responds with a plain floating-point
        value in millimeters to 'POS? <axis>'.
        """
        resp = self.inst.query(f"POS? {self.axis}")
        z_mm = float(resp.strip())
        return z_mm * 1000.0


# ---------------------------------------------------------------------------
# Alias used by workflows_hardware
# ---------------------------------------------------------------------------

class VISAStage(VisaStage):
    """
    Thin alias around VisaStage to match the name I use in workflows_hardware.

    This lets me keep the original class name (VisaStage) and still call
    `visa_stage.VISAStage()` from the hardware workflow without breaking
    anything.
    """
    pass
