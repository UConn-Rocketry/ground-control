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
        self.setWindowTitle("AIAA PL Ground Control")
        self.layout = QtWidgets.QGridLayout(self)
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
        #File input
        self.file_management_panel = file_management_widget(self.output)
        self.layout.addWidget(self.file_management_panel, 2, 0)
        
        #Text view
        self.console = QtWidgets.QTextBrowser()
        self.layout.addWidget(self.console, 2, 1, 3, 1)

        #State management
        self.state_management_panel = state_management_widget(self.output, self.file_management_panel, self._thread_pool, self.graphs, self.numerical_displays, self.program_start_time)
        self.layout.addWidget(self.state_management_panel, 3, 0)
        self.state_management_panel.signals.clear_output.connect(self.clear_console)

        #Communication output
        self.command_panel = commanding_panel()
        self.layout.addWidget(self.command_panel, 0, 4, 2, 1)
        self.command_panel.command_signal.connect(self.state_management_panel.send_command)
        self.state_management_panel.command_panel = self.command_panel
    

    def setup_number_displays(self):
        self.numerical_displays = []
        self.numerical_displays.append(custom_number_display(1, "Current State: Vibingggggggggggggggg"))
        self.layout.addWidget(self.numerical_displays[0], 4, 4)

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
       
        self.layout.addWidget(self.graphs[0], 0, 0)
        self.layout.addWidget(self.graphs[1], 0, 1)
        self.layout.addWidget(self.graphs[2], 0, 2)
        self.layout.addWidget(self.graphs[3], 0, 3)
        self.layout.addWidget(self.graphs[4], 1, 0)
        self.layout.addWidget(self.graphs[5], 1, 1)
        self.layout.addWidget(self.graphs[6], 1, 2)
        self.layout.addWidget(self.graphs[7], 1, 3)

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