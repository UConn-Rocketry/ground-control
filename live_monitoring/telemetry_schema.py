ENGINE_TELEM_KEYS = (
    "nitrogen_line_psi",
    "ethanol_tank_psi",
    "nitrous_line_psi",
    "nitrous_tank_line_psi",
    "oxygen_line_psi",
    "fuel_inlet_psi",
    "fuel_outlet_psi",
    "chamber_pressure_psi",
    "load_cell_lbs",
)

GNC_TELEM_KEYS = (
    "position_x",
    "position_y",
    "position_z",
    "velocity_x",
    "velocity_y",
    "velocity_z",
    "euler_x",
    "euler_y",
    "euler_z",
    "omega_x",
    "omega_y",
    "omega_z",
    "accel_bias_x",
    "accel_bias_y",
    "accel_bias_z",
    "omega_bias_x",
    "omega_bias_y",
    "omega_bias_z",
    "tvc_command_x",
    "tvc_command_y",
    "rcs_command",
    "thrust_command",
    "actuator_setpoint_error_x",
    "actuator_setpoint_error_y",
    "attitude_setpoint_error_x",
    "attitude_setpoint_error_y",
    "attitude_setpoint_error_z",
    "guidance_altitude_error",
    "guidance_translation_error_x",
    "guidance_translation_error_y",
)

# key, title, checkbox label, optional y-range tuple
ENGINE_PLOT_SPECS = [
    ("nitrogen_line_psi", "N2 line pressure (psi)", "N2 line pressure", (0, 1000)),
    ("ethanol_tank_psi", "Ethanol tank (psi)", "Ethanol tank", (0, 1000)),
    ("nitrous_line_psi", "Nitrous line (psi)", "Nitrous line", (0, 1000)),
    ("nitrous_tank_line_psi", "Nitrous tank line (psi)", "Nitrous tank line", (0, 1000)),
    ("oxygen_line_psi", "Oxygen line (psi)", "Oxygen line", (0, 200)),
    ("fuel_inlet_psi", "Fuel inlet (psi)", "Fuel inlet", (0, 1000)),
    ("fuel_outlet_psi", "Fuel outlet (psi)", "Fuel outlet", (0, 1000)),
    ("chamber_pressure_psi", "Chamber pressure (psi)", "Chamber pressure", (0, 1000)),
    ("load_cell_lbs", "Load cell (lb)", "Load cell", (0, 1100)),
]

# names, title, checkbox label
GNC_NAVIGATION_PLOT_SPECS = [
    (("position_x", "position_y", "position_z"), "Position (m)", "Position"),
    (("velocity_x", "velocity_y", "velocity_z"), "Velocity (m/s)", "Velocity"),
    (("euler_x", "euler_y", "euler_z"), "Euler Angles (rad)", "Euler Angles"),
    (("omega_x", "omega_y", "omega_z"), "Omega (rad/s)", "Omega"),
    (("accel_bias_x", "accel_bias_y", "accel_bias_z"), "Accelerometer Bias (m/s^2)", "Accelerometer Bias"),
    (("omega_bias_x", "omega_bias_y", "omega_bias_z"), "Gyro Bias (rad/s)", "Gyro Bias"),
]

GNC_CONTROL_PLOT_SPECS = [
    (("tvc_command_x", "tvc_command_y"), "TVC Command (rad)", "TVC Command"),
    (("rcs_command",), "RCS Command (N)", "RCS Command"),
    (("thrust_command",), "Thrust Command (N)", "Thrust Command"),
    (("attitude_setpoint_error_x", "attitude_setpoint_error_y", "attitude_setpoint_error_z"), "Attitude Setpoint Error (rad)", "Attitude Setpoint Error"),
    (("actuator_setpoint_error_x", "actuator_setpoint_error_y"), "Actuator Setpoint Error (inches)", "Actuator Setpoint Error"),
    (("guidance_altitude_error",), "Guidance Altitude Error (m)", "Guidance Altitude Error"),
    (("guidance_translation_error_x", "guidance_translation_error_y"), "Guidance Translation Error (m)", "Guidance Translation Error"),
]
