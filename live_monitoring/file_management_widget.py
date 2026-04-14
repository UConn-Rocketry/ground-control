import sys

from PySide6 import QtCore, QtWidgets
from pathlib import Path
from os import mkdir
from shutil import rmtree

import serial.tools.list_ports


class file_management_widget(QtWidgets.QWidget):
    def __init__(self, output) -> None:
        super().__init__()
        self.layout = QtWidgets.QFormLayout(self)

        select_output_directory_button = QtWidgets.QPushButton("Select output directory")
        self.show_output_directory = QtWidgets.QLineEdit()
        self.show_output_directory.setReadOnly(True)

        self.layout.addRow(select_output_directory_button, self.show_output_directory)

        self.port_input = QtWidgets.QComboBox()
        self.port_input.setEditable(True)
        self.port_input.setMinimumWidth(220)
        self.port_input.lineEdit().setPlaceholderText("Port (e.g. /dev/cu.* or COM3)")
        self.port_input.setInsertPolicy(QtWidgets.QComboBox.InsertPolicy.NoInsert)
        refresh_ports = QtWidgets.QPushButton("Refresh ports")
        refresh_ports.setToolTip("Scan for serial devices (macOS: /dev/cu.*, Windows: COM*)")
        port_row = QtWidgets.QHBoxLayout()
        port_row.addWidget(self.port_input, stretch=1)
        port_row.addWidget(refresh_ports)
        port_wrap = QtWidgets.QWidget()
        port_wrap.setLayout(port_row)
        self.layout.addRow("Serial port", port_wrap)
        refresh_ports.clicked.connect(self.refresh_serial_ports)

        self.output = output

        self.output_location = None

        self._set_to_default()

        select_output_directory_button.clicked.connect(self._get_output_location)
        self.refresh_serial_ports()

    def _set_to_default(self):
        self.output_directory = Path(__file__).parent.parent.joinpath("./runs").absolute()
        self.output_directory.mkdir(parents=True, exist_ok=True)
        self.find_next_available_save_location_in_current_directory()

    def _get_output_location(self):
        self.output_directory = Path(QtWidgets.QFileDialog.getExistingDirectory(self, "Choose output directory"))

        if not self.output_directory:
            return
        self.find_next_available_save_location_in_current_directory()

    def serial_port(self) -> str:
        return self.port_input.currentText().strip()

    def refresh_serial_ports(self):
        previous = self.serial_port()
        ports = list(serial.tools.list_ports.comports())
        if sys.platform == "darwin":
            cu = [p for p in ports if p.device.startswith("/dev/cu.")]
            if cu:
                ports = cu
        devices = sorted({p.device for p in ports})
        self.port_input.blockSignals(True)
        self.port_input.clear()
        for device in devices:
            self.port_input.addItem(device)
        self.port_input.blockSignals(False)
        if previous:
            idx = self.port_input.findText(previous, QtCore.Qt.MatchFlag.MatchExactly)
            if idx >= 0:
                self.port_input.setCurrentIndex(idx)
            else:
                self.port_input.setEditText(previous)

    def find_next_available_save_location_in_current_directory(self):
        temp_location = self.output_directory.joinpath("./run0")
        index = 1

        while temp_location.exists():
            temp_location = self.output_directory.joinpath("./run" + str(index))
            index += 1

        self.output_location = temp_location
        self.show_output_directory.setText(str(self.output_location))

    def create_files(self):
        mkdir(self.output_location)
        mkdir(self.output_location.joinpath("./Graphs"))

        data_path = self.output_location.joinpath("./data.csv")
        log_path = self.output_location.joinpath("./output.log")

        with open(data_path, "w"):
            pass

        return data_path, log_path

    def check_ready(self):
        if not self.output_location:
            self.output("Error: Output location must be set")
            return False

        return True

    def delete_files_from_current_run(self):
        rmtree(self.output_location)