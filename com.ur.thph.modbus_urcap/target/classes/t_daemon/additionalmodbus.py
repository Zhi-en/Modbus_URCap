# adds functionality of function code 23 to minimalmodbus
import minimalmodbus as modbus

# inherits the Instrument class from minimalmodbus
class Instrument(modbus.Instrument):
    def read_write_registers(
        self,
        read_registeraddress,
        read_num_of_registers,
        write_registeraddress,
        write_values
    ):
        """Read and write multiple registers from the slave (instrument). Fc23.
        
        Slave decides if the read/write occurs in holdings or inputs.
        Writing is done before reading in the slave.

        Args:
            * read_registeraddress (int): The starting read register's address
            * read_num_of_registers (int): Number of registers to read
            * write_registeraddress (int): The starting write register's address
            * write_values (list of int or bool): 0 or 1, or True or False. The first
              value in the list is for the bit at the given address.

        Returns:
            The register data (a list of int). The first value in the list is for
            the register at the given address.

        Raises:
            TypeError, ValueError, ModbusException,
            serial.SerialException (inherited from IOError)

        """
        modbus._check_registeraddress(read_registeraddress)
        modbus._check_registeraddress(write_registeraddress)
        modbus._check_int(
            read_num_of_registers,
            minvalue=1,
            maxvalue=modbus._MAX_NUMBER_OF_REGISTERS_TO_READ,
            description="number of registers",
        )
        if not isinstance(write_values, list):
            raise TypeError(
                'The "values parameter" must be a list. Given: {0!r}'.format(values)
            )
        modbus._check_int(
            len(write_values),
            minvalue=1,
            maxvalue=modbus._MAX_NUMBER_OF_REGISTERS_TO_WRITE,
            description="length of input list",
        )

        # Create payload
        payload_to_slave = _create_payload_fc23(
            read_registeraddress,
            read_num_of_registers,
            write_registeraddress,
            len(write_values),
            write_values,
        )

        # Communicate with instrument
        payload_from_slave = self._perform_command(23, payload_to_slave)

        # Parse response payload
        return _parse_payload(
            payload_from_slave,
            23,
            read_registeraddress,
            None,
            0,
            read_num_of_registers,
            0,
            False,
            0,
            modbus._PAYLOADFORMAT_REGISTERS,
        )

    # #################################### #
    # Communication implementation details #
    # #################################### #

    def _perform_command(self, functioncode, payload_to_slave):
        # no changes in this function, but replicated here to include changes in _predict_response_size function
        """Perform the command having the *functioncode*.

        Args:
            * functioncode (int): The function code for the command to be performed.
              Can for example be 'Write register' = 16.
            * payload_to_slave (str): Data to be transmitted to the slave (will be
              embedded in slaveaddress, CRC etc)

        Returns:
            The extracted data payload from the slave (a string). It has been
            stripped of CRC etc.

        Raises:
            TypeError, ValueError, ModbusException,
            serial.SerialException (inherited from IOError)

        Makes use of the :meth:`_communicate` method. The request is generated
        with the :func:`_embed_payload` function, and the parsing of the
        response is done with the :func:`_extract_payload` function.

        """
        DEFAULT_NUMBER_OF_BYTES_TO_READ = 1000

        modbus._check_functioncode(functioncode, None)
        modbus._check_string(payload_to_slave, description="payload")

        # Build request
        request = modbus._embed_payload(
            self.address, self.mode, functioncode, payload_to_slave
        )

        # Calculate number of bytes to read
        number_of_bytes_to_read = DEFAULT_NUMBER_OF_BYTES_TO_READ
        if self.precalculate_read_size:
            try:
                number_of_bytes_to_read = _predict_response_size(
                    self.mode, functioncode, payload_to_slave
                )
            except Exception:
                if self.debug:
                    template = (
                        "Could not precalculate response size for Modbus {} mode. "
                        + "Will read {} bytes. Request: {!r}"
                    )
                    self._print_debug(
                        template.format(self.mode, number_of_bytes_to_read, request)
                    )

        # Communicate
        response = self._communicate(request, number_of_bytes_to_read)

        # Extract payload
        payload_from_slave = modbus._extract_payload(
            response, self.address, self.mode, functioncode
        )
        return payload_from_slave


