#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    nom         : check_load_with_sge.py
    version     : v0.1
    description : sonde "nagios" qui renvoit le load en % par rapport au nombre de coeurs, avec alerte si > nb slots assignÃ©s par SGE.
    auteur      : 
"""

from __future__ import division

from tm_commonstuff import *

import argparse
import os
import sys
# import multiprocessing
import xml.etree.ElementTree as ET
import re
import json
import socket
    
def getSGEHosts(myself):

    cmd = "qhost -q -xml -l hostname=%s" % myself
    output = getCmdOutput(cmd, EnvironnementSGE())

    hosts=dict()

    excludedHosts = [ 'global' ]
    root = ET.fromstring(output)

    # code.interact(local=locals())

    for host in root.findall('host'):
        hostname = host.get('name')
        if hostname in excludedHosts:
            continue
        hosts[hostname]=dict()
        hosts[hostname]["queues"]=dict()

        # infos gÃ©nÃ©rales
        for infos in host.iter('hostvalue'):
            hosts[hostname][infos.attrib["name"]]=infos.text

        # infos des queues
        for queue in host.iter('queue'):
            queueName = re.sub(".q$", "", queue.attrib["name"]) 
            hosts[hostname]["queues"][queueName] = dict()
            # print hostname+" "+queue.attrib["name"]
            for queueInfo in queue.iter('queuevalue'):
                if not queueInfo.text:
                    queueInfo.text=""
                hosts[hostname]["queues"][queueName][queueInfo.attrib["name"]] = queueInfo.text
        
    # print json.dumps(hosts,indent=3)
    return hosts

def getNbCores(data):
    firstkey = next(data.__iter__())
    return int(data[firstkey]['num_proc'])
        
def getSgeSlotsUsed(data):
    slotsUsed=0
    firstkey = next(data.__iter__())
    for q in data[firstkey]["queues"]:
        slotsUsed = slotsUsed + int(data[firstkey]["queues"][q]["slots_used"])
    return slotsUsed

def main():

    """ argparse """
    parser = argparse.ArgumentParser(formatter_class=lambda prog: argparse.HelpFormatter(prog,max_help_position = 50, width=120))
    parser.add_argument('-w', '--warning',  nargs='?', required=True, metavar="warning",  help="warning as percent (ie 110%)")
    parser.add_argument('-c', '--critical', nargs='?', required=True, metavar="critical", help="critical as percent (ie 125%)")
    args = parser.parse_args()

    args.warning = int(args.warning.translate(None, '%'))
    args.critical = int(args.critical.translate(None, '%'))
    
    if args.warning >= args.critical:
        print "ERROR : warning threshold must be inferior to critical threshold."
        sys.exit(NAGIOS_UNKNOWN)

    """ Collecte """
    
    myself=socket.gethostbyaddr(socket.gethostname())[1][0]
    load = os.getloadavg()
    sgeHosts = getSGEHosts(myself)
    nbCores = getNbCores(sgeHosts)
    slotsUsed=getSgeSlotsUsed(sgeHosts)
    pctUsed = float("{0:.1f}".format(load[0] * 100 / nbCores)) # pourcentage utilisation calculÃ© par le systÃ¨me : load1 par rapport au nombre de coeurs

    """ reporting Nagios """

    
    """ multiplication par 2 des seuils quand le noeud est au max, surcharge cpu/sys """
    if slotsUsed == nbCores:
        args.warning = args.warning * 2 - 100
        args.critical = args.critical * 2 - 100
        
    
    # pctUsed = float("%.1f" % ( load[0] * 100 / nbCores ))      
    status=NAGIOS_OK
 
    if pctUsed>0.5: # on evite les trop petites valeurs (0.3% == 300% de 0.1%...)
        if (pctUsed >= args.critical):
            # print "1 pct=%s (%s) arg=%s (%s)" % (pctUsed, type(pctUsed), args.critical, type(args.critical) )
            status=NAGIOS_CRITICAL
            # print "1 status=%s" % status
        elif pctUsed >= args.warning:
            # print "2 pct=%s (%s) arg=%s (%s)" % (pctUsed, type(pctUsed), args.warning, type(args.warning) )
            status=NAGIOS_WARNING
            # print "2 status=%s" % status

    x=slotsUsed*args.critical/100
    if load[0]>0.5 or x>0.5:
        if load[0] >= x:
            # print "3 load=%s (%s) seuil=%s (%s)" % (load[0], type(load[0]), x, type(x)) 
            status=NAGIOS_CRITICAL
            # print "3 status=%s" % status
        elif load[0] >= slotsUsed*args.warning/100:
            # print "4 load=%s seuil=%s" % (load[0], (slotsUsed*args.warning/100)) 
            status=NAGIOS_WARNING
            # print "4 status=%s" % status

    # print "status=%s" % status
    message = "%s - load - [sys.load1:%s] [sge.slots:%s/%s] [usage:%s%%]" % (getNagiosStatus(status), load[0], slotsUsed, nbCores, pctUsed)
    perfdata = "cores=%s load1=%s sgeslots=%s" % (nbCores, load[0], slotsUsed)
    print "%s|%s" % (message,perfdata)
    sys.exit(status)
    
if __name__ == "__main__":
    main()
