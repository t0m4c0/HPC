#!/usr/bin/env python
# -*- coding: utf-8 -*-

from tm_commonstuff import *

import xml.etree.ElementTree as ET
import argparse
import os
import sys
import json

def checkNodeQping(node):
    sge_env=EnvironnementSGE()
    cmd="qping -info %s %s execd 1" % (node, SGE_EXECD_PORT)
    rc=getCmdReturncode(cmd, sge_env)
    if rc == 0:
        return (NAGIOS_OK, "qping is ok")
    else:
        return (NAGIOS_CRITICAL, "host is not qpinging")

def checkNodeQueues(node):
    sge_env=EnvironnementSGE()
    cmd="qhost -q -l hostname=%s -xml" % (node)
    (output, error, rc)=getCmdTriplet(cmd, sge_env)
    # print (output, error, rc)

    root = ET.fromstring(output)
    for host in root.findall('host'):
        # print("host:%s" % host.attrib["name"])
        nb_queues = 0
        nb_queues_ok = 0
        nb_queues_ko = 0
        for queue in host.iter('queue'):
            nb_queues += 1
            # qstatus = "None"
            # print("  queue:%s"%queue.attrib["name"])
            for elem in queue.findall('queuevalue'):
                if elem.get('name') == 'state_string':
                    qstatus = elem.text
                    if qstatus in ('d', 'dE'):
                        nb_queues_ko += 1
                    else:
                        nb_queues_ok += 1
            # print(" queue:%s status:%s"% (queue.attrib["name"], qstatus))
        # print "ok:%s ko:%s" % (nb_queues_ok, nb_queues_ko)

    if nb_queues_ok == nb_queues:
        return (NAGIOS_OK, "all queues are ok")
    else:
        if nb_queues_ko == nb_queues:
            return(NAGIOS_CRITICAL, "all queues are disabled or in error")
        else:
            return(NAGIOS_WARNING, "some queues are disabled or in error")

def main():

    parser = argparse.ArgumentParser(formatter_class=lambda prog: argparse.HelpFormatter(prog,max_help_position = 50, width=120))
    parser.add_argument('-n', '--nodes',  nargs='?', required=True, metavar="nodes",  help="nodes to check, separated by comma")
    args = parser.parse_args()

    NODES=args.nodes.split(',')
    
    status=dict()
    globalStatus=NAGIOS_OK
    
    """ status of qping, queues and jobs """
    for node in NODES:
        status[node]=dict()

        # print("Qpinging %s" % node)
        (ps, po) = checkNodeQping(node)
        globalStatus=max(globalStatus, ps)

        # print("checking queues")
        (qs, qo) = checkNodeQueues(node)
        globalStatus=max(globalStatus, qs)
            
    """ Nagios reporting """
    if globalStatus==NAGIOS_OK:
        print("OK - node is ok.")
    else:
        print("%s - problems found :" % getNagiosStatus(globalStatus))
        print("qping : %s - %s" % (getNagiosStatus(ps), po))
        # print " - qping status :failed : %s " % ( " ".join([ host for host in status.keys() if status[host]['qping'] == False ]) )
        print("queues : %s - %s" % (getNagiosStatus(qs), qo))
    sys.exit(globalStatus)

if __name__ == '__main__':
    main()
