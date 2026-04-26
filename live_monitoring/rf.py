from multiprocessing import Queue, Value, Process, Pipe
from time import sleep, time
import json
from json import JSONDecodeError

import serial

from telemetry_schema import ENGINE_TELEM_KEYS, GNC_TELEM_KEYS


class RF():
    TELEM_KEYS = ENGINE_TELEM_KEYS

    GNC_KEYS = GNC_TELEM_KEYS

    def __init__(self, port : str, baud : int, current_value, telem_frame_queue, log_queue, handled_most_recent : Value):

        self.port = port
        self.baud = baud

        self._delay_between_packets = .05 #Delay (in s) if there is not enough data in input buffer to be read into something meaningful



        self.input_receiver, self.input_transmitter = Pipe()

        self.handled_most_recent = handled_most_recent

        self._current_telem_frame = current_value
        self._telem_frame_queue = telem_frame_queue
        self._log_queue = log_queue
        self._receive_buffer = ""
        self._last_seq = None
        self._seq_gap_count = 0
        self._duplicate_seq_count = 0

    def connect_serial(self, port: str, baud: int) -> bool:
        try:
            self._comport = serial.Serial(port, baud, timeout=0.2, write_timeout=0.2)
            self._comport.reset_input_buffer()
            return True
        except serial.SerialException:
            return False

    def disconnect_serial(self):
        try:
            self._comport.close()
            return True
        except ValueError:
            return False


    def _listen_loop(self, running: Value):
        self._comport = serial.Serial(self.port, self.baud, timeout=0.2, write_timeout=0.2)
        self._comport.reset_input_buffer()

        while(running.value == 1):
            if(self.input_receiver.poll()):
                val = self.input_receiver.recv()
                self._comport.write(val.encode("ascii", "replace"))
                self._comport.flush()
            self.read_json()
        
        self._comport.close()

    #Starts a separate process that will connect serial port then listen for data
    def start_listen_loop(self, running: Value):
        self.process = Process(target=self._listen_loop, args=(running,), name="Data Search Loop")
        self.process.start()


    #Should be called with high frequency to ensure propper readings
    def read_json(self):
        if(self._comport.in_waiting < 1):
            sleep(self._delay_between_packets)
            return

        received = self._comport.read(self._comport.in_waiting)
        if not received:
            return

        self._receive_buffer += received.decode("utf-8", errors="replace")
        print("Received data from serial port:", self._receive_buffer)

        while "\n" in self._receive_buffer:
            raw_message, self._receive_buffer = self._receive_buffer.split("\n", 1)
            raw_message = raw_message.strip()

            if not raw_message:
                continue

            try:
                message = json.loads(raw_message)
            except JSONDecodeError:
                continue

            self._handle_message(message)

    def _handle_message(self, data):
        try:
            if not isinstance(data, dict):
                self._log_queue.put(f"Unexpected serial message type ({type(data).__name__}): {data}")
                return

            self._current_telem_frame["_meta_last_rx_epoch"] = time()

            seq = data.get("seq")
            if isinstance(seq, int):
                if self._last_seq is not None and seq == self._last_seq:
                    self._duplicate_seq_count += 1
                    self._current_telem_frame["_meta_duplicate_seq_count"] = self._duplicate_seq_count
                    self._log_queue.put(f"Serial duplicate packet ignored: seq {seq}")
                    return
                if self._last_seq is not None and seq > self._last_seq + 1:
                    missed = seq - (self._last_seq + 1)
                    self._seq_gap_count += missed
                    self._current_telem_frame["_meta_seq_gap_count"] = self._seq_gap_count
                    self._log_queue.put(
                        f"Serial sequence gap detected: missed {missed} packet(s) between seq {self._last_seq} and {seq}"
                    )
                elif self._last_seq is not None and seq <= self._last_seq:
                    self._log_queue.put(
                        f"Serial sequence out-of-order: seq {seq} arrived after seq {self._last_seq}"
                    )
                    return

                self._last_seq = seq
                self._current_telem_frame["_meta_last_seq"] = seq

            if(data["data_type"] == "string"):
                payload = data["payload"]
                self._log_queue.put(data["payload"])
            elif(data["data_type"] == "telem"):
                payload = self._payload_to_frame(data["payload"])
                message_type = data.get("type")
                queued_message = {
                    "data_type": "telem",
                    "type": message_type,
                    "payload": payload,
                }
                self._telem_frame_queue.put(queued_message)
                self._current_telem_frame.update(payload)
                self.handled_most_recent.value = 0
            else:
                self._log_queue.put(f"Unhandled data_type: {data['data_type']}")
        except KeyError as e:
            self._log_queue.put(f"Missing field in serial message ({e}): {data}")
        except Exception as e:
            self._log_queue.put(f"Unexpected serial parsing error ({e}): {data}")

    def _payload_to_frame(self, payload):
        if isinstance(payload, dict):
            return payload

        if not isinstance(payload, list):
            raise TypeError(f"Expected telemetry payload list or dict, got {type(payload).__name__}")

        if len(payload) == len(self.TELEM_KEYS):
            keys = self.TELEM_KEYS
        elif len(payload) == len(self.GNC_KEYS):
            keys = self.GNC_KEYS
        else:
            raise ValueError(
                f"Expected {len(self.TELEM_KEYS)} engine values or {len(self.GNC_KEYS)} GNC values, got {len(payload)}"
            )

        return dict(zip(keys, payload))