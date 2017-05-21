import sys
import maya.OpenMayaUI as OM_UI
import maya.cmds as cmds
from DTL.qt import QtCore, QtGui, wrapinstance
from DTL.gui.core.external.core import Core
from DTL.api import Path

#  TO DO:
#      -MayaCore has a number of utility functions that should be in a mayaUtils module that can be accessed when you are in a maya environment
#


#------------------------------------------------------------
#------------------------------------------------------------
class MayaCore(Core):
    '''Tool Environment Core for Maya'''
    
    #------------------------------------------------------------
    def __init__(self):
        super(MayaCore, self).__init__()
        self.setEnvironment(Core.EnvironmentTypes.Maya)
        print(sys.path)
    
    #------------------------------------------------------------
    def setupLogging(self):
        pass
        #Logger.setupFileLogger()
        #Logger.setupDatabaseLogger()
    
    #------------------------------------------------------------
    def rootWindow(self):
        """Get the main Maya window as a QtGui.QMainWindow instance"""
        window = None
        ptr = OM_UI.MQtUtil.mainWindow()
        if ptr is not None:
            window = wrapinstance(ptr)
        return window
    
    #------------------------------------------------------------
    def getFileFromUser(self, parent=None, ext=''):
        output = cmds.fileDialog2(fm=1, caption='Choose...')
        if output is None :
            return Path('')
        else :
            return Path(output[0])
    
    #------------------------------------------------------------
    def getDirFromUser(self, parent=None):
        output = cmds.fileDialog2(fm=3, caption='Choose...')
        if output is None :
            return Path('')
        else :
            return Path(output[0])
        
    #------------------------------------------------------------
    def getSaveFileFromUser(self, parent=None, ext=[]):
        output = cmds.fileDialog2(fm=0, okc='Save', caption='Save...')
        if output is None :
            return Path('')
        else :
            return Path(output[0])
        
    #------------------------------------------------------------
    @staticmethod
    def getMayaSelection():
        return cmds.ls(sl=1, l=1)
    
    #------------------------------------------------------------
    @staticmethod
    def clearAllAnimCurves():
        """Wipes all animation based on selection,
        if selection is empty then it wipes all animation in the scene
        """
        selection = MayaCore.getMayaSelection()
        if not selection :
            for channel in cmds.ls(type='animCurve'):
                cmds.delete(channel)
            return
        for item in selection:
            if "objectSet" == cmds.nodeType(item):
                for joint in cmds.listConnections(item, type='joint'):
                    for channel in cmds.listConnections(joint, type='animCurve'):
                        cmds.delete(channel)
            else:
                for channel in cmds.listConnections(item, type='animCurve'):
                    cmds.delete(channel)
                    
    #------------------------------------------------------------
    @staticmethod
    def clearVisor():
        """clean up all the unused clips in the visor"""
        clipLibrary = cmds.ls(type='clipLibrary')
        if not clipLibrary:
            return
        clipScheduler = cmds.ls(type='clipScheduler')
        if not clipScheduler :
            return
        
        clipLibraryList = set(cmds.listConnections(clipLibrary[0],type='animClip'))
        clipSchedulerList = set(cmds.listConnections(clipScheduler[0], type='animClip'))
        compiled = set()
        for item in clipSchedulerList :
            compiled.update(set(cmds.listConnections(item, type='animClip')))
        
        clipLibraryList.difference_update(compiled)
        for item in clipLibraryList :
            cmds.delete(item)
    
    #------------------------------------------------------------
    @staticmethod
    def clearScheduler():
        """Clears the scene of all clip schedulers"""
        for scheduler in cmds.ls(type='clipScheduler'):
            cmds.delete(scheduler)
        
        MayaCore.clearVisor()
        cmds.select(cl=1)
        MayaCore.clearAllAnimCurves()

    #------------------------------------------------------------
    @staticmethod
    def getMayaQtObject(mayaUiName):
        """Convert a Maya ui path(Ex: "scriptEditorPanel1Window|TearOffPane|scriptEditorPanel1|testButton" ) to a Qt object"""	    
        ptr = OM_UI.MQtUtil.findControl(mayaUiName)
        if ptr is None:
            ptr = OM_UI.MQtUtil.findLayout(mayaUiName)
        if ptr is None:
            ptr = OM_UI.MQtUtil.findMenuItem(mayaUiName)
        if ptr is not None:
            return sip.wrapinstance(int(ptr), QtCore.QObject)