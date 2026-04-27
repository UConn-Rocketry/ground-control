from PySide6 import QtCore, QtWidgets


class SerialControlsPanel(QtWidgets.QWidget):
    def __init__(
        self,
        on_connect,
        on_stop,
        on_reset_save,
        on_reset_discard,
        on_clear_string_logs,
    ):
        super().__init__()

        layout = QtWidgets.QFormLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setHorizontalSpacing(6)
        layout.setVerticalSpacing(6)

        self.health_badge = QtWidgets.QLabel()
        self.health_badge.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.health_badge.setMinimumWidth(160)
        self.health_badge.setMinimumHeight(30)
        self.health_badge.setToolTip("Serial link health")

        self.connect_button = QtWidgets.QPushButton("Connect Serial and Listen")
        self.stop_button = QtWidgets.QPushButton("Stop Listening")
        self.reset_save_button = QtWidgets.QPushButton("Reset and Save Graphs")
        self.reset_discard_button = QtWidgets.QPushButton("Reset and Discard")
        self.clear_string_logs_button = QtWidgets.QPushButton("Clear String Logs")

        self.connect_button.clicked.connect(on_connect)
        self.stop_button.clicked.connect(on_stop)
        self.reset_save_button.clicked.connect(on_reset_save)
        self.reset_discard_button.clicked.connect(on_reset_discard)
        self.clear_string_logs_button.clicked.connect(on_clear_string_logs)

        layout.addRow(self.health_badge)
        layout.addRow(self.connect_button)
        layout.addRow(self.stop_button)
        layout.addRow(self.reset_save_button, self.reset_discard_button)
        layout.addRow(self.clear_string_logs_button)

        self.set_health("disconnected", "Disconnected", "Serial disconnected")

    def set_button_states(self, *, connect_enabled, stop_enabled, reset_save_enabled, reset_discard_enabled):
        self.connect_button.setEnabled(connect_enabled)
        self.stop_button.setEnabled(stop_enabled)
        self.reset_save_button.setEnabled(reset_save_enabled)
        self.reset_discard_button.setEnabled(reset_discard_enabled)

    def set_health(self, status: str, text: str, tooltip: str):
        styles = {
            "healthy": "background-color: #166534; color: #ecfdf5; border: 2px solid #22c55e; border-radius: 7px; font-weight: 800; padding: 4px 10px;",
            "waiting": "background-color: #92400e; color: #fffbeb; border: 2px solid #f59e0b; border-radius: 7px; font-weight: 800; padding: 4px 10px;",
            "degraded": "background-color: #b45309; color: #fff7ed; border: 2px solid #fb923c; border-radius: 7px; font-weight: 800; padding: 4px 10px;",
            "stale": "background-color: #991b1b; color: #fef2f2; border: 2px solid #ef4444; border-radius: 7px; font-weight: 800; padding: 4px 10px;",
            "disconnected": "background-color: #374151; color: #e5e7eb; border: 2px solid #9ca3af; border-radius: 7px; font-weight: 800; padding: 4px 10px;",
        }

        self.health_badge.setText(f"{text} Link")
        self.health_badge.setStyleSheet(styles.get(status, styles["disconnected"]))
        self.health_badge.setToolTip(tooltip)
