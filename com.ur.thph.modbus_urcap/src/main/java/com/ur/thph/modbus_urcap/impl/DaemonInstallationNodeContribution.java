package com.ur.thph.modbus_urcap.impl;

import java.awt.EventQueue;
import java.util.Timer;
import java.util.TimerTask;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.ScheduledFuture;
import java.util.concurrent.TimeUnit;

import com.ur.urcap.api.contribution.DaemonContribution;
import com.ur.urcap.api.contribution.InstallationNodeContribution;
import com.ur.urcap.api.contribution.installation.CreationContext;
import com.ur.urcap.api.contribution.installation.InstallationAPIProvider;
import com.ur.urcap.api.domain.data.DataModel;
import com.ur.urcap.api.domain.script.ScriptWriter;

public class DaemonInstallationNodeContribution implements InstallationNodeContribution {
	
	private final ModbusDaemonService modbusDaemonService;
	private ModbusDaemonInterface modbusDaemonInterface;
	private static final long DAEMON_TIME_OUT_NANO_SECONDS = TimeUnit.SECONDS.toNanos(20);
	private static final long RETRY_TIME_TO_WAIT_MILLI_SECONDS = TimeUnit.SECONDS.toMillis(5);
	
	private final DaemonInstallationNodeView view;
	
	private Timer uiTimer;
	private boolean pauseTimer;
	private DataModel model;
	private final ScheduledExecutorService executorService = Executors.newScheduledThreadPool(1);
	private ScheduledFuture<?> scheduleAtFixedRate;
	
	private static final int PORT = 40408;
	private static final String HOST = "127.0.0.1";
	
	private static final String ENABLED_KEY = "enabled";
	private static final String XMLRPC_VARIABLE = "modbus_xmlrpc";
	
	

	public DaemonInstallationNodeContribution(InstallationAPIProvider apiProvider, 
											  DaemonInstallationNodeView view,
											  DataModel model, 
											  ModbusDaemonService modbusDaemonService
											  ) {
		
		this.modbusDaemonService = modbusDaemonService;
		this.modbusDaemonInterface = new ModbusDaemonInterface();
		this.pauseTimer = false;
		this.model = model;
		this.view = view;
	
		applyDesiredDaemonStatus();
	}

	private boolean getCB() {
		return (model.get(ENABLED_KEY, true));
	}

	@Override
	public void openView() {
//		modbusDaemonInterface.startMonitorThread();
		
		
		if (getCB() && (DaemonContribution.State.STOPPED.equals(this.modbusDaemonService.getDaemon().getState()))) {
			System.out.println("Daemon state: STOPPED, apply starting daemon.");
			applyDesiredDaemonStatus();
		} else if (getCB() == false) {
			this.modbusDaemonService.getDaemon().stop();
		}

		// UI updates from non-GUI threads must use EventQueue.invokeLater (or SwingUtilities.invokeLater)
		uiTimer = new Timer(true);
		uiTimer.schedule(new TimerTask() {
			
			@Override
			public void run() {
				// TODO Auto-generated method stub
				updateUI();
			}
		}, 0, 1000);
	}

	@Override
	public void closeView() {
		if(uiTimer != null) {
			uiTimer.cancel();
		}

	}

