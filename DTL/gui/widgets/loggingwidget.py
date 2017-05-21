import sys
import logging
import re
import weakref
from DTL.api import apiUtils
from DTL.qt import QtCore, QtGui
from DTL.gui import ColorSet
from DTL import resources

#------------------------------------------------------------
#------------------------------------------------------------
class LoggingColorSet(ColorSet):
    def __init__( self, *args, **defaults ):
        super(LoggingColorSet, self).__init__(*args, **defaults)
        
        self.setColorGroups(['Default'])
        
        self.setColor('Standard', QtGui.QColor('black'))
        self.setColor('Debug', QtGui.QColor('gray'))
        self.setColor('Info', QtGui.QColor('blue'))
        self.setColor('Warning', QtGui.QColor('orange').darker(150))
        self.setColor('Error', QtGui.QColor('darkRed'))
        self.setColor('Critical', QtGui.QColor('darkMagenta'))
        self.setColor('Background', QtGui.QColor(250, 250, 250))
        self.setColor('String', QtGui.QColor('darkRed'))
        self.setColor('Number', QtGui.QColor('orange').darker(150))
        self.setColor('Comment', QtGui.QColor('green'))
        self.setColor('Keyword', QtGui.QColor('blue'))
    
    @staticmethod
    def lightScheme():
        return LoggingColorSet()
    
    @staticmethod
    def darkScheme():
        out = LoggingColorSet()
        out.setColor('Standard', QtGui.QColor('white'))
        out.setColor('Debug', QtGui.QColor(220, 220, 220))
        out.setColor('Info', QtGui.QColor('cyan'))
        out.setColor('Warning', QtGui.QColor('yellow'))
        out.setColor('Error', QtGui.QColor('red'))
        out.setColor('Critical', QtGui.QColor('magenta'))
        out.setColor('Background', QtGui.QColor(40, 40, 40))
        out.setColor('String', QtGui.QColor('orange'))
        out.setColor('Number', QtGui.QColor('red'))
        out.setColor('Comment', QtGui.QColor(140, 255, 140))
        out.setColor('Keyword', QtGui.QColor('cyan'))
        
        return out

'''
class LogPipe(threading.Thread):

    def __init__(self, level):
        """Setup the object with a logger and a loglevel
        and start the thread
        """
        threading.Thread.__init__(self)
        self.daemon = False
        self.level = level
        self.fdRead, self.fdWrite = os.pipe()
        self.pipeReader = os.fdopen(self.fdRead)
        self.start()

    def fileno(self):
        """Return the write file descriptor of the pipe
        """
        return self.fdWrite

    def run(self):
        """Run the thread, logging everything.
        """
        for line in iter(self.pipeReader.readline, ''):
            logging.log(self.level, line.strip('\n'))

        self.pipeReader.close()

    def close(self):
        """Close the write end of the pipe.
        """
        os.close(self.fdWrite)
'''

#------------------------------------------------------------
#------------------------------------------------------------
class SysStreamLogger(object):
    """ Fake file-like stream object that also directs writes to a logger instance """
    
    def __init__(self, logger, log_level=logging.INFO):
        apiUtils.synthesize(self, 'logger', logger)
        apiUtils.synthesize(self, 'logLevel', log_level)
  
    def write(self, buf):
        if self.logLevel == logging.ERROR :
            sys.__stderr__.write(buf)
        else:
            sys.__stdout__.write(buf)
        for line in buf.rstrip().splitlines():
            self.logger.log(self.logLevel, line.rstrip())
            
    def flush(self):
        pass
            

#------------------------------------------------------------
#------------------------------------------------------------
class LoggingWidgetHandler(logging.Handler):
    """ Custom class for handling error exceptions via the logging system,
        based on the logging level. """
    
    def __init__( self, widget, showLevel=False, showDetails=False ):
        logging.Handler.__init__(self)
        apiUtils.synthesize(self, 'widget', weakref.ref(widget))
        apiUtils.synthesize(self, 'showLevel', showLevel)
        apiUtils.synthesize(self, 'showDetails', showDetails)
        apiUtils.synthesize(self, 'formatter', logging.Formatter())
    
    def emit( self, record ):
        """ 
        Throws an error based on the information that the logger reported,
        given the logging level.
        
        :param      record | <logging.LogRecord>
        """
        if self.widget:
            self.widget.pythonMessageLogged.emit(record.levelno, 
                                                 self.format(record) + '\n')
    
    def format( self, record ):
        """
        Formats the inputed log record into a return string.
        
        :param      record | <logging.LogRecord>
        """
        format= []
        
        if self._showLevel:
            format.append('[%(levelname)s]')
        
        if self._showDetails:
            details = 'path: %(pathname)s line: %(lineno)s'
            if ( 'func' in dir(record) ):
                details = '%(func)s ' + details
            
            format.append(details + ' ---')
        
        format.append('%(message)s')
        
        self._formatter._fmt = ' '.join(format)
        return self._formatter.format(record)
    
    def getWidget(self):
        """
        Returns the widget that is linked to this handler.
        
        :return     <QWidget>
        """
        return self._widget()

