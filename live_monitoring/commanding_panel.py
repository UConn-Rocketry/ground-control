from PySide6 import QtCore, QtWidgets

class commanding_signals(QtCore.QObject):
    command_signal = QtCore.Signal(str)

# Shared compact sizing; green/red base colors applied per role in _apply_pair_styles.
_COMPACT_BASE = "font-size: 11px; min-height: 24px; padding: 2px 8px; border-radius: 6px;"
_STYLE_GREEN = _COMPACT_BASE + "background-color: #166534; color: #ecfdf5; border: 1px solid #22c55e; font-weight: 600;"
_STYLE_RED = _COMPACT_BASE + "background-color: #991b1b; color: #fef2f2; border: 1px solid #f87171; font-weight: 600;"
_STYLE_GREY = _COMPACT_BASE + "background-color: #374151; color: #9ca3af; border: 1px solid #4b5563; font-weight: normal;"
_STYLE_GREEN_ACTIVE = _COMPACT_BASE + "background-color: #15803d; color: #ffffff; border: 2px solid #4ade80; font-weight: 700;"
_STYLE_RED_ACTIVE = _COMPACT_BASE + "background-color: #b91c1c; color: #ffffff; border: 2px solid #fca5a5; font-weight: 700;"


class commanding_panel(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.current = {}

        self.command_signals = commanding_signals()
        self.command_signal = self.command_signals.command_signal
        self.layout = QtWidgets.QVBoxLayout(self)

        # (primary_btn, secondary_btn, primary_cmd, secondary_cmd, use_spark_labels)
        self._valve_pairs = []

        self.setup_gui()
        self.connect_functionality()

    def setup_gui(self):
        self.layout.setContentsMargins(4, 4, 4, 4)
        self.layout.setSpacing(6)

        self.command = QtWidgets.QLineEdit()
        self.command.setPlaceholderText("Enter Command")
        self.layout.addWidget(self.command)

        quick_actions = QtWidgets.QHBoxLayout()
        quick_actions.setContentsMargins(0, 0, 0, 0)
        quick_actions.setSpacing(6)
        self.send_command_button = QtWidgets.QPushButton("Send Command")
        self.abort_button = QtWidgets.QPushButton("ABORT")
        self.abort_button.setStyleSheet("background: red; color: white; font-size: 12px;")
        quick_actions.addWidget(self.send_command_button)
        quick_actions.addWidget(self.abort_button)
        self.layout.addLayout(quick_actions)

        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumHeight(220)
        scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        inner = QtWidgets.QWidget()
        inner_layout = QtWidgets.QVBoxLayout(inner)
        inner_layout.setContentsMargins(4, 4, 4, 4)
        inner_layout.setSpacing(6)

        valve_group = QtWidgets.QGroupBox("Valves and ASI Spark Plug")
        valve_grid = QtWidgets.QGridLayout(valve_group)
        valve_grid.setHorizontalSpacing(6)
        valve_grid.setVerticalSpacing(4)
        valve_grid.setColumnStretch(0, 3)
        valve_grid.setColumnStretch(1, 1)
        valve_grid.setColumnStretch(2, 1)
        valve_grid.addWidget(QtWidgets.QLabel("Device"), 0, 0)
        hdr_open = QtWidgets.QLabel("Open / On")
        hdr_close = QtWidgets.QLabel("Close / Off")
        valve_grid.addWidget(hdr_open, 0, 1)
        valve_grid.addWidget(hdr_close, 0, 2)

        valve_controls = [
            ("Nitrogen Valve", "VALVE: nitrogen open", "VALVE: nitrogen close", False),
            ("Purge Valve", "VALVE: purge open", "VALVE: purge close", False),
            ("Main Ethanol Valve", "VALVE: main ethanol open", "VALVE: main ethanol close", False),
            ("Main Nitrous Valve", "VALVE: main nitrous open", "VALVE: main nitrous close", False),
            ("ASI Ethanol Valve", "VALVE: ASI ethanol open", "VALVE: ASI ethanol close", False),
            ("ASI Oxygen Valve", "VALVE: ASI oxygen open", "VALVE: ASI oxygen close", False),
            ("Nitrogen Bleed Valve", "VALVE: nitrogen bleed open", "VALVE: nitrogen bleed close", False),
            ("ASI Spark Plug", "SPARK: on", "SPARK: off", True),
        ]
        for row, (label, open_cmd, close_cmd, is_spark) in enumerate(valve_controls, start=1):
            valve_grid.addWidget(QtWidgets.QLabel(label), row, 0)
            if is_spark:
                primary_btn = QtWidgets.QPushButton("On")
                secondary_btn = QtWidgets.QPushButton("Off")
            else:
                primary_btn = QtWidgets.QPushButton("Open")
                secondary_btn = QtWidgets.QPushButton("Close")
            self._valve_pairs.append((primary_btn, secondary_btn, open_cmd, close_cmd))
            self._apply_pair_styles(primary_btn, secondary_btn, None)
            primary_btn.clicked.connect(lambda checked=False, o=open_cmd: self.send_command(o + "\n"))
            secondary_btn.clicked.connect(lambda checked=False, c=close_cmd: self.send_command(c + "\n"))
            valve_grid.addWidget(primary_btn, row, 1)
            valve_grid.addWidget(secondary_btn, row, 2)

        commands_group = QtWidgets.QGroupBox("Commands")
        commands_grid = QtWidgets.QGridLayout(commands_group)
        commands_grid.setHorizontalSpacing(6)
        commands_grid.setVerticalSpacing(4)
        command_buttons = [
            ("GoIdle", "GoIdle"),
            ("GoHotFireIdle", "GoHotfireIdle"),
            ("Ignite", "Ignite"),
            ("ASITest", "asitest"),
            ("WaterFlow", "waterflow"),
            ("Abort", "ABORT"),
        ]
        self._command_buttons = []
        cmd_compact = "font-size: 11px; min-height: 24px; padding: 2px 8px; border-radius: 6px;"
        cmd_neutral = cmd_compact + "background-color: #374151; color: #e5e7eb; border: 1px solid #6b7280;"
        cmd_active = cmd_compact + "background-color: #1d4ed8; color: #ffffff; border: 2px solid #93c5fd; font-weight: 700;"
        for index, (label, cmd) in enumerate(command_buttons):
            row, col = divmod(index, 3)
            button = QtWidgets.QPushButton(label)
            button.setStyleSheet(cmd_neutral)
            button.setProperty("cmd_key", cmd)
            button.clicked.connect(lambda checked=False, s=cmd: self.send_command(s + "\n"))
            commands_grid.addWidget(button, row, col)
            self._command_buttons.append((button, cmd))

        inner_layout.addWidget(valve_group)
        inner_layout.addWidget(commands_group)
        inner_layout.addStretch(1)

        scroll.setWidget(inner)
        self.layout.addWidget(scroll)

    def _apply_pair_styles(self, primary_btn, secondary_btn, last_sent):
        """last_sent: None (both default green/red), 'primary', or 'secondary'."""
        if last_sent is None:
            primary_btn.setStyleSheet(_STYLE_GREEN)
            secondary_btn.setStyleSheet(_STYLE_RED)
        elif last_sent == "primary":
            primary_btn.setStyleSheet(_STYLE_GREEN_ACTIVE)
            secondary_btn.setStyleSheet(_STYLE_GREY)
        else:
            primary_btn.setStyleSheet(_STYLE_GREY)
            secondary_btn.setStyleSheet(_STYLE_RED_ACTIVE)

    def _reset_command_buttons_style(self):
        cmd_compact = "font-size: 11px; min-height: 24px; padding: 2px 8px; border-radius: 6px;"
        cmd_neutral = cmd_compact + "background-color: #374151; color: #e5e7eb; border: 1px solid #6b7280;"
        for button, _ in self._command_buttons:
            button.setStyleSheet(cmd_neutral)

    def connect_functionality(self):
        self.command.returnPressed.connect(self.send_command_and_clear_text)
        self.send_command_button.clicked.connect(self.send_command_and_clear_text)
        self.abort_button.clicked.connect(lambda: self.send_command("ABORT\n"))

    def send_command(self, command: str):
        stripped = command.strip()
        self._sync_last_sent_from_command(stripped)
        self.command_signal.emit(command)

    def _sync_last_sent_from_command(self, stripped: str):
        """Update valve pair and command-button highlights when any path sends a command."""
        for pb, sb, oc, cc in self._valve_pairs:
            if stripped == oc:
                self._apply_pair_styles(pb, sb, "primary")
                return
            if stripped == cc:
                self._apply_pair_styles(pb, sb, "secondary")
                return
        # Map alternate forms (e.g. keyboard shortcut) to the same UI highlight as Abort.
        cmd_key = stripped
        if stripped == "COMMAND: ABORT":
            cmd_key = "ABORT"
        cmd_compact = "font-size: 11px; min-height: 24px; padding: 2px 8px; border-radius: 6px;"
        cmd_neutral = cmd_compact + "background-color: #374151; color: #e5e7eb; border: 1px solid #6b7280;"
        cmd_active = cmd_compact + "background-color: #1d4ed8; color: #ffffff; border: 2px solid #93c5fd; font-weight: 700;"
        for button, cmd in self._command_buttons:
            if cmd_key == cmd:
                self._reset_command_buttons_style()
                button.setStyleSheet(cmd_active)
                return

    def send_command_and_clear_text(self):
        self.send_command(self.command.text() + "\n")
        self.command.setText("")