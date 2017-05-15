#!/usr/bin/env python
# -*- coding: UTF-8 -*-
　
"""
Nom       : cl_jobs.py
Role      : Affiche les jobs SGE dans un format plus lisible et synthÃ©tique que qstat
Auteur    : FrÃ©dÃ©ric Parance
Version   : v1.0 du 12/04/2016
"""
　
import datetime
import xml.etree.ElementTree as ET
import json
import datetime
import time
import code # code.interact(local=locals())
import sys
import os
import pwd
import re
import argparse
from terminaltables import AsciiTable, DoubleTable
from colorclass import Color, enable_all_colors, disable_all_colors, is_enabled
　
colors = {
    "queue" : {
        "batch" : {
            "members" : [ "courte", "normale", "longue" ],
            "color" : "magenta"
        },
        "visu" : {
            "members" : [ "visu" ],
            "color" : "cyan"
        },
        "int" : {
            "members" : [ "int" ],
            "color" : "blue"
        }
    }
}
　
　
def getCmdOutput(cmd):
    import shlex, subprocess
    args = shlex.split(cmd)
    p = subprocess.Popen(args, stdout=subprocess.PIPE)
    (stdout, stderr) = p.communicate()
    return stdout
　
def getJobs(users="*"):
    cmd = "qstat -u \"%s\" -g t -xml" % (users)
    output = getCmdOutput(cmd)
　
    jobs=dict()
　
    root = ET.fromstring(output)
　
    #premiere passe stats generales
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
　
    
　
    # retrait 1 slot master sur les jobs parallele
    for job in jobs.keys():
        if jobs[job]["slots"] > 1:
            jobs[job]["slots"] = jobs[job]["slots"] - 1
　
    # deuxieme passe stats detaillÃ©es
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
　
        if ( temp["master"] == "MASTER" ):
             jobs[JB_job_number]["master"] = host
             
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
    output = getCmdOutput(cmd)
　
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
　
def dateReFormat(date, duree):
    result=""
    
    start = datetime.datetime.strptime(date, "%Y-%m-%dT%H:%M:%S")
    elapsed = now - start
    result = datetime.datetime.strftime(start, "%m/%d %H:%M")
    if duree:
        pct = int(elapsed.total_seconds()*100/duree)
        result = result + " [%3i%%]" % (pct)
        if is_enabled() and pct>=100:
            result = Color("{red}%s{/red}" % (result) )
     
    return result
　
def cpuReFormat(job, ext):
    result=""
    eff=0
    # print json.dumps(job, indent=3)
    # print json.dumps(ext, indent=3)
    
    nbJ = int(ext["cpu_usage"])/86400
    nbH = (int(ext["cpu_usage"])%86400) / 3600
    nbM =  int(ext["cpu_usage"]) % (86400) % 3600 / 60
    
    start = datetime.datetime.strptime(job['date'], "%Y-%m-%dT%H:%M:%S")
    elapsed = int((now - start).total_seconds())
    supposed = job['slots'] * elapsed
    if supposed>0:
        eff = int(ext['cpu_usage']) * 100 / supposed
　
    if nbJ > 0:
        result = result+"%ij " % nbJ
    result = result+ "%02i:%02i [%3s%%]" % (nbH, nbM, eff)
　
    return result
　
def enCouleur(list):
    if args.color == None:
        return list
　
    newlist = []
    color=""
　
    if args.color != None:
        if args.color == "queue":
            index=6
            
        for group in colors[args.color]:
            # print group, list[index]
            if list[index] in colors[args.color][group]["members"]:
                color=colors[args.color][group]["color"]
                break
        if color=="":
            color="white"
        for i in range(0, len(list)):
            newlist.append( Color("{%s}%s{/%s}" % (color, list[i], color) ) )
            
    return newlist
　
def hostsReformat(hosts, master):
    tmp=[]
    for host in sorted(hosts):
        if host == master:
            tmp.insert(0, "*".join( (str(hosts[host]), host)))
        else:
            tmp.append("*".join( (str(hosts[host]), host)) )
    return " ".join(tmp)
    
    
