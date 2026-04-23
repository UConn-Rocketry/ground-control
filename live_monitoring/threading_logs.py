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
    if isinstance(message, dict) and message.get("data_type") == "telem":
        message_type = message.get("type")
        if message_type == "Liquid":
            return "engine"
        if message_type == "GNC":
            return "gnc"
        message = message.get("payload")

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

                display_prefix = "Received"
                display_message = str(message)
                if isinstance(message, str) and message.startswith("sent: "):
                    display_prefix = "Sent"
                    display_message = message[len("sent: "):]

                display_stamped = display_message + " time: {:.2f}".format(time() - self.start_time)
                logged_stamped = f"{display_prefix}: {display_stamped}"

                print(logged_stamped)
                file.write(logged_stamped)
                file.write('\n')

                self.signals.log_signal.emit(f"{display_prefix}: {display_stamped}")

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
        last_gui_emit = 0.0
        with open(self.path, 'a') as file:
            while True:
                message = self.frame_queue.get()
                if message == 'STOP':
                    break

                payload = message
                if isinstance(message, dict) and message.get("data_type") == "telem":
                    payload = message.get("payload", {})

                if isinstance(payload, dict):
                    values = payload.values()
                else:
                    values = payload

                for x in values:
                    file.write(str(x) + ",")
                file.write("{:.2f}".format(time() - self.start_time))
                file.write('\n')

                if self.gui_preview_interval_s and self.gui_preview_interval_s > 0:
                    now = time()
                    if now - last_gui_emit >= self.gui_preview_interval_s:
                        last_gui_emit = now
                        elapsed = now - self.start_time
                        preview = _format_telem_gui_preview(payload)
                        formatted = f"Telem t={elapsed:.2f}s {preview}"
                        destination = _classify_telem_message(message)
                        if destination == "engine":
                            self.signals.engine_telem_signal.emit(formatted)
                        elif destination == "gnc":
                            self.signals.gnc_telem_signal.emit(formatted)
                        else:
                            self.signals.engine_telem_signal.emit(formatted)
                            self.signals.gnc_telem_signal.emit(formatted)
