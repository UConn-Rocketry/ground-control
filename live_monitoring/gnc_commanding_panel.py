from PySide6 import QtCore

from command_panel_framework import (
    ButtonGroupSpec,
    ButtonSpec,
    ConfigurableCommandPanel,
    ToggleGroupSpec,
    ToggleRowSpec,
)


class gnc_commanding_panel(ConfigurableCommandPanel):
    log_signal = QtCore.Signal(str)

    def __init__(self):
        sensor_rows = [
            ToggleRowSpec("Camera", "On", "Off", "SENSOR: camera ON", "SENSOR: camera OFF"),
            ToggleRowSpec("LiDAR", "On", "Off", "SENSOR: lidar ON", "SENSOR: lidar OFF"),
            ToggleRowSpec(
                "GPS Velocity",
                "On",
                "Off",
                "SENSOR: gps_velocity ON",
                "SENSOR: gps_velocity OFF",
            ),
            ToggleRowSpec(
                "GPS Position",
                "On",
                "Off",
                "SENSOR: gps_position ON",
                "SENSOR: gps_position OFF",
            ),
            ToggleRowSpec(
                "Magnetometer",
                "On",
                "Off",
                "SENSOR: magnetometer ON",
                "SENSOR: magnetometer OFF",
            ),
        ]

        commands = [
            ButtonSpec("Go Idle", "GoIdle"),
            ButtonSpec("Ignite", "Ignite"),
            ButtonSpec("Test TVC", "TestTVC"),
            ButtonSpec("Nav Restart", "NAV_RESTART"),
            ButtonSpec("Abort to Pad", "ABORT_PAD"),
            ButtonSpec("Abort to Ground", "ABORT_GROUND"),
        ]

        super().__init__(
            manual_placeholder="Enter GNC command",
            send_button_label="Send GNC Command",
            toggle_groups=[ToggleGroupSpec("Sensor Fusion Toggles", sensor_rows)],
            button_groups=[ButtonGroupSpec("GNC Commands", 2, commands)],
        )
