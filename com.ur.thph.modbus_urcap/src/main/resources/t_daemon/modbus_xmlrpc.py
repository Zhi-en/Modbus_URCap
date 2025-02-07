#!/usr/bin/env python

import socket
import struct
import time
import logging as Logger
import os, sys
currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)
import additionalmodbus as modbus
import serial
import subprocess

try:
    from SimpleXMLRPCServer import SimpleXMLRPCServer   # python 2
except ModuleNotFoundError:
    from xmlrpc.server import SimpleXMLRPCServer    # python 3
try:
    from SocketServer import ThreadingMixIn     # python 2
except ModuleNotFoundError:
    from socketserver import ThreadingMixIn     # python 3

isShowing = False
LOCALHOST = "127.0.0.1"

# instrument/slave 1
instrument_tool = {}
baudrate_tool = 115200
bytesize_tool = 8
parity_tool = "None"
stopbits_tool = 1
timeout_tool = 1   # seconds
num_of_registers_tool = 4  # 4 for 64-bit ints and floats using holding and input registers. 2 for 32-bit ints and floats, 1 bit 16-bit ints only
error_handling_tool = True

# instrument/slave 2
instrument_usb = {}
baudrate_usb = 115200
bytesize_usb = 8
parity_usb = "None"
stopbits_usb = 1
timeout_usb = 1   # seconds
num_of_registers_usb = 4  # 4 for 64-bit ints and floats using holding and input registers. 2 for 32-bit ints and floats, 1 bit 16-bit ints only
error_handling_usb = True


def isReachable():
    return True

''' helper functions for packing and unpacking ints and floats'''
def pack_registers(val_ls, dtype_ls):
    mapping_conversion = {
        "int16": ">h",
        "uint16": ">H",
        "int32": ">i",
        "uint32": ">I",
        "float": ">f",
        "float32": ">f",
        "int64": ">q",
        "uint64": ">Q",
        "double": ">d",
        "float64": ">d",
    }

    if len(dtype_ls) != len(val_ls):
        raise IndexError(
            "The length of the dtype list ({}) shoould be equal to the length of the values to write ({})".format(len(dtype), len(val_ls))
        )
    for dtype in dtype_ls:
        if dtype not in list(mapping_conversion.keys()):
            raise TypeError(
                "Unexpected dtype uncountered: {}".format(dtype)
            )
            
    formatcode = [mapping_conversion[dtype] for dtype in dtype_ls]
    bs_ls = [struct.pack(formatc, val) for val, formatc in zip(val_ls, formatcode)]    # convert relevant format to bytestring
    bs_ls_16bit = []
    for bs in bs_ls:
        bs_ls_16bit.extend([bs[i:i+2] for i in range(0, len(bs), 2)])   # split all bytestrings into 16bit chunks

    return [struct.unpack(">H", bytestring)[0] for bytestring in bs_ls_16bit]  # convert bytestrings to uint16


def unpack_registers(val_ls, dtype_ls):
    mapping_conversion = {
        "int16": ">h",
        "uint16": ">H",
        "int32": ">i",
        "uint32": ">I",
        "float": ">f",
        "float32": ">f",
        "int64": ">q",
        "uint64": ">Q",
        "double": ">d",
        "float64": ">d",
    }
    mapping_length = {
        "int16": 1,
        "uint16": 1,
        "int32": 2,
        "uint32": 2,
        "float": 2,
        "float32": 2,
        "int64": 4,
        "uint64": 4,
        "double": 4,
        "float64": 4,
    }

    for dtype in dtype_ls:
        if dtype not in list(mapping_conversion.keys()):
            raise TypeError(
                "Unexpected dtype uncountered: {}".format(dtype)
            )

    if len(val_ls) != sum([mapping_length[dtype] for dtype in dtype_ls]):
        raise IndexError(
            "The length of register list received {} does not match the expected length {}".format(len(bin_str), last_read)
        )
            
    bs_ls = [struct.pack(">H", val) for val in val_ls]  # convert uint16 to bytestrings
    last_read = 0
    out_ls = []
    for dtype in dtype_ls:
        read_len = mapping_length[dtype]
        bytestring = b''.join(bs_ls[last_read:last_read+read_len])
        out_ls.append(struct.unpack(mapping_conversion[dtype], bytestring)[0])
        last_read += read_len

    return out_ls

def pack_to_uint16(val_ls, dtype_ls):
    mapping_conversion = {
        "bool": bool,
        "bit": bool,
        "uint8": np.uint8,
    }
    mapping_length = {
        "bool": 1,
        "bit": 1,
        "uint8": 8,
    }

    if len(dtype_ls) != len(val_ls):
        raise IndexError(
            "The length of the dtype list ({}) shoould be equal to the length of the values to write ({})".format(len(dtype), len(val_ls))
        )
    for dtype in dtype_ls:
        if dtype not in list(mapping_conversion.keys()):
            raise TypeError(
                "Unexpected dtype uncountered: {}".format(dtype)
            )
    if sum([mapping_length[dtype] for dtype in dtype_ls]) > 16:
        raise IndexError(
            "The expected output bit length is {}, should be 16 or less".format(sum([mapping_length[dtype] for dtype in dtype_ls]))
        )

    bin_str = ''
    for val, dtype in zip(val_ls, dtype_ls):
        bin_str += bin(mapping_conversion[dtype](val))[2:].zfill(mapping_length[dtype])     # convert each val to binary and add to binary str
    bin_str += '0'*(16-len(bin_str))    # pad the remaining empty bits with 0
    return int(bin_str, 2)  # convert to integer and return

def unpack_from_uint16(val, dtype_ls):
    mapping_conversion = {
        "bool": bool,
        "bit": bool,
        "uint8": np.uint8,
    }
    mapping_length = {
        "bool": 1,
        "bit": 1,
        "uint8": 8,
    }
    if not isinstance(val, int):
        raise TypeError(
            "Expected uint16, given: {}".format(val)
        )
    if val < 0 or val > 65535:
        raise TypeError(
            "Expected uint16, given: {}".format(val)
        )
    for dtype in dtype_ls:
        if dtype not in list(mapping_conversion.keys()):
            raise TypeError(
                "Unexpected dtype uncountered: {}".format(dtype)
            )
    if sum([mapping_length[dtype] for dtype in dtype_ls]) > 16:
        raise IndexError(
            "The expected output bit length is {}, should be 16 or less".format(sum([mapping_length[dtype] for dtype in dtype_ls]))
        )

    bin_str = bin(val)[2:].zfill(16)    # convert input to binary
    last_read = 0
    out_ls = []
    for dtype in dtype_ls:
        read_len = mapping_length[dtype]
        bin_val = bin_str[last_read:last_read+read_len]
        out_ls.append(int(bin_val, 2))
        last_read += read_len
    return out_ls


''' functions for tool modbus '''
def init_tool_modbus_64bit(slave_address):
    init_tool_modbus(slave_address)
    global num_of_registers_tool
    num_of_registers_tool = 4
    return {"value":True, "error": "", "error_flag": False}

def init_tool_modbus_32bit(slave_address):
    init_tool_modbus(slave_address)
    global num_of_registers_tool
    num_of_registers_tool = 2
    return {"value":True, "error": "", "error_flag": False}

def init_tool_modbus_16bit(slave_address):
    init_tool_modbus(slave_address)
    global num_of_registers_tool
    num_of_registers_tool = 1
    return {"value":True, "error": "", "error_flag": False}

def init_tool_modbus_no_error_handling_64bit(slave_address):
    init_tool_modbus_64bit(slave_address)
    global error_handling_tool
    error_handling_tool = False
    return True

def init_tool_modbus_no_error_handling_32bit(slave_address):
    init_tool_modbus_32bit(slave_address)
    global error_handling_tool
    error_handling_tool = False
    return True

def init_tool_modbus_no_error_handling_16bit(slave_address):
    init_tool_modbus_16bit(slave_address)
    global error_handling_tool
    error_handling_tool = False
    return True

def init_tool_modbus(slave_address):
    global instrument_tool
    instrument_tool[slave_address] = modbus.Instrument('/dev/ttyTool', slave_address)
    
    instrument_tool[slave_address].serial.baudrate = baudrate_tool
    instrument_tool[slave_address].serial.bytesize = bytesize_tool
    if parity_tool == "None":
        instrument_tool[slave_address].serial.parity = serial.PARITY_NONE
    elif parity_tool == "Even":
        instrument_tool[slave_address].serial.parity = serial.PARITY_EVEN
    elif parity_tool == "Odd":
        instrument_tool[slave_address].serial.parity = serial.PARITY_ODD
    instrument_tool[slave_address].serial.stopbits = stopbits_tool
    instrument_tool[slave_address].serial.timeout = timeout_tool
    global error_handling_tool
    error_handling_tool = True


''' Functions for modifying default settings '''
def tool_modbus_set_baudrate(baudrate):
    if instrument_tool:
        for instrument in instrument_tool.values():
            instrument.serial.baudrate = baudrate
            result = {"value":True, "error": "", "error_flag": False}
    else:
        result = {"value":False, "error": "No modbus slaves connected via tool connector", "error_flag": True}

    if error_handling_tool:
        return result
    else:
        return result['value']

def tool_modbus_set_bytesize(bytesize):
    if bytesize in (5, 6, 7, 8):
        if instrument_tool:
            for instrument in instrument_tool.values():
                instrument.serial.bytesize = bytesize
                result = {"value":True, "error": "", "error_flag": False}
        else:
            result = {"value":False, "error": "No modbus slaves connected via tool connector", "error_flag": True}
    else:
        result = {"value":False, "error": "Invalid bytesize", "error_flag": True}

    if error_handling_tool:
        return result
    else:
        return result['value']

