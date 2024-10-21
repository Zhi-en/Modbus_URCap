#!/usr/bin/env python
# Changelog
# 2024-10-10: Wilfrid: Added more functions. Renamed init_modbus_communications to init_tool_modbus
# 2024-10-17: Wilfrid: Extended all functions to error handling versions which return struct.
# 2024-10-21: Zhi-en: Add error handling and number of bits (16, 32 or 64) to setting options

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

from SimpleXMLRPCServer import SimpleXMLRPCServer
from SocketServer import ThreadingMixIn

isShowing = False
LOCALHOST = "127.0.0.1"

instrument = None
value = None
baudrate = 115200
bytesize = 8
parity = "None"
stopbits = 1
timeout = 1   # seconds
num_of_registers = 4  # 4 for 64-bit ints and floats using holding and input registers. 2 for 32-bit ints and floats, 1 bit 16-bit ints only
error_handling = True


def isReachable():
  return True

def init_tool_modbus(slaveaddress):
  global instrument
  #instrument = modbus.Instrument('/dev/ttyUSB0',slaveaddress)
  instrument = modbus.Instrument('/dev/ttyTool',slaveaddress)
  #instrument = modbus.Instrument('/dev/ttyS0',slaveaddress)
  
  instrument.serial.baudrate = baudrate
  instrument.serial.bytesize = bytesize
  if parity == "None":
    instrument.serial.parity = serial.PARITY_NONE
  elif parity == "Even":
    instrument.serial.parity = serial.PARITY_EVEN
  elif parity == "Odd":
    instrument.serial.parity = serial.PARITY_ODD
  instrument.serial.stopbits = stopbits
  instrument.serial.timeout = timeout
  global error_handling
  error_handling = True
  return True

def init_tool_modbus_no_error_handling(slaveaddress):
  ''' only 1 of this or init_tool_modbus should be called to initiate the modbus URCAP '''
  init_tool_modbus(slaveaddress)
  global error_handling
  error_handling = False
  return True

''' Functions for modifying default settings '''
def tool_modbus_set_baudrate(baudrate):
  if baudrate in (9600, 19200, 38400, 57600, 115200, 1000000, 2000000, 5000000):
    instrument.serial.baudrate = baudrate
    return True
  else:
    return False

def tool_modbus_set_bytesize(bytesize):
  if bytesize in (5, 6, 7, 8):
    instrument.serial.bytesize = bytesize
    return True
  else:
    return False

def tool_modbus_set_parity(parity):
  if parity == "None":
    instrument.serial.parity = serial.PARITY_NONE
    return True
  elif parity == "Even":
    instrument.serial.parity = serial.PARITY_EVEN
    return True
  elif parity == "Odd":
    instrument.serial.parity = serial.PARITY_ODD
    return True
  else:
    return False

def tool_modbus_set_stopbit(stopbit):
  if stopbit in (1, 1.5, 2):
    instrument.serial.stopbits = stopbit
    return True
  else:
    return False

def tool_modbus_set_timeout(timeout):
  instrument.serial.timeout = timeout
  return True

def tool_modbus_set_register_chaining(register_chaining):
  if register_chaining in (1,2,4):
    global num_of_registers
    num_of_registers = register_chaining
    return True
  else:
    return False


''' Function for checking if connected in no error handling mode '''
def tool_modbus_check_connection(register_type, register):
  if register_type == "coil":
    try:
      instrument.read_bit(register, functioncode=1)
      return True
    except:
      return False
  elif register_type == "discrete":
    try:
      instrument.read_bit(register)
      return True
    except:
      return False
  elif register_type == "holding":
    try:
      instrument.read_register(0, functioncode=3)
      return True
    except:
      return False
  elif register_type == "input":
    try:
      instrument.read_register(0, functioncode=4)
      return True
    except:
      return False


