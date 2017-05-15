#!/usr/bin/env python
# -*- coding: utf-8 -*-
　
"""
Nom       : cl_hosts.py
Role      : Affiche les hosts SGE dans un format plus lisible et synthÃ©tique que qhost
Auteur    : FrÃ©dÃ©ric Parance
Version   : v1.0 du 28/04/2016
"""
　
import xml.etree.ElementTree as ET
import json
import time
import code
import sys
import os
import re
import argparse
　
from terminaltables import AsciiTable, DoubleTable
from colorclass import Color, enable_all_colors, disable_all_colors, is_enabled
　
colors = {
    "gen" : {
        "gen3" : {
            "members" : [ "btmcli{}".format(s) for s in range(45,56) ],
            "color" : "green"
        },
        "gen4" : {
            "members" : [ "btmcli{}".format(s) for s in range(56,72) ],
            "color" : "magenta"
        },
        "gen4visu" : {
            "members" : [ "btmclgvi{}".format(s) for s in range(1,3) ],
            "color" : "magenta"
        },
        "gen5" : {
            "members" : [ "btmcli{}".format(s) for s in range(21,39) ],
            "color" : "blue"
        },
        "gen5visu" : {
            "members" : [ "btmclgvi{}".format(s) for s in range(3,8) ],
            "color" : "cyan"
        }
    }
}
　
def getCmdOutput(cmd):
    import shlex, subprocess
    args = shlex.split(cmd)
    p = subprocess.Popen(args, stdout=subprocess.PIPE)
    (stdout, stderr) = p.communicate()
    return stdout
　
def getHosts():
    cmd = """qhost -q -xml"""
    output = getCmdOutput(cmd)
　
    hosts=dict()
　
    # excludedHosts = [ "btmcli%02.0f" % (i) for i in range(4,45) ] + [ 'global' ]
    excludedHosts = [ 'global', 'bdtcactusvi1' ]
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
　
def chargeReformat(host):
　
    if host["load_avg"]=='-':
        return " unk [ unk]"
    
    pct = "%3.f" % ( float(host["load_avg"]) / int(host["num_proc"]) * 100 )
　
    # re-calcul du nombre de cores utilisÃ©s ...
    slotsUsed=0
    for q in host["queues"]:
        slotsUsed = slotsUsed + int(host["queues"][q]["slots_used"])     
　
    # test de surcharge : load en % par rapport au nombde de cores et load par rapport aux slotsUsed sge, avec tolerence +1 core (systeme, surcharge io ...)
    if is_enabled() and ( int(pct) >= 100 + (100/int(host["num_proc"])) or ( float(host["load_avg"]) >= int(slotsUsed)+1 ) ):
        str = Color("{red}%4.1f [%s%%]{/red}" % (float(host["load_avg"]), pct) )
    else:
        str = "%4.1f [%s%%]" % (float(host["load_avg"]), pct)
    return str
　
def toGigs(i):
    if i[-1:] == "K":
        return float("%1.1f" % (float(i[:-1]) / 1024 / 1024))
    elif i[-1:] == "M":
        return float("%1.1f" % (float(i[:-1]) / 1024))
    else:
        return float(i[:-1])
　
def memReformat(used, total, alarm=50):
    totalG=toGigs(total)
    if used == "-":
        usedG='unk'
        str = "unk / %3.0f [ unk]" % (totalG)
    else:
        usedG=toGigs(used)
        pct = "%3.0f" % ( usedG / totalG * 100 )
        if is_enabled() and int(pct) >= alarm:
            str = Color("{red}%3.0f / %3.0f [%s%%]{/red}" % (usedG, totalG, pct) )
        else:
            str = "%3.0f / %3.0f [%s%%]" % (usedG, totalG, pct)
        # print "used=%s total=%s usedG=%s totalG=%s pct=%s" % (used, total, usedG, totalG, pct)
    return str
　
def slotsReformat(host):
    # print json.dumps(host,indent=3)
    slotsUsed = slotsResv = 0
    for q in host["queues"]:
        slotsResv = slotsResv + int(host["queues"][q]["slots_resv"])
        slotsUsed = slotsUsed + int(host["queues"][q]["slots_used"])
    if is_enabled() and slotsUsed > int(host["num_proc"]):
        str = Color("{autored}%2s / %2s / %2s{/red}" % (slotsUsed, slotsResv, host["num_proc"]) )
    else:
        str = "%2s / %2s / %2s" % (slotsUsed, slotsResv, host["num_proc"])
    return str
    
def enCouleur(list):
    if args.color == None:
        return list
　
    newlist = []
    color=""
　
    if args.color != None:
    
        if args.color == "gen":
            index=0
            
        for group in colors[args.color]:
            if list[index] in colors[args.color][group]["members"]:
                color=colors[args.color][group]["color"]
                break
　
        if color=="":
            color="white"
        for i in range(0,len(list)):
            newlist.append( Color("{%s}%s{/%s}" % (color, list[i], color) ) )
            
    return newlist
    
def displayHostsTable(hosts):
    table_data = [ [ "host", "os", "cpu", "mem (u/t)", "swap (u/t)", "slots (u/r/t)"] ]
    for host in sorted(hosts):
        # machine = hostReformat(host)
        charge=chargeReformat(hosts[host])
        mem=memReformat(hosts[host]["mem_used"],hosts[host]["mem_total"], 50)
        swap=memReformat(hosts[host]["swap_used"], hosts[host]["swap_total"], 2)
        slots=slotsReformat(hosts[host])
        os=re.search('linux-(rhel[67])-x64', hosts[host]["arch_string"], re.IGNORECASE).group(1)
        if is_enabled:
            table_data.append( enCouleur([ host, os, charge , mem, swap, slots ]) )
        else:
            table_data.append( [ host, os, charge , mem, swap, slots ] )
    if sys.stdout.isatty():
        table = DoubleTable(table_data, " SGE hosts ")
        table.justify_columns[5] = "right"
    else:
        table = AsciiTable(table_data)
    print table.table
    
def main():
    global args
    
    # options/arguments
    parser = argparse.ArgumentParser(formatter_class=lambda prog: argparse.HelpFormatter(prog,max_help_position = 50, width=120))
    parser.add_argument('-l', '--loop',  nargs='?', const=30, type=int, metavar="SECS", help="boucle automatique toutes les [SECS] secondes (30 secondes par dÃ©faut)")
    parser.add_argument('-c', '--color', nargs='?', const="gen", type=str, metavar="field", choices=['gen'], help="en couleur : -c gen ")
    args = parser.parse_args()
　
    if args.color != None:
        enable_all_colors()
    else:
        disable_all_colors()
    if not sys.stdout.isatty(): 
        disable_all_colors()
        
    # lancement
    if args.loop:
        while(True):
            hosts = getHosts()
            os.system('clear')
            displayHostsTable(hosts)
            try:
                time.sleep(args.loop)
            except KeyboardInterrupt:
                print
                sys.exit(0)
            print("reloading...")
    else:
        hosts = getHosts()
        displayHostsTable(hosts)
            
if __name__ == "__main__":
    main()
　
