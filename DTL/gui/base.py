import sys
from PyQt4 import QtGui, uic
from PyQt4.QtCore import Qt

from DTL.api import Path, Logger, Utils
from DTL.gui import Core, guiUtils

#------------------------------------------------------------
#------------------------------------------------------------
class BaseGUI(object):
    _qtclass = None  

    #------------------------------------------------------------
    def __init__( self, parent=None, flags=0, *args, **kwds ):
        parent = self._validateParent(parent)
        
        if args or kwds :
            raise Exception('Unhandled Args:\n' + str(a) + '\n' + str(kwds))       

        if flags:
            self._qtclass.__init__(self, parent, flags)
        else:
            self._qtclass.__init__(self, parent)

        self.logger = Logger.getSubLogger(self.__class__.__name__)
        self.onInit()
        self.loadUi()
        self.setupStyle()
        self.onFinalize()

    #------------------------------------------------------------
    def _validateParent(self, parent=None):
        if parent is None:
            parent = Core.rootWindow()

        return parent
    
    #------------------------------------------------------------
    def center(self):
        qr = self._qtclass.frameGeometry(self)
        cp = QtGui.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    #------------------------------------------------------------
    def closeEvent( self, event ):
        self._qtclass.closeEvent(self, event)

    #------------------------------------------------------------
    def exec_( self ):
        return self._qtclass.exec_(self)

    #------------------------------------------------------------
    def _saveSettings(self):
        settings = guiUtils.getAppSettings()
        settings.beginGroup(self.objectName())

        self.saveSettings(settings)

        settings.endGroup()

    #------------------------------------------------------------
    def _readSettings(self):
        settings = guiUtils.getAppSettings()
        settings.beginGroup(self.objectName())

        self.readSettings(settings)

        settings.endGroup()

    #------------------------------------------------------------
    # Begin Subclass Overrides
    #------------------------------------------------------------
    def onInit(self):
        pass
    
    #------------------------------------------------------------
    def loadUi(self):
        if issubclass(self.__class__, QtGui.QWizard) :
            return
        try:
            path = Path(sys.modules[self.__module__].__file__)
        except:
            path = Path(Utils.getMainDir())
        
        if path :
            ui_file = path.dir().join('views','{0}.ui'.format(self.__class__.__name__))
            if ui_file.exists() :
                self = uic.loadUi(ui_file, self)
            else:
                self.logger.warning('Unable to load ui file | {0}'.format(ui_file))
    
    #------------------------------------------------------------
    def setupStyle(self):
        if self.parent():
            self.setPalette(self.parent().palette())        

    #------------------------------------------------------------
    def onFinalize(self):
        pass

    #------------------------------------------------------------
    def saveSettings(self, settings):
        pass

    #------------------------------------------------------------
    def readSettings(self, settings):
        pass