''' Functions for bit communication '''
def tool_modbus_write_coil(register_address, data):
  '''Function to write single BOOL to slave'''
  result = {"error": "", "error_flag": False, "value": False}
  try:
    data = bool(data)
    instrument.write_bit(register_address, data, 5)
    result["value"] = True
  except Exception as e:
    Logger.error("data: %s", data)
    Logger.error("Error in modbus write method", exc_info=True)
    result["error"] = repr(e)
    result["error_flag"] = True
  if error_handling:
    return result
  elif result["error_flag"]:
    return result["error"]
  else:
    return result["value"]

def tool_modbus_read_discrete(register_address):
  '''Function to read single BOOL from slave'''
  result = {"error": "", "error_flag": False, "value": False}
  try:
    value = instrument.read_bit(register_address)
    result["value"] = bool(value)
  except Exception as e:
    Logger.error("Error in modbus read method", exc_info=True)
    result["error"] = repr(e)
    result["error_flag"] = True
  if error_handling:
    return result
  elif result["error_flag"]:
    return result["error"]
  else:
    return result["value"]

def tool_modbus_read_coil(register_address):
  '''Function to read back BOOL from master'''
  result = {"error": "", "error_flag": False, "value": False}
  try:
    value = instrument.read_bit(register_address, functioncode=1)
    result["value"] = bool(value)
  except Exception as e:
    Logger.error("Error in modbus read method", exc_info=True)
    result["error"] = repr(e)
    result["error_flag"] = True
  if error_handling:
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

''' Funcionts for 16/32/64 bit communication '''
def tool_modbus_write_holding_int(register_address, data):
  '''Function to write INT16/INT32/INT64 to slave using 1/2/4 registers. Maps register_address to multiples of 1/2/4 to ensure no overlap.'''
  result = {"error": "", "error_flag": False, "value": False}
  try:
    data = int(data)
    data = signed_to_unsigned(num_of_registers*16, data)    # most significant bit denotes sign
    val = []
    for i in range(num_of_registers-1, -1, -1):    # start from highest 16 bits to lowest 16 bits
      val.append((data >> 16*i) & 0xFFFF)
    instrument.write_registers(register_address*num_of_registers,val)
    result["value"] = True
  except Exception as e:
    Logger.error("data: %s", data)
    for i in range(len(val)):
      Logger.error("val{}: {}".format(i,val[i]))
    Logger.error("Error in modbus write method", exc_info=True)
    result["error"] =  repr(e)
    result["error_flag"] = True
  if error_handling:
    return result
  elif result["error_flag"]:
    return result["error"]
  else:
    return result["value"]

def tool_modbus_write_holding_float(register_address, data):
  '''Function to write FLOAT32/FLOAT64 to slave using 2/4 registers. Maps register_address to multiples of 2/4 to ensure no overlap. Will return error if num_of_registers = 1 '''
  result = {"error": "", "error_flag": False, "value": False}
  if num_of_registers <2:
    result["error"] =  "16-bit does not support float types"
    result["error_flag"] = True
  else:
    try:
      instrument.write_float(register_address*num_of_registers, data, number_of_registers=num_of_registers)
      result["value"] = True
    except Exception as e:
      Logger.error("data: %s", data)
      Logger.error("Error in modbus write method", exc_info=True)
      result["error"] =  repr(e)
      result["error_flag"] = True
  if error_handling:
    return result
  elif result["error_flag"]:
    return result["error"]
  else:
    return result["value"]

def tool_modbus_read_input_int(register_address):
  '''Function to read INT16/INT32/INT64 from slave using 1/2/4 registers. Maps register_address to multiples of 1/2/4 to ensure no overlap.'''
  result = {"error": "", "error_flag": False, "value": 0}
  try:
    val = instrument.read_registers(register_address*num_of_registers, num_of_registers, functioncode=4)
    val_comb = val[0]
    for i in range(1,num_of_registers):
      val_comb = (val_comb << 16) + val[i]
    result["value"] = unsigned_to_signed(num_of_registers*16, val_comb)   # most significant bit denotes sign
  except Exception as e:
    Logger.error("Error in modbus read method", exc_info=True)
    result["error"] =  repr(e)
    result["error_flag"] = True
  if error_handling:
    return result
  elif result["error_flag"]:
    return result["error"]
  else:
    return result["value"]

