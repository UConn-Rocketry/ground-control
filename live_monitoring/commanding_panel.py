from PySide6 import QtCore, QtWidgets

class commanding_signals(QtCore.QObject):
    command_signal = QtCore.Signal(str)

class commanding_panel(QtWidgets.QLabel):
    def __init__(self):
        super().__init__()
        
        self.command_signals = commanding_signals()
        self.command_signal = self.command_signals.command_signal
        self.layout = QtWidgets.QGridLayout(self)


        self.setup_gui()
        self.connect_functionality()


    def setup_gui(self):
        self.command = QtWidgets.QLineEdit()
        self.command.setPlaceholderText("Enter Command")
        self.layout.addWidget(self.command, 0, 0, 1, 2)

        self.send_command_button = QtWidgets.QPushButton("Send Command")
        self.layout.addWidget(self.send_command_button, 1, 0, 1, 2)

        self.abort_button= QtWidgets.QPushButton("ABORT")
        self.abort_button.setStyleSheet("background: red; color: white; font-size: 13px;")
        self.layout.addWidget(self.abort_button, 2, 0, 1, 2)

        self.countdown_button = QtWidgets.QPushButton("Go to countdown")
        self.countdown_button.setStyleSheet("background: green; font-size: 13px;")
        self.layout.addWidget(self.countdown_button, 3, 1)

        self.standby_button = QtWidgets.QPushButton("Nav start")
        self.standby_button.setStyleSheet("background: green; font-size: 13px;")
        self.layout.addWidget(self.standby_button, 3, 0)

        self.IncrementTVCX = QtWidgets.QPushButton("Increment TVC X")
        self.IncrementTVCX.setStyleSheet("font-size: 13px")
        self.layout.addWidget(self.IncrementTVCX, 4, 0)

        self.IncrementTVCY = QtWidgets.QPushButton("Increment TVC Y")
        self.IncrementTVCY.setStyleSheet("font-size: 13px")
        self.layout.addWidget(self.IncrementTVCY, 4, 1)

        self.DecrementTVCX = QtWidgets.QPushButton("Decrement TVC X")
        self.DecrementTVCX.setStyleSheet("font-size: 13px")
        self.layout.addWidget(self.DecrementTVCX, 5, 0)

        self.DecrementTVCY = QtWidgets.QPushButton("Decrement TVC Y")
        self.DecrementTVCY.setStyleSheet("font-size: 13px")
        self.layout.addWidget(self.DecrementTVCY, 5, 1)

        self.drop_open = QtWidgets.QPushButton("Open Dropmech")
        self.drop_open.setStyleSheet("font-size: 13px")
        self.layout.addWidget(self.drop_open, 6, 0)

        self.drop_close = QtWidgets.QPushButton("Close Dropmech")
        self.drop_close.setStyleSheet("font-size: 13px")
        self.layout.addWidget(self.drop_close, 6, 1)

    def connect_functionality(self):
        self.command.returnPressed.connect(self.send_command_and_clear_text)
        self.send_command_button.clicked.connect(self.send_command_and_clear_text)
        self.countdown_button.clicked.connect(lambda: self.send_command("COMMAND: standby_to_countdown\n"))
        self.standby_button.clicked.connect(lambda: self.send_command("COMMAND: idle_to_standby\n"))
        self.abort_button.clicked.connect(lambda : self.send_command("ABORT\n"))
        self.IncrementTVCX.clicked.connect(lambda : self.send_command("IncrementXTVC\n"))
        self.IncrementTVCY.clicked.connect(lambda : self.send_command("IncrementYTVC\n"))
        self.DecrementTVCX.clicked.connect(lambda : self.send_command("DecrementXTVC\n"))
        self.DecrementTVCY.clicked.connect(lambda : self.send_command("DecrementYTVC\n"))
        self.drop_open.clicked.connect(lambda : self.open_dropmech())
        self.drop_close.clicked.connect(lambda : self.send_command("DROPMECH: close\n"))


    def open_dropmech(self):
        try:
            if(self.current[1] > 1):
                self.send_command("DROPMECH: open\n")
            else:
                self.print("not correct mode")
        except:
            self.send_command("")

    def send_command(self, command : str):
        self.command_signal.emit(command)

    def send_command_and_clear_text(self):
        self.send_command(self.command.text() + "\n")
        self.command.setText("")
