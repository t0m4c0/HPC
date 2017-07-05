#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    nom         : tm_check_rlm.py
    version     : v0.1
    description : sonde "nagios" qui vérifie le status d'un demon RLM
    auteur      : Frédéric Parance
"""

from tm_commonstuff import *

import argparse
import os
import sys

LIC_RLMUTIL="/usr/local/rlm/bin/v9.0/rlmutil"



def main():

    """ args parsing """
    parser = argparse.ArgumentParser(formatter_class=lambda prog: argparse.HelpFormatter(prog,max_help_position = 50, width=120))
    parser.add_argument('-s', '--server', nargs='?', required=True, type=str, metavar="server",     help="server in \"port@server\" format or path to licence file.")
    args = parser.parse_args()


    """ check for rlmutil """
    if os.access(LIC_RLMUTIL, os.X_OK) == False:
        print("ERROR - %s not found or not executable" % LIC_RLMUTIL)
        sys.exit(NAGIOS_UNKNOWN)

    """ rlm """
    cmd = "%s rlmstat -c %s" % (LIC_RLMUTIL, args.server) 
    # print cmd
    (output, error, rc) = getCmdTriplet(cmd)
    # print (output, error, rc)
    if rc == 0:
        print("OK - rlm server %s is up" % args.server)
        print(output)
        sys.exit(NAGIOS_CRITICAL)
    else:
        print("CRITICAL - rlm server %s is not up" % args.server)
        print(output)
        sys.exit(NAGIOS_CRITICAL)
    
    return True

if __name__ == "__main__":
    main()
