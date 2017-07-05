#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    nom         : tm_check_ansysrsm.py
    version     : v0.1
    description : sonde "nagios" qui vÃ©rifie le status des process RSM (Manager et Server)
    auteur      : 
"""

from tm_commonstuff import *

import argparse
import os
import sys


def checkService(srv):
    output=""
    error=""
    rc=0
    
    if os.access(srv, os.X_OK) == False:
        return("service file %s not found or not executable" % srv, 3)

    cmd = "%s status" % srv
    (stdout, stderr, rc) = getCmdTriplet(cmd)
    return(stdout, rc)

def main():

    """ args parsing """
    # parser = argparse.ArgumentParser(formatter_class=lambda prog: argparse.HelpFormatter(prog,max_help_position = 50, width=120))
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--version', nargs='?', required=True, type=int, metavar="version",     help="version to check.")
    args = parser.parse_args()

    rsmmanager="/etc/init.d/rsmmanager%s" % args.version
    rsmserver="/etc/init.d/rsmserver%s" % args.version
    
    (output_manager, rc_manager)=checkService(rsmmanager)
    (output_server, rc_server)=checkService(rsmserver)

    # print (output_manager, rc_manager)
    # print (output_server, rc_server)
    if (rc_manager==0 and rc_server==0):
        STATUS=NAGIOS_OK
        MESSAGE="%s - Manager and Server for Ansys %s are running." % (getNagiosStatus(STATUS), args.version)
        MESSAGE = '\n'.join( (MESSAGE, output_manager, output_server) )
    else:
        STATUS=NAGIOS_CRITICAL
        MESSAGE="%s - Manager or Server or both for Ansys %s are not running." % (getNagiosStatus(STATUS), args.version)
        MESSAGE = '\n'.join( (MESSAGE, output_manager, output_server) )
    
        
    print MESSAGE
    sys.exit(STATUS)
        
if __name__ == "__main__":
    main()