def tool_modbus_set_parity(parity):
    parity_map = {"None": serial.PARITY_NONE, "Even": serial.PARITY_EVEN, "Odd": serial.PARITY_ODD}
    if parity in parity_map.keys():
        if instrument_tool:
            for instrument in instrument_tool.values():
                instrument.serial.parity = parity_map[parity]
                result = {"value":True, "error": "", "error_flag": False}
        else:
            result = {"value":False, "error": "No modbus slaves connected via tool connector", "error_flag": True}
    else:
        result = {"value":False, "error": "Invalid parity", "error_flag": True}

    if error_handling_tool:
        return result
    else:
        return result['value']

def tool_modbus_set_stopbits(stopbits):
    if stopbits in (1, 1.5, 2):
        if instrument_tool:
            for instrument in instrument_tool.values():
                instrument.serial.stopbits = stopbits
                result = {"value":True, "error": "", "error_flag": False}
        else:
            result = {"value":False, "error": "No modbus slaves connected via tool connector", "error_flag": True}
    else:
        result = {"value":False, "error": "Invalid stopbits", "error_flag": True}

    if error_handling_tool:
        return result
    else:
        return result['value']

def tool_modbus_set_timeout(timeout):
    if instrument_tool:
        for instrument in instrument_tool.values():
            instrument.serial.timeout = timeout
            result = {"value":True, "error": "", "error_flag": False}
    else:
        result = {"value":False, "error": "No modbus slaves connected via tool connector", "error_flag": True}

    if error_handling_tool:
        return result
    else:
        return result['value']


''' Function for checking if connected in no error handling mode '''
def tool_modbus_check_connection(slave_address, register_type, register):
    if register_type == "coil":
        result = tool_modbus_read_coil(slave_address, register_address)
    elif register_type == "discrete":
        result = tool_modbus_read_discrete(slave_address, register_address)
    elif register_type == "holding":
        result = tool_modbus_read_holding_float(slave_address, register_address)
    elif register_type == "input":
        result = tool_modbus_read_input_float(slave_address, register_address)
    if type(result) == str:
        return False
    else:
        return True


''' Functions for bit communication '''
def tool_modbus_write_coil(slave_address, register_address, data):
    '''Function to write single BOOL to slave'''
    result = {"value": data, "error": "", "error_flag": False}
    if slave_address not in instrument_tool:
        result["error"] = "Slave {} does not exist.".format(slave_address)
        result["error_flag"] = True
    else:
        try:
            data = bool(data)
            instrument_tool[slave_address].write_bit(register_address, data)
        except Exception as e:
            Logger.error("data: %s", data)
            Logger.error("Error in modbus write method", exc_info=True)
            result["error"] = repr(e)
            result["error_flag"] = True
    if error_handling_tool:
        return result
    elif result["error_flag"]:
        return result["error"]
    else:
        return True

def tool_modbus_read_discrete(slave_address, register_address):
    '''Function to read single BOOL from slave'''
    result = {"value": False, "error": "", "error_flag": False}
    if slave_address not in instrument_tool:
        result["error"] = "Slave {} does not exist.".format(slave_address)
        result["error_flag"] = True
    else:
        try:
            value = instrument_tool[slave_address].read_bit(register_address, functioncode=2)
            result["value"] = bool(value)
        except Exception as e:
            Logger.error("Error in modbus read method", exc_info=True)
            result["error"] = repr(e)
            result["error_flag"] = True
    if error_handling_tool:
        return result
    elif result["error_flag"]:
        return result["error"]
    else:
        return result["value"]

def tool_modbus_read_coil(slave_address, register_address):
    '''Function to read back BOOL from master'''
    result = {"value": False, "error": "", "error_flag": False}
    if slave_address not in instrument_tool:
        result["error"] = "Slave {} does not exist.".format(slave_address)
        result["error_flag"] = True
    else:
        try:
            value = instrument_tool[slave_address].read_bit(register_address, functioncode=1)
            result["value"] = bool(value)
        except Exception as e:
            Logger.error("Error in modbus read method", exc_info=True)
            result["error"] = repr(e)
            result["error_flag"] = True
    if error_handling_tool:
        return result
    elif result["error_flag"]:
        return result["error"]
    else:
        return result["value"]

def tool_modbus_write_coils(slave_address, register_address, data):
    '''Function to write multiple BOOL to slave in list format or single BOOL in BOOL or list format'''
    result = {"value": data, "error": "", "error_flag": False}
    if not isinstance(data, list):
        data = [data]
    if slave_address not in instrument_tool:
        result["error"] = "Slave {} does not exist.".format(slave_address)
        result["error_flag"] = True
    else:
        try:
            data = list(map(bool,data))
            instrument_tool[slave_address].write_bits(register_address, data)
        except Exception as e:
            for i in range(len(data)):
                Logger.error("val{}:{}".format(i,data[i]))
            Logger.error("Error in modbus write method", exc_info=True)
            result["error"] = repr(e).replace('"',"'")      # replace all " with ' to prevent UR string errors
            result["error_flag"] = True
    if error_handling_tool:
        return result
    elif result["error_flag"]:
        return result["error"]
    else:
        return True

def tool_modbus_read_discretes(slave_address, register_address, num_of_registers):
    '''Function to read multiple BOOL from slave in list format or single BOOL as BOOL'''
    result = {"value": [False]*num_of_registers, "error": "", "error_flag": False}
    if slave_address not in instrument_tool:
        result["error"] = "Slave {} does not exist.".format(slave_address)
        result["error_flag"] = True
    else:
        try:
            value = instrument_tool[slave_address].read_bits(register_address, num_of_registers, functioncode=2)
            if num_of_registers == 1:
                result["value"] = bool(value[0])
            else:
                result["value"] = list(map(bool,value))
        except Exception as e:
            Logger.error("Error in modbus read method", exc_info=True)
            result["error"] = repr(e).replace('"',"'")      # replace all " with ' to prevent UR string errors
            result["error_flag"] = True
    if error_handling_tool:
        return result
    elif result["error_flag"]:
        return result["error"]
    else:
        return result["value"]

def tool_modbus_read_coils(slave_address, register_address, num_of_registers):
    '''Function to read back multiple BOOL from master in list format or single BOOL as BOOL'''
    result = {"value": [False]*num_of_registers, "error": "", "error_flag": False}
    if slave_address not in instrument_tool:
        result["error"] = "Slave {} does not exist.".format(slave_address)
        result["error_flag"] = True
    else:
        try:
            value = instrument_tool[slave_address].read_bits(register_address, num_of_registers, functioncode=1)
            if num_of_registers == 1:
                result["value"] = bool(value[0])
            else:
                result["value"] = list(map(bool,value))
        except Exception as e:
            Logger.error("Error in modbus read method", exc_info=True)
            result["error"] = repr(e).replace('"',"'")      # replace all " with ' to prevent UR string errors
            result["error_flag"] = True
    if error_handling_tool:
        return result
    elif result["error_flag"]:
        return result["error"]
    else:
        return result["value"]


''' Functions for 16/32/64 bit communication '''
def tool_modbus_read_write_registers(slave_address, read_register_address, read_dtype, write_register_address, write_data, write_dtype):
    '''Function to write and read multiple types of data to slave. Underlying communication uses registers'''
    if not isinstance(write_data, list):
        write_data = [write_data]
    if not isinstance(write_dtype, list):
        write_dtype = [write_dtype]
    if not isinstance(read_dtype, list):
        read_dtype = [read_dtype]
    read_num_of_values = len(read_dtype)
    if read_num_of_values == 1:
        result = {"value": 0, "error": "", "error_flag": False}
    else:
        result = {"value": [0]*read_num_of_values, "error": "", "error_flag": False}
    try:
        for i in range(len(write_data)):
            if write_dtype[i] in ["int", "uint"]:
                write_data[i] = int(write_data[i])
            elif write_dtype[i] in ["float"]:
                write_data[i] = float(write_data[i])
        write_dtype = [dtype + str(16*num_of_registers_tool) for dtype in write_dtype]
        read_dtype = [dtype + str(16*num_of_registers_tool) for dtype in read_dtype]
    except Exception as e:
        result["error"] = repr(e).replace('"',"'")
    else:
        if slave_address not in instrument_tool:
            result["error"] = "Slave {} does not exist.".format(slave_address)
            result["error_flag"] = True
        else:
            try:
                write_ls = pack_registers(write_data, write_dtype)
                read_ls = instrument_tool[slave_address].read_write_registers(
                    read_register_address*num_of_registers_tool,
                    read_num_of_values*num_of_registers_tool,
                    write_register_address*num_of_registers_tool,
                    write_ls)
                value = unpack_registers(read_ls, read_dtype)
                if read_num_of_values == 1:
                    result["value"] = value[0]
                else:
                    result["value"] = value
            except Exception as e:
                for i in range(len(write_data)):
                    Logger.error("val{}: {}".format(i,write_data[i]))
                Logger.error("Error in modbus write method", exc_info=True)
                result["error"] = repr(e).replace('"',"'")      # replace all " with ' to prevent UR string errors
                result["error_flag"] = True
    if error_handling_tool:
        return result
    elif result["error_flag"]:
        return result["error"]
    else:
        return result["value"]


def tool_modbus_write_holdings(slave_address, register_address, data, dtype):
    '''Function to write multiple INT16/INT32/INT64/FLOAT32/FLOAT64 to slave using 1/2/4 registers. Maps register_address to multiples of 1/2/4 to ensure no overlap.
    length of data should be equal to length of dtype'''
    result = {"value": data, "error": "", "error_flag": False}
    if not isinstance(data, list):
        data = [data]
    if not isinstance(dtype, list):
        dtype = [dtype]
    try:
        for i in range(len(data)):
            if dtype[i] in ["int", "uint", int]:
                data[i] = int(data[i])
            elif dtype[i] in ["float", float]:
                data[i] = float(data[i])
        dtype = [dtypes + str(16*num_of_registers_tool) for dtypes in dtype]
    except Exception as e:
        result["error"] = repr(e).replace('"',"'")
    else:
        if slave_address not in instrument_tool:
            result["error"] = "Slave {} does not exist.".format(slave_address)
            result["error_flag"] = True
        else:
            try:
                val_ls = pack_registers(data, dtype)
                instrument_tool[slave_address].write_registers(register_address*num_of_registers_tool, val_ls)
            except Exception as e:
                for i in range(len(data)):
                    Logger.error("val{}: {}".format(i,data[i]))
                Logger.error("Error in modbus write method", exc_info=True)
                result["error"] = repr(e).replace('"',"'")      # replace all " with ' to prevent UR string errors
                result["error_flag"] = True
    if error_handling_tool:
        return result
    elif result["error_flag"]:
        return result["error"]
    else:
        return True

