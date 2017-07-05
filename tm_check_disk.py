#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    nom         : check_disk.py
    version     : v0.1
    description : sonde "nagios" qui renvoit le mÃªme format de sortie que la sonde centreon check_centreon_snmp_remote_storage
    auteur      : 
"""

from __future__ import division

from tm_commonstuff import *

import argparse
import os
import sys


"""
fonction qui transforme les bytes en MB,GB,TB
"""
def humanisation(bytes):
    if bytes >= 1099511627776:
        human = "%0.3fTB" % (bytes/1099511627776)
    elif bytes >= 1073741824:
        human = "%0.3fGB" % (bytes/1073741824)
    elif bytes >= 1048576:
        human = "%0.3fMB" % (bytes/1048576)
    return human


def main():

    global args
    
    # options/arguments
    parser = argparse.ArgumentParser(formatter_class=lambda prog: argparse.HelpFormatter(prog,max_help_position = 50, width=120))
    parser.add_argument('-w', '--warning',  nargs='?', required=True, type=int, choices=range(0, 101), metavar="warning",  help="warning as percent [0-100]")
    parser.add_argument('-c', '--critical', nargs='?', required=True, type=int, choices=range(0, 101), metavar="critical", help="critical as percent [0-100]")
    parser.add_argument('-p', '--path',     nargs='?', required=True, type=str, metavar="path",     help="path")
    args = parser.parse_args()

    if args.warning <= args.critical:
        print "ERROR : critical thresholfd must be inferior to warning threshold."
        sys.exit(NAGIOS_UNKNOWN)

    if not os.path.exists(args.path):
        print "ERROR : path does not exists."
        sys.exit(NAGIOS_UNKNOWN)

    try:
        statvfs = os.statvfs(args.path)
    except:
        print "ERROR : could not get path stats"
        sys.exit(NAGIOS_UNKNOWN)
    
    # print statvfs
    # posix.statvfs_result(f_bsize=4096, f_frsize=4096, f_blocks=143754030, f_bfree=143402495, f_bavail=136094425, f_files=36519936, f_ffree=36519153, f_favail=36519153, f_flag=4096, f_namemax=255)

    
    fs_size = statvfs.f_blocks * statvfs.f_frsize
    fs_used = (statvfs.f_blocks - statvfs.f_bfree) * statvfs.f_frsize
    fs_free = statvfs.f_bfree * statvfs.f_frsize
    fs_warn = int( fs_size* (100 - args.warning) / 100 )
    fs_crit = int( fs_size * (100 - args.critical) / 100 )

    ERR_CODE=3
    # output template : Disk OK - /ESLT TOTAL: 548.378GB USED: 1.341GB (0%) FREE: 547.037GB (100%)
    if fs_used < fs_warn:
        status="OK"
        ERR_CODE=NAGIOS_OK
    elif fs_used < fs_crit:
        status="WARNING"
        ERR_CODE=NAGIOS_WARNING
    else:
        status="CRITICAL"
        ERR_CODE=NAGIOS_CRITICAL

    human_total=humanisation(fs_size)
    human_used=humanisation(fs_used)
    pct_used = ( ( statvfs.f_blocks - statvfs.f_bfree ) * 100 )  / statvfs.f_blocks
    human_free=humanisation(fs_free)
    pct_free = ( statvfs.f_bfree * 100 ) / statvfs.f_blocks

    MESSAGE="Disk %s - %s TOTAL: %s USED: %s (%0.2f%%) FREE: %s (%0.2f%%)" % (status, args.path, human_total, human_used, pct_used, human_free, pct_free )
    PERFDATA= "size=%sB used=%sB;%s;%s;0;%s" % ( fs_size, fs_used, fs_warn, fs_crit, fs_size)

    print "%s | %s" % ( MESSAGE, PERFDATA )
    sys.exit(ERR_CODE)

if __name__ == "__main__":
    main()
