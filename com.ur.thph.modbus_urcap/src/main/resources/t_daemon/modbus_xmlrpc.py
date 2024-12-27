#!/usr/bin/env python

import socket
import struct
import time
import logging as Logger
import os, sys
currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)
import minimalmodbus as modbus
import serial
import subprocess

from SimpleXMLRPCServer import SimpleXMLRPCServer
from SocketServer import ThreadingMixIn

isShowing = False
LOCALHOST = "127.0.0.1"

# instrument/slave 1
instrument_tool = None
baudrate_tool = 115200
bytesize_tool = 8
parity_tool = "None"
stopbits_tool = 1
timeout_tool = 1   # seconds
num_of_registers_tool = 4  # 4 for 64-bit ints and floats using holding and input registers. 2 for 32-bit ints and floats, 1 bit 16-bit ints only
error_handling_tool = True

# instrument/slave 2
instrument_usb = []
baudrate_usb = 115200
bytesize_usb = 8
parity_usb = "None"
stopbits_usb = 1
timeout_usb = 1   # seconds
num_of_registers_usb = 4  # 4 for 64-bit ints and floats using holding and input registers. 2 for 32-bit ints and floats, 1 bit 16-bit ints only
error_handling_usb = True


def isReachable():
    return True

''' functions for tool modbus '''
def init_tool_modbus_64bit():
    init_tool_modbus()
    global num_of_registers_tool
    num_of_registers_tool = 4
    return True

def init_tool_modbus_32bit():
    init_tool_modbus()
    global num_of_registers_tool
    num_of_registers_tool = 2
    return True

def init_tool_modbus_16bit():
    init_tool_modbus()
    global num_of_registers_tool
    num_of_registers_tool = 1
    return True

def init_tool_modbus_no_error_handling_64bit():
    init_tool_modbus_64bit()
    global error_handling_tool
    error_handling_tool = False
    return True

def init_tool_modbus_no_error_handling_32bit():
    init_tool_modbus_32bit()
    global error_handling_tool
    error_handling_tool = False
    return True

def init_tool_modbus_no_error_handling_16bit():
    init_tool_modbus_16bit()
    global error_handling_tool
    error_handling_tool = False
    return True

def init_tool_modbus():
    global instrument_tool
    instrument_tool = modbus.Instrument('/dev/ttyTool')
    
    instrument_tool.serial.baudrate = baudrate_tool
    instrument_tool.serial.bytesize = bytesize_tool
    if parity_tool == "None":
        instrument_tool.serial.parity = serial.PARITY_NONE
    elif parity_tool == "Even":
        instrument_tool.serial.parity = serial.PARITY_EVEN
    elif parity_tool == "Odd":
        instrument_tool.serial.parity = serial.PARITY_ODD
    instrument_tool.serial.stopbits = stopbits_tool
    instrument_tool.serial.timeout = timeout_tool
    global error_handling_tool
    error_handling_tool = True


''' Functions for modifying default settings '''
def tool_modbus_set_baudrate(baudrate):
    if baudrate in (9600, 19200, 38400, 57600, 115200, 1000000, 2000000, 5000000):
        if type(instrument_tool) != type(None):
            instrument_tool.serial.baudrate = baudrate
            result = {"value":True, "error": "", "error_flag": False}
        else:
            result = {"value":False, "error": "No modbus slaves connected via tool connector", "error_flag": True}
    else:
        result = {"value":False, "error": "Invalid baudrate", "error_flag": True}

    if error_handling_tool:
        return result
    else:
        return result['value']

def tool_modbus_set_bytesize(bytesize):
    if bytesize in (5, 6, 7, 8):
        if type(instrument_tool) != type(None):
            instrument_tool.serial.bytesize = bytesize
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
        if type(instrument_tool) != type(None):
            instrument_tool.serial.parity = parity_map[parity]
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
        if type(instrument_tool) != type(None):
            instrument_tool.serial.stopbits = stopbits
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
    if type(instrument_tool) != type(None):
        instrument_tool.serial.timeout = timeout
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
    try:
        data = bool(data)
        instrument_tool.write_bit(slave_address, register_address, data, 5)
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
    try:
        value = instrument_tool.read_bit(slave_address, register_address)
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
    try:
        value = instrument_tool.read_bit(slave_address, register_address, functioncode=1)
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


