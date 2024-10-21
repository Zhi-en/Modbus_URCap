# Modbus_URCap

## A tool modbus RTU URCap.
The URCap runs on port: 40408 on a daemon. Following script functions is added by this URCap:
 
*	**init_tool_modbus(address)** where address is an int.
*	**tool_modbus_write_coil(register_address, data)** where register_address is an int and data is a bool.
*	**tool_modbus_read_discrete(register_address)** where register_address is an int.
*	**tool_modbus_read_coil(register_address)** where register_address is an int.
*	**tool_modbus_write_holding_int(register_address, data)** where register_address is an int and data is an int.
*	**tool_modbus_write_holding_float(register_address, data)** where register_address is an int and data is a float.
*	**tool_modbus_read_input_int(register_address)** where register_address is an int.
*	**tool_modbus_read_input_float(register_address)** where register_address is an int.
*	**tool_modbus_read_holding_int(register_address)** where register_address is an int.
*	**tool_modbus_read_holding_float(register_address)** where register_address is an int.

The RS485 settings can be modified with the functions:

*	**tool_modbus_set_baudrate(baudrate)** where baudrate values are 9600, 19200, 38400, 57600, 115200, 1000000, 2000000, 5000000
*	**tool_modbus_set_bytesize(bytesize)** where bytesize values are 5, 6, 7, 8
*	**tool_modbus_set_parity(parity)** where parity values are "None", "Even", "Odd"
*	**tool_modbus_set_stopbit(stop)** where stop values are 1, 1.5, 2
*	**tool_modbus_set_timeout(timeout)** where timeout is in seconds

Multiple 16-bit registers can be chained together to transmit 32-bit or 64-bit data, the default uses 64-bit. The settings can be modified with:

*	**tool_modbus_set_register_chaining(register_chaining)** where register_chaining is in 1, 2, or 4. Float functions can only be used with register_chaining of 2 and 4.

## An example script program:
    init_tool_modbus(1)

    tool_modbus_write_coil(0, True)
    bool1 = tool_modbus_read_discrete(0)
    tool_modbus_write_holding_int(0, 1)
    int1 = tool_modbus_read_input_int(0)
    tool_modbus_write_holding_float(1, 0.1)
    float1 = tool_modbus_read_input_float(1)