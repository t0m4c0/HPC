#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    nom         : tm_check_sge_jobs.py
    version     : v0.1
    description : sonde "nagios" qui check les jobs en anomalie 
    auteur      : 
"""

from tm_commonstuff import *

import argparse
import os
import sys
import datetime
import xml.etree.ElementTree as ET
import json
import time

def getJobs(users="*"):
    cmd = "qstat -u \"%s\" -g t -xml" % (users)
    output = getCmdOutput(cmd, EnvironnementSGE())

    jobs=dict()

    root = ET.fromstring(output)

    #premiere passe stages generales
    for job in root.findall('queue_info/job_list'):
        # print "job :", job.get('state')
        # print job.keys
        temp=dict()
        for child in job.getchildren():
            # print("    %s : %s" % ( child.tag, child.text) )
            temp[child.tag]=child.text

        JB_job_number = temp["JB_job_number"]
        try:
            foo = jobs[JB_job_number]["slots"]
        except:
            jobs[JB_job_number] = dict()
            jobs[JB_job_number]["slots"] = 0

        jobs[JB_job_number]["slots"] = jobs[JB_job_number]["slots"] + int(temp["slots"])
        jobs[JB_job_number]["JB_owner"] = temp["JB_owner"]
        jobs[JB_job_number]["state"] = temp["state"]
        jobs[JB_job_number]["JB_name"] = temp["JB_name"]
        jobs[JB_job_number]["date"] = temp["JAT_start_time"]
        jobs[JB_job_number]["queue"] = temp["queue_name"].split(".")[0]

    

    # retrait slot master sur les jobs parallele
    for job in jobs.keys():
        if jobs[job]["slots"] > 1:
            jobs[job]["slots"] = jobs[job]["slots"] - 1

    # deuxieme passe stats detaillées
    for job in root.findall('queue_info/job_list'):

        temp=dict()
        for child in job.getchildren():
            temp[child.tag]=child.text
        # print temp


        JB_job_number = temp["JB_job_number"]

        ( queue, host ) = temp["queue_name"].split("@")
	host = host.replace("btmcli", "btmcl")
	host = host.replace("btmclgvi", "btmclgv")

        jobs[JB_job_number]["queue"] = queue.replace(".q", "")
        # host = temp["queue_name"].split("@")[1]
        try:
            foo = jobs[JB_job_number]["hosts"]
        except:
            jobs[JB_job_number]["hosts"]=dict()
            jobs[JB_job_number]["hosts"][host] = 0

        try:
            foo = jobs[JB_job_number]["hosts"][host]
        except:
            jobs[JB_job_number]["hosts"][host] = 0
        if ((temp["master"] == "MASTER" and jobs[JB_job_number]["slots"] == 1) or (temp["master"] == "SLAVE" and jobs[JB_job_number]["slots"] > 1) ):
            jobs[JB_job_number]["hosts"][host] = jobs[JB_job_number]["hosts"][host] + int(temp["slots"])

    # jobs not running
    for job in root.findall('job_info/job_list'):
        temp=dict()
        for child in job.getchildren():
            temp[child.tag]=child.text
        JB_job_number = temp["JB_job_number"]

        jobs[JB_job_number] = dict()
        jobs[JB_job_number]["slots"] = int(temp["slots"])
        jobs[JB_job_number]["JB_owner"] = temp["JB_owner"]
        jobs[JB_job_number]["state"] = temp["state"]
        jobs[JB_job_number]["JB_name"] = temp["JB_name"]
        jobs[JB_job_number]["date"] = temp["JB_submission_time"]
        # jobs[JB_job_number]["duree"] = -1
        # jobs[JB_job_number]["queue"] = ""

    return jobs

def getJobsExt(users="*"):
    cmd = "qstat -u \"%s\" -ext -r -xml" % (users)
    output = getCmdOutput(cmd, EnvironnementSGE())

    ext=dict()

    root = ET.fromstring(output)
    for job in root.findall('queue_info/job_list'):

        temp=dict()
        for child in job.getchildren():
            temp[child.tag]=child.text
            for res in child.iter('hard_request'):
                # print ("hard_request : %s=%s" % (res.attrib['name'], res.text))
                if ( res.attrib['name'] == "h_cpu" or res.attrib['name'] == "h_rt" ):
                    temp["duree"] = res.text
            # if ( child.tag == 'hard_req_queue' and child.text == "visu.q" ):
                # temp["duree"] = 0
        # print json.dumps(temp,indent=3)
        JB_job_number = temp["JB_job_number"]

        ext[JB_job_number] = dict()
        try:
            ext[JB_job_number]["cpu_usage"] = "%.0f" % float(temp["cpu_usage"])
            ext[JB_job_number]["mem_usage"] = "%.0f" % float(temp["mem_usage"])
            ext[JB_job_number]["io_usage"] = "%.0f" % float(temp["io_usage"])
            ext[JB_job_number]["duree"] = int(temp["duree"])
        except KeyError:
            # json.dumps(xml, indent=3)
            # print "job hs:"+JB_job_number
            ext[JB_job_number]["cpu_usage"] = 0
            ext[JB_job_number]["mem_usage"] = 0
            ext[JB_job_number]["io_usage"] = 0
            ext[JB_job_number]["duree"] = 0
    return ext

    
""" jobs qui glandent rien... cpu_usage <<< elapsed*cores """
def checkUnderrun(jobs,ext, warning, critical):
    STATUS=NAGIOS_OK
    tmp=""
    underrun=0
    now = datetime.datetime.now()
    
    for j in [ x for x in jobs.keys() if (jobs[x]['state']=='r' and jobs[x]['queue'] in ( 'normale', 'courte', 'long', 'prioritaire', 'surcharge') )] :
        start = datetime.datetime.strptime(jobs[j]['date'], "%Y-%m-%dT%H:%M:%S")
        elapsed = int((now - start).total_seconds())
        supposed = jobs[j]['slots'] * elapsed
        pct = int(ext[j]['cpu_usage']) * 100 / supposed
        # print("%8s - elapsed=%10s - slots=%-3s - cpuusage=%-10s - supposed=%-10s - pct=%3s" % (j, elapsed, jobs[j]['slots'], ext[j]['cpu_usage'], supposed, pct) )
        if elapsed>300: # jobs de plus de 5 minutes pour avoir des valeurs >>> 0
            JSTATUS=NAGIOS_OK
            if pct <= critical:
                STATUS=max(STATUS, NAGIOS_CRITICAL)
                JSTATUS=NAGIOS_CRITICAL
            elif pct <= warning:
                STATUS=max(STATUS, NAGIOS_WARNING)        
                JSTATUS=NAGIOS_WARNING
            if JSTATUS>NAGIOS_OK:
                tmp="\n".join ( (tmp, "- %s : %s is at %s%% cpu utilization." % ( getNagiosStatus(JSTATUS), j, pct)))
                underrun+=1
        
    if STATUS == NAGIOS_OK:
        MESSAGE="%s - no jobs in idle state" % getNagiosStatus(STATUS)
    else:
        MESSAGE="%s - some jobs are in idle state" % getNagiosStatus(STATUS)
        MESSAGE="\n".join( (MESSAGE,tmp))
    PERFDATA="underrun=%s"%underrun
    return ("%s|%s"%(MESSAGE,PERFDATA),STATUS)
    
def checkOverrun(jobs, ext, warning, critical):
    STATUS=NAGIOS_OK
    tmp=""
    overrun=0
    now = datetime.datetime.now()
    running = [ x for x in jobs.keys() if jobs[x]['state']=='r' ]
    for j in running:
        start = datetime.datetime.strptime(jobs[j]['date'], "%Y-%m-%dT%H:%M:%S")
        elapsed = int((now - start).total_seconds())
        if elapsed>300: # jobs de plus de 5 minutes pour avoir des valeurs >>> 0 et les exts valides
            JSTATUS=NAGIOS_OK
            pct = elapsed*100/ext[j]['duree']
#            print("%7s - %19s - %8s - %8s - %0d" % (j, start, elapsed, ext[j]['duree'], pct))
            if elapsed > (ext[j]['duree']*critical/100):
                JSTATUS=NAGIOS_CRITICAL
                STATUS=max(STATUS, NAGIOS_CRITICAL)
            elif elapsed >= (ext[j]['duree']*warning/100):
                STATUS=max(STATUS, NAGIOS_WARNING)        
                JSTATUS=NAGIOS_WARNING
            if JSTATUS>NAGIOS_OK:
                tmp="\n".join ( (tmp, "- %s : job %s is running for a long time." % ( getNagiosStatus(JSTATUS), j)))
                overrun+=1

    if STATUS==NAGIOS_OK:
        MESSAGE="OK - no long running job found."
    else:
        MESSAGE="\n".join( ( "%s - some jobs are running for a long time" % getNagiosStatus(STATUS), tmp ) )
    PERFDATA="overrun=%s"%overrun
    return("%s|%s" % (MESSAGE, PERFDATA), STATUS)

def checkOverpend(jobs, warning, critical):
    STATUS=NAGIOS_OK
    tmp=""
    overpend=0
    now = datetime.datetime.now()
    pend = [ x for x in jobs.keys() if jobs[x]['state']=='qw' ]
    for j in pend:
        submit = datetime.datetime.strptime(jobs[j]['date'], "%Y-%m-%dT%H:%M:%S")
        elapsed = now - submit
        hours = elapsed.total_seconds()/3600
        # print("%20s - %20s - %25s - %s (%s)" % (submit, now, elapsed, hours, type(hours)))
        if hours >= critical:
            STATUS=max(STATUS, NAGIOS_CRITICAL)
            tmp="\n".join( (tmp, "- CRITICAL : job %s is pending for %s hours" % (j,int(hours))) )
            overpend+=1
        elif hours >= warning:
            STATUS=max(STATUS, NAGIOS_WARNING)
            tmp="\n".join( (tmp, "- WARNING : job %s is pending for %s hours" % (j,int(hours))) )
            overpend+=1
    if STATUS==NAGIOS_OK:
        MESSAGE="OK - no long pending job found."
    else:
        MESSAGE="\n".join( ( "%s - some jobs are pending for a long time" % getNagiosStatus(STATUS), tmp ) )
    PERFDATA="overpend=%s"%overpend
    return("%s|%s"%(MESSAGE,PERFDATA), STATUS)

def checkExecerror(jobs):
    err = [ x for x in jobs.keys() if jobs[x]['state']=='Eqw' ]
    if err:
        STATUS=NAGIOS_CRITICAL
        MESSAGE="%s - some jobs exited with error" % getNagiosStatus(STATUS)
        for job in err:
            MESSAGE="\n".join( (MESSAGE, " - %s" % job ))
    else:
        STATUS=NAGIOS_OK
        MESSAGE="%s - no job in error" % getNagiosStatus(STATUS)
    PERFDATA="error=%s" % len(err)
    return("%s|%s" % (MESSAGE, PERFDATA), STATUS)

def nagiosReport(output, status):
    print("%s"%output)
    sys.exit(status)
    
def main():

    """ args parsing """
    parser = argparse.ArgumentParser(formatter_class=lambda prog: argparse.HelpFormatter(prog,max_help_position = 50, width=120))
    parser.add_argument('--check', nargs='?', required=True, type=str, choices=('overrun', 'underrun', 'overpend', 'execerror'), metavar="check", help="check type : overrrun underrun overpend execerror")
    parser.add_argument('-w', '--warning', nargs='?',  type=int, metavar="warning",   help="warning (in hours)")
    parser.add_argument('-c', '--critical', nargs='?', type=int, metavar="critical", help="critical (in hours)")
    args = parser.parse_args()

    if args.check in ( 'overpend', 'underrun'):
        if not args.warning or not args.critical:
            print("ERROR: need both warning and critical values for this check.")
            sys.exit(NAGIOS_UNKNOWN)

    """ get jobs infos from SGE """
    jobs = getJobs()
    ext = getJobsExt()
    
    if args.check == "overrun":
        (output, status) = checkOverrun(jobs, ext, args.warning, args.critical)
        nagiosReport(output,status)
    
    if args.check == "underrun":
        (output, status) = checkUnderrun(jobs, ext, args.warning, args.critical)
        nagiosReport(output,status)

    elif args.check == "overpend":
        (output, status) = checkOverpend(jobs, args.warning, args.critical)
        nagiosReport(output,status)
    
    elif args.check == "execerror":
        (output, status) = checkExecerror(jobs)
        nagiosReport(output,status)
        
    else:
        print("SCRIPT ERROR")
        sys.exit(NAGIOS_UNKNOWN)
    
if __name__ == "__main__":
    main()
