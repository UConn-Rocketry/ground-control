from PySide6 import QtCore, QtWidgets
from multiprocessing import Queue
from time import time

class log_signals(QtCore.QObject):
    log_signal = QtCore.Signal(str)

class telem_signals(QtCore.QObject):
    telem_signal = QtCore.Signal(str)

class log_handler(QtCore.QRunnable):
    def __init__(self, path : str, log_queue: Queue, start: float):
        super().__init__()
        self.path = path
        self.log_queue = log_queue
        self.signals = log_signals()

        self.start_time = start

    def run(self):
        self.signals.log_signal.emit('GUI: Start logging')
        with open(self.path, 'a') as file:
            while(True):
                message = self.log_queue.get()
                if(message == 'STOP'):
                    break
        
                stamped = str(message) + " time: {:.2f}".format(time() - self.start_time)

                print(stamped)
                file.write(stamped)
                file.write('\n')

                self.signals.log_signal.emit(f"Received: {stamped}")

        self.signals.log_signal.emit('GUI: End Logging, Saved')


class telem_frame_handler(QtCore.QRunnable):
    def __init__(self, path : str, frame_queue: Queue, start: float):
        super().__init__()
        self.path = path
        self.signals = telem_signals()
        self.frame_queue = frame_queue

        self.start_time = start
        

    def run(self):
        self.signals.telem_signal.emit('GUI: Start data logging')
        with open(self.path, 'a') as file:
            while(True):
                message = self.frame_queue.get()
                if(message == 'STOP'):
                    break
        
                if isinstance(message, dict):
                    values = message.values()
                else:
                    values = message

                for x in values:
                    file.write(str(x) + ",")
                file.write("{:.2f}".format(time() - self.start_time))
                file.write('\n')

        self.signals.telem_signal.emit('GUI: End data logging, Saved')