def tool_modbus_read_inputs(slave_address, register_address, dtype):
    '''Function to read INT16/INT32/INT64/FLOAT32/FLOAT64 from slave using 1/2/4 registers. Maps register_address to multiples of 1/2/4 to ensure no overlap.
    uses length of dtype as number of registers to read'''
    if not isinstance(dtype, list):
        dtype = [dtype]
    num_of_values = len(dtype)
    if num_of_values == 1:
        result = {"value": 0, "error": "", "error_flag": False}
    else:
        result = {"value": [0]*num_of_values, "error": "", "error_flag": False}
    if slave_address not in instrument_tool:
        result["error"] = "Slave {} does not exist.".format(slave_address)
        result["error_flag"] = True
    else:
        try:
            dtype = [dtypes + str(16*num_of_registers_tool) for dtypes in dtype]
            val_ls = instrument_tool[slave_address].read_registers(register_address*num_of_registers_tool, num_of_values*num_of_registers_tool, functioncode=4)
            value = unpack_registers(val_ls, dtype)
            if num_of_values == 1:
                result["value"] = value[0]
            else:
                result["value"] = value
        except Exception as e:
            Logger.error("Error in modbus read method", exc_info=True)
            result["error"] = repr(e).replace('"',"'")      # replace all " with ' to prevent UR string errors
            result["error_flag"] = True
    if error_handling_tool:
        return result
    elif result["error_flag"]:
        return result["error"]
    else:
        return result["value"]

def tool_modbus_read_holdings(slave_address, register_address, dtype):
    '''Function to read back INT16/INT32/INT64/FLOAT32/FLOAT64 from master using 1/2/4 registers. Maps register_address to multiples of 1/2/4 to ensure no overlap.
    uses length of dtype as number of registers to read'''
    if not isinstance(dtype, list):
        dtype = [dtype]
    num_of_values = len(dtype)
    if num_of_values == 1:
        result = {"value": 0, "error": "", "error_flag": False}
    else:
        result = {"value": [0]*num_of_values, "error": "", "error_flag": False}
    if slave_address not in instrument_tool:
        result["error"] = "Slave {} does not exist.".format(slave_address)
        result["error_flag"] = True
    else:
        try:
            dtype = [dtypes + str(16*num_of_registers_tool) for dtypes in dtype]
            val_ls = instrument_tool[slave_address].read_registers(register_address*num_of_registers_tool, num_of_values*num_of_registers_tool, functioncode=3)
            value = unpack_registers(val_ls, dtype)
            if num_of_values == 1:
                result["value"] = value[0]
            else:
                result["value"] = value
        except Exception as e:
            Logger.error("Error in modbus read method", exc_info=True)
            result["error"] = repr(e).replace('"',"'")      # replace all " with ' to prevent UR string errors
            result["error_flag"] = True
    if error_handling_tool:
        return result
    elif result["error_flag"]:
        return result["error"]
    else:
        return result["value"]


def tool_modbus_write_holding_int(slave_address, register_address, data):
    '''Function to write INT16/INT32/INT64 to slave using 1/2/4 registers. Maps register_address to multiples of 1/2/4 to ensure no overlap.'''
    result = {"value": data, "error": "", "error_flag": False}
    if slave_address not in instrument_tool:
        result["error"] = "Slave {} does not exist.".format(slave_address)
        result["error_flag"] = True
    else:
        try:
            data = int(data)
            dtype = "int" + str(16*num_of_registers_tool)
            val_ls = pack_registers([data], [dtype])
            instrument_tool[slave_address].write_registers(register_address*num_of_registers_tool, val_ls)
        except Exception as e:
            Logger.error("data: %s", data)
            Logger.error("Error in modbus write method", exc_info=True)
            result["error"] =  repr(e)
            result["error_flag"] = True
    if error_handling_tool:
        return result
    elif result["error_flag"]:
        return result["error"]
    else:
        return True

def tool_modbus_write_holding_float(slave_address, register_address, data):
    '''Function to write FLOAT32/FLOAT64 to slave using 2/4 registers. Maps register_address to multiples of 2/4 to ensure no overlap. Will return error if num_of_registers = 1 '''
    result = {"value": data, "error": "", "error_flag": False}
    if num_of_registers_tool <2:
        result["error"] =  "16-bit does not support float types"
        result["error_flag"] = True
    elif slave_address not in instrument_tool:
        result["error"] = "Slave {} does not exist.".format(slave_address)
        result["error_flag"] = True
    else:
        try:
            instrument_tool[slave_address].write_float(register_address*num_of_registers_tool, data, number_of_registers=num_of_registers_tool)
        except Exception as e:
            Logger.error("data: %s", data)
            Logger.error("Error in modbus write method", exc_info=True)
            result["error"] =  repr(e)
            result["error_flag"] = True
    if error_handling_tool:
        return result
    elif result["error_flag"]:
        return result["error"]
    else:
        True

def tool_modbus_read_input_int(slave_address, register_address):
    '''Function to read INT16/INT32/INT64 from slave using 1/2/4 registers. Maps register_address to multiples of 1/2/4 to ensure no overlap.'''
    result = {"value": 0, "error": "", "error_flag": False}
    if slave_address not in instrument_tool:
        result["error"] = "Slave {} does not exist.".format(slave_address)
        result["error_flag"] = True
    else:
        try:
            dtype = "int" + str(16*num_of_registers_tool)
            val_ls = instrument_tool[slave_address].read_registers(register_address*num_of_registers_tool, num_of_registers_tool, functioncode=4)
            value = unpack_registers(val_ls, [dtype])
            result["value"] = int(value[0])
        except Exception as e:
            Logger.error("Error in modbus read method", exc_info=True)
            result["error"] =  repr(e)
            result["error_flag"] = True
    if error_handling_tool:
        return result
    elif result["error_flag"]:
        return result["error"]
    else:
        return result["value"]

def tool_modbus_read_input_float(slave_address, register_address):
    '''Function to read FLOAT32/FLOAT64 from slave using 2/4 registers. Maps register_address to multiples of 2/4 to ensure no overlap. Will return error if num_of_registers = 1 '''
    result = {"value": 0.0, "error": "", "error_flag": False}
    if num_of_registers_tool <2:
        result["error"] =  "16-bit does not support float types"
        result["error_flag"] = True
    elif slave_address not in instrument_tool:
        result["error"] = "Slave {} does not exist.".format(slave_address)
        result["error_flag"] = True
    else:
        try:
            result["value"] = instrument_tool[slave_address].read_float(register_address*num_of_registers_tool, number_of_registers=num_of_registers_tool, functioncode=4)
        except Exception as e:
            Logger.error("Error in modbus read method", exc_info=True)
            result["error"] =  repr(e)
            result["error_flag"] = True
    if error_handling_tool:
        return result
    elif result["error_flag"]:
        return result["error"]
    else:
        return result["value"]

def tool_modbus_read_holding_int(slave_address, register_address):
    '''Function to read back INT16/INT32/INT64 from master using 1/2/4 registers. Maps register_address to multiples of 1/2/4 to ensure no overlap.'''
    result = {"value": 0, "error": "", "error_flag": False}
    if slave_address not in instrument_tool:
        result["error"] = "Slave {} does not exist.".format(slave_address)
        result["error_flag"] = True
    else:
        try:
            dtype = "int" + str(16*num_of_registers_tool)
            val_ls = instrument_tool[slave_address].read_registers(register_address*num_of_registers_tool, num_of_registers_tool, functioncode=3)
            value = unpack_registers(val_ls, [dtype])
            result["value"] = int(value[0])
        except Exception as e:
            Logger.error("Error in modbus read method", exc_info=True)
            result["error"] =  repr(e)
            result["error_flag"] = True
    if error_handling_tool:
        return result
    elif result["error_flag"]:
        return result["error"]
    else:
        return result["value"]

def tool_modbus_read_holding_float(slave_address, register_address):
    '''Function to read back FLOAT32/FLOAT64 from master using 2/4 registers. Maps register_address to multiples of 2/4 to ensure no overlap. Will return error if num_of_registers = 1 '''
    result = {"value": 0.0, "error": "", "error_flag": False}
    if num_of_registers_tool <2:
        result["error"] =  "16-bit does not support float types"
        result["error_flag"] = True
    elif slave_address not in instrument_tool:
        result["error"] = "Slave {} does not exist.".format(slave_address)
        result["error_flag"] = True
    else:
        try:
            result["value"] = instrument_tool[slave_address].read_float(register_address*num_of_registers_tool, number_of_registers=num_of_registers_tool, functioncode=3)
        except Exception as e:
            Logger.error("Error in modbus read method", exc_info=True)
            result["error"] =  repr(e)
            result["error_flag"] = True
    if error_handling_tool:
        return result
    elif result["error_flag"]:
        return result["error"]
    else:
        return result["value"]

