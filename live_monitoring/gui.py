import sys
import pyqtgraph as pg
from PySide6 import QtCore, QtWidgets
from time import time
import qdarkstyle

from state_management_widget import state_management_widget
from file_management_widget import file_management_widget
from custom_graph_widget import custom_graph_widget
from custom_number_display import custom_number_display
from commanding_panel import commanding_panel


#https://www.pythonguis.com/tutorials/plotting-pyqtgraph/



class GroundControlWindow(QtWidgets.QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("UConn Rocketry Ground Control")
        self.layout = QtWidgets.QVBoxLayout(self)  # Main vertical layout
        self._thread_pool = QtCore.QThreadPool.globalInstance()

        self.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyside6'))
        
        pg.setConfigOption('background', 'black')
         
        self.program_start_time = time()
        
        self.setup_number_displays()
        self.setup_graphs()
        self.init_widgets()

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Space:
            self.command_panel.send_command("COMMAND: ABORT")

    def init_widgets(self):
        # Bottom row - Control widgets (separate horizontal layout)
        bottom_row_widget = QtWidgets.QWidget()
        bottom_row_layout = QtWidgets.QHBoxLayout(bottom_row_widget)
        
        #File input
        self.file_management_panel = file_management_widget(self.output)
        bottom_row_layout.addWidget(self.file_management_panel, 1)  # Stretch factor 1
        
        #Text view - commented out (not being added to layout)
        self.console = QtWidgets.QTextBrowser()
        #bottom_row_layout.addWidget(self.console)

        #State management
        self.state_management_panel = state_management_widget(self.output, self.file_management_panel, self._thread_pool, self.graphs, self.numerical_displays, self.program_start_time)
        bottom_row_layout.addWidget(self.state_management_panel, 2)  # Stretch factor 2 (more space)
        self.state_management_panel.signals.clear_output.connect(self.clear_console)

        #Communication output
        self.command_panel = commanding_panel()
        bottom_row_layout.addWidget(self.command_panel, 2)  # Stretch factor 2 (more space)
        self.command_panel.command_signal.connect(self.state_management_panel.send_command)
        self.state_management_panel.command_panel = self.command_panel
        
        # Add number display to bottom row
        bottom_row_layout.addWidget(self.numerical_displays[0], 1)  # Stretch factor 1
        
        # Add bottom row to main layout
        self.layout.addWidget(bottom_row_widget, 2)  # Stretch factor 2 (taller)
    

    def setup_number_displays(self):
        self.numerical_displays = []
        self.numerical_displays.append(custom_number_display(1, "Current State: Vibingggggggggggggggg"))

    def setup_graphs(self):
        self.graphs = []

        #self.graphs.append(custom_graph_widget(indexes_in_struct=[1], names=('Nitrogen Line Pressure (psig)'), start=self.program_start_time))
        #self.graphs.append(custom_graph_widget(indexes_in_struct=[2], names=('Ethanol Tank Pressure (psig)'), start=self.program_start_time))
        #self.graphs.append(custom_graph_widget(indexes_in_struct=[3], names=('Nitrous Line Pressure (psig)'), start=self.program_start_time))
        #self.graphs.append(custom_graph_widget(indexes_in_struct=[4], names=('Oxygen Line Pressure (psig)'), start=self.program_start_time))
        #self.graphs.append(custom_graph_widget(indexes_in_struct=[5], names=('Fuel Inlet Pressure (psig)'), start=self.program_start_time))
        #self.graphs.append(custom_graph_widget(indexes_in_struct=[6], names=('Fuel Outlet Pressure (psig)'), start=self.program_start_time))
        #self.graphs.append(custom_graph_widget(indexes_in_struct=[7], names=('Engine Chamber Pressure (psig)'), start=self.program_start_time))
        #self.graphs.append(custom_graph_widget(indexes_in_struct=[8], names=('Load Cell (lbf)'), start=self.program_start_time))
        self.graphs.append(custom_graph_widget(names=('Nitrogen Line Pressure (psig)'), start=self.program_start_time))
        self.graphs.append(custom_graph_widget(names=('Ethanol Tank Pressure (psig)'), start=self.program_start_time))
        self.graphs.append(custom_graph_widget(names=('Nitrous Line Pressure (psig)'), start=self.program_start_time))
        self.graphs.append(custom_graph_widget(names=('Oxygen Line Pressure (psig)'), start=self.program_start_time))
        self.graphs.append(custom_graph_widget(names=('Fuel Inlet Pressure (psig)'), start=self.program_start_time))
        self.graphs.append(custom_graph_widget(names=('Fuel Outlet Pressure (psig)'), start=self.program_start_time))
        self.graphs.append(custom_graph_widget(names=('Engine Chamber Pressure (psig)'), start=self.program_start_time))
        self.graphs.append(custom_graph_widget(names=('Load Cell (lbf)'), start=self.program_start_time))
        self.graphs.append(custom_graph_widget(names=('euler_x', 'euler_y', 'euler_z'), start=self.program_start_time))
        self.graphs.append(custom_graph_widget(names=('input_x', 'input_y', 'dt'), start=self.program_start_time))
        self.graphs.append(custom_graph_widget(names=('velocity_x', 'velocity_y', 'velocity_z'), start=self.program_start_time))
       
        # Top row - Pressure readouts (separate horizontal layout)
        top_row_widget = QtWidgets.QWidget()
        top_row_layout = QtWidgets.QHBoxLayout(top_row_widget)
        top_row_layout.addWidget(self.graphs[0])  # Nitrogen Line Pressure
        top_row_layout.addWidget(self.graphs[1])  # Ethanol Tank Pressure
        top_row_layout.addWidget(self.graphs[2])  # Nitrous Line Pressure
        top_row_layout.addWidget(self.graphs[3])  # Oxygen Line Pressure
        top_row_layout.addWidget(self.graphs[4])  # Fuel Inlet Pressure
        top_row_layout.addWidget(self.graphs[5])  # Fuel Outlet Pressure
        top_row_layout.addWidget(self.graphs[6])  # Engine Chamber Pressure
        top_row_layout.addWidget(self.graphs[7])  # Load Cell
        self.layout.addWidget(top_row_widget, 1)  # Stretch factor 1 (shorter)
        
        # Middle row - Big readouts (separate horizontal layout)
        middle_row_widget = QtWidgets.QWidget()
        middle_row_layout = QtWidgets.QHBoxLayout(middle_row_widget)
        middle_row_layout.addWidget(self.graphs[8])   # euler_x, euler_y, euler_z
        middle_row_layout.addWidget(self.graphs[9])   # input_x, input_y, dt
        middle_row_layout.addWidget(self.graphs[10])  # velocity_x, velocity_y, velocity_z
        self.layout.addWidget(middle_row_widget, 3)  # Stretch factor 3 (taller)

    def output(self, text):
        self.console.append(text)

    def clear_console(self):
        self.console.clear()

    def closeEvent(self, event):
        self.state_management_panel.stop_listening()

if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    app.setStyle('Fusion')

    window = GroundControlWindow()
    window.resize(800, 600)
    window.show()
    
    sys.exit(app.exec())