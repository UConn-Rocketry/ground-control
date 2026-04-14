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
        self._reflow_graphs()

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Space:
            self.command_panel.send_command("COMMAND: ABORT\n")

    def init_widgets(self):
        self.file_management_panel = file_management_widget(self.output)

        self.console = QtWidgets.QTextBrowser()
        self.console.setObjectName("consoleOutput")
        self.console.setFont(QtGui.QFont("Menlo", 10))
        self.console.setOpenExternalLinks(True)
        self.console.setPlaceholderText("Telemetry and command logs will appear here...")
        self.console.setMinimumHeight(100)

        self.state_management_panel = state_management_widget(
            self.output,
            self.file_management_panel,
            self._thread_pool,
            self.graphs,
            self.numerical_displays,
            self.program_start_time,
        )
        self.state_management_panel.signals.clear_output.connect(self.clear_console)

        self.command_panel = commanding_panel()
        self.command_panel.command_signal.connect(self.state_management_panel.send_command)
        self.state_management_panel.command_panel = self.command_panel

        self.command_panel.setMinimumWidth(300)
        self.command_panel.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Preferred,
            QtWidgets.QSizePolicy.Policy.Expanding,
        )
        self.state_management_panel.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Preferred,
            QtWidgets.QSizePolicy.Policy.Preferred,
        )

        live_tab = QtWidgets.QWidget()
        live_grid = QtWidgets.QGridLayout(live_tab)
        live_grid.setContentsMargins(8, 8, 8, 8)
        live_grid.setHorizontalSpacing(10)
        live_grid.setVerticalSpacing(8)

        r_plot = self._LIVE_PLOT_ROW_SPAN
        live_grid.addWidget(self.graph_container, 0, 0, r_plot, 4)
        live_grid.addWidget(self.command_panel, 0, 4, r_plot, 1)

        bottom_row = r_plot
        live_grid.addWidget(self.state_management_panel, bottom_row, 0)
        live_grid.addWidget(self.console, bottom_row, 1, 1, 4)

        for c in range(4):
            live_grid.setColumnStretch(c, 1)
        live_grid.setColumnStretch(4, 0)

        for r in range(r_plot):
            live_grid.setRowStretch(r, 1)
        live_grid.setRowStretch(bottom_row, 0)

        settings_tab = QtWidgets.QWidget()
        settings_layout = QtWidgets.QVBoxLayout(settings_tab)
        settings_layout.setContentsMargins(8, 8, 8, 8)
        settings_layout.setSpacing(12)
        settings_layout.addWidget(self.plots_group)
        settings_layout.addWidget(self.file_management_panel)
        settings_layout.addStretch(1)

        self.tabs = QtWidgets.QTabWidget()
        self.tabs.addTab(live_tab, "Live")
        self.tabs.addTab(settings_tab, "Settings")

        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(0)
        root.addWidget(self.tabs, 1)

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
        self.graphs = []
        self._graph_checkboxes = []
        T = RF.TELEM_KEYS

        self.graphs.append(
            custom_graph_widget(names=T[0:3], start=self.program_start_time, plot_title="Euler (x, y, z)")
        )
        self.graphs.append(
            custom_graph_widget(
                names=(T[3], T[4], T[8]),
                start=self.program_start_time,
                plot_title="Control input (x, y, dt)",
            )
        )
        self.graphs.append(
            custom_graph_widget(names=T[5:8], start=self.program_start_time, plot_title="Velocity (x, y, z)")
        )
        self.graphs.append(
            custom_graph_widget(names=(T[9],), start=self.program_start_time, plot_title="N₂ line pressure (psi)")
        )
        self.graphs.append(
            custom_graph_widget(names=(T[10],), start=self.program_start_time, plot_title="Ethanol tank (psi)")
        )
        self.graphs.append(
            custom_graph_widget(names=(T[11],), start=self.program_start_time, plot_title="Nitrous line (psi)")
        )
        self.graphs.append(
            custom_graph_widget(names=(T[12],), start=self.program_start_time, plot_title="Oxygen line (psi)")
        )
        self.graphs.append(
            custom_graph_widget(names=(T[13],), start=self.program_start_time, plot_title="Fuel inlet (psi)")
        )
        self.graphs.append(
            custom_graph_widget(names=(T[14],), start=self.program_start_time, plot_title="Fuel outlet (psi)")
        )
        self.graphs.append(
            custom_graph_widget(names=(T[15],), start=self.program_start_time, plot_title="Chamber pressure (psi)")
        )
        self.graphs.append(
            custom_graph_widget(names=(T[16],), start=self.program_start_time, plot_title="Load cell (lb)")
        )

        graph_labels = [
            "Euler (x,y,z)",
            "Input (x,y, dt)",
            "Velocity (x,y,z)",
            "N₂ line pressure",
            "Ethanol tank",
            "Nitrous line",
            "Oxygen line",
            "Fuel inlet",
            "Fuel outlet",
            "Chamber pressure",
            "Load cell",
        ]

        self.plots_group = QtWidgets.QGroupBox("Visible plots")
        plots_inner = QtWidgets.QWidget()
        plots_grid = QtWidgets.QGridLayout(plots_inner)
        plots_grid.setContentsMargins(4, 4, 4, 4)
        plots_grid.setHorizontalSpacing(10)
        plots_grid.setVerticalSpacing(4)
        cols = 4
        for i, label in enumerate(graph_labels):
            cb = QtWidgets.QCheckBox(label)
            cb.setChecked(True)
            cb.setToolTip(", ".join(self.graphs[i].names))
            cb.stateChanged.connect(lambda *_: self._reflow_graphs())
            self._graph_checkboxes.append(cb)
            plots_grid.addWidget(cb, i // cols, i % cols)

        plots_scroll = QtWidgets.QScrollArea()
        plots_scroll.setWidgetResizable(True)
        plots_scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        plots_scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        plots_scroll.setWidget(plots_inner)
        plots_scroll.setMaximumHeight(200)
        plots_group_layout = QtWidgets.QVBoxLayout(self.plots_group)
        plots_group_layout.addWidget(plots_scroll)

        self.graph_container = QtWidgets.QWidget()
        self.graph_grid = QtWidgets.QGridLayout(self.graph_container)
        self.graph_grid.setContentsMargins(0, 0, 0, 0)
        self.graph_container.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Expanding,
        )

        for g in self.graphs:
            g.setParent(self.graph_container)

        self.graphs[3].setYRange(0, 1000)
        self.graphs[4].setYRange(0, 1000)
        self.graphs[5].setYRange(0, 1000)
        self.graphs[6].setYRange(0, 200)
        self.graphs[7].setYRange(0, 1000)
        self.graphs[8].setYRange(0, 1000)
        self.graphs[9].setYRange(0, 1000)
        self.graphs[10].setYRange(0, 1100)

        for gi in range(3, 11):
            self.graphs[gi].showGrid(x=True, y=True)

    def _reflow_graphs(self):
        for g in self.graphs:
            self.graph_grid.removeWidget(g)

        for r in range(self._GRAPH_GRID_MAX_ROWS):
            self.graph_grid.setRowStretch(r, 0)
        for c in range(self._GRAPH_GRID_MAX_COLS):
            self.graph_grid.setColumnStretch(c, 0)

        visible = []
        for i, g in enumerate(self.graphs):
            if i < len(self._graph_checkboxes) and self._graph_checkboxes[i].isChecked():
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
            self.graph_grid.addWidget(g, row, col, 1, colspan)

        for r in range(nrows):
            self.graph_grid.setRowStretch(r, 1)
        for c in range(ncols):
            self.graph_grid.setColumnStretch(c, 1)

    def output(self, text):
        self.console.append(text)

    def clear_console(self):
        self.console.clear()

    def closeEvent(self, event):
        self.state_management_panel.stop_listening()


if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    app.setStyle("Fusion")

    window = GroundControlWindow()
    window.resize(1800, 1000)
    window.show()

    sys.exit(app.exec())