''' Functions for 16/32/64 bit communication '''
def tool_modbus_write_holding_int(slave_address, register_address, data):
    '''Function to write INT16/INT32/INT64 to slave using 1/2/4 registers. Maps register_address to multiples of 1/2/4 to ensure no overlap.'''
    result = {"value": data, "error": "", "error_flag": False}
    try:
        data = int(data)
        data = signed_to_unsigned(num_of_registers_tool*16, data)    # most significant bit denotes sign
        val = []
        for i in range(num_of_registers_tool-1, -1, -1):    # start from highest 16 bits to lowest 16 bits
            val.append((data >> 16*i) & 0xFFFF)
        instrument_tool.write_registers(slave_address, register_address*num_of_registers_tool,val)
    except Exception as e:
        Logger.error("data: %s", data)
        for i in range(len(val)):
            Logger.error("val{}: {}".format(i,val[i]))
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
    else:
        try:
            instrument_tool.write_float(slave_address, register_address*num_of_registers_tool, data, number_of_registers=num_of_registers_tool)
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
    try:
        val = instrument_tool.read_registers(slave_address, register_address*num_of_registers_tool, num_of_registers_tool, functioncode=4)
        val_comb = val[0]
        for i in range(1,num_of_registers_tool):
            val_comb = (val_comb << 16) + val[i]
        result["value"] = unsigned_to_signed(num_of_registers_tool*16, val_comb)   # most significant bit denotes sign
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
    try:
        result["value"] = instrument_tool.read_float(slave_address, register_address*num_of_registers_tool, number_of_registers=num_of_registers_tool, functioncode=4)
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
    try:
        val = instrument_tool.read_registers(slave_address, register_address*num_of_registers_tool, num_of_registers_tool, functioncode=3)
        val_comb = val[0]
        for i in range(1,num_of_registers_tool):
            val_comb = (val_comb << 16) + val[i]
        result["value"] = unsigned_to_signed(num_of_registers_tool*16, val_comb)   # most significant bit denotes sign
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
    try:
        result["value"] = instrument_tool.read_float(slave_address, register_address*num_of_registers_tool, number_of_registers=num_of_registers_tool, functioncode=3)
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

def init_usb_modbus_64bit(usb_devname_contains, usb_IDserial_contains):
    result = init_usb_modbus(usb_devname_contains, usb_IDserial_contains)
    global num_of_registers_usb
    num_of_registers_usb = 4
    return result

def init_usb_modbus_32bit(usb_devname_contains, usb_IDserial_contains):
    result = init_usb_modbus(usb_devname_contains, usb_IDserial_contains)
    global num_of_registers_usb
    num_of_registers_usb = 2
    return result

def init_usb_modbus_16bit(usb_devname_contains, usb_IDserial_contains):
    result = init_usb_modbus(usb_devname_contains, usb_IDserial_contains)
    global num_of_registers_usb
    num_of_registers_usb = 1
    return result

def init_usb_modbus_no_error_handling_64bit(usb_devname_contains, usb_IDserial_contains):
    result = init_usb_modbus_64bit(usb_devname_contains, usb_IDserial_contains)
    global error_handling_usb
    error_handling_usb = False
    return result["value"]

def init_usb_modbus_no_error_handling_32bit(usb_devname_contains, usb_IDserial_contains):
    result = init_usb_modbus_32bit(usb_devname_contains, usb_IDserial_contains)
    global error_handling_usb
    error_handling_usb = False
    return result["value"]

def init_usb_modbus_no_error_handling_16bit(usb_devname_contains, usb_IDserial_contains):
    result = init_usb_modbus_16bit(usb_devname_contains, usb_IDserial_contains)
    global error_handling_usb
    error_handling_usb = False
    return result["value"]

