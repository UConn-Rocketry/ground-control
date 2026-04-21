import sys
import math
import pyqtgraph as pg
from PySide6 import QtCore, QtWidgets, QtGui
from time import time
import qdarkstyle

from state_management_widget import state_management_widget
from file_management_widget import file_management_widget
from custom_graph_widget import custom_graph_widget
from commanding_panel import commanding_panel
from gnc_commanding_panel import gnc_commanding_panel
from gui_page_builders import build_engine_page, build_gnc_page
from serial_controls_panel import SerialControlsPanel
from telemetry_schema import (
    ENGINE_PLOT_SPECS,
    GNC_CONTROL_PLOT_SPECS,
    GNC_NAVIGATION_PLOT_SPECS,
)
from rf import RF


# https://www.pythonguis.com/tutorials/plotting-pyqtgraph/


class GroundControlWindow(QtWidgets.QWidget):
    _GRAPH_GRID_MAX_ROWS = 8
    _GRAPH_GRID_MAX_COLS = 8
    _GRAPH_MAX_COLS = 4
    # Match liquids layout: plot block height (rows) + command sidebar spanning same rows.
    _LIVE_PLOT_ROW_SPAN = 3

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("AIAA PL Ground Control")
        self._thread_pool = QtCore.QThreadPool.globalInstance()

        self.setStyleSheet(qdarkstyle.load_stylesheet(qt_api="pyside6") + self._custom_stylesheet())
        self.setMinimumSize(1280, 820)

        pg.setConfigOption("background", "#121722")
        pg.setConfigOption("foreground", "#D5DEE8")

        self.program_start_time = time()

        self.setup_number_displays()
        self.setup_graphs()
        self.init_widgets()
        self._reflow_all_graphs()

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Space:
            self.engine_command_panel.send_command("COMMAND: ABORT\n")
            return

        if hasattr(self, "tabs") and self.tabs.currentIndex() == 1:
            if event.key() == QtCore.Qt.Key_Left:
                self._switch_gnc_view(-1)
                return
            if event.key() == QtCore.Qt.Key_Right:
                self._switch_gnc_view(1)
                return

        super().keyPressEvent(event)

    def init_widgets(self):
        self.file_management_panel = file_management_widget(self.output)

        self.console = QtWidgets.QTextBrowser()
        self.console.setObjectName("consoleOutput")
        self.console.setFont(QtGui.QFont("Menlo", 10))
        self.console.setOpenExternalLinks(True)
        self.console.setPlaceholderText("Telemetry and command logs will appear here...")
        self.console.setMinimumHeight(100)

        self.gnc_console = QtWidgets.QTextBrowser()
        self.gnc_console.setObjectName("consoleOutput")
        self.gnc_console.setFont(QtGui.QFont("Menlo", 10))
        self.gnc_console.setPlaceholderText("GNC logs will appear here...")
        self.gnc_console.setMinimumHeight(90)

        self.state_management_panel = state_management_widget(
            self.output,
            self.output_gnc,
            self.output_both,
            self.file_management_panel,
            self._thread_pool,
            self.all_live_graphs,
            self.numerical_displays,
            self.program_start_time,
        )
        self.state_management_panel.signals.clear_output.connect(self.clear_console)
        self.state_management_panel.signals.connection_monitor.connect(self._sync_serial_button_states)
        self.state_management_panel.signals.serial_health.connect(self._on_serial_health_changed)

        self.engine_command_panel = commanding_panel()
        self.engine_command_panel.command_signal.connect(self._send_engine_command)
        self.state_management_panel.command_panel = self.engine_command_panel

        self.gnc_command_panel = gnc_commanding_panel()
        self.gnc_command_panel.command_signal.connect(self._send_gnc_command)
        self.gnc_command_panel.log_signal.connect(self.output_gnc)
        self.engine_serial_controls_panel = SerialControlsPanel(
            on_connect=lambda: self._invoke_serial_action(self.state_management_panel.connect_and_listen),
            on_stop=lambda: self._invoke_serial_action(self.state_management_panel.stop_listening),
            on_reset_save=lambda: self._invoke_serial_action(self.state_management_panel.save_and_reset),
            on_reset_discard=lambda: self._invoke_serial_action(self.state_management_panel.discard_files_and_reset),
            on_clear_logs=self.console.clear,
        )
        self.gnc_serial_controls_panel = SerialControlsPanel(
            on_connect=lambda: self._invoke_serial_action(self.state_management_panel.connect_and_listen),
            on_stop=lambda: self._invoke_serial_action(self.state_management_panel.stop_listening),
            on_reset_save=lambda: self._invoke_serial_action(self.state_management_panel.save_and_reset),
            on_reset_discard=lambda: self._invoke_serial_action(self.state_management_panel.discard_files_and_reset),
            on_clear_logs=self.gnc_console.clear,
        )
        self._serial_control_panels = [self.engine_serial_controls_panel, self.gnc_serial_controls_panel]

        self.engine_command_panel.setMinimumWidth(400)
        self.engine_command_panel.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Preferred,
            QtWidgets.QSizePolicy.Policy.Expanding,
        )
        self.gnc_command_panel.setMinimumWidth(375)
        self.gnc_command_panel.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Preferred,
            QtWidgets.QSizePolicy.Policy.Expanding,
        )
        self.engine_serial_controls_panel.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Preferred,
            QtWidgets.QSizePolicy.Policy.Preferred,
        )
        self.gnc_serial_controls_panel.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Preferred,
            QtWidgets.QSizePolicy.Policy.Preferred,
        )
        self.state_management_panel.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Preferred,
            QtWidgets.QSizePolicy.Policy.Preferred,
        )

        engine_tab = build_engine_page(
            graph_container=self.engine_graph_container,
            command_panel=self.engine_command_panel,
            serial_controls_panel=self.engine_serial_controls_panel,
            console=self.console,
            live_plot_row_span=self._LIVE_PLOT_ROW_SPAN,
        )

        gnc_parts = build_gnc_page(
            gnc_navigation_graph_container=self.gnc_navigation_graph_container,
            gnc_control_graph_container=self.gnc_control_graph_container,
            gnc_command_panel=self.gnc_command_panel,
            gnc_serial_controls_panel=self.gnc_serial_controls_panel,
            gnc_console=self.gnc_console,
        )
        self.gnc_tab = gnc_parts.page
        self.gnc_view_stack = gnc_parts.view_stack
        self.gnc_view_label = gnc_parts.view_label
        self.gnc_prev_button = gnc_parts.prev_button
        self.gnc_next_button = gnc_parts.next_button
        self.gnc_prev_button.clicked.connect(lambda: self._switch_gnc_view(-1))
        self.gnc_next_button.clicked.connect(lambda: self._switch_gnc_view(1))
        self._set_gnc_view(0)

        gnc_tab = self.gnc_tab
        settings_tab = QtWidgets.QWidget()
        settings_layout = QtWidgets.QVBoxLayout(settings_tab)
        settings_layout.setContentsMargins(8, 8, 8, 8)
        settings_layout.setSpacing(12)
        settings_layout.addWidget(self.engine_plots_group)
        settings_layout.addWidget(self.gnc_navigation_plots_group)
        settings_layout.addWidget(self.gnc_control_plots_group)
        settings_layout.addWidget(self.file_management_panel)
        settings_layout.addStretch(1)

        self.tabs = QtWidgets.QTabWidget()
        self.tabs.addTab(engine_tab, "Engine")
        self.tabs.addTab(gnc_tab, "GNC")
        self.tabs.addTab(settings_tab, "Settings")

        # Force an initial explicit render so health state is visible before any serial action.
        self._on_serial_health_changed("disconnected", "Serial disconnected")

        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(0)
        root.addWidget(self.tabs, 1)

    def _set_gnc_view(self, index):
        if not hasattr(self, "gnc_view_stack"):
            return

        count = self.gnc_view_stack.count()
        if count == 0:
            return

        wrapped_index = index % count
        self.gnc_view_stack.setCurrentIndex(wrapped_index)

        titles = ["Navigation", "Control"]
        if wrapped_index < len(titles):
            self.gnc_view_label.setText(f"GNC {titles[wrapped_index]}")
        else:
            self.gnc_view_label.setText("GNC")

    def _switch_gnc_view(self, delta):
        if not hasattr(self, "gnc_view_stack"):
            return
        self._set_gnc_view(self.gnc_view_stack.currentIndex() + delta)

    def _invoke_serial_action(self, action):
        action()
        self._sync_serial_button_states()

    def _sync_serial_button_states(self, *_):
        if not hasattr(self, "_serial_control_panels"):
            return

        source = self.state_management_panel
        for panel in self._serial_control_panels:
            panel.set_button_states(
                connect_enabled=source.connect_serial_button.isEnabled(),
                stop_enabled=source.stop_listening_button.isEnabled(),
                reset_save_enabled=source.reset_and_save_graphs_button.isEnabled(),
                reset_discard_enabled=source.reset_and_discard_button.isEnabled(),
            )

    def _on_serial_health_changed(self, status: str, message: str):
        status_text = {
            "healthy": "Healthy",
            "waiting": "Waiting",
            "degraded": "Degraded",
            "stale": "Stale",
            "disconnected": "Disconnected",
        }.get(status, "Disconnected")

        if not hasattr(self, "_serial_control_panels"):
            return

        for panel in self._serial_control_panels:
            panel.set_health(status, status_text, message)

    def _send_engine_command(self, command: str):
        self.state_management_panel.send_command(command, on_error=self.output)

    def _send_gnc_command(self, command: str):
        self.state_management_panel.send_command(command, on_error=self.output_gnc)

    def _custom_stylesheet(self):
        return """
        QWidget {
            font-size: 11pt;
        }
        QTextBrowser#consoleOutput {
            background-color: #0F141C;
            border: 1px solid #2B3544;
            border-radius: 10px;
            padding: 8px;
            color: #D3DEE8;
        }
        QGroupBox {
            border: 1px solid #2B3544;
            border-radius: 10px;
            margin-top: 10px;
            padding-top: 8px;
        }
        QGroupBox::title {
            left: 10px;
            padding: 0 4px;
            color: #E3EAF1;
        }
        QPushButton {
            border-radius: 8px;
            min-height: 28px;
            padding: 4px 10px;
            font-weight: 600;
        }
        QLineEdit, QTextEdit, QComboBox {
            border-radius: 7px;
        }
        QTabWidget::pane {
            border: 1px solid #2B3544;
            border-radius: 8px;
            top: -1px;
        }
        QTabBar::tab {
            padding: 8px 16px;
            margin-right: 2px;
        }
        """

    def setup_number_displays(self):
        self.numerical_displays = []

    def setup_graphs(self):
        self.engine_graphs = []
        self.gnc_graphs = []
        self.gnc_navigation_graphs = []
        self.gnc_control_graphs = []
        self._engine_graph_checkboxes = []
        self._gnc_navigation_graph_checkboxes = []
        self._gnc_control_graph_checkboxes = []
        T = RF.TELEM_KEYS

        available_engine_keys = set(T)
        engine_graph_labels = []
        engine_ranges_by_key = {}
        for key, title, label, y_range in ENGINE_PLOT_SPECS:
            if key in available_engine_keys:
                self.engine_graphs.append(
                    custom_graph_widget(names=(key,), start=self.program_start_time, plot_title=title)
                )
                engine_graph_labels.append(label)
                engine_ranges_by_key[key] = y_range

        # Fallback: if keys are renamed/unknown, still render whatever telemetry keys are present.
        if not self.engine_graphs:
            for key in T:
                self.engine_graphs.append(
                    custom_graph_widget(names=(key,), start=self.program_start_time, plot_title=key)
                )
                engine_graph_labels.append(key)

        gnc_navigation_graph_labels = []
        for names, plot_title, label in GNC_NAVIGATION_PLOT_SPECS:
            self.gnc_navigation_graphs.append(
                custom_graph_widget(
                    names=names,
                    start=self.program_start_time,
                    plot_title=plot_title,
                )
            )
            gnc_navigation_graph_labels.append(label)

        gnc_control_graph_labels = []
        for names, plot_title, label in GNC_CONTROL_PLOT_SPECS:
            self.gnc_control_graphs.append(
                custom_graph_widget(
                    names=names,
                    start=self.program_start_time,
                    plot_title=plot_title,
                )
            )
            gnc_control_graph_labels.append(label)

        self.gnc_graphs = self.gnc_navigation_graphs + self.gnc_control_graphs
        self.all_live_graphs = self.engine_graphs + self.gnc_graphs

        self.engine_plots_group = self._build_plot_visibility_group(
            title="Visible Engine Plots",
            graph_labels=engine_graph_labels,
            graphs=self.engine_graphs,
            checkbox_store=self._engine_graph_checkboxes,
        )
        self.gnc_navigation_plots_group = self._build_plot_visibility_group(
            title="Visible GNC Navigation Plots",
            graph_labels=gnc_navigation_graph_labels,
            graphs=self.gnc_navigation_graphs,
            checkbox_store=self._gnc_navigation_graph_checkboxes,
        )
        self.gnc_control_plots_group = self._build_plot_visibility_group(
            title="Visible GNC Control Plots",
            graph_labels=gnc_control_graph_labels,
            graphs=self.gnc_control_graphs,
            checkbox_store=self._gnc_control_graph_checkboxes,
        )

        self.engine_graph_container = QtWidgets.QWidget()
        self.engine_graph_grid = QtWidgets.QGridLayout(self.engine_graph_container)
        self.engine_graph_grid.setContentsMargins(0, 0, 0, 0)
        self.engine_graph_container.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Expanding,
        )
        self.gnc_navigation_graph_container = QtWidgets.QWidget()
        self.gnc_navigation_graph_grid = QtWidgets.QGridLayout(self.gnc_navigation_graph_container)
        self.gnc_navigation_graph_grid.setContentsMargins(0, 0, 0, 0)
        self.gnc_navigation_graph_container.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Expanding,
        )

        self.gnc_control_graph_container = QtWidgets.QWidget()
        self.gnc_control_graph_grid = QtWidgets.QGridLayout(self.gnc_control_graph_container)
        self.gnc_control_graph_grid.setContentsMargins(0, 0, 0, 0)
        self.gnc_control_graph_container.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Expanding,
        )

        for g in self.engine_graphs:
            g.setParent(self.engine_graph_container)
        for g in self.gnc_navigation_graphs:
            g.setParent(self.gnc_navigation_graph_container)
        for g in self.gnc_control_graphs:
            g.setParent(self.gnc_control_graph_container)

        for graph in self.engine_graphs:
            key = graph.names[0] if graph.names else ""
            y_range = engine_ranges_by_key.get(key)
            if y_range is not None:
                graph.setYRange(y_range[0], y_range[1])

            graph.showGrid(x=True, y=True)

    def _build_plot_visibility_group(self, title, graph_labels, graphs, checkbox_store):
        group = QtWidgets.QGroupBox(title)
        plots_inner = QtWidgets.QWidget()
        plots_grid = QtWidgets.QGridLayout(plots_inner)
        plots_grid.setContentsMargins(4, 4, 4, 4)
        plots_grid.setHorizontalSpacing(10)
        plots_grid.setVerticalSpacing(4)
        cols = 4
        for i, label in enumerate(graph_labels):
            cb = QtWidgets.QCheckBox(label)
            cb.setChecked(True)
            cb.setToolTip(", ".join(graphs[i].names))
            cb.stateChanged.connect(lambda *_: self._reflow_all_graphs())
            checkbox_store.append(cb)
            plots_grid.addWidget(cb, i // cols, i % cols)

        plots_scroll = QtWidgets.QScrollArea()
        plots_scroll.setWidgetResizable(True)
        plots_scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        plots_scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        plots_scroll.setWidget(plots_inner)
        plots_scroll.setMaximumHeight(200)
        plots_group_layout = QtWidgets.QVBoxLayout(group)
        plots_group_layout.addWidget(plots_scroll)

        return group

    def _reflow_graphs(self, graphs, checkboxes, graph_grid):
        for g in graphs:
            graph_grid.removeWidget(g)

        for r in range(self._GRAPH_GRID_MAX_ROWS):
            graph_grid.setRowStretch(r, 0)
        for c in range(self._GRAPH_GRID_MAX_COLS):
            graph_grid.setColumnStretch(c, 0)

        visible = []
        for i, g in enumerate(graphs):
            if i < len(checkboxes) and checkboxes[i].isChecked():
                visible.append(g)
                g.show()
            else:
                g.hide()

        n = len(visible)
        if n == 0:
            return

        ncols = min(self._GRAPH_MAX_COLS, max(1, math.ceil(math.sqrt(n))))
        nrows = (n + ncols - 1) // ncols

        for idx, g in enumerate(visible):
            row, col = divmod(idx, ncols)
            g.setSizePolicy(
                QtWidgets.QSizePolicy.Policy.Expanding,
                QtWidgets.QSizePolicy.Policy.Expanding,
            )
            g.setMinimumSize(0, 0)
            colspan = ncols - col if idx == n - 1 else 1
            graph_grid.addWidget(g, row, col, 1, colspan)

        for r in range(nrows):
            graph_grid.setRowStretch(r, 1)
        for c in range(ncols):
            graph_grid.setColumnStretch(c, 1)

    def _reflow_all_graphs(self):
        self._reflow_graphs(
            graphs=self.engine_graphs,
            checkboxes=self._engine_graph_checkboxes,
            graph_grid=self.engine_graph_grid,
        )
        self._reflow_graphs(
            graphs=self.gnc_navigation_graphs,
            checkboxes=self._gnc_navigation_graph_checkboxes,
            graph_grid=self.gnc_navigation_graph_grid,
        )
        self._reflow_graphs(
            graphs=self.gnc_control_graphs,
            checkboxes=self._gnc_control_graph_checkboxes,
            graph_grid=self.gnc_control_graph_grid,
        )

    def _append_console_message(self, console, text: str):
        if console is not None:
            console.append(text)

    def _show_warning_dialog(self, text: str):
        if not isinstance(text, str) or "Warning:" not in text:
            return

        message_box = QtWidgets.QMessageBox(self)
        message_box.setIcon(QtWidgets.QMessageBox.Icon.Warning)
        message_box.setWindowTitle("Warning")
        message_box.setText(text)
        message_box.addButton(QtWidgets.QMessageBox.StandardButton.Ok)
        exit_button = message_box.addButton("Exit", QtWidgets.QMessageBox.ButtonRole.DestructiveRole)
        message_box.exec()

        if message_box.clickedButton() == exit_button:
            app = QtWidgets.QApplication.instance()
            if app is not None:
                app.quit()

    def output(self, text):
        self._show_warning_dialog(text)
        self._append_console_message(self.console, text)

    def output_gnc(self, text):
        self._show_warning_dialog(text)
        if hasattr(self, "gnc_console"):
            self._append_console_message(self.gnc_console, text)

    def output_both(self, text):
        self._show_warning_dialog(text)
        self._append_console_message(self.console, text)
        if hasattr(self, "gnc_console"):
            self._append_console_message(self.gnc_console, text)

    def clear_console(self):
        self.console.clear()
        if hasattr(self, "gnc_console"):
            self.gnc_console.clear()

    def closeEvent(self, event):
        self.state_management_panel.stop_listening()


if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    app.setStyle("Fusion")

    window = GroundControlWindow()
    window.resize(1800, 1000)
    window.show()

    sys.exit(app.exec())
