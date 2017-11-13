#!/usr/bin/python

# Import required libraries
import sys
import os
import time
import threading
import RPi.GPIO as GPIO
import logging
import re
from subprocess import Popen, PIPE
import shlex
import pexpect
import signal

def signal_term_handler(signal, frame):
  global ErrorLed
  print 'got SIGTERM'
  blink(ErrorLed,3,0.1)
  GPIO.cleanup()
  sys.exit(0)

def blink ( led, times, speed ):
  for i in range(0,times):
    GPIO.output(led,GPIO.LOW)
    time.sleep(float(speed))
    GPIO.output(led,GPIO.HIGH)
    time.sleep(float(speed))

def btcheck ( addr ):
  global ConnectionLed
  global ErrorLed
  logging.debug("BT Subprocess:"+str(addr))
  initconnection = pexpect.spawn('/usr/bin/sudo /usr/bin/rfcomm connect 0 '+addr+' 1')
  index = initconnection.expect(['Connected /dev/rfcomm0 to '+addr+' on channel 1', "Can't connect RFCOMM socket: Host is down", "Can't connect RFCOMM socket: Device or resource busy","Can't connect RFCOMM socket: Connection timed out",$
  if index == 0:
    blinkthread1 = threading.Thread(target=blink, args=(ConnectionLed,1,0.2))
    blinkthread1.daemon = True
    blinkthread1.start()
    time.sleep(2)
    checkstrength = pexpect.spawn('/usr/bin/hcitool',['rssi',str(addr)])
    strength = checkstrength.readline()
    #logging.debug("BT: read: "+str(strength))
    strength = strength.replace("RSSI return value:","")
    if strength == 'Not connected.\r\n' or strength == 'Not connected.':
      strength = '-99'         # connection was dropped mid-query
    strength = int(strength)
    logging.debug("BT: RSSI:"+str(strength))
    initconnection.sendcontrol('c')
    initconnection.sendcontrol('c')  # yes, twice.  magically works reliably if this is done.
    # write strength to overwritten file
    rf = open(rssifile,'w')
    rf.write(str(strength))
    rf.flush()
    rf.close()
    if strength == 0:
      return -1
    if 0 < strength <= 50:
      blinkthread2 = threading.Thread(target=blink, args=(ConnectionLed,3,0.1))
      blinkthread2.daemon = True
      blinkthread2.start()
      return 1
  elif index == 2 or index == 5:
    logging.debug("BT: RFCOMM needs a kill")
    slaycmd = "/usr/bin/sudo /usr/bin/killall -9 rfcomm"
    slayprocess = Popen(shlex.split(slaycmd), stdout=PIPE)
    blink(ErrorLed,1,0.25)
    return -1
  elif index == 3 or index == 1:
    blink(ErrorLed,2,0.25)
    logging.debug("BT: Connection Timeout.")
  return 0

def savestate( state ):
  global statefile
  global DiskLed
  blinkthread = threading.Thread(target=blink, args=(DiskLed,2,0.25))
  blinkthread.daemon = True
  blinkthread.start()
  f = open(statefile,'w')
  f.write(state)
  f.flush()
  f.close()
  logging.debug('wrote motor='+state)

def readstate():
  global statefile
  global DiskLed
  if os.path.isfile(statefile):
    blinkthread = threading.Thread(target=blink, args=(DiskLed,1,0.25))
    blinkthread.daemon = True
    blinkthread.start()
    f = open(statefile,'r')
    data = f.read()
    logging.debug("READSTATE:"+str(data))
    f.close()
    return data
  else:
    savestate("closed")
    return "closed"

def turnmotor( stepper_direction, speed ):
  logging.debug("Motor: "+stepper_direction+" \nSpeed: "+speed)
  Seq = [[1,0,0,1],
         [1,0,0,0],
         [1,1,0,0],
         [0,1,0,0],
         [0,1,1,0],
         [0,0,1,0],
         [0,0,1,1],
         [0,0,0,1]]

  StepCount = len(Seq)

  if speed == 'fast':
    StepDir = 2
  elif speed == 'slow':
    StepDir = 1

  if stepper_direction == 'counterclockwise':
    StepDir *= -1

  WaitTime = 5/float(1000)
  StepCounter = 0
  totalcounter = 0
  totalrevolutions = 4
  stepstorevolve = abs(4096 / StepDir)

  while totalcounter<totalrevolutions*stepstorevolve:
    for pin in range(0, 4):
      xpin = StepPins[pin]
      if Seq[StepCounter][pin]!=0:
        GPIO.output(xpin, True)
      else:
        GPIO.output(xpin, False)

    StepCounter += StepDir

    if (StepCounter>=StepCount):
      StepCounter = 0
    if (StepCounter<0):
      StepCounter = StepCount+StepDir

    totalcounter += 1
    time.sleep(WaitTime)

  return 0

def main():
        # main code block starts

        # check for the btaddr
        if len(sys.argv) == 1:
          logging.warning("No Bluetooth Address Specified")
          sys.exit()

        btaddr=sys.argv[1]

        # check the btaddr length
        if len(btaddr) != 17:
          logging.warning("Invalid Bluetooth Address Length: " + str(len(btaddr)) + " != 17")
          sys.exit()

        # check the format
        regex = re.compile(r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$', flags=re.IGNORECASE)
        if not regex.match(btaddr):
          logging.warning("Invalid Bluetooth Address Format: XX:XX:XX:XX:XX:XX vs "+str(btaddr))
          sys.exit()

        # define how many seconds between checks.  Account for the sleeps in the btcheck.
        sleeplen = 9

        # get current motor state from filesystem
        motorstate=readstate()
        presencemeter=0

        while True:
          btstatep = btcheck(btaddr)
          logging.debug('Bluetooth Presence Script Returned: ' + str(btstatep))
          if btstatep == 1:
                btstate = True
          elif btstatep == 0:
                btstate = False
          elif btstatep == -1:
                btstate = None

          logging.debug('Bluetooth State Now: ' + str(btstate))
          logging.debug('Motor State='+str(motorstate))

          if btstate and presencemeter < 3:
                presencemeter+=1
          elif presencemeter > -3 and btstate == False:
                presencemeter-=1

          logging.debug('Presence Meter='+str(presencemeter))
          openthread = threading.Thread(target=turnmotor, args=("clockwise","fast"))
          openthread.daemon = True
          closethread = threading.Thread(target=turnmotor, args=("counterclockwise","slow"))
          closethread.daemon = True

          if presencemeter > 2 and motorstate == 'closed':
                logging.info("Hoist tha\' mizzenmast!  Tha\' captain be aboard!")
                while closethread.isAlive():
                  time.sleep(5)
                openthread.start()
                savestate("open")
                motorstate = readstate()
                presencemeter = 0
          elif presencemeter < -2 and motorstate == 'open':
                logging.info("Batten down th\' hatches, th\' captain be fightin\' some landlubbers!")
                while openthread.isAlive():
                  time.sleep(5)
                closethread.start()
                savestate("closed")
                motorstate = readstate()
                presencemeter = 0

          logging.debug('Sleeping for '+str(sleeplen)+'s')
          time.sleep(sleeplen)

try:
    # Physical pins 11,13,15,16
    StepPins = [17,27,22,23]
    ConnectionLed = 26
    ErrorLed = 5
    DiskLed = 6
    LedPins = [ConnectionLed, ErrorLed, DiskLed]
    
	# initialize GPIO
    GPIO.setmode(GPIO.BCM)
    
	# Set all pins as output
    for pin in StepPins:
      GPIO.setup(pin,GPIO.OUT)
      GPIO.output(pin, False)
    for pin in LedPins:
      GPIO.setup(pin,GPIO.OUT)
      GPIO.output(pin,GPIO.HIGH)

    #get current script dir, build the logging config/environment, and the motor status file
    scriptdir = os.path.dirname(os.path.realpath(__file__))
    #logging.basicConfig(filename=scriptdir+'/mizzenmast.log', level=logging.INFO, format='%(asctime)s %(levelname)s:%(message)s')
    logging.basicConfig(filename='/tmp/tmpfs/mizzenmast.log', level=logging.INFO, format='%(asctime)s %(levelname)s:%(message)s')
    statefile = str(scriptdir)+'/.mizzenmast_motorstate'
    rssifile = '/tmp/tmpfs/rssi'
    
	# handle kills
    signal.signal(signal.SIGTERM, signal_term_handler)
    main()
	
except KeyboardInterrupt:
    pass
finally:
    blink(ErrorLed,5,0.25)
    GPIO.cleanup()
    sys.exit(0)