def init_usb_modbus(usb_devname_contains, usb_IDserial_contains):
    if type(usb_devname_contains) == str:
        usb_devname_contains = [usb_devname_contains]
    if type(usb_IDserial_contains) == str:
        usb_IDserial_contains = [usb_IDserial_contains]
    devname_ls = find_usb_device(usb_devname_contains, usb_IDserial_contains)
    if not devname_ls:
        return {"value": 0, "error": "Unable to find " + ", ".join(usb_IDserial_contains) + " among USB devices", "error_flag": True}

    global instrument_usb
    instrument_usb = []
    for devname in devname_ls:
        instrument = modbus.Instrument('/dev/{}'.format(devname))
    
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

        instrument_usb.append(instrument)

    global error_handling_usb
    error_handling_usb = True

    return {"value":len(instrument_usb), "error": "Devices found: " + ", ".join(devname_ls), "error_flag": False}


''' Functions for modifying default settings '''
def usb_modbus_set_baudrate(baudrate):
    if baudrate in (9600, 19200, 38400, 57600, 115200, 1000000, 2000000, 5000000):
        if instrument_usb:
            for instrument in instrument_usb:
                instrument.serial.baudrate = baudrate
                result = {"value":True, "error": "", "error_flag": False}
        else:
            result = {"value":False, "error": "No modbus slaves connected via USB", "error_flag": True}
    else:
        result = {"value":False, "error": "Invalid baudrate", "error_flag": True}
    
    if error_handling_usb:
        return result
    else:
        return result['value']

def usb_modbus_set_bytesize(bytesize):
    if bytesize in (5, 6, 7, 8):
        if instrument_usb:
            for instrument in instrument_usb:
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
            for instrument in instrument_usb:
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
            for instrument in instrument_usb:
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
        for instrument in instrument_usb:
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
    for instrument in instrument_usb:
        try:
            data = bool(data)
            instrument.write_bit(slave_address, register_address, data, 5)
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
    for instrument in instrument_usb:
        try:
            value = instrument.read_bit(slave_address, register_address)
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
    for instrument in instrument_usb:
        try:
            value = instrument.read_bit(slave_address, register_address, functioncode=1)
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


''' Functions for 16/32/64 bit communication '''
def usb_modbus_write_holding_int(slave_address, register_address, data):
    '''Function to write INT16/INT32/INT64 to slave using 1/2/4 registers. Maps register_address to multiples of 1/2/4 to ensure no overlap.'''
    result = {"value": data, "error": "", "error_flag": True}
    try:
        data = int(data)
        data = signed_to_unsigned(num_of_registers_usb*16, data)    # most significant bit denotes sign
        val = []
        for i in range(num_of_registers_usb-1, -1, -1):    # start from highest 16 bits to lowest 16 bits
            val.append((data >> 16*i) & 0xFFFF)
    except Exception as e:
        result["error"] = repr(e)
    else:
        for instrument in instrument_usb:
            try:
                instrument.write_registers(slave_address, register_address*num_of_registers_usb,val)
                result = {"value": data, "error": "", "error_flag": False}
                break
            except Exception as e:
                Logger.error("data: %s", data)
                for i in range(len(val)):
                    Logger.error("val{}: {}".format(i,val[i]))
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
        for instrument in instrument_usb:
            try:
                instrument.write_float(slave_address, register_address*num_of_registers_usb, data, number_of_registers=num_of_registers_usb)
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
    for instrument in instrument_usb:
        try:
            val = instrument.read_registers(slave_address, register_address*num_of_registers_usb, num_of_registers_usb, functioncode=4)
            result = {"value": 0, "error": "", "error_flag": False}
            break
        except Exception as e:
            Logger.error("Error in modbus read method", exc_info=True)
            result["error"] = result["error"] + "{}: ".format(instrument.serial.port) + repr(e) + ", "
    if not result["error_flag"]:
        try:
            val_comb = val[0]
            for i in range(1,num_of_registers_usb):
                val_comb = (val_comb << 16) + val[i]
            result["value"] = unsigned_to_signed(num_of_registers_usb*16, val_comb)   # most significant bit denotes sign
        except Exception as e:
            result = {"value": 0, "error": repr(e), "error_flag": True}
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
        for instrument in instrument_usb:
            try:
                val = instrument.read_float(slave_address, register_address*num_of_registers_usb, number_of_registers=num_of_registers_usb, functioncode=4)
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
    for instrument in instrument_usb:
        try:
            val = instrument.read_registers(slave_address, register_address*num_of_registers_usb, num_of_registers_usb, functioncode=3)
            result = {"value": 0, "error": "", "error_flag": False}
            break
        except Exception as e:
            Logger.error("Error in modbus read method", exc_info=True)
            result["error"] = result["error"] + "{}: ".format(instrument.serial.port) + repr(e) + ", "
    if not result["error_flag"]:
        try:
            val_comb = val[0]
            for i in range(1,num_of_registers_usb):
                val_comb = (val_comb << 16) + val[i]
            result["value"] = unsigned_to_signed(num_of_registers_usb*16, val_comb)   # most significant bit denotes sign
        except Exception as e:
            result = {"value": 0, "error": repr(e), "error_flag": True}
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
        for instrument in instrument_usb:
            try:
                val = instrument.read_float(slave_address, register_address*num_of_registers_usb, number_of_registers=num_of_registers_usb, functioncode=3)
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


