import os
import sys
import traceback
from functools import partial
from P4 import P4, P4Exception

from DTL.api import Path, apiUtils
from DTL.gui import guiUtils
from DTL.gui.widgets import LoginWidget, ChoiceWidget

#------------------------------------------------------------
#------------------------------------------------------------
class P4Client(object):
    
    def __init__(self, username=None, password=None, client=None, port=None, verbose=False):
        apiUtils.synthesize(self, 'p4Conn', None)
        apiUtils.synthesize(self, 'p4Info', {})
        apiUtils.synthesize(self, 'verbose', verbose)
        apiUtils.synthesize(self, 'p4User', username or os.getenv('P4USER'))
        apiUtils.synthesize(self, 'p4Password', password or os.getenv('P4PASSWD'))
        apiUtils.synthesize(self, 'p4Client', client or os.getenv('P4CLIENT'))
        apiUtils.synthesize(self, 'p4Port', port or os.getenv('P4PORT'))
        
        self._connect()
        
    def _tryCredentials(self, msg='P4 Login', force=False):
        #Validate Credentials
        if self.p4User is None or self.p4Password is None:
            success, user, password = LoginWidget.getCredentials(loginMsg=msg,
                                                                 credentialsFile=Path.getTempPath().join('p4_login.dat'),
                                                                 force=force)
            if not success:
                raise ValueError('Invalid Login Infomation!')
            self.setP4User(user)
            self.setP4Password(password)
        
        self.p4Conn.user = self.p4User
        self.p4Conn.password = self.p4Password
        
        try:
            self.p4Conn.run_login()
        except P4Exception as e:
            self.setP4User(None)
            self.setP4Password(None)
            self._tryCredentials(msg='P4 Login Invalid!', force=True)
        except:
            raise
        
    def _tryWorkspace(self):
        #Validate Client Workspace
        if self.p4Client is None:
            success, client = guiUtils.getUserInput(msg='Please Enter Default Workspace:')
            if not success :
                raise P4Exception('Unable to determine P4CLIENT')
            self.setP4Client(client)
            
        if self.p4Client == '' :
            self._tryWorkspace()
            return
        
        #Set the env's for next time
        if 'P4CLIENT' not in os.environ:
            apiUtils.setEnv('P4CLIENT', self.p4Client)
        
        self.p4Conn.client = self.p4Client
        
    def _tryServer(self):
        #Validate P4 Port
        if self.p4Port is None:
            success, port = guiUtils.getUserInput(msg='Please Enter P4 Server:')
            if not success :
                raise P4Exception('Unable to determine P4PORT')
            self.setP4Port(port)
            
        if self.p4Port == '' :
            self._tryWorkspace()
            return
        
        #Set the env's for next time
        if 'P4PORT' not in os.environ:
            apiUtils.setEnv('P4PORT', self.p4Port)
        
        self.p4Conn.port = self.p4Port
        
    def _tryInfo(self):
        #Grab p4Info
        p4info = self.p4Conn.run("info")[0] # Run "p4 info" (returns a dict)
        if self.verbose :
            for key, value in list(p4info.items()) :
                print(key, '\t', value)
        #Test Connection
        if not self.p4Conn.connected() :
            raise P4Exception('Unable to validate p4 connection.')
        
        self.setP4Info(p4info)
    
    def _setupConnection(self):
        self.setP4Conn(P4())
        
        #self._tryWorkspace()
        self._tryServer()
        
        self.p4Conn.connect()
        self.p4Conn.prog = "DTL Perforce Python Tools"
        self.p4Conn.exception_level = 1 # ignore warnings
        
        self._tryCredentials()
        self._tryInfo()
    
    def _connect(self):
        try:
            if self.p4Conn.connected() :
                return
        except AttributeError:
            #If unable to check connected then we don't have a P4 Obj so 
            self._setupConnection()
        except:
            raise
        
    def run(self, *args, **kwds):
        return partial(self.p4Conn.run, *args, **kwds)()
    
    def sync(self, path=None):
        self.run('sync', path or (self.getWorkspaceRoot() + "\\..."))
        
    def getLatestChange(self):
        return self.run('changes', '-s', 'submitted', '-m', '1')[0]['change']
    
    def getWorkspaceRoot(self):
        return Path(self.p4Info['clientRoot'])
    
    def getWorkspaceFiles(self):
        return self.getWorkspaceRoot().walk()
    
    def getCounterChange(self, counter_name):
        return self.run('counter', counter_name)[0]['value']

    def getWorkspacePath(self, path):
        return Path(path.replace("//" + self.p4Info['clientName'],
                                 self.p4Info['clientRoot']))
    
    def getChangeDescription(self, change_num):
        try:
            return self.p4Conn.fetch_changelist(change_num)
        except P4Exception :
            return None
        except:
            raise
    
    def updateWorkspace(self, mappings, root=[]):
        if guiUtils.getConfirmDialog('Would you like to use your default workspace?\n{0}'.format(self.p4Client())) :
            workspace_name = self.p4Client
        else:
            sample = str(os.getenv('USERNAME') + '_' + os.getenv('COMPUTERNAME') + '_dev')
            workspace_success, workspace_name = guiUtils.getUserInput('Please specify a name for the P4 workspace to update.\n EXAMPLE:  {0}'.format(os.getenv('P4CLIENT',sample)))
            if not workspace_success:
                return
            workspace_name = workspace_name.replace(" ","_")
        
        client_spec = self.p4Conn.fetch_client(workspace_name)
        if 'Update' not in client_spec or 'Access' not in client_spec : #NEW WORKSPACE
            drives = apiUtils.getDrives()
            success, choice = ChoiceWidget.getChoice(msg='Please specify a drive location for this P4 workspace.', choices=drives)
            if not success:
                return False
            client_spec['Root'] = str(Path(drives[choice] + ':\\').join(*root))
        
        client_spec['View'] = [x.format(workspace_name) for x in mappings]
        self.p4Conn.save_client(client_spec)
        return True
    
if __name__ == '__main__':
    p4 = P4Client()
    print(p4.getChangeDescription(5688))