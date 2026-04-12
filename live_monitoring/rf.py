from multiprocessing import Queue, Value, Process, Pipe
from time import sleep
import json
from json import JSONDecodeError

import serial


class RF():
    TELEM_KEYS = (
        "euler_x",
        "euler_y",
        "euler_z",
        "input_x",
        "input_y",
        "velocity_x",
        "velocity_y",
        "velocity_z",
        "dt",
    )

    LIQUID_TELEM_KEYS = (
        "nitrogen_line_psi",
        "ethanol_tank_psi",
        "nitrous_line_psi",
        "oxygen_line_psi",
        "fuel_inlet_psi",
        "fuel_outlet_psi",
        "chamber_pressure_psi",
        "load_cell_lbs",
    )

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

        while "\n" in self._receive_buffer:
            raw_message, self._receive_buffer = self._receive_buffer.split("\n", 1)
            raw_message = raw_message.strip()

            if not raw_message:
                continue

            try:
                message = json.loads(raw_message)
            except JSONDecodeError:
                self._log_queue.put(f"Malformed serial message: {raw_message}")
                continue

            self._handle_message(message)

    def _handle_message(self, data):
        try:
            print(data)

            if not isinstance(data, dict):
                self._log_queue.put(f"Unexpected serial message type ({type(data).__name__}): {data}")
                return

            if(data["data_type"] == "string"):
                self._log_queue.put(data["payload"])
            elif(data["data_type"] == "telem"):
                payload = self._payload_to_frame(data["payload"], self.TELEM_KEYS)
                print("PayLoad = ", payload)
                self._telem_frame_queue.put(payload)
                self._current_telem_frame.update(payload)
                self.handled_most_recent.value = 0
            elif(data["data_type"] == "liquid_telem"):
                payload = self._payload_to_frame(data["payload"], self.LIQUID_TELEM_KEYS)
                self._current_telem_frame.update(payload)
                self.handled_most_recent.value = 0
            else:
                self._log_queue.put(f"Unhandled data_type: {data['data_type']}")
        except JSONDecodeError:
            self._log_queue.put(f"Malformed serial message: {data}")
        except KeyError as e:
            self._log_queue.put(f"Missing field in serial message ({e}): {data}")
        except Exception as e:
            self._log_queue.put(f"Unexpected serial parsing error ({e}): {data}")

    def _payload_to_frame(self, payload, keys):
        if isinstance(payload, dict):
            return payload

        if not isinstance(payload, list):
            raise TypeError(f"Expected telemetry payload list or dict, got {type(payload).__name__}")

        if len(payload) != len(keys):
            raise ValueError(f"Expected {len(keys)} values, got {len(payload)}")

        return dict(zip(keys, payload))
