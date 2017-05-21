import os.path
import subprocess
import base64
from DTL.qt import QtGui, QtCore
from DTL.api import apiUtils
from DTL.gui import Dialog, guiUtils

#------------------------------------------------------------
#------------------------------------------------------------
class ChoiceWidget(Dialog):
    choiceSubmitted = QtCore.pyqtSignal(int)
    
    #------------------------------------------------------------
    def onFinalize(self, msg='Choose', choices=[]):
        apiUtils.synthesize(self, 'msg', msg)
        apiUtils.synthesize(self, 'submitted', False)
        
        self.setModal(True)
        
        self.ui_message.setText(self.msg)
        self.ui_submit.clicked.connect(self.emitChoiceSubmitted)
        for choice in choices :
            self.ui_choices.addItem(choice)
        self.center()
        
    #------------------------------------------------------------
    def emitChoiceSubmitted(self):
        if not self.signalsBlocked():
            choice = self.ui_choices.currentIndex()
            self.choiceSubmitted.emit(choice)
            self.setSubmitted(True)
            self.close()
            
    #------------------------------------------------------------
    @staticmethod
    def getChoice(*args, **kwds):
        success, choice = False, None
        widget = ChoiceWidget(*args, **kwds)
        if not widget.submitted :
            widget.exec_()
        success = widget.submitted
        if success :
            choice = widget.ui_choices.currentIndex()
        
        return success, choice
    

if __name__ == "__main__":
    print(ChoiceWidget.getChoice(msg='Choose a drive', choices=apiUtils.getDrives()))
    
    
