#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    nom         : tm_check_lic_dlimd8.py
    version     : v0.1
    description : sonde "nagios" qui vÃ©rifie le status d'une licence dlim8
    auteur      : 
"""

from tm_commonstuff import *

import argparse
import os
import sys


def main():

    """ args parsing """
    parser = argparse.ArgumentParser(formatter_class=lambda prog: argparse.HelpFormatter(prog,max_help_position = 50, width=120))
    parser.add_argument('--bin', nargs='?', required=True, type=str, metavar="bin", help="path to dlimd8_status.")
    parser.add_argument('--key',    nargs='?', required=True, type=str, metavar="key",    help="path to key file.")
    args = parser.parse_args()


    """ check for bin and key """
    if os.access(args.bin, os.X_OK) == False:
        print("ERROR - %s not found or not executable" % args.bin)
        sys.exit(NAGIOS_UNKNOWN)
    if os.access(args.key, os.R_OK) == False:
        print("ERROR - %s not found or not readable by nrpe" % args.key)
        sys.exit(NAGIOS_UNKNOWN)

    """ dlimd8 """
    os.chdir('/tmp')
    cmd = "%s %s" % (args.bin, args.key) 
    (output, error, rc) = getCmdTriplet(cmd)
    if rc == 0:
        print("OK - dlimd8 is up")
        print(error)
        sys.exit(NAGIOS_OK)
    else:
        print("CRITICAL - dlimd8 output :")
        print(error)
        sys.exit(NAGIOS_CRITICAL)

if __name__ == "__main__":
    main()
