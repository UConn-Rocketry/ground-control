from command_panel_framework import (
    ButtonGroupSpec,
    ButtonSpec,
    ConfigurableCommandPanel,
    ToggleGroupSpec,
    ToggleRowSpec,
)

class commanding_panel(ConfigurableCommandPanel):
    def __init__(self):
        valve_rows = [
            ToggleRowSpec("Nitrogen Valve", "Open", "Close", "VALVE: nitrogen open", "VALVE: nitrogen close"),
            ToggleRowSpec("Purge Valve", "Open", "Close", "VALVE: purge open", "VALVE: purge close"),
            ToggleRowSpec(
                "Main Ethanol Valve",
                "Open",
                "Close",
                "VALVE: main ethanol open",
                "VALVE: main ethanol close",
            ),
            ToggleRowSpec(
                "Main Nitrous Valve",
                "Open",
                "Close",
                "VALVE: main nitrous open",
                "VALVE: main nitrous close",
            ),
            ToggleRowSpec(
                "ASI Ethanol Valve",
                "Open",
                "Close",
                "VALVE: ASI ethanol open",
                "VALVE: ASI ethanol close",
            ),
            ToggleRowSpec(
                "ASI Oxygen Valve",
                "Open",
                "Close",
                "VALVE: ASI oxygen open",
                "VALVE: ASI oxygen close",
            ),
            ToggleRowSpec(
                "Nitrogen Bleed Valve",
                "Open",
                "Close",
                "VALVE: nitrogen bleed open",
                "VALVE: nitrogen bleed close",
            ),
            ToggleRowSpec("ASI Spark Plug", "On", "Off", "SPARK: on", "SPARK: off"),
        ]

        command_buttons = [
            ButtonSpec("GoIdle", "GoIdle"),
            ButtonSpec("GoHotFireIdle", "GoHotfireIdle"),
            ButtonSpec("Ignite", "Ignite"),
            ButtonSpec("ASITest", "asitest"),
            ButtonSpec("WaterFlow", "waterflow"),
            ButtonSpec("3SecondHotFire", "3second"),
            ButtonSpec("Abort", "ABORT"),
        ]

        super().__init__(
            manual_placeholder="Enter Command",
            send_button_label="Send Command",
            toggle_groups=[ToggleGroupSpec("Valves and ASI Spark Plug", valve_rows)],
            button_groups=[ButtonGroupSpec("Commands", 3, command_buttons)],
            extra_quick_buttons=[("ABORT", "ABORT", "background: red; color: white; font-size: 12px;")],
            command_aliases={"COMMAND: ABORT": "ABORT"},
        )

        self.current = {}
