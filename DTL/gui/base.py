import sys
import logging
from DTL.qt import QtCore, QtGui, loadUi
from DTL.api import Path, loggingUtils, apiUtils
from DTL.gui import Core, guiUtils

#------------------------------------------------------------
#------------------------------------------------------------
class BaseGUI(object):
    _qtclass = None  
    _instance = None

    #------------------------------------------------------------
    @classmethod
    def instance(cls, *args, **kwds):
        """If you only want to have one instance of a GUI, use this method.
        It will only create a new instance of the class if the class variable _instance is none."""
        if cls._instance is None:
            cls._instance = cls(*args, **kwds)
        return cls._instance   

    #------------------------------------------------------------
    def __init__( self, parent=None, flags=0, *args, **kwds ):
        parent = self._validateParent(parent)
        
        if args :
            raise Exception('Unhandled Args:\n' + str(a))       

        if flags:
            self._qtclass.__init__(self, parent, flags)
        else:
            self._qtclass.__init__(self, parent)
        
        self.loadUi(parent)
        self.setupStyle()
        self.onFinalize(**kwds)
        self._readSettings()

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
        self._saveSettings()
        self._qtclass.closeEvent(self, event)

    #------------------------------------------------------------
    def exec_( self ):
        return self._qtclass.exec_(self)

    #------------------------------------------------------------
    def _saveSettings(self):
        settings = QtCore.QSettings(Path.getTempPath().join('ui_settings', apiUtils.getClassName(self) + '.ini'),
                                    QtCore.QSettings.IniFormat)
        settings.beginGroup(self.objectName())

        self.saveSettings(settings)

        settings.endGroup()

    #------------------------------------------------------------
    def _readSettings(self):
        settings = QtCore.QSettings(Path.getTempPath().join('ui_settings', apiUtils.getClassName(self) + '.ini'),
                                    QtCore.QSettings.IniFormat)
        settings.beginGroup(self.objectName())

        self.readSettings(settings)

        settings.endGroup()

    #------------------------------------------------------------
    # Begin Subclass Overrides
    #------------------------------------------------------------
    def loadUi(self, parent=None):
        if issubclass(self.__class__, QtGui.QWizard) :
            return
        try:
            path = Path(sys.modules[self.__module__].__file__)
        except:
            path = Path(apiUtils.getMainDir())
        
        if path :
            ui_file = path.dir().join('views','{0}.ui'.format(self.__class__.__name__))
            if ui_file.exists() :
                self = loadUi(ui_file, parent, self, self.customWidgets())
            else:
                print('Unable to load ui file | {0}'.format(ui_file))
                #self.log.warning('Unable to load ui file | {0}'.format(ui_file))
                
    def customWidgets(self):
        from DTL.gui.widgets import LoginWidget, PathWidget, ColorPickerWidget, ColorPickerButton, ChoiceWidget, ProgressWidget, PropertiesEditor
        return {'LoginWidget':LoginWidget,
                'PathWidget':PathWidget,
                'ColorPickerWidget':ColorPickerWidget,
                'ColorPickerButton':ColorPickerButton,
                'ChoiceWidget':ChoiceWidget,
                'ProgressWidget':ProgressWidget,
                'PropertiesEditor':PropertiesEditor}
    
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

if __name__ == '__main__':
    pass