def tool_modbus_write_holdings_int(slave_address, register_address, data):
    '''Function to write multiple INT16/INT32/INT64 to slave using 1/2/4 registers. Maps register_address to multiples of 1/2/4 to ensure no overlap.'''
    result = {"value": data, "error": "", "error_flag": False}
    if not isinstance(data, list):
        data = [data]
    if slave_address not in instrument_tool:
        result["error"] = "Slave {} does not exist.".format(slave_address)
        result["error_flag"] = True
    else:
        try:
            data = list(map(int,data))
            dtype = ["int" + str(16*num_of_registers_tool) for i in range(len(data))]
            val_ls = pack_registers(data, dtype)
            instrument_tool[slave_address].write_registers(register_address*num_of_registers_tool, val_ls)
        except Exception as e:
            for i in range(len(data)):
                Logger.error("val{}: {}".format(i,data[i]))
            Logger.error("Error in modbus write method", exc_info=True)
            result["error"] = repr(e).replace('"',"'")      # replace all " with ' to prevent UR string errors
            result["error_flag"] = True
    if error_handling_tool:
        return result
    elif result["error_flag"]:
        return result["error"]
    else:
        return True

def tool_modbus_write_holdings_float(slave_address, register_address, data):
    '''Function to write FLOAT32/FLOAT64 to slave using 2/4 registers. Maps register_address to multiples of 2/4 to ensure no overlap. Will return error if num_of_registers = 1 '''
    result = {"value": data, "error": "", "error_flag": False}
    if not isinstance(data, list):
        data = [data]
    if num_of_registers_tool <2:
        result["error"] =  "16-bit does not support float types"
        result["error_flag"] = True
    elif slave_address not in instrument_tool:
        result["error"] = "Slave {} does not exist.".format(slave_address)
        result["error_flag"] = True
    else:
        try:
            data = list(map(float,data))
            dtype = ["float" + str(16*num_of_registers_tool) for i in range(len(data))]
            val_ls = pack_registers(data, dtype)
            instrument_tool[slave_address].write_registers(register_address*num_of_registers_tool, val_ls)
        except Exception as e:
            for i in range(len(data)):
                Logger.error("val{}: {}".format(i,data[i]))
            Logger.error("Error in modbus write method", exc_info=True)
            result["error"] = repr(e).replace('"',"'")      # replace all " with ' to prevent UR string errors
            result["error_flag"] = True
    if error_handling_tool:
        return result
    elif result["error_flag"]:
        return result["error"]
    else:
        True

def tool_modbus_read_inputs_int(slave_address, register_address, num_of_values):
    '''Function to read INT16/INT32/INT64 from slave using 1/2/4 registers. Maps register_address to multiples of 1/2/4 to ensure no overlap.'''
    if num_of_values == 1:
        result = {"value": 0, "error": "", "error_flag": False}
    else:
        result = {"value": [0]*num_of_values, "error": "", "error_flag": False}
    if slave_address not in instrument_tool:
        result["error"] = "Slave {} does not exist.".format(slave_address)
        result["error_flag"] = True
    else:
        try:
            dtype = ["int" + str(16*num_of_registers_tool) for i in range(num_of_values)]
            val_ls = instrument_tool[slave_address].read_registers(register_address*num_of_registers_tool, num_of_values*num_of_registers_tool, functioncode=4)
            value = unpack_registers(val_ls, dtype)
            if num_of_values == 1:
                result["value"] = int(value[0])
            else:
                result["value"] = list(map(int,value))
        except Exception as e:
            Logger.error("Error in modbus read method", exc_info=True)
            result["error"] = repr(e).replace('"',"'")      # replace all " with ' to prevent UR string errors
            result["error_flag"] = True
    if error_handling_tool:
        return result
    elif result["error_flag"]:
        return result["error"]
    else:
        return result["value"]

def tool_modbus_read_inputs_float(slave_address, register_address, num_of_values):
    '''Function to read FLOAT32/FLOAT64 from slave using 2/4 registers. Maps register_address to multiples of 2/4 to ensure no overlap. Will return error if num_of_registers = 1 '''
    if num_of_values == 1:
        result = {"value": 0.0, "error": "", "error_flag": False}
    else:
        result = {"value": [0.0]*num_of_values, "error": "", "error_flag": False}
    if num_of_registers_tool <2:
        result["error"] =  "16-bit does not support float types"
        result["error_flag"] = True
    elif slave_address not in instrument_tool:
        result["error"] = "Slave {} does not exist.".format(slave_address)
        result["error_flag"] = True
    else:
        try:
            dtype = ["float" + str(16*num_of_registers_tool) for i in range(num_of_values)]
            val_ls = instrument_tool[slave_address].read_registers(register_address*num_of_registers_tool, num_of_values*num_of_registers_tool, functioncode=4)
            value = unpack_registers(val_ls, dtype)
            if num_of_values == 1:
                result["value"] = float(value[0])
            else:
                result["value"] = list(map(float,value))
        except Exception as e:
            Logger.error("Error in modbus read method", exc_info=True)
            result["error"] = repr(e).replace('"',"'")      # replace all " with ' to prevent UR string errors
            result["error_flag"] = True
    if error_handling_tool:
        return result
    elif result["error_flag"]:
        return result["error"]
    else:
        return result["value"]

def tool_modbus_read_holdings_int(slave_address, register_address, num_of_values):
    '''Function to read INT16/INT32/INT64 from slave using 1/2/4 registers. Maps register_address to multiples of 1/2/4 to ensure no overlap.'''
    if num_of_values == 1:
        result = {"value": 0, "error": "", "error_flag": False}
    else:
        result = {"value": [0]*num_of_values, "error": "", "error_flag": False}
    if slave_address not in instrument_tool:
        result["error"] = "Slave {} does not exist.".format(slave_address)
        result["error_flag"] = True
    else:
        try:
            dtype = ["int" + str(16*num_of_registers_tool) for i in range(num_of_values)]
            val_ls = instrument_tool[slave_address].read_registers(register_address*num_of_registers_tool, num_of_values*num_of_registers_tool, functioncode=3)
            value = unpack_registers(val_ls, dtype)
            if num_of_values == 1:
                result["value"] = int(value[0])
            else:
                result["value"] = list(map(int,value))
        except Exception as e:
            Logger.error("Error in modbus read method", exc_info=True)
            result["error"] = repr(e).replace('"',"'")      # replace all " with ' to prevent UR string errors
            result["error_flag"] = True
    if error_handling_tool:
        return result
    elif result["error_flag"]:
        return result["error"]
    else:
        return result["value"]

def tool_modbus_read_holdings_float(slave_address, register_address, num_of_values):
    '''Function to read FLOAT32/FLOAT64 from slave using 2/4 registers. Maps register_address to multiples of 2/4 to ensure no overlap. Will return error if num_of_registers = 1 '''
    if num_of_values == 1:
        result = {"value": 0.0, "error": "", "error_flag": False}
    else:
        result = {"value": [0.0]*num_of_values, "error": "", "error_flag": False}
    if num_of_registers_tool <2:
        result["error"] =  "16-bit does not support float types"
        result["error_flag"] = True
    elif slave_address not in instrument_tool:
        result["error"] = "Slave {} does not exist.".format(slave_address)
        result["error_flag"] = True
    else:
        try:  
            dtype = ["float" + str(16*num_of_registers_tool) for i in range(num_of_values)]
            val_ls = instrument_tool[slave_address].read_registers(register_address*num_of_registers_tool, num_of_values*num_of_registers_tool, functioncode=3)
            value = unpack_registers(val_ls, dtype)
            if num_of_values == 1:
                result["value"] = float(value[0])
            else:
                result["value"] = list(map(float,value))
        except Exception as e:
            Logger.error("Error in modbus read method", exc_info=True)
            result["error"] = repr(e).replace('"',"'")      # replace all " with ' to prevent UR string errors
            result["error_flag"] = True
    if error_handling_tool:
        return result
    elif result["error_flag"]:
        return result["error"]
    else:
        return result["value"]


''' functions for usb modbus '''
def find_usb_device(devname_contains_ls, IDserial_contains_ls):
    ''' function to find usb device with the defined devname prefix and string to search for in the ID serial, returns first such device'''
    devnames = []
    usb_devices = subprocess.check_output("find /sys/bus/usb/devices/usb*/ -name dev", shell=True).decode().split()
    
    for sysdevpath in usb_devices:
        syspath = os.path.dirname(sysdevpath)
        try:
            # Get the device name
            devname = subprocess.check_output("udevadm info -q name -p {}".format(syspath), shell=True).decode().strip()
            # Ignore devices which devname is not any of those in devname_contains_ls
            if not any([name in devname for name in devname_contains_ls]):
                continue

            # Get device properties
            properties = subprocess.check_output("udevadm info -q property --export -p {}".format(syspath), shell=True).decode()
            properties_dict = dict(line.split('=') for line in properties.splitlines() if '=' in line)
            
            # Get device ID_SERIAL
            id_serial = properties_dict.get("ID_SERIAL")
            # Ignore devices which IDserial is not any of those in IDserial_contains_ls
            if any([ID in id_serial for ID in IDserial_contains_ls]):
                devnames.append(devname)
        
        except subprocess.CalledProcessError as e:
            pass
            # print("Could not retrieve information for device at {}: {}".format(syspath, e))
    
    return devnames

def init_usb_modbus_64bit(slave_address, usb_devname_contains, usb_IDserial_contains):
    result = init_usb_modbus(slave_address, usb_devname_contains, usb_IDserial_contains)
    global num_of_registers_usb
    num_of_registers_usb = 4
    return result

def init_usb_modbus_32bit(slave_address, usb_devname_contains, usb_IDserial_contains):
    result = init_usb_modbus(slave_address, usb_devname_contains, usb_IDserial_contains)
    global num_of_registers_usb
    num_of_registers_usb = 2
    return result

def init_usb_modbus_16bit(slave_address, usb_devname_contains, usb_IDserial_contains):
    result = init_usb_modbus(slave_address, usb_devname_contains, usb_IDserial_contains)
    global num_of_registers_usb
    num_of_registers_usb = 1
    return result

def init_usb_modbus_no_error_handling_64bit(slave_address, usb_devname_contains, usb_IDserial_contains):
    result = init_usb_modbus_64bit(slave_address, usb_devname_contains, usb_IDserial_contains)
    global error_handling_usb
    error_handling_usb = False
    return result["value"]