def tool_modbus_read_input_float(register_address):
  '''Function to read FLOAT32/FLOAT64 from slave using 2/4 registers. Maps register_address to multiples of 2/4 to ensure no overlap. Will return error if num_of_registers = 1 '''
  result = {"error": "", "error_flag": False, "value": 0.0}
  if num_of_registers <2:
    result["error"] =  "16-bit does not support float types"
    result["error_flag"] = True
  try:
    result["value"] = instrument.read_float(register_address*num_of_registers, number_of_registers=num_of_registers, functioncode=4)
  except Exception as e:
    Logger.error("Error in modbus read method", exc_info=True)
    result["error"] =  repr(e)
    result["error_flag"] = True
  if error_handling:
    return result
  elif result["error_flag"]:
    return result["error"]
  else:
    return result["value"]

def tool_modbus_read_holding_int(register_address):
  '''Function to read back INT16/INT32/INT64 from master using 1/2/4 registers. Maps register_address to multiples of 1/2/4 to ensure no overlap.'''
  result = {"error": "", "error_flag": False, "value": 0}
  try:
    val = instrument.read_registers(register_address*num_of_registers, num_of_registers, functioncode=3)
    val_comb = val[0]
    for i in range(1,num_of_registers):
      val_comb = (val_comb << 16) + val[i]
    result["value"] = unsigned_to_signed(num_of_registers*16, val_comb)   # most significant bit denotes sign
  except Exception as e:
    Logger.error("Error in modbus read method", exc_info=True)
    result["error"] =  repr(e)
    result["error_flag"] = True
  if error_handling:
    return result
  elif result["error_flag"]:
    return result["error"]
  else:
    return result["value"]

def tool_modbus_read_holding_float(register_address):
  '''Function to read back FLOAT32/FLOAT64 from master using 2/4 registers. Maps register_address to multiples of 2/4 to ensure no overlap. Will return error if num_of_registers = 1 '''
  result = {"error": "", "error_flag": False, "value": 0.0}
  if num_of_registers <2:
    result["error"] =  "16-bit does not support float types"
    result["error_flag"] = True
  try:
    result["value"] = instrument.read_float(register_address*num_of_registers, number_of_registers=num_of_registers, functioncode=3)
  except Exception as e:
    Logger.error("Error in modbus read method", exc_info=True)
    result["error"] =  repr(e)
    result["error_flag"] = True
  if error_handling:
    return result
  elif result["error_flag"]:
    return result["error"]
  else:
    return result["value"]

''' Unused functions '''
def tool_modbus_write_holding(register_address, data):
  '''Function to write INT-16 data to slave using 1 register'''
  if data is None:
    return False
  try:
    instrument.write_register(register_address,data,0, 16, True)
  except Exception as e:
    Logger.error("data: %s", data)
    Logger.error("Error in modbus write method", exc_info=True)
    return repr(e)
  return True

def tool_modbus_read_input(register_address):
  '''Function to read INT-16 data from slave using 1 register'''
  global value
  try:
    value = int(instrument.read_register(register_address, 0, 4, True))
  except Exception as e:
    Logger.error("Error in modbus read method", exc_info=True)
    return repr(e)
  return value

def tool_modbus_read_holding(register_address):
  '''Function to read back INT-16 data from master using 1 register'''
  try:
    value = int(instrument.read_register(register_address, 0, 3, True))
  except Exception as e:
    Logger.error("Error in modbus read method", exc_info=True)
    return repr(e)
  return value

def tool_modbus_write_holdings(register_address, num_of_registers, decimal, data):
  '''Function to write data to slave with the specified number of registers (size = 16*num_of_registers), to the specified decimal, signed'''
  if data is None:
    return False
  data = float(data) * 10**decimal # scaling
  data = signed_to_unsigned(num_of_registers*16, data)
  data = int(data)
  val = []
  for i in range(num_of_registers-1, -1, -1):    # start from highest 16 bits to lowest 16 bits
    val.append((data >> 16*i) & 0xFFFF)
  try:
    instrument.write_registers(register_address,val)
  except Exception as e:
    Logger.error("data: %s", data)
    for i in range(len(val)):
      Logger.error("val{}: {}".format(i,val[i]))
    Logger.error("Error in modbus write method", exc_info=True)
    return repr(e)
  return True

