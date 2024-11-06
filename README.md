# Modbus_URCap

## A tool modbus RTU URCap.
The URCap runs on port: 40408 on a daemon. Following script functions is added by this URCap:
 
*	**init_tool_modbus_64bit(address)** where address is an int.
*	**init_tool_modbus_32bit(address)** where address is an int.
*	**init_tool_modbus_16bit(address)** where address is an int.
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

Multiple 16-bit registers can be chained together to transmit 32-bit or 64-bit data, this is selected at instatiation by running init_tool_modbus_64bit for 64-bit data transmission (chaining 4 registers), init_tool_modbus_32bit for 32-bit data transmission (chaining 2 registers), and init_tool_modbus_16bit for 16-bit data transmission (no chaining)

## An example script program:
    init_tool_modbus_64bit(1)

    tool_modbus_write_coil(0, True)
    bool1 = tool_modbus_read_discrete(0)
    tool_modbus_write_holding_int(0, 1)
    int1 = tool_modbus_read_input_int(0)
    tool_modbus_write_holding_float(1, 0.1)
    float1 = tool_modbus_read_input_float(1)

## Change log
2024-10-10  Wilfrid     Added more functions. Renamed init_modbus_communications to init_tool_modbus
2024-10-17  Wilfrid     Extended all functions to error handling versions which return struct.
2024-11-6   Zhi-en      Streamline functions, error handling and default number of bits set at instantiation