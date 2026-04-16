from PySide6 import QtCore, QtWidgets

from ui_button_styles import (
    STYLE_COMMAND_ACTIVE,
    STYLE_DANGER,
    STYLE_DANGER_ACTIVE,
    STYLE_MUTED,
    STYLE_NEUTRAL,
    STYLE_PRIMARY,
    STYLE_SUCCESS,
    STYLE_SUCCESS_ACTIVE,
)


class ToggleRowSpec:
    def __init__(
        self,
        label: str,
        primary_label: str,
        secondary_label: str,
        primary_command: str,
        secondary_command: str,
    ):
        self.label = label
        self.primary_label = primary_label
        self.secondary_label = secondary_label
        self.primary_command = primary_command
        self.secondary_command = secondary_command


class ToggleGroupSpec:
    def __init__(self, title: str, rows: list[ToggleRowSpec]):
        self.title = title
        self.rows = rows


class ButtonSpec:
    def __init__(self, label: str, command: str):
        self.label = label
        self.command = command


class ButtonGroupSpec:
    def __init__(self, title: str, columns: int, buttons: list[ButtonSpec]):
        self.title = title
        self.columns = columns
        self.buttons = buttons


class ConfigurableCommandPanel(QtWidgets.QWidget):
    command_signal = QtCore.Signal(str)

    def __init__(
        self,
        manual_placeholder: str,
        send_button_label: str,
        toggle_groups: list[ToggleGroupSpec],
        button_groups: list[ButtonGroupSpec],
        extra_quick_buttons: list[tuple[str, str, str]] | None = None,
        command_aliases: dict[str, str] | None = None,
    ):
        super().__init__()

        self._toggle_pairs = []
        self._command_buttons = []
        self._command_aliases = command_aliases or {}

        self._build_ui(
            manual_placeholder=manual_placeholder,
            send_button_label=send_button_label,
            toggle_groups=toggle_groups,
            button_groups=button_groups,
            extra_quick_buttons=extra_quick_buttons or [],
        )

    def _build_ui(
        self,
        manual_placeholder: str,
        send_button_label: str,
        toggle_groups: list[ToggleGroupSpec],
        button_groups: list[ButtonGroupSpec],
        extra_quick_buttons: list[tuple[str, str, str]],
    ):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(6)

        self.command_input = QtWidgets.QLineEdit()
        self.command_input.setPlaceholderText(manual_placeholder)
        self.command_input.returnPressed.connect(self.send_manual_command)
        layout.addWidget(self.command_input)

        quick_actions = QtWidgets.QHBoxLayout()
        quick_actions.setContentsMargins(0, 0, 0, 0)
        quick_actions.setSpacing(6)

        self.send_button = QtWidgets.QPushButton(send_button_label)
        self.send_button.clicked.connect(self.send_manual_command)
        quick_actions.addWidget(self.send_button)

        for label, command, style in extra_quick_buttons:
            button = QtWidgets.QPushButton(label)
            if style:
                button.setStyleSheet(style)
            button.clicked.connect(lambda checked=False, c=command: self.send_command(c))
            quick_actions.addWidget(button)

        layout.addLayout(quick_actions)

        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumHeight(220)
        scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        inner = QtWidgets.QWidget()
        inner_layout = QtWidgets.QVBoxLayout(inner)
        inner_layout.setContentsMargins(4, 4, 4, 4)
        inner_layout.setSpacing(6)

        for group in toggle_groups:
            inner_layout.addWidget(self._build_toggle_group(group))

        for group in button_groups:
            inner_layout.addWidget(self._build_button_group(group))

        inner_layout.addStretch(1)
        scroll.setWidget(inner)
        layout.addWidget(scroll)

    def _build_toggle_group(self, group_spec: ToggleGroupSpec):
        group = QtWidgets.QGroupBox(group_spec.title)
        grid = QtWidgets.QGridLayout(group)
        grid.setHorizontalSpacing(6)
        grid.setVerticalSpacing(4)
        grid.setColumnStretch(0, 3)
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(2, 1)
        grid.addWidget(QtWidgets.QLabel("Device"), 0, 0)
        grid.addWidget(QtWidgets.QLabel("Open / On"), 0, 1)
        grid.addWidget(QtWidgets.QLabel("Close / Off"), 0, 2)

        for row, spec in enumerate(group_spec.rows, start=1):
            grid.addWidget(QtWidgets.QLabel(spec.label), row, 0)
            primary_btn = QtWidgets.QPushButton(spec.primary_label)
            secondary_btn = QtWidgets.QPushButton(spec.secondary_label)
            primary_btn.setCheckable(True)
            secondary_btn.setCheckable(True)
            self._apply_pair_styles(primary_btn, secondary_btn, None)

            self._toggle_pairs.append(
                (primary_btn, secondary_btn, spec.primary_command, spec.secondary_command)
            )
            primary_btn.clicked.connect(
                lambda checked=False, c=spec.primary_command: self.send_command(c)
            )
            secondary_btn.clicked.connect(
                lambda checked=False, c=spec.secondary_command: self.send_command(c)
            )

            grid.addWidget(primary_btn, row, 1)
            grid.addWidget(secondary_btn, row, 2)

        return group

    def _build_button_group(self, group_spec: ButtonGroupSpec):
        group = QtWidgets.QGroupBox(group_spec.title)
        grid = QtWidgets.QGridLayout(group)
        grid.setHorizontalSpacing(6)
        grid.setVerticalSpacing(4)

        for index, spec in enumerate(group_spec.buttons):
            row, col = divmod(index, max(1, group_spec.columns))
            button = QtWidgets.QPushButton(spec.label)
            button.setStyleSheet(STYLE_NEUTRAL)
            button.clicked.connect(lambda checked=False, c=spec.command: self.send_command(c))
            self._command_buttons.append((button, spec.command))
            grid.addWidget(button, row, col)

        return group

    def _apply_pair_styles(self, primary_btn, secondary_btn, last_sent):
        if last_sent is None:
            primary_btn.setStyleSheet(STYLE_SUCCESS)
            secondary_btn.setStyleSheet(STYLE_DANGER)
        elif last_sent == "primary":
            primary_btn.setStyleSheet(STYLE_SUCCESS_ACTIVE)
            secondary_btn.setStyleSheet(STYLE_MUTED)
        else:
            primary_btn.setStyleSheet(STYLE_MUTED)
            secondary_btn.setStyleSheet(STYLE_DANGER_ACTIVE)

    def _sync_last_sent_from_command(self, stripped: str):
        for primary_btn, secondary_btn, primary_cmd, secondary_cmd in self._toggle_pairs:
            if stripped == primary_cmd:
                primary_btn.setChecked(True)
                secondary_btn.setChecked(False)
                self._apply_pair_styles(primary_btn, secondary_btn, "primary")
                return
            if stripped == secondary_cmd:
                primary_btn.setChecked(False)
                secondary_btn.setChecked(True)
                self._apply_pair_styles(primary_btn, secondary_btn, "secondary")
                return

        cmd_key = self._command_aliases.get(stripped, stripped)
        for button, command in self._command_buttons:
            if cmd_key == command:
                for other_button, _ in self._command_buttons:
                    other_button.setStyleSheet(STYLE_NEUTRAL)
                button.setStyleSheet(STYLE_COMMAND_ACTIVE)
                return

    def send_command(self, command: str):
        stripped = command.strip()
        if not stripped:
            return

        self._sync_last_sent_from_command(stripped)
        self.command_signal.emit(stripped + "\n")

    def send_manual_command(self):
        self.send_command(self.command_input.text())
        self.command_input.setText("")