# ################ #
# Payload handling #
# ################ #


def _create_payload_fc23(
    read_registeraddress,
    read_num_of_registers,
    write_registeraddress,
    write_num_of_registers,
    write_values
):
    """Create the payload for fc23.

    Error checking should have been done before calling this function.

    """
    registerdata = modbus._valuelist_to_bytestring(write_values, write_num_of_registers)
    return (
        modbus._num_to_twobyte_string(read_registeraddress)
        + modbus._num_to_twobyte_string(read_num_of_registers)
        + modbus._num_to_twobyte_string(write_registeraddress)
        + modbus._num_to_twobyte_string(write_num_of_registers)
        + modbus._num_to_onebyte_string(len(registerdata))
        + registerdata
    )


def _parse_payload(
    payload,
    functioncode,
    registeraddress,
    value,
    number_of_decimals,
    number_of_registers,
    number_of_bits,
    signed,
    byteorder,
    payloadformat,
):
    # added fc23 to register reading fc list, also replicated here to include changes in _check_response_payload function
    _check_response_payload(
        payload,
        functioncode,
        registeraddress,
        value,
        number_of_decimals,
        number_of_registers,
        number_of_bits,
        signed,
        byteorder,
        payloadformat,
    )

    if functioncode in [1, 2]:
        registerdata = payload[modbus._NUMBER_OF_BYTES_BEFORE_REGISTERDATA:]
        if payloadformat == modbus._PAYLOADFORMAT_BIT:
            return modbus._bytestring_to_bits(registerdata, number_of_bits)[0]
        elif payloadformat == modbus._PAYLOADFORMAT_BITS:
            return modbus._bytestring_to_bits(registerdata, number_of_bits)

    if functioncode in [3, 4, 23]:
        registerdata = payload[modbus._NUMBER_OF_BYTES_BEFORE_REGISTERDATA:]
        if payloadformat == modbus._PAYLOADFORMAT_STRING:
            return modbus._bytestring_to_textstring(registerdata, number_of_registers)

        elif payloadformat == modbus._PAYLOADFORMAT_LONG:
            return modbus._bytestring_to_long(
                registerdata, signed, number_of_registers, byteorder
            )

        elif payloadformat == modbus._PAYLOADFORMAT_FLOAT:
            return modbus._bytestring_to_float(registerdata, number_of_registers, byteorder)

        elif payloadformat == modbus._PAYLOADFORMAT_REGISTERS:
            return modbus._bytestring_to_valuelist(registerdata, number_of_registers)

        elif payloadformat == modbus._PAYLOADFORMAT_REGISTER:
            return modbus._twobyte_string_to_num(
                registerdata, number_of_decimals, signed=signed
            )


# ###################################### #
# Serial communication utility functions #
# ###################################### #


