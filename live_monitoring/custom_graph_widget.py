import pyqtgraph as pg
from time import time
import math

#TODO. FIX FOR JSON DATA. Currently expecting binary data and therefore crashing.
class custom_graph_widget(pg.PlotWidget):
    def __init__(self, names: tuple, start=0, plot_title: str | None = None):
        super().__init__()
        self.names = names
        self._plot_title = plot_title if plot_title is not None else ", ".join(self.names)

        self.graphed_values_num = 40

        self.start_time = start

        self.graph_lines = {} # name -> ([array of time], [array of data], graphitem)
        self._apply_style()

    def _apply_style(self):
        self.setBackground("#121722")
        self.plotItem.setClipToView(True)
        self.plotItem.showGrid(x=True, y=True, alpha=0.25)
        self.plotItem.getAxis("left").setPen(pg.mkPen("#8FA0B3"))
        self.plotItem.getAxis("bottom").setPen(pg.mkPen("#8FA0B3"))
        self.plotItem.getAxis("left").setTextPen(pg.mkPen("#C7D0DA"))
        self.plotItem.getAxis("bottom").setTextPen(pg.mkPen("#C7D0DA"))
        self.plotItem.setLabel("bottom", "Time (s)")
        self.plotItem.setTitle(self._plot_title, color="#E6EDF3", size="10pt")

    def setup_connection(self, current_frame):
        self.plotItem.addLegend()

        self.current_frame = current_frame
        for index, name in enumerate(self.names):
            line_pen = pg.intColor(index, hues=max(len(self.names), 3), values=1, maxValue=255, minValue=180)
            self.graph_lines[name] = ([], [], self.plot([], [], pen=pg.mkPen(line_pen, width=2), name=name))

    def update_lines(self):
        for name, graph_line in self.graph_lines.items():
            if name not in self.current_frame:
                continue

            value = self.current_frame[name]
            if not isinstance(value, (int, float)) or not math.isfinite(value):
                continue

            self.graph_lines[name][0].append(time() - self.start_time)
            self.graph_lines[name][1].append(float(value))

            x_values = self.graph_lines[name][0][-self.graphed_values_num:]
            y_values = self.graph_lines[name][1][-self.graphed_values_num:]

            self.graph_lines[name][2].setData(x_values, y_values)
            self._stabilize_view(x_values, y_values)

    def show_history(self):
        for name, graph_line in self.graph_lines.items():
            self.graph_lines[name][2].setData(self.graph_lines[name][0], self.graph_lines[name][1])
            self._stabilize_view(self.graph_lines[name][0], self.graph_lines[name][1])

    def _stabilize_view(self, x_values, y_values):
        if not x_values or not y_values:
            return

        x_min = min(x_values)
        x_max = max(x_values)
        y_min = min(y_values)
        y_max = max(y_values)

        if x_min == x_max:
            x_min -= 0.5
            x_max += 0.5

        if y_min == y_max:
            padding = max(abs(y_min) * 0.05, 0.5)
            y_min -= padding
            y_max += padding

        self.plotItem.setXRange(x_min, x_max, padding=0.02)
        self.plotItem.setYRange(y_min, y_max, padding=0.1)