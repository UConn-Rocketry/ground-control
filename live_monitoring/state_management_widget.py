from PySide6 import QtCore, QtWidgets
import pyqtgraph as pg
from pyqtgraph import exporters
from time import time
from multiprocessing import Array, Value, Queue, Manager

from file_management_widget import file_management_widget

import gui_util
from threading_logs import telem_frame_handler, log_handler
from rf import RF


class state_signals(QtCore.QObject):
    connection_monitor = QtCore.Signal(bool)
    clear_output = QtCore.Signal()

class state_management_widget(QtWidgets.QWidget):
    def __init__(self, output, file_management_panel : file_management_widget, thread_pool, graphs, numerical_displays, start) -> None:
        super().__init__()
        self.layout = QtWidgets.QFormLayout(self)

        self.output = output #function that handles output messages
        self.file_management_panel = file_management_panel
        self.thread_pool = thread_pool 
        self.graphs = graphs #list of graphs type: pg.PlotWidget
        self.numerical_displays = numerical_displays #List of extension of QLabels

        self.manager = Manager()

        self.start_time = start

        self.signals = state_signals()

        #connect button
        self.connect_serial_button = QtWidgets.QPushButton("Connect Serial and Listen")
        self.layout.addRow(self.connect_serial_button)
        self.connect_serial_button.clicked.connect(self.connect_and_listen)

        #stop and save button
        self.stop_listening_button = QtWidgets.QPushButton("Stop Listening")
        self.layout.addRow(self.stop_listening_button)
        self.stop_listening_button.clicked.connect(self.stop_listening)
        self.stop_listening_button.setEnabled(False)

        #Reset and Save Graphs
        self.reset_and_save_graphs_button = QtWidgets.QPushButton("Reset and Save Graphs")
        self.reset_and_discard_button = QtWidgets.QPushButton("Reset and Discard")

        self.layout.addRow(self.reset_and_save_graphs_button, self.reset_and_discard_button)
        self.reset_and_save_graphs_button.clicked.connect(self.save_and_reset)
        self.reset_and_discard_button.clicked.connect(self.discard_files_and_reset)

        self.reset_and_discard_button.setEnabled(False)
        self.reset_and_save_graphs_button.setEnabled(False)


    def _update_plot_data(self):
        if(self.graphed_most_recent_value.value == 0):
            for graph in self.graphs:
                graph.update_lines()
            for number_display in self.numerical_displays:
                number_display.update_value()
            self.graphed_most_recent_value.value = 1

    def _start_animation_timer(self):
        if not hasattr(self, "animation_timer") or self.animation_timer is None:
            self.animation_timer = QtCore.QTimer(self)
            self.animation_timer.setInterval(25)
            self.animation_timer.timeout.connect(self._update_plot_data)
        self.animation_timer.start()

    def reset_graphs(self):
        self.reset_and_discard_button.setEnabled(False)
        self.reset_and_save_graphs_button.setEnabled(False)
        for i, graph in enumerate(self.graphs):
            exporter = pg.exporters.ImageExporter(graph.getPlotItem())

            try:
                path = str(self.file_management_panel.output_location.joinpath('./Graphs/'+str(i)+'.png'))
                exporter.export(path)
            except Exception as e:
                print(e)

            graph.getPlotItem().clear()

        self.file_management_panel.find_next_available_save_location_in_current_directory()

        self.connect_serial_button.setEnabled(True)
        self.reset_and_save_graphs_button.setEnabled(False)

        self.signals.clear_output.emit()

    def connect_and_listen(self):
        if(not self.file_management_panel.check_ready()):
            return

        port = self.file_management_panel.serial_port()
        if not gui_util.serial_port_available(port):
            self.output("GUI: Invalid Serial Port")
            return

        self.initialize_rf(port, 9600)
        self.signals.connection_monitor.emit(True) 
        self._start_animation_timer()
            
        self.data_path, self.log_path = self.file_management_panel.create_files()

        self.looping_for_data.value = 1
        self.rf.start_listen_loop(self.looping_for_data)

        logging = log_handler(self.log_path, self.log_queue, self.start_time)
        telem = telem_frame_handler(self.data_path, self.frame_queue, self.start_time)

        logging.signals.log_signal.connect(self.output)
        telem.signals.telem_signal.connect(self.output)

        self.thread_pool.start(logging)
        self.thread_pool.start(telem)
        
        self.stop_listening_button.setEnabled(True)
        self.connect_serial_button.setEnabled(False)

    def stop_listening(self):
        try:
            self.log_queue.put('STOP')
            self.frame_queue.put('STOP')
            self.looping_for_data.value = 0

            self.stop_listening_button.setEnabled(False)
            self.connect_serial_button.setEnabled(False)
        
            for graph in self.graphs:
                graph.show_history()

            self.animation_timer.stop()
            
            self.reset_and_save_graphs_button.setEnabled(True)
            self.reset_and_discard_button.setEnabled(True)
            
            self.rf.input_transmitter.close()

            self.rf.process.join(timeout=1)
            if self.rf.process.is_alive():
                self.rf.process.terminate()
            self.rf = None

        except AttributeError:
            pass
        finally:
            self.signals.connection_monitor.emit(False)

    def discard_files_and_reset(self):
        self.file_management_panel.delete_files_from_current_run()
        self.reset_graphs()

    def save_and_reset(self):
        self.reset_graphs()

    #does not connect the port, just passses the info to the RF class so it can be used later
    def initialize_rf(self, port : str, baud : int):
        self.current_frame = self.manager.dict() #Most recent data frame received
        self.log_queue = self.manager.Queue() #queue of all logs
        self.frame_queue = self.manager.Queue() #queue of all data frames received

        self.graphed_most_recent_value = Value('B')
        self.graphed_most_recent_value.value = 1

        self.command_panel.current = self.current_frame

        self.looping_for_data = Value('i', 1) #Controls whether the listenig process is running.

        self.rf = RF(port, baud, self.current_frame, self.frame_queue, self.log_queue, handled_most_recent=self.graphed_most_recent_value)

        for graph in self.graphs:
            graph.setup_connection(self.current_frame)
        for number in self.numerical_displays:
            number.setup_connection(self.current_frame)

        
            
    
    def send_command(self, command: str):
        try:
            self.rf.input_transmitter.send(command)
            self.rf._log_queue.put("sent: " + command)
        except AttributeError:
            self.output("Serial not Connected")