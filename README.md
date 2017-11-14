# mizzenmast
Python code for bluetooth proximity detection of a given device to open and close blinds.

Checks every 9 seconds (plus time for bluetooth RSSI checks) for proximity of commandline-defined bluetooth address.  You need to have paired and trusted that device prior to execution!

To pair/replace tracked device:

	$ sudo bluetoothctl
	
		[bluetooth]# remove OL:DD:EV:BT:AD:DR
		
		[bluetooth]# power on
		
		[bluetooth]# pairable on
		
		[bluetooth]# discoverable on
		
		[bluetooth]# agent on
		
		[bluetooth]# default-agent
		
		[bluetooth]# scan on
		
		[bluetooth]# pair NE:WD:EV:BT:AD:DR
		
		[bluetooth]# trust NE:WD:EV:BT:AD:DR
		
	$ sudo rfcomm connect 0 NE:WD:EV:BT:AD:DR

Stepper motor needs to be connected to (or redefined):
   
   StepPins = [17,27,22,23]
   
A RGB LED can be connected as such:

    ConnectionLed (BLUE) = 26
	ErrorLed (RED) = 5
	DiskLed (GREEN) = 6

LED Codes:

	Program Exit - ErrorLed, 5x, 0.25s delay
	Program Terminated - ErrorLed, 3x, 0.1s delay
	Bluetooth Session started - ConnectionLed, 1x, 0.2s delay
	Bluetooth Strength in tolerance - ConnectionLed, 3x, 0.1s delay
	Disk Writing - DiskLed, 2x, 0.25s delay
	Disk Reading - DiskLed, 1x, 0.25s delay    

Informational logging can be found in: /tmp/tmpfs/mizzenmast.log

To facilitate logging to RAMDISK, add this to rc.local

	mkdir /tmp/tmpfs
	
	mount -t tmpfs -o size=64m tmpfs /tmp/tmpfs/
	
The state of the motor is saved to (script directory)/.mizzenmast_motorstate

RSSI logging is available in: /tmp/tmpfs/rssi .  Query this file periodically to see what RSSI value your device is returning, or use the btstrength.sh script in a new terminal session after establishing your rfcomm session.
	
To enable on boot:

	$ crontab -l
	
	@reboot /usr/bin/python /home/pi/mizzenmast/mizzenmast.py DE:VI:CE:BT:AD:DR
	


