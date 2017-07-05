#!/usr/bin/env python
# -*- coding: utf-8 -*-

from tm_commonstuff import *
import argparse
import os
import sys

def checkQmaster(host):
    sge_env=EnvironnementSGE()
    cmd="qping -info %s %s qmaster 1" % (host, SGE_QMASTER_PORT)
    rc=getCmdReturncode(cmd, sge_env)
    if rc == 0:
        return True
    else:
        return False

def main():

    parser = argparse.ArgumentParser(formatter_class=lambda prog: argparse.HelpFormatter(prog,max_help_position = 50, width=120))
    parser.add_argument('-m', '--masters',  nargs='?', required=True, metavar="masters",  help="masters list separated by coma (example: \"btmclx1,btmclx2\")")
    args = parser.parse_args()

    MASTERS=args.masters.split(',') 

    currentMaster=""
    for master in MASTERS:
        # print("checking %s" % master)
        if checkQmaster(master):
            currentMaster=master
            break
    if currentMaster:
        print("OK - qmaster running on %s." % currentMaster)
        sys.exit(NAGIOS_OK)
    else:
        print("CRITICAL - no running SGE qmaster found")
        sys.exit(NAGIOS_CRITICAL)

if __name__ == '__main__':
    main()