def init_usb_modbus_no_error_handling_32bit(slave_address, usb_devname_contains, usb_IDserial_contains):
    result = init_usb_modbus_32bit(slave_address, usb_devname_contains, usb_IDserial_contains)
    global error_handling_usb
    error_handling_usb = False
    return result["value"]

def init_usb_modbus_no_error_handling_16bit(slave_address, usb_devname_contains, usb_IDserial_contains):
    result = init_usb_modbus_16bit(slave_address, usb_devname_contains, usb_IDserial_contains)
    global error_handling_usb
    error_handling_usb = False
    return result["value"]

def init_usb_modbus(slave_address, usb_devname_contains, usb_IDserial_contains):
    if type(usb_devname_contains) == str:
        usb_devname_contains = [usb_devname_contains]
    if type(usb_IDserial_contains) == str:
        usb_IDserial_contains = [usb_IDserial_contains]
    devname_ls = find_usb_device(usb_devname_contains, usb_IDserial_contains)
    if not devname_ls:
        return {"value": 0, "error": "Unable to find " + ", ".join(usb_IDserial_contains) + " among USB devices", "error_flag": True}

    instrument_ls = []
    for devname in devname_ls:
        instrument = modbus.Instrument('/dev/{}'.format(devname), slave_address)
    
        instrument.serial.baudrate = baudrate_usb
        instrument.serial.bytesize = bytesize_usb
        if parity_usb == "None":
            instrument.serial.parity = serial.PARITY_NONE
        elif parity_usb == "Even":
            instrument.serial.parity = serial.PARITY_EVEN
        elif parity_usb == "Odd":
            instrument.serial.parity = serial.PARITY_ODD
        instrument.serial.stopbits = stopbits_usb
        instrument.serial.timeout = timeout_usb

        instrument_ls.append(instrument)
    
    global instrument_usb
    instrument_usb[slave_address] = instrument_ls

    global error_handling_usb
    error_handling_usb = True

    return {"value":len(instrument_ls), "error": "Devices found: " + ", ".join(devname_ls), "error_flag": False}


''' Functions for modifying default settings '''
def usb_modbus_set_baudrate(baudrate):
    if instrument_usb:
        for instrument_ls in instrument_usb.values():
            for instrument in instrument_ls:
                instrument.serial.baudrate = baudrate
                result = {"value":True, "error": "", "error_flag": False}
    else:
        result = {"value":False, "error": "No modbus slaves connected via USB", "error_flag": True}
    
    if error_handling_usb:
        return result
    else:
        return result['value']

def usb_modbus_set_bytesize(bytesize):
    if bytesize in (5, 6, 7, 8):
        if instrument_usb:
            for instrument_ls in instrument_usb.values():
                for instrument in instrument_ls:
                    instrument.serial.bytesize = bytesize
                    result = {"value":True, "error": "", "error_flag": False}
        else:
            result = {"value":False, "error": "No modbus slaves connected via USB", "error_flag": True}
    else:
        result = {"value":False, "error": "Invalid bytesize", "error_flag": True}
    
    if error_handling_usb:
        return result
    else:
        return result['value']

def usb_modbus_set_parity(parity):
    parity_map = {"None": serial.PARITY_NONE, "Even": serial.PARITY_EVEN, "Odd": serial.PARITY_ODD}
    if parity in parity_map.keys():
        if instrument_usb:
            for instrument_ls in instrument_usb.values():
                for instrument in instrument_ls:
                    instrument.serial.parity = parity_map[parity]
                    result = {"value":True, "error": "", "error_flag": False}
        else:
            result = {"value":False, "error": "No modbus slaves connected via USB", "error_flag": True}
    else:
        result = {"value":False, "error": "Invalid parity", "error_flag": True}
    
    if error_handling_usb:
        return result
    else:
        return result['value']

def usb_modbus_set_stopbits(stopbits):
    if stopbits in (1, 1.5, 2):
        if instrument_usb:
            for instrument_ls in instrument_usb.values():
                for instrument in instrument_ls:
                    instrument.serial.stopbits = stopbits
                    result = {"value":True, "error": "", "error_flag": False}
        else:
            result = {"value":False, "error": "No modbus slaves connected via USB", "error_flag": True}
    else:
        result = {"value":False, "error": "Invalid stopbits", "error_flag": True}
    
    if error_handling_usb:
        return result
    else:
        return result['value']

def usb_modbus_set_timeout(timeout):
    if instrument_usb:
        for instrument_ls in instrument_usb.values():
            for instrument in instrument_ls:
                instrument.serial.timeout = timeout
                result = {"value":True, "error": "", "error_flag": False}
    else:
        result = {"value":False, "error": "No modbus slaves connected via USB", "error_flag": True}
    
    if error_handling_usb:
        return result
    else:
        return result['value']


''' Function for checking if connected in no error handling mode '''
def usb_modbus_check_connection(slave_address, register_type, register_address):
    if register_type == "coil":
        result = usb_modbus_read_coil(slave_address, register_address)
    elif register_type == "discrete":
        result = usb_modbus_read_discrete(slave_address, register_address)
    elif register_type == "holding":
        result = usb_modbus_read_holding_float(slave_address, register_address)
    elif register_type == "input":
        result = usb_modbus_read_input_float(slave_address, register_address)
    if type(result) == str:
        return False
    else:
        return True


''' Functions for bit communication '''
def usb_modbus_write_coil(slave_address, register_address, data):
    '''Function to write single BOOL to slave'''
    result = {"value": data, "error": "", "error_flag": True}
    if slave_address not in instrument_usb:
        result["error"] = "Slave {} does not exist.".format(slave_address)
    else:
        for instrument in instrument_usb[slave_address]:
            try:
                data = bool(data)
                instrument.write_bit(register_address, data)
                result = {"value": data, "error": "", "error_flag": False}
                break
            except Exception as e:
                Logger.error("data: %s", data)
                Logger.error("Error in modbus write method", exc_info=True)
                result["error"] = result["error"] + "{}: ".format(instrument.serial.port) + repr(e) + ", "
    if error_handling_usb:
        return result
    elif result["error_flag"]:
        return result["error"]
    else:
        return True

def usb_modbus_read_discrete(slave_address, register_address):
    '''Function to read single BOOL from slave'''
    result = {"value": False, "error": "", "error_flag": True}
    if slave_address not in instrument_usb:
        result["error"] = "Slave {} does not exist.".format(slave_address)
    else:
        for instrument in instrument_usb[slave_address]:
            try:
                value = instrument.read_bit(register_address, functioncode=2)
                result = {"value": bool(value), "error": "", "error_flag": False}
                break
            except Exception as e:
                Logger.error("Error in modbus read method", exc_info=True)
                result["error"] = result["error"] + "{}: ".format(instrument.serial.port) + repr(e) + ", "
    if error_handling_usb:
        return result
    elif result["error_flag"]:
        return result["error"]
    else:
        return result["value"]

def usb_modbus_read_coil(slave_address, register_address):
    '''Function to read back BOOL from master'''
    result = {"value": False, "error": "", "error_flag": True}
    if slave_address not in instrument_usb:
        result["error"] = "Slave {} does not exist.".format(slave_address)
    else:
        for instrument in instrument_usb[slave_address]:
            try:
                value = instrument.read_bit(register_address, functioncode=1)
                result = {"value": bool(value), "error": "", "error_flag": False}
                break
            except Exception as e:
                Logger.error("Error in modbus read method", exc_info=True)
                result["error"] = result["error"] + "{}: ".format(instrument.serial.port) + repr(e) + ", "
    if error_handling_usb:
        return result
    elif result["error_flag"]:
        return result["error"]
    else:
        return result["value"]

def usb_modbus_write_coils(slave_address, register_address, data):
    '''Function to write multiple BOOL to slave in list format or single BOOL in BOOL or list format'''
    result = {"value": data, "error": "", "error_flag": True}
    if not isinstance(data, list):
        data = [data]
    if slave_address not in instrument_usb:
        result["error"] = "Slave {} does not exist.".format(slave_address)
    else:
        for instrument in instrument_usb[slave_address]:
            try:
                data = list(map(bool,data))
                instrument.write_bits(register_address, data)
                result = {"value": data, "error": "", "error_flag": False}
                break
            except Exception as e:
                for i in range(len(data)):
                    Logger.error("val{}:{}".format(i,data[i]))
                Logger.error("Error in modbus write method", exc_info=True)
                result["error"] = result["error"] + "{}: ".format(instrument.serial.port) + repr(e).replace('"',"'") + ", "
    if error_handling_usb:
        return result
    elif result["error_flag"]:
        return result["error"]
    else:
        return True

def usb_modbus_read_discretes(slave_address, register_address, num_of_registers):
    '''Function to read multiple BOOL from slave in list format or single BOOL as BOOL'''
    result = {"value": [False]*num_of_registers, "error": "", "error_flag": True}
    if slave_address not in instrument_usb:
        result["error"] = "Slave {} does not exist.".format(slave_address)
    else:
        for instrument in instrument_usb[slave_address]:
            try:
                value = instrument.read_bits(register_address, num_of_registers, functioncode=2)
                if num_of_registers == 1:
                    result = {"value": bool(value[0]), "error": "", "error_flag": False}
                else:
                    result = {"value": list(map(bool,value)), "error": "", "error_flag": False}
                break
            except Exception as e:
                Logger.error("Error in modbus read method", exc_info=True)
                result["error"] = result["error"] + "{}: ".format(instrument.serial.port) + repr(e).replace('"',"'") + ", "
    if error_handling_usb:
        return result
    elif result["error_flag"]:
        return result["error"]
    else:
        return result["value"]

