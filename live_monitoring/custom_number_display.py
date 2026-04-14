from PySide6 import QtCore, QtWidgets

class custom_number_display(QtWidgets.QLabel):
    def __init__(self, name: str, label: str):
        super().__init__()
        self.label = label
        self.name = name

        self.setText(label)
        self.setAlignment(QtCore.Qt.AlignCenter)
        self.setStyleSheet(" font: bold italic large \"Arial\"; font-size: 16px;")
        
    def setup_connection(self, current_frame):
        self.current_frame = current_frame

    def update_value(self):
        value = self.current_frame.get(self.name, "—")
        self.setText(f"{self.label}: {value}")