	@Override
	public void generateScript(ScriptWriter writer) {
		//writer.assign(XMLRPC_VARIABLE, "rpc_factory(\"xmlrpc\", \"http://127.0.0.1:40408/RPC2\")");
		writer.assign(XMLRPC_VARIABLE, "rpc_factory(\"xmlrpc\", \"" + ModbusDaemonInterface.getDaemonUrl() + "\")");
		
		writer.appendLine("isConnected = modbus_xmlrpc.isReachable()");
		writer.appendLine("if ( isConnected != True):");
		writer.appendLine("popup(\"Modbus xmlrpc is not available!\")");
		writer.appendLine("end");
        
        //Modbus init method: ex --> init_tool_modbus_64bit(1)
		writer.appendLine("def init_tool_modbus_64bit(slave_address):");
		writer.appendLine("local response = modbus_xmlrpc.init_tool_modbus_64bit(slave_address)");
		writer.appendLine("return response");
		writer.appendLine("end");
		
		//Modbus init method: ex --> init_tool_modbus_32bit(1)
		writer.appendLine("def init_tool_modbus_32bit(slave_address):");
		writer.appendLine("local response = modbus_xmlrpc.init_tool_modbus_32bit(slave_address)");
		writer.appendLine("return response");
		writer.appendLine("end");
		
		//Modbus init method: ex --> init_tool_modbus_16bit(1)
		writer.appendLine("def init_tool_modbus_16bit(slave_address):");
		writer.appendLine("local response = modbus_xmlrpc.init_tool_modbus_16bit(slave_address)");
		writer.appendLine("return response");
		writer.appendLine("end");
		
		//Modbus init method: ex --> init_tool_modbus_no_error_handling_64bit(1)
		writer.appendLine("def init_tool_modbus_no_error_handling_64bit(slave_address):");
		writer.appendLine("local response = modbus_xmlrpc.init_tool_modbus_no_error_handling_64bit(slave_address)");
		writer.appendLine("return response");
		writer.appendLine("end");
		
		//Modbus init method: ex --> init_tool_modbus_no_error_handling_32bit(1)
		writer.appendLine("def init_tool_modbus_no_error_handling_32bit(slave_address):");
		writer.appendLine("local response = modbus_xmlrpc.init_tool_modbus_no_error_handling_32bit(slave_address)");
		writer.appendLine("return response");
		writer.appendLine("end");
		
		//Modbus init method: ex --> init_tool_modbus_no_error_handling_16bit(1)
		writer.appendLine("def init_tool_modbus_no_error_handling_16bit(slave_address):");
		writer.appendLine("local response = modbus_xmlrpc.init_tool_modbus_no_error_handling_16bit(slave_address)");
		writer.appendLine("return response");
		writer.appendLine("end");
		
		//Modbus init method: ex --> tool_modbus_set_baudrate(115200)
		writer.appendLine("def tool_modbus_set_baudrate(baudrate):");
		writer.appendLine("local response = modbus_xmlrpc.tool_modbus_set_baudrate(baudrate)");
		writer.appendLine("return response");
		writer.appendLine("end");
		
		//Modbus init method: ex --> tool_modbus_set_bytesize(8)
		writer.appendLine("def tool_modbus_set_bytesize(bytesize):");
		writer.appendLine("local response = modbus_xmlrpc.tool_modbus_set_bytesize(bytesize)");
		writer.appendLine("return response");
		writer.appendLine("end");
		
		//Modbus init method: ex --> tool_modbus_set_parity("None")
		writer.appendLine("def tool_modbus_set_parity(parity):");
		writer.appendLine("local response = modbus_xmlrpc.tool_modbus_set_parity(parity)");
		writer.appendLine("return response");
		writer.appendLine("end");
		
		//Modbus init method: ex --> tool_modbus_set_stopbits(1)
		writer.appendLine("def tool_modbus_set_stopbits(stopbits):");
		writer.appendLine("local response = modbus_xmlrpc.tool_modbus_set_stopbits(stopbits)");
		writer.appendLine("return response");
		writer.appendLine("end");
		
		//Modbus init method: ex --> tool_modbus_set_timeout(1)
		writer.appendLine("def tool_modbus_set_timeout(timeout):");
		writer.appendLine("local response = modbus_xmlrpc.tool_modbus_set_timeout(timeout)");
		writer.appendLine("return response");
		writer.appendLine("end");
		
		//Modbus init method: ex --> tool_modbus_check_connection(1, "holding", 0)
		writer.appendLine("def tool_modbus_check_connection(slave_address, register_type, register):");
		writer.appendLine("local response = modbus_xmlrpc.tool_modbus_check_connection(slave_address, register_type, register)");
		writer.appendLine("return response");
		writer.appendLine("end");

		//Modbus init method: ex --> tool_modbus_write_coil(1, 0, false)
		writer.appendLine("def tool_modbus_write_coil(slave_address, register_address, value):");
		writer.appendLine("local response = modbus_xmlrpc.tool_modbus_write_coil(slave_address, register_address, value)");
		writer.appendLine("return response");
		writer.appendLine("end");

		//Modbus init method: ex --> tool_modbus_read_discrete(1, 0)
		writer.appendLine("def tool_modbus_read_discrete(slave_address, register_address):");
		writer.appendLine("local response = modbus_xmlrpc.tool_modbus_read_discrete(slave_address, register_address)");
		writer.appendLine("return response");
		writer.appendLine("end");

		//Modbus init method: ex --> tool_modbus_read_coil(1, 0)
		writer.appendLine("def tool_modbus_read_coil(slave_address, register_address):");
		writer.appendLine("local response = modbus_xmlrpc.tool_modbus_read_coil(slave_address, register_address)");
		writer.appendLine("return response");
		writer.appendLine("end");

		//Modbus init method: ex --> tool_modbus_write_coils(1, 0, false)
		writer.appendLine("def tool_modbus_write_coils(slave_address, register_address, value):");
		writer.appendLine("local response = modbus_xmlrpc.tool_modbus_write_coils(slave_address, register_address, value)");
		writer.appendLine("return response");
		writer.appendLine("end");

		//Modbus init method: ex --> tool_modbus_read_discretes(1, 0, 1)
		writer.appendLine("def tool_modbus_read_discretes(slave_address, register_address, num_of_registers):");
		writer.appendLine("local response = modbus_xmlrpc.tool_modbus_read_discretes(slave_address, register_address, num_of_registers)");
		writer.appendLine("return response");
		writer.appendLine("end");

		//Modbus init method: ex --> tool_modbus_read_coils(1, 0, 1)
		writer.appendLine("def tool_modbus_read_coils(slave_address, register_address, num_of_registers):");
		writer.appendLine("local response = modbus_xmlrpc.tool_modbus_read_coils(slave_address, register_address, num_of_registers)");
		writer.appendLine("return response");
		writer.appendLine("end");
	
		//Modbus init method: ex --> tool_modbus_write_holdings(1, 0, [-1, 1, 1.1], ["int", "uint", "float"])
		writer.appendLine("def tool_modbus_write_holdings(slave_address, register_address, data, dtype):");
		writer.appendLine("local response = modbus_xmlrpc.tool_modbus_write_holdings(slave_address, register_address, data, dtype)");
		writer.appendLine("return response");
		writer.appendLine("end");
	
		//Modbus init method: ex --> tool_modbus_read_inputs(1, 0, ["int", "uint", "float"])
		writer.appendLine("def tool_modbus_read_inputs(slave_address, register_address, dtype):");
		writer.appendLine("local response = modbus_xmlrpc.tool_modbus_read_inputs(slave_address, register_address, dtype)");
		writer.appendLine("return response");
		writer.appendLine("end");
	
		//Modbus init method: ex --> tool_modbus_read_holdings(1, 0, ["int", "uint", "float"])
		writer.appendLine("def tool_modbus_read_holdings(slave_address, register_address, dtype):");
		writer.appendLine("local response = modbus_xmlrpc.tool_modbus_read_holdings(slave_address, register_address, dtype)");
		writer.appendLine("return response");
		writer.appendLine("end");

		//Modbus init method: ex --> tool_modbus_write_holding_int(1, 0, 1)
		writer.appendLine("def tool_modbus_write_holding_int(slave_address, register_address, value):");
		writer.appendLine("local response = modbus_xmlrpc.tool_modbus_write_holding_int(slave_address, register_address, value)");
		writer.appendLine("return response");
		writer.appendLine("end");

		//Modbus init method: ex --> tool_modbus_write_holding_float(1, 0, 1.1)
		writer.appendLine("def tool_modbus_write_holding_float(slave_address, register_address, value):");
		writer.appendLine("local response = modbus_xmlrpc.tool_modbus_write_holding_float(slave_address, register_address, value)");
		writer.appendLine("return response");
		writer.appendLine("end");
	
		//Modbus init method: ex --> tool_modbus_read_input_int(1, 0)
		writer.appendLine("def tool_modbus_read_input_int(slave_address, register_address):");
		writer.appendLine("local response = modbus_xmlrpc.tool_modbus_read_input_int(slave_address, register_address)");
		writer.appendLine("return response");
		writer.appendLine("end");
	
		//Modbus init method: ex --> tool_modbus_read_input_float(1, 0)
		writer.appendLine("def tool_modbus_read_input_float(slave_address, register_address):");
		writer.appendLine("local response = modbus_xmlrpc.tool_modbus_read_input_float(slave_address, register_address)");
		writer.appendLine("return response");
		writer.appendLine("end");
	
		//Modbus init method: ex --> tool_modbus_read_holding_int(1, 0)
		writer.appendLine("def tool_modbus_read_holding_int(slave_address, register_address):");
		writer.appendLine("local response = modbus_xmlrpc.tool_modbus_read_holding_int(slave_address, register_address)");
		writer.appendLine("return response");
		writer.appendLine("end");
	
		//Modbus init method: ex --> tool_modbus_read_holding_float(1, 0)
		writer.appendLine("def tool_modbus_read_holding_float(slave_address, register_address):");
		writer.appendLine("local response = modbus_xmlrpc.tool_modbus_read_holding_float(slave_address, register_address)");
		writer.appendLine("return response");
		writer.appendLine("end");

		//Modbus init method: ex --> tool_modbus_write_holdings_int(1, 0, 1)
		writer.appendLine("def tool_modbus_write_holdings_int(slave_address, register_address, value):");
		writer.appendLine("local response = modbus_xmlrpc.tool_modbus_write_holdings_int(slave_address, register_address, value)");
		writer.appendLine("return response");
		writer.appendLine("end");

		//Modbus init method: ex --> tool_modbus_write_holdings_float(1, 0, 1.1)
		writer.appendLine("def tool_modbus_write_holdings_float(slave_address, register_address, value):");
		writer.appendLine("local response = modbus_xmlrpc.tool_modbus_write_holdings_float(slave_address, register_address, value)");
		writer.appendLine("return response");
		writer.appendLine("end");
	
		//Modbus init method: ex --> tool_modbus_read_inputs_int(1, 0, 1)
		writer.appendLine("def tool_modbus_read_inputs_int(slave_address, register_address, num_of_values):");
		writer.appendLine("local response = modbus_xmlrpc.tool_modbus_read_inputs_int(slave_address, register_address, num_of_values)");
		writer.appendLine("return response");
		writer.appendLine("end");
	
		//Modbus init method: ex --> tool_modbus_read_inputs_float(1, 0, 1)
		writer.appendLine("def tool_modbus_read_inputs_float(slave_address, register_address, num_of_values):");
		writer.appendLine("local response = modbus_xmlrpc.tool_modbus_read_inputs_float(slave_address, register_address, num_of_values)");
		writer.appendLine("return response");
		writer.appendLine("end");
	
		//Modbus init method: ex --> tool_modbus_read_holdings_int(1, 0, 1)
		writer.appendLine("def tool_modbus_read_holdings_int(slave_address, register_address, num_of_values):");
		writer.appendLine("local response = modbus_xmlrpc.tool_modbus_read_holdings_int(slave_address, register_address, num_of_values)");
		writer.appendLine("return response");
		writer.appendLine("end");
	
		//Modbus init method: ex --> tool_modbus_read_holdings_float(1, 0, 1)
		writer.appendLine("def tool_modbus_read_holdings_float(slave_address, register_address, num_of_values):");
		writer.appendLine("local response = modbus_xmlrpc.tool_modbus_read_holdings_float(slave_address, register_address, num_of_values)");
		writer.appendLine("return response");
		writer.appendLine("end");
		
		// Modbus init method: ex --> init_usb_modbus_64bit(1, "ttyACM", "Arduino")
		writer.appendLine("def init_usb_modbus_64bit(slave_address, usb_devname_contains, usb_IDserial_contains):");
		writer.appendLine("local response = modbus_xmlrpc.init_usb_modbus_64bit(slave_address, usb_devname_contains, usb_IDserial_contains)");
		writer.appendLine("return response");
		writer.appendLine("end");
		
		//Modbus init method: ex --> init_usb_modbus_32bit(1, "ttyACM", "Arduino")
		writer.appendLine("def init_usb_modbus_32bit(slave_address, usb_devname_contains, usb_IDserial_contains):");
		writer.appendLine("local response = modbus_xmlrpc.init_usb_modbus_32bit(slave_address, usb_devname_contains, usb_IDserial_contains)");
		writer.appendLine("return response");
		writer.appendLine("end");
		
		//Modbus init method: ex --> init_usb_modbus_16bit(1, "ttyACM", "Arduino")
		writer.appendLine("def init_usb_modbus_16bit(slave_address, usb_devname_contains, usb_IDserial_contains):");
		writer.appendLine("local response = modbus_xmlrpc.init_usb_modbus_16bit(slave_address, usb_devname_contains, usb_IDserial_contains)");
		writer.appendLine("return response");
		writer.appendLine("end");
		
		//Modbus init method: ex --> init_usb_modbus_no_error_handling_64bit(1, "ttyACM", "Arduino")
		writer.appendLine("def init_usb_modbus_no_error_handling_64bit(slave_address, usb_devname_contains, usb_IDserial_contains):");
		writer.appendLine("local response = modbus_xmlrpc.init_usb_modbus_no_error_handling_64bit(slave_address, usb_devname_contains, usb_IDserial_contains)");
		writer.appendLine("return response");
		writer.appendLine("end");
		
		//Modbus init method: ex --> init_usb_modbus_no_error_handling_32bit(1, "ttyACM", "Arduino")
		writer.appendLine("def init_usb_modbus_no_error_handling_32bit(slave_address, usb_devname_contains, usb_IDserial_contains):");
		writer.appendLine("local response = modbus_xmlrpc.init_usb_modbus_no_error_handling_32bit(slave_address, usb_devname_contains, usb_IDserial_contains)");
		writer.appendLine("return response");
		writer.appendLine("end");
		
		//Modbus init method: ex --> init_usb_modbus_no_error_handling_16bit(1, "ttyACM", "Arduino")
		writer.appendLine("def init_usb_modbus_no_error_handling_16bit(slave_address, usb_devname_contains, usb_IDserial_contains):");
		writer.appendLine("local response = modbus_xmlrpc.init_usb_modbus_no_error_handling_16bit(slave_address, usb_devname_contains, usb_IDserial_contains)");
		writer.appendLine("return response");
		writer.appendLine("end");
		
		//Modbus init method: ex --> usb_modbus_set_baudrate(115200)
		writer.appendLine("def usb_modbus_set_baudrate(baudrate):");
		writer.appendLine("local response = modbus_xmlrpc.usb_modbus_set_baudrate(baudrate)");
		writer.appendLine("return response");
		writer.appendLine("end");
		
		//Modbus init method: ex --> usb_modbus_set_bytesize(8)
		writer.appendLine("def usb_modbus_set_bytesize(bytesize):");
		writer.appendLine("local response = modbus_xmlrpc.usb_modbus_set_bytesize(bytesize)");
		writer.appendLine("return response");
		writer.appendLine("end");
		
		//Modbus init method: ex --> usb_modbus_set_parity("None")
		writer.appendLine("def usb_modbus_set_parity(parity):");
		writer.appendLine("local response = modbus_xmlrpc.usb_modbus_set_parity(parity)");
		writer.appendLine("return response");
		writer.appendLine("end");
		
		//Modbus init method: ex --> usb_modbus_set_stopbits(1)
		writer.appendLine("def usb_modbus_set_stopbits(stopbits):");
		writer.appendLine("local response = modbus_xmlrpc.usb_modbus_set_stopbits(stopbits)");
		writer.appendLine("return response");
		writer.appendLine("end");
		
		//Modbus init method: ex --> usb_modbus_set_timeout(1)
		writer.appendLine("def usb_modbus_set_timeout(timeout):");
		writer.appendLine("local response = modbus_xmlrpc.usb_modbus_set_timeout(timeout)");
		writer.appendLine("return response");
		writer.appendLine("end");
		
		//Modbus init method: ex --> usb_modbus_check_connection(1, "holding", 0)
		writer.appendLine("def usb_modbus_check_connection(slave_address, register_type, register):");
		writer.appendLine("local response = modbus_xmlrpc.usb_modbus_check_connection(slave_address, register_type, register)");
		writer.appendLine("return response");
		writer.appendLine("end");

		//Modbus init method: ex --> usb_modbus_write_coil(1, 0, false)
		writer.appendLine("def usb_modbus_write_coil(slave_address, register_address, value):");
		writer.appendLine("local response = modbus_xmlrpc.usb_modbus_write_coil(slave_address, register_address, value)");
		writer.appendLine("return response");
		writer.appendLine("end");

		//Modbus init method: ex --> usb_modbus_read_discrete(1, 0)
		writer.appendLine("def usb_modbus_read_discrete(slave_address, register_address):");
		writer.appendLine("local response = modbus_xmlrpc.usb_modbus_read_discrete(slave_address, register_address)");
		writer.appendLine("return response");
		writer.appendLine("end");

		//Modbus init method: ex --> usb_modbus_read_coil(1, 0)
		writer.appendLine("def usb_modbus_read_coil(slave_address, register_address):");
		writer.appendLine("local response = modbus_xmlrpc.usb_modbus_read_coil(slave_address, register_address)");
		writer.appendLine("return response");
		writer.appendLine("end");

		//Modbus init method: ex --> usb_modbus_write_coils(1, 0, false)
		writer.appendLine("def usb_modbus_write_coils(slave_address, register_address, value):");
		writer.appendLine("local response = modbus_xmlrpc.usb_modbus_write_coils(slave_address, register_address, value)");
		writer.appendLine("return response");
		writer.appendLine("end");

		//Modbus init method: ex --> usb_modbus_read_discretes(1, 0, 1)
		writer.appendLine("def usb_modbus_read_discretes(slave_address, register_address, num_of_registers):");
		writer.appendLine("local response = modbus_xmlrpc.usb_modbus_read_discretes(slave_address, register_address, num_of_registers)");
		writer.appendLine("return response");
		writer.appendLine("end");

		//Modbus init method: ex --> usb_modbus_read_coils(1, 0, 1)
		writer.appendLine("def usb_modbus_read_coils(slave_address, register_address, num_of_registers):");
		writer.appendLine("local response = modbus_xmlrpc.usb_modbus_read_coils(slave_address, register_address, num_of_registers)");
		writer.appendLine("return response");
		writer.appendLine("end");
	
		//Modbus init method: ex --> usb_modbus_write_holdings(1, 0, [-1, 1, 1.1], ["int", "uint", "float"])
		writer.appendLine("def usb_modbus_write_holdings(slave_address, register_address, data, dtype):");
		writer.appendLine("local response = modbus_xmlrpc.usb_modbus_write_holdings(slave_address, register_address, data, dtype)");
		writer.appendLine("return response");
		writer.appendLine("end");
	
		//Modbus init method: ex --> usb_modbus_read_inputs(1, 0, ["int", "uint", "float"])
		writer.appendLine("def usb_modbus_read_inputs(slave_address, register_address, dtype):");
		writer.appendLine("local response = modbus_xmlrpc.usb_modbus_read_inputs(slave_address, register_address, dtype)");
		writer.appendLine("return response");
		writer.appendLine("end");
	
		//Modbus init method: ex --> usb_modbus_read_holdings(1, 0, ["int", "uint", "float"])
		writer.appendLine("def usb_modbus_read_holdings(slave_address, register_address, dtype):");
		writer.appendLine("local response = modbus_xmlrpc.usb_modbus_read_holdings(slave_address, register_address, dtype)");
		writer.appendLine("return response");
		writer.appendLine("end");

		//Modbus init method: ex --> usb_modbus_write_holding_int(1, 0, 1)
		writer.appendLine("def usb_modbus_write_holding_int(slave_address, register_address, value):");
		writer.appendLine("local response = modbus_xmlrpc.usb_modbus_write_holding_int(slave_address, register_address, value)");
		writer.appendLine("return response");
		writer.appendLine("end");

		//Modbus init method: ex --> usb_modbus_write_holding_float(1, 0, 1.1)
		writer.appendLine("def usb_modbus_write_holding_float(slave_address, register_address, value):");
		writer.appendLine("local response = modbus_xmlrpc.usb_modbus_write_holding_float(slave_address, register_address, value)");
		writer.appendLine("return response");
		writer.appendLine("end");
	
		//Modbus init method: ex --> usb_modbus_read_input_int(1, 0)
		writer.appendLine("def usb_modbus_read_input_int(slave_address, register_address):");
		writer.appendLine("local response = modbus_xmlrpc.usb_modbus_read_input_int(slave_address, register_address)");
		writer.appendLine("return response");
		writer.appendLine("end");
	
		//Modbus init method: ex --> usb_modbus_read_input_float(1, 0)
		writer.appendLine("def usb_modbus_read_input_float(slave_address, register_address):");
		writer.appendLine("local response = modbus_xmlrpc.usb_modbus_read_input_float(slave_address, register_address)");
		writer.appendLine("return response");
		writer.appendLine("end");
	
		//Modbus init method: ex --> usb_modbus_read_holding_int(1, 0)
		writer.appendLine("def usb_modbus_read_holding_int(slave_address, register_address):");
		writer.appendLine("local response = modbus_xmlrpc.usb_modbus_read_holding_int(slave_address, register_address)");
		writer.appendLine("return response");
		writer.appendLine("end");
	
		//Modbus init method: ex --> usb_modbus_read_holding_float(1, 0)
		writer.appendLine("def usb_modbus_read_holding_float(slave_address, register_address):");
		writer.appendLine("local response = modbus_xmlrpc.usb_modbus_read_holding_float(slave_address, register_address)");
		writer.appendLine("return response");
		writer.appendLine("end");

		//Modbus init method: ex --> usb_modbus_write_holdings_int(1, 0, 1)
		writer.appendLine("def usb_modbus_write_holdings_int(slave_address, register_address, value):");
		writer.appendLine("local response = modbus_xmlrpc.usb_modbus_write_holdings_int(slave_address, register_address, value)");
		writer.appendLine("return response");
		writer.appendLine("end");

		//Modbus init method: ex --> usb_modbus_write_holdings_float(1, 0, 1.1)
		writer.appendLine("def usb_modbus_write_holdings_float(slave_address, register_address, value):");
		writer.appendLine("local response = modbus_xmlrpc.usb_modbus_write_holdings_float(slave_address, register_address, value)");
		writer.appendLine("return response");
		writer.appendLine("end");
	
		//Modbus init method: ex --> usb_modbus_read_inputs_int(1, 0, 1)
		writer.appendLine("def usb_modbus_read_inputs_int(slave_address, register_address, num_of_values):");
		writer.appendLine("local response = modbus_xmlrpc.usb_modbus_read_inputs_int(slave_address, register_address, num_of_values)");
		writer.appendLine("return response");
		writer.appendLine("end");
	
		//Modbus init method: ex --> usb_modbus_read_inputs_float(1, 0, 1)
		writer.appendLine("def usb_modbus_read_inputs_float(slave_address, register_address, num_of_values):");
		writer.appendLine("local response = modbus_xmlrpc.usb_modbus_read_inputs_float(slave_address, register_address, num_of_values)");
		writer.appendLine("return response");
		writer.appendLine("end");
	
		//Modbus init method: ex --> usb_modbus_read_holdings_int(1, 0, 1)
		writer.appendLine("def usb_modbus_read_holdings_int(slave_address, register_address, num_of_values):");
		writer.appendLine("local response = modbus_xmlrpc.usb_modbus_read_holdings_int(slave_address, register_address, num_of_values)");
		writer.appendLine("return response");
		writer.appendLine("end");
	
		//Modbus init method: ex --> usb_modbus_read_holdings_float(1, 0, 1)
		writer.appendLine("def usb_modbus_read_holdings_float(slave_address, register_address, num_of_values):");
		writer.appendLine("local response = modbus_xmlrpc.usb_modbus_read_holdings_float(slave_address, register_address, num_of_values)");
		writer.appendLine("return response");
		writer.appendLine("end");
	}
	