def usb_modbus_read_coils(slave_address, register_address, num_of_registers):
    '''Function to read back multiple BOOL from master in list format or single BOOL as BOOL'''
    result = {"value": [False]*num_of_registers, "error": "", "error_flag": True}
    if slave_address not in instrument_usb:
        result["error"] = "Slave {} does not exist.".format(slave_address)
    else:
        for instrument in instrument_usb[slave_address]:
            try:
                value = instrument.read_bits(register_address, num_of_registers, functioncode=1)
                if num_of_registers == 1:
                    result = {"value": bool(value[0]), "error": "", "error_flag": False}
                else:
                    result = {"value": list(map(bool,value)), "error": "", "error_flag": False}
                break
            except Exception as e:
                Logger.error("Error in modbus read method", exc_info=True)
                result["error"] = result["error"] + "{}: ".format(instrument.serial.port) + repr(e).replace('"',"'") + ", "
    if error_handling_usb:
        return result
    elif result["error_flag"]:
        return result["error"]
    else:
        return result["value"]


''' Functions for 16/32/64 bit communication '''
def usb_modbus_read_write_registers(slave_address, read_register_address, read_dtype, write_register_address, write_data, write_dtype):
    '''Function to write and read multiple types of data to slave. Underlying communication uses registers'''
    if not isinstance(write_data, list):
        write_data = [write_data]
    if not isinstance(write_dtype, list):
        write_dtype = [write_dtype]
    if not isinstance(read_dtype, list):
        read_dtype = [read_dtype]
    read_num_of_values = len(read_dtype)
    if read_num_of_values == 1:
        result = {"value": 0, "error": "", "error_flag": True}
    else:
        result = {"value": [0]*read_num_of_values, "error": "", "error_flag": True}

    try:
        for i in range(len(write_data)):
            if write_dtype[i] in ["int", "uint"]:
                write_data[i] = int(write_data[i])
            elif write_dtype[i] in ["float"]:
                write_data[i] = float(write_data[i])
        write_dtype = [dtype + str(16*num_of_registers_usb) for dtype in write_dtype]
        read_dtype = [dtype + str(16*num_of_registers_usb) for dtype in read_dtype]
    except Exception as e:
        result["error"] = repr(e).replace('"',"'")
    else:
        if slave_address not in instrument_usb:
            result["error"] = "Slave {} does not exist.".format(slave_address)
        else:
            for instrument in instrument_usb[slave_address]:
                try:
                    write_ls = pack_registers(write_data, write_dtype)
                    read_ls = instrument.read_write_registers(
                        read_register_address*num_of_registers_usb,
                        read_num_of_values*num_of_registers_usb,
                        write_register_address*num_of_registers_usb,
                        write_ls)
                    value = unpack_registers(read_ls, read_dtype)
                    if read_num_of_values == 1:
                        result = {"value": value[0], "error": "", "error_flag": False}
                    else:
                        result = {"value": value, "error": "", "error_flag": False}
                    break
                except Exception as e:
                    for i in range(len(write_data)):
                        Logger.error("val{}: {}".format(i,write_data[i]))
                    Logger.error("Error in modbus write method", exc_info=True)
                    result["error"] = result["error"] + "{}: ".format(instrument.serial.port) + repr(e).replace('"',"'") + ", "
    if error_handling_tool:
        return result
    elif result["error_flag"]:
        return result["error"]
    else:
        return result["value"]


def usb_modbus_write_holdings(slave_address, register_address, data, dtype):
    '''Function to write multiple INT16/INT32/INT64/FLOAT32/FLOAT64 to slave using 1/2/4 registers. Maps register_address to multiples of 1/2/4 to ensure no overlap.
    length of data should be equal to length of dtype'''
    result = {"value": data, "error": "", "error_flag": True}
    if not isinstance(data, list):
        data = [data]
    if not isinstance(dtype, list):
        dtype = [dtype]
    try:
        for i in range(len(data)):
            if dtype[i] in ["int", "uint", int]:
                data[i] = int(data[i])
            elif dtype[i] in ["float", float]:
                data[i] = float(data[i])
        dtype = [dtypes + str(16*num_of_registers_usb) for dtypes in dtype]
    except Exception as e:
        result["error"] = repr(e).replace('"',"'")
    else:
        if slave_address not in instrument_usb:
            result["error"] = "Slave {} does not exist.".format(slave_address)
        else:
            for instrument in instrument_usb[slave_address]:
                try:
                    val_ls = pack_registers(data, dtype)
                    instrument.write_registers(register_address*num_of_registers_usb, val_ls)
                    result = {"value": data, "error": "", "error_flag": False}
                    break
                except Exception as e:
                    for i in range(len(data)):
                        Logger.error("val{}: {}".format(i,data[i]))
                    Logger.error("Error in modbus write method", exc_info=True)
                    result["error"] = result["error"] + "{}: ".format(instrument.serial.port) + repr(e).replace('"',"'") + ", "
    if error_handling_usb:
        return result
    elif result["error_flag"]:
        return result["error"]
    else:
        return True

def usb_modbus_read_inputs(slave_address, register_address, dtype):
    '''Function to read INT16/INT32/INT64/FLOAT32/FLOAT64 from slave using 1/2/4 registers. Maps register_address to multiples of 1/2/4 to ensure no overlap.
    uses length of dtype as number of registers to read'''
    if not isinstance(dtype, list):
        dtype = [dtype]
    num_of_values = len(dtype)
    if num_of_values == 1:
        result = {"value": 0, "error": "", "error_flag": True}
    else:
        result = {"value": [0]*num_of_values, "error": "", "error_flag": True}
    try:
        dtype = [dtypes + str(16*num_of_registers_usb) for dtypes in dtype]
    except Exception as e:
        result["error"] = repr(e)
    else:
        if slave_address not in instrument_usb:
            result["error"] = "Slave {} does not exist.".format(slave_address)
        else:
            for instrument in instrument_usb[slave_address]:
                try:
                    val_ls = instrument.read_registers(register_address*num_of_registers_usb, num_of_values*num_of_registers_usb, functioncode=4)
                    value = unpack_registers(val_ls, dtype)
                    if num_of_values == 1:
                        result = {"value": value[0], "error": "", "error_flag": False}
                    else:
                        result = {"value": value, "error": "", "error_flag": False}
                    break
                except Exception as e:
                    Logger.error("Error in modbus read method", exc_info=True)
                    result["error"] = result["error"] + "{}: ".format(instrument.serial.port) + repr(e).replace('"',"'") + ", "
    if error_handling_usb:
        return result
    elif result["error_flag"]:
        return result["error"]
    else:
        return result["value"]

def usb_modbus_read_holdings(slave_address, register_address, dtype):
    '''Function to read back INT16/INT32/INT64/FLOAT32/FLOAT64 from master using 1/2/4 registers. Maps register_address to multiples of 1/2/4 to ensure no overlap.
    uses length of dtype as number of registers to read'''
    if not isinstance(dtype, list):
        dtype = [dtype]
    num_of_values = len(dtype)
    if num_of_values == 1:
        result = {"value": 0, "error": "", "error_flag": True}
    else:
        result = {"value": [0]*num_of_values, "error": "", "error_flag": True}
    try:
        dtype = [dtypes + str(16*num_of_registers_usb) for dtypes in dtype]
    except Exception as e:
        result["error"] = repr(e)
    else:
        if slave_address not in instrument_usb:
            result["error"] = "Slave {} does not exist.".format(slave_address)
        else:
            for instrument in instrument_usb[slave_address]:
                try:
                    val_ls = instrument.read_registers(register_address*num_of_registers_usb, num_of_values*num_of_registers_usb, functioncode=3)
                    value = unpack_registers(val_ls, dtype)
                    if num_of_values == 1:
                        result = {"value": value[0], "error": "", "error_flag": False}
                    else:
                        result = {"value": value, "error": "", "error_flag": False}
                    break
                except Exception as e:
                    Logger.error("Error in modbus read method", exc_info=True)
                    result["error"] = result["error"] + "{}: ".format(instrument.serial.port) + repr(e).replace('"',"'") + ", "
    if error_handling_usb:
        return result
    elif result["error_flag"]:
        return result["error"]
    else:
        return result["value"]
        

def usb_modbus_write_holding_int(slave_address, register_address, data):
    '''Function to write INT16/INT32/INT64 to slave using 1/2/4 registers. Maps register_address to multiples of 1/2/4 to ensure no overlap.'''
    result = {"value": data, "error": "", "error_flag": True}
    try:
        data = int(data)
        dtype = "int" + str(16*num_of_registers_usb)
    except Exception as e:
        result["error"] = repr(e)
    else:
        if slave_address not in instrument_usb:
            result["error"] = "Slave {} does not exist.".format(slave_address)
        else:
            for instrument in instrument_usb[slave_address]:
                try:
                    val_ls = pack_registers([data], [dtype])
                    instrument.write_registers(register_address*num_of_registers_usb, val_ls)
                    result = {"value": data, "error": "", "error_flag": False}
                    break
                except Exception as e:
                    Logger.error("data: %s", data)
                    Logger.error("Error in modbus write method", exc_info=True)
                    result["error"] = result["error"] + "{}: ".format(instrument.serial.port) + repr(e) + ", "
    if error_handling_usb:
        return result
    elif result["error_flag"]:
        return result["error"]
    else:
        return True

def usb_modbus_write_holding_float(slave_address, register_address, data):
    '''Function to write FLOAT32/FLOAT64 to slave using 2/4 registers. Maps register_address to multiples of 2/4 to ensure no overlap. Will return error if num_of_registers = 1 '''
    result = {"value": data, "error": "", "error_flag": True}
    if num_of_registers_usb <2:
        result["error"] =  "16-bit does not support float types"
    else:
        if slave_address not in instrument_usb:
            result["error"] = "Slave {} does not exist.".format(slave_address)
        else:
            for instrument in instrument_usb[slave_address]:
                try:
                    instrument.write_float(register_address*num_of_registers_usb, data, number_of_registers=num_of_registers_usb)
                    result = {"value": data, "error": "", "error_flag": False}
                    break
                except Exception as e:
                    Logger.error("data: %s", data)
                    Logger.error("Error in modbus write method", exc_info=True)
                    result["error"] = result["error"] + "{}: ".format(instrument.serial.port) + repr(e) + ", "
    if error_handling_usb:
        return result
    elif result["error_flag"]:
        return result["error"]
    else:
        True

