# Modbus_URCap

## A modbus RTU URCap.
The URCap runs on port: 40408 on a daemon. Following script functions is added by this URCap:

For connecting to devices via tool connector:
 
*	**init_tool_modbus_64bit()**
*	**init_tool_modbus_32bit()**
*	**init_tool_modbus_16bit()**

For sending and receiving data via tool connector:

*	**tool_modbus_write_coil(slave_address, register_address, data)** where slave_address is an int, register_address is an int and data is a bool.
*	**tool_modbus_read_discrete(slave_address, register_address)** where slave_address is an int and register_address is an int.
*	**tool_modbus_read_coil(slave_address, register_address)** where slave_address is an int and register_address is an int.
*	**tool_modbus_write_coils(slave_address, register_address, data)** where slave_address is an int, register_address is an int and data is a list of bool.
*	**tool_modbus_read_discretes(slave_address, register_address, num_of_data)** where slave_address is an int, register_address is an int and num_of_data is an int.
*	**tool_modbus_read_coils(slave_address, register_address, num_of_data)** where slave_address is an int, register_address is an int and num_of_data is an int.
*	**tool_modbus_write_holding_int(slave_address, register_address, data)** where slave_address is an int, register_address is an int and data is an int.
*	**tool_modbus_write_holding_float(slave_address, register_address, data)** where slave_address is an int, register_address is an int and data is a float.
*	**tool_modbus_read_input_int(slave_address, register_address)** where slave_address is an int and register_address is an int.
*	**tool_modbus_read_input_float(slave_address, register_address)** where slave_address is an int and register_address is an int.
*	**tool_modbus_read_holding_int(slave_address, register_address)** where slave_address is an int and register_address is an int.
*	**tool_modbus_read_holding_float(slave_address, register_address)** where slave_address is an int and register_address is an int.
*	**tool_modbus_write_holdings_int(slave_address, register_address, data)** where slave_address is an int, register_address is an int and data is a list of int.
*	**tool_modbus_write_holdings_float(slave_address, register_address, data)** where slave_address is an int, register_address is an int and data is a list of float.
*	**tool_modbus_read_inputs_int(slave_address, register_address, num_of_data)** where slave_address is an int, register_address is an int and num_of_data is an int.
*	**tool_modbus_read_inputs_float(slave_address, register_address, num_of_data)** where slave_address is an int, register_address is an int and num_of_data is an int.
*	**tool_modbus_read_holdings_int(slave_address, register_address, num_of_data)** where slave_address is an int, register_address is an int and num_of_data is an int.
*	**tool_modbus_read_holdings_float(slave_address, register_address, num_of_data)** where slave_address is an int, register_address is an int and num_of_data is an int.
*	**tool_modbus_write_holdings(slave_address, register_address, data, dtypes)** where slave_address is an int, register_address is an int, data is a list of int/floats and dtype is a list of "int" or "float".
*	**tool_modbus_read_inputs(slave_address, register_address, dtypes)** where slave_address is an int, register_address is an int and dtypes is a list of "int" or "float" whose length corresponds to the number of registers to read.
*	**tool_modbus_read_holdings(slave_address, register_address, dtypes)** where slave_address is an int, register_address is an int and dtypes is a list of "int" or "float" whose length corresponds to the number of registers to read.

The RS485 settings can be modified with the functions:

*	**tool_modbus_set_baudrate(baudrate)** where baudrate values are 9600, 19200, 38400, 57600, 115200, 1000000, 2000000, 5000000
*	**tool_modbus_set_bytesize(bytesize)** where bytesize values are 5, 6, 7, 8
*	**tool_modbus_set_parity(parity)** where parity values are "None", "Even", "Odd"
*	**tool_modbus_set_stopbit(stop)** where stop values are 1, 1.5, 2
*	**tool_modbus_set_timeout(timeout)** where timeout is in seconds

For connecting to devices via USB:
 
*	**init_usb_modbus_64bit(usb_devname_contains, usb_IDserial_contains)** where usb_devname_contains is a string and usb_IDserial_contains is a string.
*	**init_usb_modbus_32bit(usb_devname_contains, usb_IDserial_contains)** where usb_devname_contains is a string and usb_IDserial_contains is a string.
*	**init_usb_modbus_16bit(usb_devname_contains, usb_IDserial_contains)** where usb_devname_contains is a string and usb_IDserial_contains is a string.

For sending and receiving data via US, refer to the functions for tool connector, all function names replace tool with usb

