#!/usr/bin/env python
# -*- coding: utf-8 -*-

from tm_commonstuff import *

"""
    nom         : check_jobs.py
    version     : v0.1
    description : sonde "nagios" qui identifie des process utilisateurs hors job SGE (ie process qui trainent...)
    auteur      : 
"""

import nis
import re
import json
import sys

""" renvoie la liste des uids des comptes utilisateurs depuis le NIS """
def getNisUids():
    cat = nis.cat("passwd")
    uids = [ user.split(':')[2] for user in cat.values() ]
    return [ int(x) for x in uids ]

""" renvoie le pid du process recherché par nom+user"""
def pidof(list, cmd, uid=-1):
    for process in list.keys():
        if re.match("/SGE/.*/sge_execd", list[process]["cmd"]):
            if uid:
                if list[process]["uid"] == int(uid):
                    return process
            else:
                return process

""" liste des process via un exec de la commande ps (dirty...) """
def getProcess():
    cmd = """/usr/bin/ps -eo uid,pid,ppid,cmd --no-header"""
    output = getCmdOutput(cmd)

    # entries = [re.split(":? *", entry.lstrip(), 3) for entry in re.split("\n", output.rstrip())]
    # return entries

    r=dict()
    for entry in re.split("\n", output.rstrip()):
        tmp = re.split(":? *", entry.lstrip(), 3)
        r[int(tmp[1])] = { "uid": int(tmp[0]), "ppid":int(tmp[2]), "cmd":tmp[3] }
    return r


def isBadProcess(pid):
    if not processes[pid]["uid"] in nisUids:
        return False
    if processes[pid]["uid"] == sgeadmin_uid:
        return False
    if pid == sgeexecd_pid:
        return False
    if processes[pid]["ppid"] == 1:
        return True
    else:
        return isBadProcess(processes[pid]["ppid"])

def nagiosReport(tokill):
    if tokill:
        message = "WARNING - some process don't belong to any job and may need a kill..."
        message = message+"\n\n"
        message = message+"quick copy/paste ps : ps -H -o user,pid,ppid,rss,pcpu,start_time,cmd -p "+",".join(map( str, [ p for p in tokill ]))+"\n"
        message = message+"quick copy/paste kill : kill -KILL "+" ".join(map( str, [ p for p in tokill ]))+"\n"
    
        psoutput = getCmdOutput("/usr/bin/ps --no-header -o rss -p %s" % (",".join(map( str, [ p for p in tokill ]))))
        wastedmem=0
        for entry in re.split("\n", psoutput.rstrip()):
            wastedmem += int(entry)
        
        perfdata = "badprocess=%s wastedmem=%sB" % ( len(tokill), wastedmem*1024 )
        
        exit = NAGIOS_WARNING
    else:
        message = "OK - no out-of-job process found."
        perfdata = "badprocess=0 wastedmem=0B"
        exit  = NAGIOS_OK

    print("%s|%s" % (message, perfdata))
    sys.exit(exit)    


    
def main():

    global nisUids
    nisUids = getNisUids()

    global processes
    processes = getProcess()
    # print json.dumps(processes, indent=3)

    # process sge_execd du user sgeadmin
    global sgeexecd_pid,sgeadmin_uid
    sgeadmin_uid=int(nis.match("sgeadmin", "passwd").split(':')[2])
    sgeexecd_pid=pidof(processes, "sge_execd", sgeadmin_uid)
    
 
    """ identification des process hors-jobs SGE """
    processToKill=list()
    for k,v in processes.iteritems():
        if isBadProcess(k):
            processToKill.append(k)

    nagiosReport(processToKill)        
    
if __name__ == "__main__":
    main()