def usb_modbus_read_input_int(slave_address, register_address):
    '''Function to read INT16/INT32/INT64 from slave using 1/2/4 registers. Maps register_address to multiples of 1/2/4 to ensure no overlap.'''
    result = {"value": 0, "error": "", "error_flag": True}
    dtype = "int" + str(16*num_of_registers_usb)
    if slave_address not in instrument_usb:
        result["error"] = "Slave {} does not exist.".format(slave_address)
    else:
        for instrument in instrument_usb[slave_address]:
            try:
                val_ls = instrument.read_registers(register_address*num_of_registers_usb, num_of_registers_usb, functioncode=4)
                value = unpack_registers(val_ls, [dtype])
                result = {"value": int(value[0]), "error": "", "error_flag": False}
                break
            except Exception as e:
                Logger.error("Error in modbus read method", exc_info=True)
                result["error"] = result["error"] + "{}: ".format(instrument.serial.port) + repr(e) + ", "
    if error_handling_usb:
        return result
    elif result["error_flag"]:
        return result["error"]
    else:
        return result["value"]

def usb_modbus_read_input_float(slave_address, register_address):
    '''Function to read FLOAT32/FLOAT64 from slave using 2/4 registers. Maps register_address to multiples of 2/4 to ensure no overlap. Will return error if num_of_registers = 1 '''
    result = {"value": 0.0, "error": "", "error_flag": True}
    if num_of_registers_usb <2:
        result["error"] =  "16-bit does not support float types"
    else:
        if slave_address not in instrument_usb:
            result["error"] = "Slave {} does not exist.".format(slave_address)
        else:
            for instrument in instrument_usb[slave_address]:
                try:
                    val = instrument.read_float(register_address*num_of_registers_usb, number_of_registers=num_of_registers_usb, functioncode=4)
                    result = {"value": val, "error": "", "error_flag": False}
                    break
                except Exception as e:
                    Logger.error("Error in modbus read method", exc_info=True)
                    result["error"] = result["error"] + "{}: ".format(instrument.serial.port) + repr(e) + ", "
    if error_handling_usb:
        return result
    elif result["error_flag"]:
        return result["error"]
    else:
        return result["value"]

def usb_modbus_read_holding_int(slave_address, register_address):
    '''Function to read back INT16/INT32/INT64 from master using 1/2/4 registers. Maps register_address to multiples of 1/2/4 to ensure no overlap.'''
    result = {"value": 0, "error": "", "error_flag": True}
    dtype = "int" + str(16*num_of_registers_usb)
    if slave_address not in instrument_usb:
        result["error"] = "Slave {} does not exist.".format(slave_address)
    else:
        for instrument in instrument_usb[slave_address]:
            try:
                val_ls = instrument.read_registers(register_address*num_of_registers_usb, num_of_registers_usb, functioncode=4)
                value = unpack_registers(val_ls, [dtype])
                result = {"value": int(value[0]), "error": "", "error_flag": False}
                break
            except Exception as e:
                Logger.error("Error in modbus read method", exc_info=True)
                result["error"] = result["error"] + "{}: ".format(instrument.serial.port) + repr(e) + ", "
    if error_handling_usb:
        return result
    elif result["error_flag"]:
        return result["error"]
    else:
        return result["value"]

def usb_modbus_read_holding_float(slave_address, register_address):
    '''Function to read back FLOAT32/FLOAT64 from master using 2/4 registers. Maps register_address to multiples of 2/4 to ensure no overlap. Will return error if num_of_registers = 1 '''
    result = {"value": 0.0, "error": "", "error_flag": True}
    if num_of_registers_usb <2:
        result["error"] =  "16-bit does not support float types"
    else:
        if slave_address not in instrument_usb:
            result["error"] = "Slave {} does not exist.".format(slave_address)
        else:
            for instrument in instrument_usb[slave_address]:
                try:
                    val = instrument.read_float(register_address*num_of_registers_usb, number_of_registers=num_of_registers_usb, functioncode=3)
                    result = {"value": val, "error": "", "error_flag": False}
                    break
                except Exception as e:
                    Logger.error("Error in modbus read method", exc_info=True)
                    result["error"] = result["error"] + "{}: ".format(instrument.serial.port) + repr(e) + ", "
    if error_handling_usb:
        return result
    elif result["error_flag"]:
        return result["error"]
    else:
        return result["value"]

def usb_modbus_write_holdings_int(slave_address, register_address, data):
    '''Function to write multiple INT16/INT32/INT64 to slave using 1/2/4 registers. Maps register_address to multiples of 1/2/4 to ensure no overlap.'''
    result = {"value": data, "error": "", "error_flag": True}
    if not isinstance(data, list):
        data = [data]
    try:
        data = list(map(int,data))
        dtype = ["int" + str(16*num_of_registers_usb) for i in range(len(data))]
    except Exception as e:
        result["error"] = repr(e)
    else:
        if slave_address not in instrument_usb:
            result["error"] = "Slave {} does not exist.".format(slave_address)
        else:
            for instrument in instrument_usb[slave_address]:
                try:
                    val_ls = pack_registers(data, dtype)
                    instrument.write_registers(register_address*num_of_registers_usb, val_ls)
                    result = {"value": data, "error": "", "error_flag": False}
                    break
                except Exception as e:
                    for i in range(len(data)):
                        Logger.error("val{}: {}".format(i,data[i]))
                    Logger.error("Error in modbus write method", exc_info=True)
                    result["error"] = result["error"] + "{}: ".format(instrument.serial.port) + repr(e).replace('"',"'") + ", "
    if error_handling_usb:
        return result
    elif result["error_flag"]:
        return result["error"]
    else:
        return True

def usb_modbus_write_holdings_float(slave_address, register_address, data):
    '''Function to write FLOAT32/FLOAT64 to slave using 2/4 registers. Maps register_address to multiples of 2/4 to ensure no overlap. Will return error if num_of_registers = 1 '''
    result = {"value": data, "error": "", "error_flag": True}
    if not isinstance(data, list):
        data = [data]
    try:
        data = list(map(float,data))
        dtype = ["float" + str(16*num_of_registers_usb) for i in range(len(data))]
    except Exception as e:
        result["error"] = repr(e)
    else:
        if slave_address not in instrument_usb:
            result["error"] = "Slave {} does not exist.".format(slave_address)
        else:
            for instrument in instrument_usb[slave_address]:
                try:
                    val_ls = pack_registers(data, dtype)
                    instrument.write_registers(register_address*num_of_registers_usb, val_ls)
                    result = {"value": data, "error": "", "error_flag": False}
                    break
                except Exception as e:
                    for i in range(len(data)):
                        Logger.error("val{}: {}".format(i,data[i]))
                    Logger.error("Error in modbus write method", exc_info=True)
                    result["error"] = result["error"] + "{}: ".format(instrument.serial.port) + repr(e).replace('"',"'") + ", "
    if error_handling_usb:
        return result
    elif result["error_flag"]:
        return result["error"]
    else:
        True

def usb_modbus_read_inputs_int(slave_address, register_address, num_of_values):
    '''Function to read INT16/INT32/INT64 from slave using 1/2/4 registers. Maps register_address to multiples of 1/2/4 to ensure no overlap.'''
    if num_of_values == 1:
        result = {"value": 0, "error": "", "error_flag": True}
    else:
        result = {"value": [0]*num_of_values, "error": "", "error_flag": True}
    try:
        dtype = ["int" + str(16*num_of_registers_usb) for i in range(num_of_values)]
    except Exception as e:
        result["error"] = repr(e)
    else:
        if slave_address not in instrument_usb:
            result["error"] = "Slave {} does not exist.".format(slave_address)
        else:
            for instrument in instrument_usb[slave_address]:
                try:
                    val_ls = instrument.read_registers(register_address*num_of_registers_usb, num_of_values*num_of_registers_usb, functioncode=4)
                    value = unpack_registers(val_ls, dtype)
                    if num_of_values == 1:
                        result = {"value": int(value[0]), "error": "", "error_flag": False}
                    else:
                        result = {"value": list(map(int,value)), "error": "", "error_flag": False}
                    break
                except Exception as e:
                    Logger.error("Error in modbus read method", exc_info=True)
                    result["error"] = result["error"] + "{}: ".format(instrument.serial.port) + repr(e).replace('"',"'") + ", "
    if error_handling_usb:
        return result
    elif result["error_flag"]:
        return result["error"]
    else:
        return result["value"]

def usb_modbus_read_inputs_float(slave_address, register_address, num_of_values):
    '''Function to read FLOAT32/FLOAT64 from slave using 2/4 registers. Maps register_address to multiples of 2/4 to ensure no overlap. Will return error if num_of_registers = 1 '''
    if num_of_values == 1:
        result = {"value": 0.0, "error": "", "error_flag": True}
    else:
        result = {"value": [0.0]*num_of_values, "error": "", "error_flag": True}
    try:
        dtype = ["float" + str(16*num_of_registers_usb) for i in range(num_of_values)]
    except Exception as e:
        result["error"] = repr(e)
    else:
        if slave_address not in instrument_usb:
            result["error"] = "Slave {} does not exist.".format(slave_address)
        else:
            for instrument in instrument_usb[slave_address]:
                try:
                    val_ls = instrument.read_registers(register_address*num_of_registers_usb, num_of_values*num_of_registers_usb, functioncode=4)
                    value = unpack_registers(val_ls, dtype)
                    if num_of_values == 1:
                        result = {"value": float(value[0]), "error": "", "error_flag": False}
                    else:
                        result = {"value": list(map(float,value)), "error": "", "error_flag": False}
                    break
                except Exception as e:
                    Logger.error("Error in modbus read method", exc_info=True)
                    result["error"] = result["error"] + "{}: ".format(instrument.serial.port) + repr(e).replace('"',"'") + ", "
    if error_handling_usb:
        return result
    elif result["error_flag"]:
        return result["error"]
    else:
        return result["value"]

