import math
import sys
from time import perf_counter

from PySide6 import QtCore, QtWidgets

from gui import GroundControlWindow


class GuiPlotDemo:
    def __init__(self, window: GroundControlWindow) -> None:
        self.window = window
        self.start = perf_counter()
        self.frame = {}

        # Wire every live graph to the same synthetic frame dictionary.
        for graph in self.window.all_live_graphs:
            graph.setup_connection(self.frame)

        self.timer = QtCore.QTimer(self.window)
        self.timer.setInterval(40)
        self.timer.timeout.connect(self._tick)
        self.timer.start()

    def _tick(self) -> None:
        t = perf_counter() - self.start

        # Engine telemetry (smaller packet supported by current RF.TELEM_KEYS).
        self.frame["nitrogen_line_psi"] = 520.0 + 35.0 * math.sin(0.35 * t)
        self.frame["ethanol_tank_psi"] = 460.0 + 28.0 * math.sin(0.31 * t + 0.4)
        self.frame["nitrous_line_psi"] = 610.0 + 55.0 * math.sin(0.24 * t + 1.2)
        self.frame["oxygen_line_psi"] = 95.0 + 18.0 * math.sin(0.47 * t)
        self.frame["fuel_inlet_psi"] = 390.0 + 32.0 * math.sin(0.29 * t + 0.9)
        self.frame["fuel_outlet_psi"] = 340.0 + 26.0 * math.sin(0.33 * t + 1.7)
        self.frame["chamber_pressure_psi"] = 680.0 + 75.0 * math.sin(0.43 * t)
        self.frame["load_cell_lbs"] = 780.0 + 140.0 * math.sin(0.21 * t + 0.6)

        # Navigation telemetry.
        self.frame["position_x"] = 6.0 * math.sin(0.21 * t)
        self.frame["position_y"] = 4.0 * math.cos(0.18 * t)
        self.frame["position_z"] = 2.0 + 1.8 * math.sin(0.14 * t + 0.3)

        self.frame["velocity_x"] = 1.4 * math.cos(0.21 * t)
        self.frame["velocity_y"] = -0.9 * math.sin(0.18 * t)
        self.frame["velocity_z"] = 0.6 * math.cos(0.14 * t + 0.3)

        self.frame["rotation_x"] = 0.35 * math.sin(0.7 * t)
        self.frame["rotation_y"] = 0.28 * math.cos(0.6 * t + 0.9)
        self.frame["rotation_z"] = 0.52 * math.sin(0.45 * t + 0.2)

        self.frame["omega_x"] = 0.15 * math.cos(0.9 * t)
        self.frame["omega_y"] = 0.13 * math.sin(0.8 * t + 0.5)
        self.frame["omega_z"] = 0.11 * math.cos(0.75 * t + 1.1)

        # Bias keys for both legacy and newer naming.
        accel_bx = 0.03 * math.sin(0.12 * t)
        accel_by = 0.02 * math.cos(0.10 * t + 0.7)
        accel_bz = 0.015 * math.sin(0.11 * t + 0.3)
        gyro_bx = 0.008 * math.sin(0.15 * t)
        gyro_by = 0.007 * math.cos(0.13 * t + 0.2)
        gyro_bz = 0.006 * math.sin(0.14 * t + 0.8)

        self.frame["accelerometer_bias_x"] = accel_bx
        self.frame["accelerometer_bias_y"] = accel_by
        self.frame["accelerometer_bias_z"] = accel_bz
        self.frame["accel_bias_x"] = accel_bx
        self.frame["accel_bias_y"] = accel_by
        self.frame["accel_bias_z"] = accel_bz

        self.frame["gyro_bias_x"] = gyro_bx
        self.frame["gyro_bias_y"] = gyro_by
        self.frame["gyro_bias_z"] = gyro_bz
        self.frame["omega_bias_x"] = gyro_bx
        self.frame["omega_bias_y"] = gyro_by
        self.frame["omega_bias_z"] = gyro_bz

        # Control telemetry.
        self.frame["tvc_command_x"] = 0.65 * math.sin(0.55 * t)
        self.frame["tvc_command_y"] = 0.55 * math.cos(0.52 * t + 0.4)
        self.frame["rcs_command"] = 0.35 * math.sin(0.9 * t)
        self.frame["thrust_command"] = 0.72 + 0.18 * math.sin(0.25 * t)

        self.frame["attitude_setpoint_error_x"] = 2.4 * math.sin(0.41 * t)
        self.frame["attitude_setpoint_error_y"] = 1.8 * math.cos(0.46 * t + 0.1)
        self.frame["attitude_setpoint_error_z"] = 1.2 * math.sin(0.39 * t + 0.7)

        self.frame["actuator_setpoint_error_x"] = 0.22 * math.sin(0.61 * t)
        self.frame["actuator_setpoint_error_y"] = 0.19 * math.cos(0.58 * t + 0.3)

        self.frame["guidance_altitude_error"] = 4.5 * math.sin(0.2 * t)
        self.frame["guidance_translation_error_x"] = 3.2 * math.sin(0.23 * t)
        self.frame["guidance_translation_error_y"] = 2.6 * math.cos(0.26 * t + 0.4)

        for graph in self.window.all_live_graphs:
            graph.update_lines()

def main() -> int:
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle("Fusion")

    window = GroundControlWindow()
    window.resize(1800, 1000)
    window.show()

    demo = GuiPlotDemo(window)
    window._plot_demo = demo

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