def _predict_response_size(mode, functioncode, payload_to_slave):
    # added fc23 to register reading fc list
    """Calculate the number of bytes that should be received from the slave.

    Args:
     * mode (str): The modbus protcol mode (MODE_RTU or MODE_ASCII)
     * functioncode (int): Modbus function code.
     * payload_to_slave (str): The raw request that is to be sent to the slave
       (not hex encoded string)

    Returns:
        The preducted number of bytes (int) in the response.

    Raises:
        ValueError, TypeError.

    """
    MIN_PAYLOAD_LENGTH = 4  # For implemented functioncodes here
    BYTERANGE_FOR_GIVEN_SIZE = slice(2, 4)  # Within the payload

    NUMBER_OF_PAYLOAD_BYTES_IN_WRITE_CONFIRMATION = 4
    NUMBER_OF_PAYLOAD_BYTES_FOR_BYTECOUNTFIELD = 1

    RTU_TO_ASCII_PAYLOAD_FACTOR = 2

    NUMBER_OF_RTU_RESPONSE_STARTBYTES = 2
    NUMBER_OF_RTU_RESPONSE_ENDBYTES = 2
    NUMBER_OF_ASCII_RESPONSE_STARTBYTES = 5
    NUMBER_OF_ASCII_RESPONSE_ENDBYTES = 4

    # Argument validity testing
    modbus._check_mode(mode)
    modbus._check_functioncode(functioncode, None)
    modbus._check_string(payload_to_slave, description="payload", minlength=MIN_PAYLOAD_LENGTH)

    # Calculate payload size
    if functioncode in [5, 6, 15, 16]:
        response_payload_size = NUMBER_OF_PAYLOAD_BYTES_IN_WRITE_CONFIRMATION

    elif functioncode in [1, 2, 3, 4, 23]:
        given_size = modbus._twobyte_string_to_num(payload_to_slave[BYTERANGE_FOR_GIVEN_SIZE])
        if functioncode in [1, 2]:
            # Algorithm from MODBUS APPLICATION PROTOCOL SPECIFICATION V1.1b
            number_of_inputs = given_size
            response_payload_size = (
                NUMBER_OF_PAYLOAD_BYTES_FOR_BYTECOUNTFIELD
                + number_of_inputs // 8
                + (1 if number_of_inputs % 8 else 0)
            )

        elif functioncode in [3, 4, 23]:
            number_of_registers = given_size
            response_payload_size = (
                NUMBER_OF_PAYLOAD_BYTES_FOR_BYTECOUNTFIELD
                + number_of_registers * modbus._NUMBER_OF_BYTES_PER_REGISTER
            )

    else:
        raise ValueError(
            "Wrong functioncode: {}. The payload is: {!r}".format(
                functioncode, payload_to_slave
            )
        )

    # Calculate number of bytes to read
    if mode == modbus.MODE_ASCII:
        return (
            NUMBER_OF_ASCII_RESPONSE_STARTBYTES
            + response_payload_size * RTU_TO_ASCII_PAYLOAD_FACTOR
            + NUMBER_OF_ASCII_RESPONSE_ENDBYTES
        )
    else:
        return (
            NUMBER_OF_RTU_RESPONSE_STARTBYTES
            + response_payload_size
            + NUMBER_OF_RTU_RESPONSE_ENDBYTES
        )


# ######################## #
# Error checking functions #
# ######################## #


def _check_response_payload(
    payload,
    functioncode,
    registeraddress,
    value,
    number_of_decimals,
    number_of_registers,
    number_of_bits,
    signed,
    byteorder,  # Not used. For keeping same signature as _parse_payload()
    payloadformat,  # Not used. For keeping same signature as _parse_payload()
):
    # added fc23 to bit reading fc list
    if functioncode in [1, 2, 3, 4, 23]:
        modbus._check_response_bytecount(payload)

    if functioncode in [5, 6, 15, 16]:
        modbus._check_response_registeraddress(payload, registeraddress)

    if functioncode == 5:
        modbus._check_response_writedata(payload, modbus._bit_to_bytestring(value))
    elif functioncode == 6:
        modbus._check_response_writedata(
            payload, modbus._num_to_twobyte_string(value, number_of_decimals, signed=signed)
        )
    elif functioncode == 15:
        # response number of bits
        modbus._check_response_number_of_registers(payload, number_of_bits)

    elif functioncode == 16:
        modbus._check_response_number_of_registers(payload, number_of_registers)

    # Response for read bits
    if functioncode in [1, 2]:
        registerdata = payload[modbus._NUMBER_OF_BYTES_BEFORE_REGISTERDATA:]
        expected_number_of_bytes = modbus._calculate_number_of_bytes_for_bits(number_of_bits)
        if len(registerdata) != expected_number_of_bytes:
            raise modbus.InvalidResponseError(
                "The data length is wrong for payloadformat BIT/BITS."
                + " Expected: {} Actual: {}.".format(
                    expected_number_of_bytes, len(registerdata)
                )
            )

    # Response for read registers
    if functioncode in [3, 4, 23]:
        registerdata = payload[modbus._NUMBER_OF_BYTES_BEFORE_REGISTERDATA:]
        number_of_register_bytes = number_of_registers * modbus._NUMBER_OF_BYTES_PER_REGISTER
        if len(registerdata) != number_of_register_bytes:
            raise modbus.InvalidResponseError(
                "The register data length is wrong. "
                + "Registerdata: {!r} bytes. Expected: {!r}.".format(
                    len(registerdata), number_of_register_bytes
                )
            )