#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    nom         : tm_check_nfs_mounts.py
    version     : v0.1
    description : sonde "nagios" qui compare le nombre de montages nfs entre /etc/fstab et /proc/mounts
    auteur      : Frédéric Parance
"""

from tm_commonstuff import *

import os
import sys
import re

def getNfsMountsFromProcMounts():
    res=list()
    fd=open('/proc/mounts', 'r')
    for line in fd:
        line = line.strip()
        fields = line.split(' ')
        if fields[2] == 'nfs':
            res.append( fields[1] )
    fd.close()
    return res

def getNfsMountsFromFstab():
    res=list()
    fd=open('/etc/fstab', 'r')
    for line in fd:
        line=line.strip()
        fields = re.findall(r"[\w.:/,=#'-]+", line)
        if fields:
            # print fields
            if not re.search('^#', fields[0]):              # retrait commentaires
                if len(fields)>2 and fields[2] == 'nfs':    # retrait non nfs
                    if re.search('systemd\.automount', fields[3]):
                        # print "OK1 %s" % fields
                        res.append( fields[1] )
                    else:
                        if not re.search('noauto', fields[3]):
                            # print "OK2 %s" % fields
                            res.append( fields[1] )
                        # else:
                            # print("SKIP1 %s" % fields)
            # else:
                # print("SKIP2 %s" % fields)
    fd.close()
    return res

def main():
    mounts=getNfsMountsFromProcMounts()
    # print "mounts:",mounts
    
    confs=getNfsMountsFromFstab()
    # print "fstab:",confs

    diff = list( set(confs) - set(mounts) )
    # print diff
    
    if diff:
        status=NAGIOS_WARNING
        print("%s - some NFS filesystems are not mounted :" % getNagiosStatus(status) )
        for m in diff:
            print("- %s" % m)
    else:
        status=NAGIOS_OK
        print("%s - all NFS filesystems are mounted." % getNagiosStatus(status) )
        
    sys.exit(status)

if __name__ == "__main__":
    main()