''' helper functions for adding sign '''
def signed_to_unsigned(num_bits, value):
    '''Function to convert INT-num_bits to UINT-num_bits'''
    if value < 0:
        value += (1<<num_bits)
    return value
 
def unsigned_to_signed(num_bits, value):
    '''Function to convert UINT-num_bits to INT-num_bits'''
    if value >= (1 << (num_bits-1)):
        value -= (1 << (num_bits))
    return value



''' Unused functions '''
# def tool_modbus_write_holding(slave_address, register_address, data):
#     '''Function to write INT-16 data to slave using 1 register'''
#     if data is None:
#         return False
#     try:
#         instrument_tool.write_register(slave_address, register_address,data,0, 16, True)
#     except Exception as e:
#         Logger.error("data: %s", data)
#         Logger.error("Error in modbus write method", exc_info=True)
#         return repr(e)
#     return True

# def tool_modbus_read_input(slave_address, register_address):
#     '''Function to read INT-16 data from slave using 1 register'''
#     try:
#         value = int(instrument_tool.read_register(slave_address, register_address, 0, 4, True))
#     except Exception as e:
#         Logger.error("Error in modbus read method", exc_info=True)
#         return repr(e)
#     return value

# def tool_modbus_read_holding(slave_address, register_address):
#     '''Function to read back INT-16 data from master using 1 register'''
#     try:
#         value = int(instrument_tool.read_register(slave_address, register_address, 0, 3, True))
#     except Exception as e:
#         Logger.error("Error in modbus read method", exc_info=True)
#         return repr(e)
#     return value

# def tool_modbus_write_holdings(slave_address, register_address, num_of_registers, decimal, data):
#     '''Function to write data to slave with the specified number of registers (size = 16*num_of_registers), to the specified decimal, signed'''
#     if data is None:
#         return False
#     data = float(data) * 10**decimal # scaling
#     data = signed_to_unsigned(num_of_registers*16, data)
#     data = int(data)
#     val = []
#     for i in range(num_of_registers-1, -1, -1):    # start from highest 16 bits to lowest 16 bits
#         val.append((data >> 16*i) & 0xFFFF)
#     try:
#         instrument_tool.write_registers(slave_address, register_address,val)
#     except Exception as e:
#         Logger.error("data: %s", data)
#         for i in range(len(val)):
#         Logger.error("val{}: {}".format(i,val[i]))
#         Logger.error("Error in modbus write method", exc_info=True)
#         return repr(e)
#     return True

# def tool_modbus_read_inputs(slave_address, register_address, num_of_registers, decimal):
#     '''Function to read data from slave with the specified number of registers (size = 16*num_of_registers), to the specified decimal, signed'''
#     try:
#         val = instrument_tool.read_registers(slave_address, register_address, num_of_registers, functioncode=4)
#         val_comb = val[0]
#         for i in range(1,num_of_registers):
#         val_comb = (val_comb << 16) + val[i]
#         val_comb = unsigned_to_signed(num_of_registers*16, val_comb)
#         value = val_comb/(10**decimal)
#     except Exception as e:
#         Logger.error("Error in modbus read method", exc_info=True)
#         return repr(e)
#     return value