	private void updateUI() {
		String text = "";
		if(modbusDaemonInterface.isDaemonReachable()){
			text = "Daemon is running.";
			view.setStartButtonEnabled(false);
			view.setStopButtonEnabled(true);
		} else {
			text = "Daemon is not running.";
			view.setStartButtonEnabled(true);
			view.setStopButtonEnabled(false);
		}
		
		view.setStatusLabel(text);
	}
	
	
	private DaemonContribution.State getDaemonState() {
		return this.modbusDaemonService.getDaemon().getState();

	}
	private boolean isDaemonEnabled() {
		return  model.get(ENABLED_KEY, true); // This daemon is enabled by default
	}

	public void onStartClick() {
		model.set(ENABLED_KEY, true);
		applyDesiredDaemonStatus();
	}

	public void onStopClick() {
		model.set(ENABLED_KEY, false);
		applyDesiredDaemonStatus();
	}


	public ModbusDaemonInterface getXmlRpcDaemonInterface() {
		return this.modbusDaemonInterface;
	}

	private void applyDesiredDaemonStatus() {
		new Thread(new Runnable() {
			@Override
			public void run() {
				if (isDaemonEnabled()) {
					// Download the daemon settings to the daemon process on initial start for
					// real-time preview purposes
					System.out.println("Starting daemon");
					try {
						awaitDaemonRunning(10000);
						boolean test = modbusDaemonInterface.isDaemonReachable();
						if(test) {
							System.out.println("Daemon is running");
						}else {
							System.out.println("Daemon is not running");
						}
					} catch (Exception e) {
						System.err.println("Could not reach the daemon process.");
						Thread.currentThread().interrupt();
					} 
				} else {
					modbusDaemonService.getDaemon().stop();
				}
			}
		}).start();
	}

	private void awaitDaemonRunning(long timeOutMilliSeconds) throws InterruptedException {
		modbusDaemonService.getDaemon().start();
		long endTime = System.nanoTime() + timeOutMilliSeconds * 1000L * 1000L;
		while(System.nanoTime() < endTime && (modbusDaemonService.getDaemon().getState() != DaemonContribution.State.RUNNING || !modbusDaemonInterface.isDaemonReachable())) {
			Thread.sleep(100);
		}
	}

	public String getXMLRPCVariable() {
		return XMLRPC_VARIABLE;
	}
}
