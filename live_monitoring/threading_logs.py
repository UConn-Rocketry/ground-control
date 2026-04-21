from PySide6 import QtCore
from multiprocessing import Queue
from time import time

from telemetry_schema import ENGINE_TELEM_KEYS, GNC_TELEM_KEYS

_GUI_TELEM_PREVIEW_MAX_LEN = 320
_ENGINE_TELEM_KEY_SET = set(ENGINE_TELEM_KEYS)
_GNC_TELEM_KEY_SET = set(GNC_TELEM_KEYS)


def _format_telem_gui_preview(message) -> str:
    if isinstance(message, dict):
        parts = [f"{k}={v}" for k, v in sorted(message.items())]
        text = " | ".join(parts)
    else:
        text = str(message)
    if len(text) > _GUI_TELEM_PREVIEW_MAX_LEN:
        return text[: _GUI_TELEM_PREVIEW_MAX_LEN - 3] + "..."
    return text


class log_signals(QtCore.QObject):
    log_signal = QtCore.Signal(str)

class telem_signals(QtCore.QObject):
    engine_telem_signal = QtCore.Signal(str)
    gnc_telem_signal = QtCore.Signal(str)


def _classify_telem_message(message) -> str | None:
    if not isinstance(message, dict):
        return None

    keys = set(message.keys())
    if keys and keys.issubset(_ENGINE_TELEM_KEY_SET):
        return "engine"
    if keys and keys.issubset(_GNC_TELEM_KEY_SET):
        return "gnc"
    return None

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
    def __init__(
        self,
        path: str,
        frame_queue: Queue,
        start: float,
        gui_preview_interval_s: float = 0.25,
    ):
        super().__init__()
        self.path = path
        self.signals = telem_signals()
        self.frame_queue = frame_queue

        self.start_time = start
        self.gui_preview_interval_s = gui_preview_interval_s

    def run(self):
        self.signals.engine_telem_signal.emit('GUI: Start data logging')
        self.signals.gnc_telem_signal.emit('GUI: Start data logging')
        last_gui_emit = 0.0
        with open(self.path, 'a') as file:
            while True:
                message = self.frame_queue.get()
                if message == 'STOP':
                    break

                if isinstance(message, dict):
                    values = message.values()
                else:
                    values = message

                for x in values:
                    file.write(str(x) + ",")
                file.write("{:.2f}".format(time() - self.start_time))
                file.write('\n')

                if self.gui_preview_interval_s and self.gui_preview_interval_s > 0:
                    now = time()
                    if now - last_gui_emit >= self.gui_preview_interval_s:
                        last_gui_emit = now
                        elapsed = now - self.start_time
                        preview = _format_telem_gui_preview(message)
                        formatted = f"Telem t={elapsed:.2f}s {preview}"
                        destination = _classify_telem_message(message)
                        if destination == "engine":
                            self.signals.engine_telem_signal.emit(formatted)
                        elif destination == "gnc":
                            self.signals.gnc_telem_signal.emit(formatted)
                        else:
                            self.signals.engine_telem_signal.emit(formatted)
                            self.signals.gnc_telem_signal.emit(formatted)

        self.signals.engine_telem_signal.emit('GUI: End data logging, Saved')
        self.signals.gnc_telem_signal.emit('GUI: End data logging, Saved')
