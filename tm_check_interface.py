#!/usr/bin/env python
# -*- coding: utf-8 -*-

from tm_commonstuff import *

import argparse
import os
import sys
import json


MESSAGE=""
STATUS=NAGIOS_OK


def pingHost(hostname):
    global MESSAGE
    global STATUS
  
    (stdout, stderr, rc)=getCmdTriplet("ping -c1 -W1 %s" % hostname)
    if rc==0:
        MESSAGE="%s [ping:%s:ok]" % (MESSAGE, hostname)
    else:
        MESSAGE="%s [ping:%s:ko]" % (MESSAGE, hostname)
        STATUS=NAGIOS_WARNING
    return

    
""" getCmdOutput Ã  remplacer par un open du fichier + readline() """
def checkEthDevice(interface, speed):
    """ attenttion :  type(speed) = str """

    global MESSAGE
    global STATUS

    # check link
    link = getCmdOutput("cat /sys/class/net/%s/operstate" % interface)
    link = link.rstrip()
    if link != "up":
        STATUS=NAGIOS_CRITICAL
        MESSAGE="[link:down]"
    else:
        # check speed
        sp = getCmdOutput("cat /sys/class/net/%s/speed" % interface)
        sp = sp.rstrip()
        if sp != speed:
            STATUS=NAGIOS_CRITICAL
            MESSAGE="[link:up] [speed:%s:error]"%sp
        else:
            MESSAGE="[link:up] [speed:%s:ok]"%sp

    return

def checkIBDevice(interface, device, port, speed):
    """ attenttion :  type(speed) = str """

    global MESSAGE
    global STATUS
    
    slink=sstate=srate="-"
    
    # check link
    link = getCmdOutput("cat /sys/class/infiniband/%s/ports/%s/phys_state" % (device, port))
    link = link.rstrip()
    if link == "5: LinkUp":
        slink="up"
    else:
        STATUS=NAGIOS_CRITICAL
        slink="down"

    #check ibstate    
    if STATUS == NAGIOS_OK:
        state = getCmdOutput("cat /sys/class/infiniband/%s/ports/%s/state" % (device, port))
        state = state.rstrip()
        if state == "4: ACTIVE":
            sstate="active"
        else:
            STATUS=NAGIOS_CRITICAL
            sstate="not active:%s" % state

    # check ib rate    
    if STATUS == NAGIOS_OK:
        rate = getCmdOutput("cat /sys/class/infiniband/%s/ports/%s/rate" % (device,port))
        rate = rate.rstrip().split(' ')[0]  # format "56 Gb/sec (4X FDR)"
        if rate == speed:
            srate="ok:%sGb/sec"%rate
        else:
            STATUS=NAGIOS_CRITICAL
            srate="error:%sGb/sec"%rate

    MESSAGE="[link:%s] [ibstate:%s] [speed:%s]" % (slink, sstate, srate)

    return


def checkDevice(interface, type, device, port, speed, ping):
    # print json.dumps( (interface, type, device, port, speed, ping) )
    
    if type == "ethernet" or type == "eth" :
        checkEthDevice(interface, speed)
        pingHost(ping)
    elif type == "infiniband" or type == "ib":
        checkIBDevice(interface, device, port, speed)
        pingHost(ping)
    
    return True

def main():

    """ argparse """
    parser = argparse.ArgumentParser(formatter_class=lambda prog: argparse.HelpFormatter(prog,max_help_position = 50, width=120))
    parser.add_argument('-d', '--device',  nargs='?', required=True, type=str, metavar="warning",  help="warning as percent (ie 110%)")
    args = parser.parse_args()

    """ exit with OK status if --device=none (exception for bdtvir00 in hostgroup that dont have IB device) """
    if args.device == "none":
        print("interface not configured.")
        sys.exit(NAGIOS_OK)


    """ split param """
    try:
        (interface, type, device, port, speed, ping) = args.device.split(':')
    except ValueError:
        print("wrong device parameters")
        sys.exit(NAGIOS_UNKNOWN)

        
    """ checks link, speed, ping """
    checkDevice(interface, type, device, port, speed, ping)

    """ Nagios report """
    print("%s - %s - %s" % (interface, getNagiosStatus(STATUS), MESSAGE) )
    sys.exit(STATUS)


if __name__ == "__main__":
    main()