def displayJobs(jobs,ext):
    table_data = [ [ "jobid", "user", "job name", "s", "date", "slots", "queue", "hosts", "cpu", "mem", "io" ] ]
　
    runningJobs = []
    otherJobs = []
    # print json.dumps(jobs)
    for job in sorted(jobs):
        if (jobs[job]["state"] == "r"):
            try:
                tmp = [
                    job,
                    jobs[job]["JB_owner"],
                    jobs[job]["JB_name"],
                    jobs[job]["state"],
                    dateReFormat(jobs[job]["date"], ext[job]["duree"]),
                    str(jobs[job]["slots"]),
                    jobs[job]["queue"],
                    hostsReformat(jobs[job]["hosts"], jobs[job]["master"]),
                    cpuReFormat(jobs[job], ext[job]),
                    str(ext[job]["mem_usage"]),
                    str(ext[job]["io_usage"])
                    ]
            except KeyError:
                tmp = [
                    job,
                    jobs[job]["JB_owner"],
                    jobs[job]["JB_name"],
                    jobs[job]["state"],
                    "-",
                    str(jobs[job]["slots"]),
                    jobs[job]["queue"],
                    hostsReformat(jobs[job]["hosts"], jobs[job]["master"]),
                    "-",
                    "-",
                    "-"
                    ]
            if is_enabled:
                runningJobs.append( enCouleur ( tmp ) )
            else:
                runningJobs.append( tmp )
        else:
            tmp = [
                job,
                jobs[job]["JB_owner"],
                jobs[job]["JB_name"],
                jobs[job]["state"],
                dateReFormat(jobs[job]["date"],0), str(jobs[job]["slots"]),
                "", "", "", "", "" ]
            otherJobs.append( tmp )
    table_data = table_data+runningJobs
    table_data = table_data+otherJobs
    # print json.dumps(table_data,indent=3)
　
    if sys.stdout.isatty():
        table = DoubleTable(table_data, " SGE jobs ")
        # print table.column_max_width(7)
    else:
        table = AsciiTable(table_data, " SGE jobs ")
    table.justify_columns[5] = "right"
    table.justify_columns[8] = "right"
    table.justify_columns[9] = "right"
    table.justify_columns[10] = "right"
　
    # code.interact(local=locals())
    # compression liste hosts
    if sys.stdout.isatty():
        hostIndex=7
        maxHostWidth = table.column_max_width(hostIndex)
        for l in table.table_data:
            if len(l[hostIndex]) > maxHostWidth:
                if is_enabled():
                    l[hostIndex]=Color(re.sub("btmcl", "cl", l[hostIndex]))
                    if len(l[hostIndex]) > maxHostWidth:
                        l[hostIndex]=Color(l[hostIndex][:maxHostWidth-3]+"...")+Color("{white}{/white}") # bugfix sinon ca colorise la barre ...
                else:
                    l[hostIndex]=re.sub("btmcl", "cl", l[hostIndex])
                    if len(l[hostIndex]) > maxHostWidth:
                        l[hostIndex]=l[hostIndex][:maxHostWidth-3]+"..."
    
    try:
        print table.table    
    except:
        print json.dumps(table_data,indent=3)
        sys.exit(1)
　
def main():
    global now
    global args
    
    # options/arguments
    parser = argparse.ArgumentParser(formatter_class=lambda prog: argparse.HelpFormatter(prog,max_help_position = 50, width=120))
    parser.add_argument('-l', '--loop', nargs='?', const=30, type=int, metavar="SECS", help="""boucle automatique toutes les [SECS] secondes (30 secondes par dÃ©faut)""")
    parser.add_argument('-u', '--user', type=str, help="""filtre par utilisateur(s), sÃ©parÃ©s par une virgule : -u user[,user2]. -u all ou -u "*" pour tous les users (par dÃ©faut en tant que root """)
    parser.add_argument('-c', '--color', nargs='?', const="queue", type=str, metavar="field", help="""en couleur : -c queue, -c jobname """)
　
    # parser.add_argument('-s', '--sort', nargs='?', const='jobid', type=str, metavar="SORT", help="tri sur le champs <SORT> (jobid par dÃ©faut) [NON IMPLEMENTE POUR LE MOMENT]")
    args = parser.parse_args()
　
    
    if args.color != None:
        enable_all_colors()
    else:
        disable_all_colors()
    if not sys.stdout.isatty(): 
        disable_all_colors()
    
    if args.user:
        filtre_users = args.user
        if args.user == "all":
            filtre_users = "*"
    else:
        if pwd.getpwuid(os.getuid()).pw_uid == 0:
            filtre_users = "*"
        else:
            # filtre_users = pwd.getpwuid(os.getuid()).pw_name
            filtre_users = "*"
    # print("filtre_users=%s" % filtre_users)
    # sys.exit(0)
    
    
    
    # lancement
    if args.loop:
        while(True):
            now = datetime.datetime.now()
            jobs = getJobs(users=filtre_users)
            ext = getJobsExt(users=filtre_users)
            os.system('clear')
            displayJobs(jobs, ext)
            try:
                time.sleep(args.loop)
            except KeyboardInterrupt:
                print
                sys.exit(0)
            print("reloading...")
    else:
        now = datetime.datetime.now()
        jobs = getJobs(users=filtre_users)
        ext = getJobsExt(users=filtre_users)
        displayJobs(jobs, ext)
            
if __name__ == "__main__":
    main()
　
