"""
$ ls -al /dev/name/local/_tracelog  
nrw-rw-rw-   1 root      nto               0 Oct 11 14:38 /dev/name/local/_tracelog
$ python3.2 replay.py 
Could not find platform independent libraries <prefix>
Consider setting $PYTHONHOME to <prefix>[:<exec_prefix>]
1073741825
-1
$ ls -al /dev/name/local/_tracelog  
ls: No such file or directory (/dev/name/local/_tracelog)
"""

import os
import sys

from ctypes import *

libc = CDLL("libc.so")

CRASH_DIR = "./crashes/"
FILE_NAME = "7246816.bin"
ENDPOINT = sys.argv[1]
SIZE = 5430

# Script which replays a captured testcase
fd = open(CRASH_DIR + FILE_NAME,"rb")
testcase = fd.read()
print(testcase)
fd.close()

coid = libc.name_open(ENDPOINT,0)
print(coid)

ret = libc.MsgSend(coid,testcase,SIZE,0,0)
print(ret)

# Check if endpoint is still alive:

print(os.path.exists('/dev/name/local/phone-service'))