#------------------------------------------------------------
#------------------------------------------------------------
class LoggingWidget(QtGui.QTextEdit):    
    LoggingMap = {
        logging.DEBUG:    ('debug',    resources.find('img/log/bug.png')),
        logging.INFO:     ('info',     resources.find('img/log/info.png')),
        logging.WARN:     ('warning',  resources.find('img/log/warning.png')),
        logging.ERROR:    ('error',    resources.find('img/log/error.png')),
        logging.CRITICAL: ('critical', resources.find('img/log/critical.png')),
    }
    
    messageLogged       = QtCore.Signal(int, str)
    pythonMessageLogged = QtCore.Signal(int, str)
        
    def __init__(self, parent=None, overrideStdOut=False, overrideStdErr=False):
        super(LoggingWidget, self).__init__(parent)
        
        # set standard properties
        self.setReadOnly(True)
        self.setLineWrapMode(LoggingWidget.NoWrap)
        
        # setup the sys.stdout iterceptor
        handler = LoggingWidgetHandler(self)
        logger = logging.getLogger(apiUtils.getClassName(self))
        logger.setLevel(logging.DEBUG)
        logger.addHandler(handler)
        
        if overrideStdOut :
            loggerStdOut = SysStreamLogger(logger, logging.INFO)
            sys.stdout = loggerStdOut
            apiUtils.synthesize(self, 'loggerStdOut', loggerStdOut)
        
        if overrideStdErr :
            loggerStdErr = SysStreamLogger(logger, logging.ERROR)
            sys.stderr = loggerStdErr
            apiUtils.synthesize(self, 'loggerStdErr', loggerStdErr)
        
        # define custom properties
        apiUtils.synthesize(self, 'logger', logger)
        apiUtils.synthesize(self, 'clearOnClose', True)
        apiUtils.synthesize(self, 'handler', handler)
        apiUtils.synthesize(self, 'currentMode', 'standard')
        apiUtils.synthesize(self, 'blankCache', '')
        apiUtils.synthesize(self, 'mutex', QtCore.QMutex())
                
        # determine whether or not to use the light or dark configuration
        palette = self.palette()
        base    = palette.color(palette.Base)
        avg     = (base.red() + base.green() + base.blue()) / 3.0
        
        if ( avg < 160 ):
            colorSet = LoggingColorSet.darkScheme()
        else:
            colorSet = LoggingColorSet.lightScheme()
        
        apiUtils.synthesize(self, 'colorSet', colorSet)
        palette.setColor(palette.Text, colorSet.color('Standard'))
        palette.setColor(palette.Base, colorSet.color('Background'))
        self.setPalette(palette)
        
        # setup the levels
        self._loggingEnabled = {
            'debug':        True,
            'info':         True,
            'warning':      True,
            'error':        True,
            'critical':     True,
            'fatal':        True,
        }
        
        # create connections
        self.pythonMessageLogged.connect(self.log)
    
    def closeEvent( self, event ):
        """
        Clear the handler from the logger when this widget closes.
        
        :param      event | <QCloseEvent>
        """
        if ( self.clearOnClose ):
            self.setLogger(None)
            sys.stdout = sys.__stdout__
            
        super(LoggingWidget, self).closeEvent(event)
    
    def color( self, key ):
        """
        Returns the color value for the given key for this console.
        
        :param      key | <unicode>
        
        :return     <QColor>
        """
        return self._colorSet.color(str(key).capitalize())
    
    def critical( self, msg ):
        """
        Logs a critical message to the console.
        
        :param      msg | <unicode>
        """
        self.log('critical', msg)
        
    def info( self, msg ):
        """
        Inserts a debug message to the current system.
        
        :param      msg | <unicode>
        """
        self.log('info', msg)
    
    def debug( self, msg ):
        """
        Inserts a debug message to the current system.
        
        :param      msg | <unicode>
        """
        self.log('debug', msg)
        
    def warning( self, msg ):
        """
        Inserts a debug message to the current system.
        
        :param      msg | <unicode>
        """
        self.log('warning', msg)
    
    def error( self, msg ):
        """
        Inserts an error message to the current system.
        
        :param      msg | <unicode>
        """
        self.log('error', msg)
    
    def fatal( self, msg ):
        """
        Logs a fatal message to the system.
        
        :param      msg | <unicode>
        """
        self.log('fatal', msg)
    
    def isLoggingEnabled( self, level ):
        """
        Returns whether or not logging is enabled for the given level.
        
        :param      level | <int>
        """
        if ( type(level) == int ):
            level = self.LoggingMap.get(level, ('info', ''))[0]
            
        return self._loggingEnabled.get(level, True)
    
    def log( self, level, msg ):
        """
        Logs the inputed message with the given level.
        
        :param      level | <int> | logging level value
                    msg   | <unicode>
        
        :return     <bool> success
        """
        locker = QtCore.QMutexLocker(self.mutex)
        
        if ( not self.isLoggingEnabled(level) ):
            return False
        
        msg = self._blankCache + str(msg)
        if msg.endswith('\n'):
            self._blankCache = '\n'
            msg = msg[:-1]
        else:
            self._blankCache = ''
        
        self.setCurrentMode(level)
        self.insertPlainText(msg)
        
        if not self.signalsBlocked():
            self.messageLogged.emit(level, msg)
        
        self.scrollToEnd()
        
        return True
    
    def scrollToEnd( self ):
        """
        Scrolls to the end for this console edit.
        """
        vsbar = self.verticalScrollBar()
        vsbar.setValue(vsbar.maximum())
        
        hbar = self.horizontalScrollBar()
        hbar.setValue(0)
    
    def setColor( self, key, value ):
        """
        Sets the color value for the inputed color.
        
        :param      key     | <unicode>
                    value   | <QColor>
        """
        key = str(key).capitalize()
        self._colorSet.setColor(key, value)
        
        # update the palette information
        if ( key == 'Background' ):
            palette = self.palette()
            palette.setColor( palette.Base, value )
            self.setPalette(palette)
    
    def setColorSet( self, colorSet ):
        """
        Sets the colors for this console to the inputed collection.
        
        :param      colors | <LoggingColorSet>
        """
        self._colorSet = colorSet
        
        # update the palette information
        palette = self.palette()
        palette.setColor( palette.Text, colorSet.color('Standard') )
        palette.setColor( palette.Base, colorSet.color('Background') )
        self.setPalette(palette)
    
    def setCurrentMode( self, mode ):
        """
        Sets the current color mode for this console to the inputed value.
        
        :param      mode | <unicode>
        """
        if ( type(mode) == int ):
            mode = self.LoggingMap.get(mode, ('standard', ''))[0]
            
        if ( mode == self._currentMode ):
            return
            
        self._currentMode = mode
        
        color = self.color(mode)
        if ( not color.isValid() ):
            return
            
        format = QtGui.QTextCharFormat()
        format.setForeground( color )
        self.setCurrentCharFormat( format )
    
    def setLoggingEnabled( self, level, state ):
        """
        Sets whether or not this widget should log the inputed level amount.
        
        :param      level | <int>
                    state | <bool>
        """
        if ( type(level) == int ):
            level = self.LoggingMap.get(level, ('standard', ''))[0]
            
        self._loggingEnabled[level] = state
        
    def setLogger(self, logger):
        """
        Sets the logger instance that this widget will monitor.
        
        :param      logger  | <logging.Logger>
        """
        if self._logger == logger:
            return
        
        if self._logger:
            self._logger.removeHandler(self._handler)
        
        self._logger = logger
        try: self._loggerStdOut.logger = logger 
        except: pass
        try: self._loggerStdErr.logger = logger 
        except: pass
        
        if logger:
            logger.addHandler(self._handler)
                    


if __name__ == '__main__':
    from DTL.gui import Core
    import logging
    loggerwidget = LoggingWidget()
    
    loggerwidget.handler.showDetails = False
    loggerwidget.handler.showLevel = True
    logger = loggerwidget.logger    
    
    logger.log(logging.INFO, 'Hello World')
    logger.debug('Debug')
    logger.info('Info')
    logger.warning('Warning')
    logger.error('Error')
    logger.critical('Critical')
    logger.fatal('Fatal')
    
    print('This is a test message')
    print("here")

    loggerwidget.show()
    Core.Start()
    
    print('This is a test message 2')
    print("Here")
    