*	**usb_modbus_write_coil(slave_address, register_address, data)**
*	**usb_modbus_read_discrete(slave_address, register_address)**
*	**usb_modbus_read_coil(slave_address, register_address)**
*	**usb_modbus_write_coils(slave_address, register_address, data)**
*	**usb_modbus_read_discretes(slave_address, register_address, num_of_data)**
*	**usb_modbus_read_coils(slave_address, register_address, num_of_data)**
*	**usb_modbus_write_holding_int(slave_address, register_address, data)**
*	**usb_modbus_write_holding_float(slave_address, register_address, data)**
*	**usb_modbus_read_input_int(slave_address, register_address)**
*	**usb_modbus_read_input_float(slave_address, register_address)**
*	**usb_modbus_read_holding_int(slave_address, register_address)**
*	**usb_modbus_read_holding_float(slave_address, register_address)**
*	**usb_modbus_write_holdings_int(slave_address, register_address, data)**
*	**usb_modbus_write_holdings_float(slave_address, register_address, data)**
*	**usb_modbus_read_inputs_int(slave_address, register_address, num_of_data)**
*	**usb_modbus_read_inputs_float(slave_address, register_address, num_of_data)**
*	**usb_modbus_read_holdings_int(slave_address, register_address, num_of_data)**
*	**usb_modbus_read_holdings_float(slave_address, register_address, num_of_data)**
*	**usb_modbus_write_holdings(slave_address, register_address, data, dtypes)**
*	**usb_modbus_read_inputs(slave_address, register_address, dtypes)**
*	**usb_modbus_read_holdings(slave_address, register_address, dtypes)**

The USB Serial settings can be modified with the functions:

*	**usb_modbus_set_baudrate(baudrate)** where baudrate values are 9600, 19200, 38400, 57600, 115200, 1000000, 2000000, 5000000
*	**usb_modbus_set_bytesize(bytesize)** where bytesize values are 5, 6, 7, 8
*	**usb_modbus_set_parity(parity)** where parity values are "None", "Even", "Odd"
*	**usb_modbus_set_stopbit(stop)** where stop values are 1, 1.5, 2
*	**usb_modbus_set_timeout(timeout)** where timeout is in seconds

## An example script program:

For tool connector:

    init_tool_modbus_64bit()

    tool_modbus_write_coil(1, 0, True)
    bool1 = tool_modbus_read_discrete(1, 0).value
    tool_modbus_write_holding_int(1, 0, 1)
    int1 = tool_modbus_read_input_int(1, 0).value
    tool_modbus_write_holding_float(1, 1, 0.1)
    float1 = tool_modbus_read_input_float(1, 1).value

For USB:

    init_usb_modbus_64bit("ttyACM", "Arduino")

    usb_modbus_write_coil(1, 0, True)
    bool1 = usb_modbus_read_discrete(1, 0).value
    usb_modbus_write_holding_int(1, 0, 1)
    int1 = usb_modbus_read_input_int(1, 0).value
    usb_modbus_write_holding_float(1, 1, 0.1)
    float1 = usb_modbus_read_input_float(1, 1).value

## Additional notes
Slave addresses can only be positive integers starting from 1
Register addresses can only be positive integers

Multiple 16-bit registers can be chained together to transmit 32-bit or 64-bit data, this is selected at instatiation by running init_tool_modbus_64bit for 64-bit data transmission (chaining 4 registers), init_tool_modbus_32bit for 32-bit data transmission (chaining 2 registers), and init_tool_modbus_16bit for 16-bit data transmission (no chaining). By default integers are all signed.

Multiple devices over different USB ports will all be connected via init_usb_modbus_64bit if they fulfill the criteria of the devname containing the 1st string input and the IDserial containing the 2nd string input. Multiple criteria can be used to connect to multiple devices of different types, for example:

    init_usb_modbus_64bit(["ttyACM", "ttyUSB"], ["Arduino", "FTDI"])

Do note that all the tool devices must share the same RS485 settings (baurate, bytesize, parity, stopbit, timeout) and each slave device must have a different slave address. Likewise, all USB devices share the same settings and each slave device would need a different slave address. 

## Change log
2024-10-10  Wilfrid             Added more functions. Renamed init_modbus_communications to init_tool_modbus
2024-10-17  Wilfrid             Extended all functions to error handling versions which return struct.
2024-11-6   Zhi-en      v1.8    Streamline functions, error handling and default number of bits set at instantiation
2024-12-24  Zhi-en      v2.0    Added modbus over USB functionality
2024-12-27  Zhi-en      v2.1    Shift slave address from init to individual functions to allow communication with multiple slaves over the same cable
2025-01-16  Zhi-en      v2.2    Enable reading and writing of multiple coils, discretes, holdings and inputs.