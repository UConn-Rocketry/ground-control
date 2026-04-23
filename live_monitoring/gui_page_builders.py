from PySide6 import QtCore, QtWidgets


class GncPageParts:
    def __init__(self, page, view_stack, view_label, prev_button, next_button):
        self.page = page
        self.view_stack = view_stack
        self.view_label = view_label
        self.prev_button = prev_button
        self.next_button = next_button


def build_collapsible_section(title, content_widget, start_expanded=True):
    container = QtWidgets.QWidget()
    layout = QtWidgets.QVBoxLayout(container)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(4)

    toggle = QtWidgets.QToolButton()
    toggle.setText(title)
    toggle.setCheckable(True)
    toggle.setChecked(start_expanded)
    toggle.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
    toggle.setArrowType(
        QtCore.Qt.ArrowType.DownArrow if start_expanded else QtCore.Qt.ArrowType.RightArrow
    )

    body = QtWidgets.QWidget()
    body_layout = QtWidgets.QVBoxLayout(body)
    body_layout.setContentsMargins(0, 0, 0, 0)
    body_layout.addWidget(content_widget)
    body.setVisible(start_expanded)

    def _on_toggle(expanded):
        body.setVisible(expanded)
        toggle.setArrowType(
            QtCore.Qt.ArrowType.DownArrow if expanded else QtCore.Qt.ArrowType.RightArrow
        )

    toggle.toggled.connect(_on_toggle)

    layout.addWidget(toggle)
    layout.addWidget(body)
    return container


def build_engine_page(
    graph_container,
    command_panel,
    serial_controls_panel,
    console,
    shared_console,
    live_plot_row_span,
):
    page = QtWidgets.QWidget()
    page_grid = QtWidgets.QGridLayout(page)
    page_grid.setContentsMargins(8, 8, 8, 8)
    page_grid.setHorizontalSpacing(10)
    page_grid.setVerticalSpacing(8)

    page_grid.addWidget(graph_container, 0, 0, live_plot_row_span, 4)
    page_grid.addWidget(command_panel, 0, 4, live_plot_row_span, 1)

    ops_panel = QtWidgets.QWidget()
    ops_layout = QtWidgets.QGridLayout(ops_panel)
    ops_layout.setContentsMargins(0, 0, 0, 0)
    ops_layout.setHorizontalSpacing(10)
    ops_layout.setVerticalSpacing(0)
    ops_layout.addWidget(serial_controls_panel, 0, 0)
    console_stack = QtWidgets.QWidget()
    console_stack_layout = QtWidgets.QHBoxLayout(console_stack)
    console_stack_layout.setContentsMargins(0, 0, 0, 0)
    console_stack_layout.setSpacing(8)
    console_stack_layout.addWidget(console)
    console_stack_layout.addWidget(shared_console)
    ops_layout.addWidget(console_stack, 0, 1)
    ops_layout.setColumnStretch(0, 0)
    ops_layout.setColumnStretch(1, 1)

    combined_section = build_collapsible_section(
        "Serial Controls and Log Output",
        ops_panel,
        start_expanded=True,
    )
    page_grid.addWidget(combined_section, live_plot_row_span, 0, 1, 5)

    for c in range(4):
        page_grid.setColumnStretch(c, 1)
    page_grid.setColumnStretch(4, 0)

    for r in range(live_plot_row_span):
        page_grid.setRowStretch(r, 1)
    page_grid.setRowStretch(live_plot_row_span, 0)

    return page


def build_gnc_page(
    gnc_navigation_graph_container,
    gnc_control_graph_container,
    gnc_command_panel,
    gnc_serial_controls_panel,
    gnc_console,
    shared_console,
):
    page = QtWidgets.QWidget()
    page_grid = QtWidgets.QGridLayout(page)
    page_grid.setContentsMargins(8, 8, 8, 8)
    page_grid.setHorizontalSpacing(10)
    page_grid.setVerticalSpacing(8)

    nav_group = QtWidgets.QGroupBox("Navigation")
    nav_layout = QtWidgets.QVBoxLayout(nav_group)
    nav_layout.setContentsMargins(6, 6, 6, 6)
    nav_layout.addWidget(gnc_navigation_graph_container)

    control_group = QtWidgets.QGroupBox("Control")
    control_layout = QtWidgets.QVBoxLayout(control_group)
    control_layout.setContentsMargins(6, 6, 6, 6)
    control_layout.addWidget(gnc_control_graph_container)

    gnc_view_stack = QtWidgets.QStackedWidget()
    gnc_view_stack.addWidget(nav_group)
    gnc_view_stack.addWidget(control_group)

    gnc_prev_button = QtWidgets.QPushButton("<")
    gnc_next_button = QtWidgets.QPushButton(">")
    gnc_prev_button.setFixedWidth(36)
    gnc_next_button.setFixedWidth(36)
    gnc_view_label = QtWidgets.QLabel()
    gnc_view_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
    gnc_view_label.setStyleSheet("font-weight: 600; color: #D3DEE8;")

    gnc_header = QtWidgets.QHBoxLayout()
    gnc_header.setContentsMargins(0, 0, 0, 0)
    gnc_header.setSpacing(8)
    gnc_header.addWidget(gnc_prev_button)
    gnc_header.addWidget(gnc_view_label, 1)
    gnc_header.addWidget(gnc_next_button)

    gnc_left_panel = QtWidgets.QWidget()
    gnc_left_layout = QtWidgets.QVBoxLayout(gnc_left_panel)
    gnc_left_layout.setContentsMargins(0, 0, 0, 0)
    gnc_left_layout.setSpacing(8)
    gnc_left_layout.addLayout(gnc_header)
    gnc_left_layout.addWidget(gnc_view_stack, 1)

    page_grid.addWidget(gnc_left_panel, 0, 0)
    page_grid.addWidget(gnc_command_panel, 0, 1)

    gnc_ops_panel = QtWidgets.QWidget()
    gnc_ops_layout = QtWidgets.QGridLayout(gnc_ops_panel)
    gnc_ops_layout.setContentsMargins(0, 0, 0, 0)
    gnc_ops_layout.setHorizontalSpacing(10)
    gnc_ops_layout.setVerticalSpacing(0)
    gnc_ops_layout.addWidget(gnc_serial_controls_panel, 0, 0)
    console_stack = QtWidgets.QWidget()
    console_stack_layout = QtWidgets.QHBoxLayout(console_stack)
    console_stack_layout.setContentsMargins(0, 0, 0, 0)
    console_stack_layout.setSpacing(8)
    console_stack_layout.addWidget(gnc_console)
    console_stack_layout.addWidget(shared_console)
    gnc_ops_layout.addWidget(console_stack, 0, 1)
    gnc_ops_layout.setColumnStretch(0, 0)
    gnc_ops_layout.setColumnStretch(1, 1)

    gnc_status_section = build_collapsible_section(
        "Serial Controls and Log Output",
        gnc_ops_panel,
        start_expanded=True,
    )
    page_grid.addWidget(gnc_status_section, 1, 0, 1, 2)

    page_grid.setColumnStretch(0, 1)
    page_grid.setColumnStretch(1, 0)
    page_grid.setRowStretch(0, 1)
    page_grid.setRowStretch(1, 0)

    return GncPageParts(
        page=page,
        view_stack=gnc_view_stack,
        view_label=gnc_view_label,
        prev_button=gnc_prev_button,
        next_button=gnc_next_button,
    )
