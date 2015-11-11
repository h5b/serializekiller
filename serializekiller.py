#!/usr/bin/env python
#-------------------------------------------------------------------------------
# Name:        SerializeKiller
# Purpose:     Finding vulnerable vulnerable servers
#
# Author:      (c) John de Kroon, 2015
#-------------------------------------------------------------------------------

import os
import subprocess
import json
import threading
import time
import socket
import sys
import argparse

from datetime import datetime

parser = argparse.ArgumentParser(prog='serializekiller.py', formatter_class=argparse.RawDescriptionHelpFormatter, description="""SerialIceKiller.
    Usage:
    ./serializekiller.py targets.txt
""")
parser.add_argument('file', help='File with targets')
args = parser.parse_args()


def nmap(url, retry = False, *args):
    global num_threads
    global shellCounter
    global threads

    num_threads +=1
    found = False
    cmd = 'nmap --open -p 1099,5005,8880,7001,16200 '+url
    print "Scanning: "+url
    try:
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        out, err = p.communicate()
        if "5005" in out:
            if(verify(url, "5005")):
                found = True
        if "8880" in out:
            if(verify(url, "8880")):
                found = True
        if "1099" in out:
            print " - (Possibly) Vulnerable "+url+" (1099)"
            found = True
        if "7001" in out:
            if(weblogic(url, 7001)):
                found = True
        if "16200" in out:
            if(weblogic(url, 16200)):
                found = True
        if(found):
            shellCounter +=1
        num_threads -=1
    except:
        num_threads -=1
        threads -= 1
        time.sleep(5)
        if(retry):
            print " ! Unable to scan this host "+url
        else:
            nmap(url, True)

def verify(url, port, retry = False):
    try:
        cmd = 'curl -m 10 --insecure https://'+url+":"+port
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        out, err = p.communicate()
        if "rO0AB" in out:
            print " - Vulnerable Websphere: "+url+" ("+port+")"
            return True
        
        cmd = 'curl -m 10 http://'+url+":"+port
        with open(os.devnull, 'w') as fp:
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        out, err = p.communicate()
        if "rO0AB" in out:
            print " - Vulnerable Websphere: "+url+" ("+port+")"
            return True
    except:
        time.sleep(3)
        if(retry):
            print " ! Unable to verify vulnerablity for host "+url+":"+str(port)
            return False
        return verify(url, port, True)

#Used this part from https://github.com/foxglovesec/JavaUnserializeExploits
def weblogic(url, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    server_address = (url, port)
    sock.connect(server_address)
    
    # Send headers
    headers='t3 12.2.1\nAS:255\nHL:19\nMS:10000000\nPU:t3://us-l-breens:7001\n\n'
    sock.sendall(headers)
    data = sock.recv(1024)
    sock.close()
    if "HELO" in data:
        print " - Vulnerable Weblogic: "+url+" ("+str(port)+")"
        return True
    return False

def dispatch(url):
    try:
        threading.Thread(target=nmap, args=(url, False, 1)).start()
    except:
        print " ! Unable to start thread. Waiting..."
        time.sleep(2)
        threads -= 2
        dispatch(url)

def worker():
    with open(args.file) as f:
        content = f.readlines()
        for url in content:
            while((num_threads > threads)):
                time.sleep(1)
            url = str(url.replace("\r", ''))
            url = str(url.replace("\n", '')) 
            url = str(url.replace("/", ''))
            dispatch(url)
        while(num_threads > 1):
            time.sleep(1)
        if(shellCounter > 0):
            shellCounterText = "\033[1;31m"+str(shellCounter)+"\033[1;m"
        else:
            shellCounterText = str(shellCounter)

        print "\r\n => scan done. "+shellCounterText+" vulnerable hosts found."
        print "Execution time: "+str(datetime.now() - startTime)
        exit()

if __name__ == '__main__':
    startTime = datetime.now()  
    print "\033[1;31mStart SerializeKiller...\033[1;m"
    print "This could take a while. Be patient.\r\n"
    num_threads = 0
    threads = 30
    shellCounter = 0
    t = threading.Thread(target=worker).start()