# def tool_modbus_read_holdings(slave_address, register_address, num_of_registers, decimal):
#     '''Function to read back data from master with the specified number of registers (size = 16*num_of_registers), to the specified decimal, signed'''
#     try:
#         val = instrument_tool.read_registers(slave_address, register_address, num_of_registers, functioncode=3)
#         val_comb = val[0]
#         for i in range(1,num_of_registers):
#         val_comb = (val_comb << 16) + val[i]
#         val_comb = unsigned_to_signed(num_of_registers*16, val_comb)
#         value = val_comb/(10**decimal)
#     except Exception as e:
#         Logger.error("Error in modbus read method", exc_info=True)
#         return repr(e)
#     return value

# def tool_modbus_write_coils(slave_address, register_address, data):
#     '''Function to write multiple BOOL to slave in list format or single BOOL in BOOL or list format'''
#     if data is None:
#         return False
#     elif isinstance(data, list):
#         data = list(map(bool,data))
#     else:
#         data = [bool(data)]
#     try:
#         instrument_tool.write_bits(slave_address, register_address, data)
#     except Exception as e:
#         for i in range(len(data)):
#         Logger.error("val{}:{}".format(i,data[i]))
#         Logger.error("Error in modbus write method", exc_info=True)
#         return repr(e)
#     return True

# def tool_modbus_read_discretes(slave_address, register_address, num_of_registers):
#     '''Function to read multiple BOOL from slave in list format or single BOOL as BOOL'''
#     try:
#         val = instrument_tool.read_bits(slave_address, register_address, num_of_registers, functioncode=2)
#         value = list(map(bool,val))
#     except Exception as e:
#         Logger.error("Error in modbus read method", exc_info=True)
#         return repr(e)
#     if num_of_registers == 1:
#         return value[0]
#     else:
#         return value

# def tool_modbus_read_coils(slave_address, register_address, num_of_registers):
#     '''Function to read multiple BOOL from slave in list format or single BOOL as BOOL'''
#     try:
#         val = instrument_tool.read_bits(slave_address, register_address, num_of_registers, functioncode=1)
#         value = list(map(bool,val))
#     except Exception as e:
#         Logger.error("Error in modbus read method", exc_info=True)
#         return repr(e)
#     if num_of_registers == 1:
#         return value[0]
#     else:
#         return value

# def tool_modbus_increment(data, inc):
#     if data is not None:
#         new_data = data + inc
#         return new_data
#     Logger.error("Error in modbus increment method", exc_info=True)
#     return None


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
server.register_function(tool_modbus_write_holding_int,"tool_modbus_write_holding_int")
server.register_function(tool_modbus_write_holding_float,"tool_modbus_write_holding_float")
server.register_function(tool_modbus_read_input_int,"tool_modbus_read_input_int")
server.register_function(tool_modbus_read_input_float,"tool_modbus_read_input_float")
server.register_function(tool_modbus_read_holding_int,"tool_modbus_read_holding_int")
server.register_function(tool_modbus_read_holding_float,"tool_modbus_read_holding_float")

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
server.register_function(usb_modbus_write_holding_int,"usb_modbus_write_holding_int")
server.register_function(usb_modbus_write_holding_float,"usb_modbus_write_holding_float")
server.register_function(usb_modbus_read_input_int,"usb_modbus_read_input_int")
server.register_function(usb_modbus_read_input_float,"usb_modbus_read_input_float")
server.register_function(usb_modbus_read_holding_int,"usb_modbus_read_holding_int")
server.register_function(usb_modbus_read_holding_float,"usb_modbus_read_holding_float")

''' Unused functions '''
# server.register_function(tool_modbus_write_holding,"tool_modbus_write_holding")
# server.register_function(tool_modbus_read_input,"tool_modbus_read_input")
# server.register_function(tool_modbus_read_holding,"tool_modbus_read_holding")
# server.register_function(tool_modbus_write_holdings,"tool_modbus_write_holdings")
# server.register_function(tool_modbus_read_inputs,"tool_modbus_read_inputs")
# server.register_function(tool_modbus_read_holdings,"tool_modbus_read_holdings")
# server.register_function(tool_modbus_write_coils,"tool_modbus_write_coils")
# server.register_function(tool_modbus_read_discretes,"tool_modbus_read_discretes")
# server.register_function(tool_modbus_read_coils,"tool_modbus_read_coils")

server.serve_forever()

