import os
import sys
from DTL.api import apiUtils

class App(object):
    def __init__(self, *args, **kwds):
        pass
    
    def run(self):        
        cmd = ['C:\\Python27\\pythonw.exe',
               'C:\\Program Files (x86)\\Google\\google_appengine\\dev_appserver.py',
               '--skip_sdk_update_check=yes',
               '--port=9080',
               '--admin_port=8000',
               os.path.dirname(sys.argv[0])]
        print(cmd)
        apiUtils.execute(cmd)