def usb_modbus_read_holdings_int(slave_address, register_address, num_of_values):
    '''Function to read INT16/INT32/INT64 from slave using 1/2/4 registers. Maps register_address to multiples of 1/2/4 to ensure no overlap.'''
    if num_of_values == 1:
        result = {"value": 0, "error": "", "error_flag": True}
    else:
        result = {"value": [0]*num_of_values, "error": "", "error_flag": True}
    try:
        dtype = ["int" + str(16*num_of_registers_usb) for i in range(num_of_values)]
    except Exception as e:
        result["error"] = repr(e)
    else:
        if slave_address not in instrument_usb:
            result["error"] = "Slave {} does not exist.".format(slave_address)
        else:
            for instrument in instrument_usb[slave_address]:
                try:
                    val_ls = instrument.read_registers(register_address*num_of_registers_usb, num_of_values*num_of_registers_usb, functioncode=3)
                    value = unpack_registers(val_ls, dtype)
                    if num_of_values == 1:
                        result = {"value": int(value[0]), "error": "", "error_flag": False}
                    else:
                        result = {"value": list(map(int,value)), "error": "", "error_flag": False}
                    break
                except Exception as e:
                    Logger.error("Error in modbus read method", exc_info=True)
                    result["error"] = result["error"] + "{}: ".format(instrument.serial.port) + repr(e).replace('"',"'") + ", "
    if error_handling_usb:
        return result
    elif result["error_flag"]:
        return result["error"]
    else:
        return result["value"]

def usb_modbus_read_holdings_float(slave_address, register_address, num_of_values):
    '''Function to read FLOAT32/FLOAT64 from slave using 2/4 registers. Maps register_address to multiples of 2/4 to ensure no overlap. Will return error if num_of_registers = 1 '''
    if num_of_values == 1:
        result = {"value": 0.0, "error": "", "error_flag": True}
    else:
        result = {"value": [0.0]*num_of_values, "error": "", "error_flag": True}
    try:
        dtype = ["float" + str(16*num_of_registers_usb) for i in range(num_of_values)]
    except Exception as e:
        result["error"] = repr(e)
    else:
        if slave_address not in instrument_usb:
            result["error"] = "Slave {} does not exist.".format(slave_address)
        else:
            for instrument in instrument_usb[slave_address]:
                try:
                    val_ls = instrument.read_registers(register_address*num_of_registers_usb, num_of_values*num_of_registers_usb, functioncode=3)
                    value = unpack_registers(val_ls, dtype)
                    if num_of_values == 1:
                        result = {"value": float(value[0]), "error": "", "error_flag": False}
                    else:
                        result = {"value": list(map(float,value)), "error": "", "error_flag": False}
                    break
                except Exception as e:
                    Logger.error("Error in modbus read method", exc_info=True)
                    result["error"] = result["error"] + "{}: ".format(instrument.serial.port) + repr(e).replace('"',"'") + ", "
    if error_handling_usb:
        return result
    elif result["error_flag"]:
        return result["error"]
    else:
        return result["value"]


class MultithreadedSimpleXMLRPCServer(ThreadingMixIn, SimpleXMLRPCServer):
    pass

# Connection related functions
server = MultithreadedSimpleXMLRPCServer((LOCALHOST, 40408), allow_none=True)
server.RequestHandlerClass.protocol_version = "HTTP/1.1"
print("Listening on port 40408...")

server.register_function(isReachable,"isReachable")

server.register_function(init_tool_modbus_64bit,"init_tool_modbus_64bit")
server.register_function(init_tool_modbus_32bit,"init_tool_modbus_32bit")
server.register_function(init_tool_modbus_16bit,"init_tool_modbus_16bit")
server.register_function(init_tool_modbus_no_error_handling_64bit,"init_tool_modbus_no_error_handling_64bit")
server.register_function(init_tool_modbus_no_error_handling_32bit,"init_tool_modbus_no_error_handling_32bit")
server.register_function(init_tool_modbus_no_error_handling_16bit,"init_tool_modbus_no_error_handling_16bit")

server.register_function(tool_modbus_set_baudrate,"tool_modbus_set_baudrate")
server.register_function(tool_modbus_set_bytesize,"tool_modbus_set_bytesize")
server.register_function(tool_modbus_set_parity,"tool_modbus_set_parity")
server.register_function(tool_modbus_set_stopbits,"tool_modbus_set_stopbits")
server.register_function(tool_modbus_set_timeout,"tool_modbus_set_timeout")
server.register_function(tool_modbus_check_connection,"tool_modbus_check_connection")

server.register_function(tool_modbus_write_coil,"tool_modbus_write_coil")
server.register_function(tool_modbus_read_discrete,"tool_modbus_read_discrete")
server.register_function(tool_modbus_read_coil,"tool_modbus_read_coil")

server.register_function(tool_modbus_write_coils,"tool_modbus_write_coils")
server.register_function(tool_modbus_read_discretes,"tool_modbus_read_discretes")
server.register_function(tool_modbus_read_coils,"tool_modbus_read_coils")

server.register_function(tool_modbus_read_write_registers,"tool_modbus_read_write_registers")

server.register_function(tool_modbus_write_holdings,"tool_modbus_write_holdings")
server.register_function(tool_modbus_read_inputs,"tool_modbus_read_inputs")
server.register_function(tool_modbus_read_holdings,"tool_modbus_read_holdings")

server.register_function(tool_modbus_write_holding_int,"tool_modbus_write_holding_int")
server.register_function(tool_modbus_write_holding_float,"tool_modbus_write_holding_float")
server.register_function(tool_modbus_read_input_int,"tool_modbus_read_input_int")
server.register_function(tool_modbus_read_input_float,"tool_modbus_read_input_float")
server.register_function(tool_modbus_read_holding_int,"tool_modbus_read_holding_int")
server.register_function(tool_modbus_read_holding_float,"tool_modbus_read_holding_float")

server.register_function(tool_modbus_write_holdings_int,"tool_modbus_write_holdings_int")
server.register_function(tool_modbus_write_holdings_float,"tool_modbus_write_holdings_float")
server.register_function(tool_modbus_read_inputs_int,"tool_modbus_read_inputs_int")
server.register_function(tool_modbus_read_inputs_float,"tool_modbus_read_inputs_float")
server.register_function(tool_modbus_read_holdings_int,"tool_modbus_read_holdings_int")
server.register_function(tool_modbus_read_holdings_float,"tool_modbus_read_holdings_float")


server.register_function(init_usb_modbus_64bit,"init_usb_modbus_64bit")
server.register_function(init_usb_modbus_32bit,"init_usb_modbus_32bit")
server.register_function(init_usb_modbus_16bit,"init_usb_modbus_16bit")
server.register_function(init_usb_modbus_no_error_handling_64bit,"init_usb_modbus_no_error_handling_64bit")
server.register_function(init_usb_modbus_no_error_handling_32bit,"init_usb_modbus_no_error_handling_32bit")
server.register_function(init_usb_modbus_no_error_handling_16bit,"init_usb_modbus_no_error_handling_16bit")

server.register_function(usb_modbus_set_baudrate,"usb_modbus_set_baudrate")
server.register_function(usb_modbus_set_bytesize,"usb_modbus_set_bytesize")
server.register_function(usb_modbus_set_parity,"usb_modbus_set_parity")
server.register_function(usb_modbus_set_stopbits,"usb_modbus_set_stopbits")
server.register_function(usb_modbus_set_timeout,"usb_modbus_set_timeout")
server.register_function(usb_modbus_check_connection,"usb_modbus_check_connection")

server.register_function(usb_modbus_write_coil,"usb_modbus_write_coil")
server.register_function(usb_modbus_read_discrete,"usb_modbus_read_discrete")
server.register_function(usb_modbus_read_coil,"usb_modbus_read_coil")

server.register_function(usb_modbus_write_coils,"usb_modbus_write_coils")
server.register_function(usb_modbus_read_discretes,"usb_modbus_read_discretes")
server.register_function(usb_modbus_read_coils,"usb_modbus_read_coils")

server.register_function(usb_modbus_read_write_registers,"usb_modbus_read_write_registers")

server.register_function(usb_modbus_write_holdings,"usb_modbus_write_holdings")
server.register_function(usb_modbus_read_inputs,"usb_modbus_read_inputs")
server.register_function(usb_modbus_read_holdings,"usb_modbus_read_holdings")

server.register_function(usb_modbus_write_holding_int,"usb_modbus_write_holding_int")
server.register_function(usb_modbus_write_holding_float,"usb_modbus_write_holding_float")
server.register_function(usb_modbus_read_input_int,"usb_modbus_read_input_int")
server.register_function(usb_modbus_read_input_float,"usb_modbus_read_input_float")
server.register_function(usb_modbus_read_holding_int,"usb_modbus_read_holding_int")
server.register_function(usb_modbus_read_holding_float,"usb_modbus_read_holding_float")

server.register_function(usb_modbus_write_holdings_int,"usb_modbus_write_holdings_int")
server.register_function(usb_modbus_write_holdings_float,"usb_modbus_write_holdings_float")
server.register_function(usb_modbus_read_inputs_int,"usb_modbus_read_inputs_int")
server.register_function(usb_modbus_read_inputs_float,"usb_modbus_read_inputs_float")
server.register_function(usb_modbus_read_holdings_int,"usb_modbus_read_holdings_int")
server.register_function(usb_modbus_read_holdings_float,"usb_modbus_read_holdings_float")

server.serve_forever()
