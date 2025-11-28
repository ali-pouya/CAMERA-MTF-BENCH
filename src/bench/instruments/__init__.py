"""
Instrument abstraction layer.

Defines abstract interfaces and mock implementations for:
- Stage (focus axis motion)
- Camera (image acquisition)
- VISA-based instruments (scope, power meter) - later

For this implementation in here, I have only define Stage and Camera skeletons.
"""
from .stage import MockStage, Stage
from .camera import Camera, MockCameraFocusStack
from .stage_kinesis import ThorlabsKMTS50Stage


__all__ = [
    "Camera",
    "Stage",
    "MockCameraFocusStack",
    "MockStage",
    "ThorlabsKMTS50Stage",
]