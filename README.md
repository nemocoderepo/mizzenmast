# mizzenmast
Python code for bluetooth proximity detection of a given device to open and close blinds.

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
	

To facilitate logging to RAMDISK, add this to rc.local

	mkdir /tmp/tmpfs
	
	mount -t tmpfs -o size=64m tmpfs /tmp/tmpfs/
	
	
To enable on boot:

	$ crontab -l
	
	@reboot /usr/bin/python /home/pi/mizzenmast/mizzenmast.py DE:VI:CE:BT:AD:DR
	