def tool_modbus_read_inputs(register_address, num_of_registers, decimal):
  '''Function to read data from slave with the specified number of registers (size = 16*num_of_registers), to the specified decimal, signed'''
  try:
    val = instrument.read_registers(register_address, num_of_registers, functioncode=4)
    val_comb = val[0]
    for i in range(1,num_of_registers):
      val_comb = (val_comb << 16) + val[i]
    val_comb = unsigned_to_signed(num_of_registers*16, val_comb)
    value = val_comb/(10**decimal)
  except Exception as e:
    Logger.error("Error in modbus read method", exc_info=True)
    return repr(e)
  return value

def tool_modbus_read_holdings(register_address, num_of_registers, decimal):
  '''Function to read back data from master with the specified number of registers (size = 16*num_of_registers), to the specified decimal, signed'''
  try:
    val = instrument.read_registers(register_address, num_of_registers, functioncode=3)
    val_comb = val[0]
    for i in range(1,num_of_registers):
      val_comb = (val_comb << 16) + val[i]
    val_comb = unsigned_to_signed(num_of_registers*16, val_comb)
    value = val_comb/(10**decimal)
  except Exception as e:
    Logger.error("Error in modbus read method", exc_info=True)
    return repr(e)
  return value

def tool_modbus_write_coils(register_address, data):
  '''Function to write multiple BOOL to slave in list format or single BOOL in BOOL or list format'''
  if data is None:
    return False
  elif isinstance(data, list):
    data = list(map(bool,data))
  else:
    data = [bool(data)]
  try:
    instrument.write_bits(register_address, data)
  except Exception as e:
    for i in range(len(data)):
      Logger.error("val{}:{}".format(i,data[i]))
    Logger.error("Error in modbus write method", exc_info=True)
    return repr(e)
  return True

def tool_modbus_read_discretes(register_address, num_of_registers):
  '''Function to read multiple BOOL from slave in list format or single BOOL as BOOL'''
  try:
    val = instrument.read_bits(register_address, num_of_registers, functioncode=2)
    value = list(map(bool,val))
  except Exception as e:
    Logger.error("Error in modbus read method", exc_info=True)
    return repr(e)
  if num_of_registers == 1:
    return value[0]
  else:
    return value

def tool_modbus_read_coils(register_address, num_of_registers):
  '''Function to read multiple BOOL from slave in list format or single BOOL as BOOL'''
  try:
    val = instrument.read_bits(register_address, num_of_registers, functioncode=1)
    value = list(map(bool,val))
  except Exception as e:
    Logger.error("Error in modbus read method", exc_info=True)
    return repr(e)
  if num_of_registers == 1:
    return value[0]
  else:
    return value

def tool_modbus_increment(data, inc):
  if data is not None:
    new_data = data + inc
    return new_data
  Logger.error("Error in modbus increment method", exc_info=True)
  return None


class MultithreadedSimpleXMLRPCServer(ThreadingMixIn, SimpleXMLRPCServer):
    pass

# Connection related functions
server = MultithreadedSimpleXMLRPCServer((LOCALHOST, 40408), allow_none=True)
server.RequestHandlerClass.protocol_version = "HTTP/1.1"
print("Listening on port 40408...")

server.register_function(isReachable,"isReachable")
server.register_function(init_tool_modbus,"init_tool_modbus")
server.register_function(init_tool_modbus_no_error_handling,"init_tool_modbus_no_error_handling")
server.register_function(tool_modbus_set_baudrate,"tool_modbus_set_baudrate")
server.register_function(tool_modbus_set_bytesize,"tool_modbus_set_bytesize")
server.register_function(tool_modbus_set_parity,"tool_modbus_set_parity")
server.register_function(tool_modbus_set_stopbit,"tool_modbus_set_stopbit")
server.register_function(tool_modbus_set_timeout,"tool_modbus_set_timeout")
server.register_function(tool_modbus_set_register_chaining,"tool_modbus_set_register_chaining")
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

