#!/usr/bin/env python
# -*- coding: utf-8 -*-

import shlex,subprocess
import os


"""
	NAGIOS STUFF
"""

RET_OK=NAGIOS_OK=0
RET_WARN=RET_WARNING=NAGIOS_WARNING=1
RET_CRIT=RET_CRITICAL=NAGIOS_CRITICAL=2
RET_UNKN=RET_UNKNOWN=NAGIOS_UNKNOWN=3


def getNagiosStatus(status):
    if status == NAGIOS_OK:
        return "OK"
    elif status == NAGIOS_WARNING:
        return "WARNING"
    elif status == NAGIOS_CRITICAL:
        return "CRITICAL"
    elif status == NAGIOS_UNKNOWN:
        return "UNKNOWN"
    else:
        return ""

def getCmdOutput(cmd, newenv=False):
    args = shlex.split(cmd)
    if not newenv:
        newenv=os.environ.copy()
    p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=newenv)
    (stdout, stderr) = p.communicate()
    rc = p.returncode
    return stdout

def getCmdReturncode(cmd, newenv=False):
    args = shlex.split(cmd)
    if not newenv:
        newenv=os.environ.copy()
    child = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=newenv)
    (stdout, stderr) = child.communicate()
    rc = child.returncode
    return rc

def getCmdTriplet(cmd, newenv=False):
    args = shlex.split(cmd)
    if not newenv:
        newenv=os.environ.copy()
    child = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=newenv)
    (stdout, stderr) = child.communicate()
    rc = child.returncode
    return (stdout, stderr, rc)

"""
	SGE STUFF
"""

def EnvironnementSGE():
    current=os.environ.copy()
    current["SGE_CELL"]="TM_CL"
    current["SGE_ROOT"]="/SGE/GE2011.11p1"
    current["SGE_CLUSTER_NAME"]="turbomeca"
    current["PATH"] = ":".join( ( current["PATH"], "SGE/GE2011.11p1/bin/linux-rhel7-x64") )
    return current	

SGE_QMASTER_PORT=33001
SGE_EXECD_PORT=33002


def main():
    return True
    
if __name__ == "__main__":
    main()
