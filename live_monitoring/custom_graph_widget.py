import pyqtgraph as pg
from time import time
import math

#TODO. FIX FOR JSON DATA. Currently expecting binary data and therefore crashing.
class custom_graph_widget(pg.PlotWidget):
    def __init__(
        self,
        names: tuple,
        start=0,
        plot_title: str | None = None,
        fixed_y_range: tuple[float, float] | None = None,
    ):
        super().__init__()
        self.names = names
        self._plot_title = plot_title if plot_title is not None else ", ".join(self.names)
        self.fixed_y_range = fixed_y_range

        self.graphed_values_num = 40

        self.start_time = start

        self.graph_lines = {} # name -> ([array of time], [array of data], graphitem)
        self._apply_style()
        if self.fixed_y_range is not None:
            self._apply_fixed_y_axis()

    def _apply_style(self):
        self.setBackground("#121722")
        self.plotItem.setClipToView(True)
        self.plotItem.showGrid(x=True, y=True, alpha=0.25)
        self.plotItem.getAxis("left").setPen(pg.mkPen("#8FA0B3"))
        self.plotItem.getAxis("bottom").setPen(pg.mkPen("#8FA0B3"))
        self.plotItem.getAxis("left").setTextPen(pg.mkPen("#C7D0DA"))
        self.plotItem.getAxis("bottom").setTextPen(pg.mkPen("#C7D0DA"))
        self._set_x_tick_spacing(5)
        self.plotItem.setLabel("bottom", "Time (s)")
        self.plotItem.setTitle(self._plot_title, color="#E6EDF3", size="10pt")

    def setup_connection(self, current_frame):
        self.plotItem.clear()
        if self.plotItem.legend is not None:
            self.plotItem.legend.scene().removeItem(self.plotItem.legend)
            self.plotItem.legend = None

        self.graph_lines = {}

        use_legend = len(self.names) > 1
        if use_legend:
            self.plotItem.addLegend()

        self.current_frame = current_frame
        for index, name in enumerate(self.names):
            line_pen = pg.intColor(index, hues=max(len(self.names), 3), values=1, maxValue=255, minValue=180)
            legend_name = self._legend_label(index, name) if use_legend else None
            self.graph_lines[name] = (
                [],
                [],
                self.plot([], [], pen=pg.mkPen(line_pen, width=2), name=legend_name),
            )

    def _legend_label(self, index, name):
        lowered = str(name).lower()
        if lowered.endswith("_x"):
            return "x"
        if lowered.endswith("_y"):
            return "y"
        if lowered.endswith("_z"):
            return "z"
        if lowered.endswith("_n"):
            return "n"
        if lowered.endswith("_e"):
            return "e"
        if lowered.endswith("_d"):
            return "d"
        if lowered.endswith("_w"):
            return "w"

        compact_fallback = ("x", "y", "z", "w")
        if index < len(compact_fallback):
            return compact_fallback[index]
        return f"v{index + 1}"

    def _apply_fixed_y_axis(self):
        y_min, y_max = self.fixed_y_range
        view_min, view_max = self._fixed_y_view_range(y_min, y_max)
        self.plotItem.setYRange(view_min, view_max, padding=0)
        self.plotItem.getAxis("left").setTicks([self._fixed_y_ticks(y_min, y_max)])

    def _fixed_y_view_range(self, y_min, y_max):
        if y_min == y_max:
            margin = max(abs(y_min) * 0.05, 0.5)
        else:
            margin = abs(y_max - y_min) * 0.03

        return y_min - margin, y_max + margin

    def _fixed_y_ticks(self, y_min, y_max):
        tick_count = 5
        if y_min == y_max:
            return [(y_min, self._format_tick_label(y_min))]

        step = (y_max - y_min) / (tick_count - 1)
        return [
            (value, self._format_tick_label(value))
            for value in (y_min + step * index for index in range(tick_count))
        ]

    def _format_tick_label(self, value):
        if abs(value) < 1e-9:
            value = 0
        return f"{value:g}"

    def _set_x_tick_spacing(self, major):
        self.plotItem.getAxis("bottom").setTickSpacing(major=major, minor=major / 5)

    def _apply_x_axis_for_range(self, x_min, x_max):
        span = max(x_max - x_min, 0)
        if span <= 30:
            major = 5
        elif span <= 60:
            major = 10
        elif span <= 120:
            major = 20
        elif span <= 300:
            major = 60
        elif span <= 600:
            major = 120
        else:
            major = 300

        self._set_x_tick_spacing(major)

    def update_lines(self):
        combined_x_values = []
        combined_y_values = []

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
            combined_x_values.extend(x_values)
            combined_y_values.extend(y_values)

        self._stabilize_view(combined_x_values, combined_y_values)

    def show_history(self):
        combined_x_values = []
        combined_y_values = []

        for name, graph_line in self.graph_lines.items():
            history_x = self.graph_lines[name][0]
            history_y = self.graph_lines[name][1]
            self.graph_lines[name][2].setData(history_x, history_y)
            combined_x_values.extend(history_x)
            combined_y_values.extend(history_y)

        self._stabilize_view(combined_x_values, combined_y_values)

    def _stabilize_view(self, x_values, y_values):
        if not x_values or not y_values:
            return

        x_min = min(x_values)
        x_max = max(x_values)
        if x_min == x_max:
            x_min -= 0.5
            x_max += 0.5

        self._apply_x_axis_for_range(x_min, x_max)
        self.plotItem.setXRange(x_min, x_max, padding=0.02)
        if self.fixed_y_range is None:
            y_min = min(y_values)
            y_max = max(y_values)

            if y_min == y_max:
                padding = max(abs(y_min) * 0.05, 0.5)
                y_min -= padding
                y_max += padding

            self.plotItem.setYRange(y_min, y_max, padding=0.1)
        else:
            self._apply_fixed_y_axis()
