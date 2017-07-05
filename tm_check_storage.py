#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division

from tm_commonstuff import *

import argparse
import os
import re
import sys

""" Global Parameters """
SMCLI="/opt/SMgr/client/SMcli"


def main():

    global args
    
    # options/arguments
    parser = argparse.ArgumentParser(formatter_class=lambda prog: argparse.HelpFormatter(prog,max_help_position = 50, width=120))
    parser.add_argument('-H', '--host',    nargs='?', required=True, type=str, metavar="host",    help="host/controller to check")
    # parser.add_argument('-c', '--command', nargs='?', required=True, type=str, metavar="command", help="command to send to SMcli")
    args = parser.parse_args()

    if not os.path.exists(SMCLI):
        print("ERROR : SMcli (%s) not found." % SMCLI)
        sys.exit(RET_UNKN)
        
    # lancement du SMcli
    cmd = """sudo %s %s -c "%s" -S""" % (SMCLI, args.host, "show storageArray healthStatus;")
    output = getCmdOutput(cmd)

    # interprétation du résultat
    regexp = re.search('Storage array health status = (.*).', output)
    if regexp:
        if regexp.group(1) == "optimal":
            print(output.rstrip())
            sys.exit(RET_OK)
        else:
            print(output)
            sys.exit(RET_CRIT)
    else:
        print(output)
        sys.exit(RET_UNKN)

    sys.exit(3)

if __name__ == "__main__":
    main()
