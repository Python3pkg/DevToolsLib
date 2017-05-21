import sys
import time
import cProfile
import pstats
import datetime
from functools import wraps

from DTL.api import loggingUtils, threadlib, Path

#------------------------------------------------------------
#------------------------------------------------------------
class PreAndPost(object, metaclass=loggingUtils.LoggingMetaclass):
    def __init__(self, func):
        self.func = func
        wraps(func)(self)

    def __get__(self, obj, type=None):
        return self.__class__(self.func.__get__(obj, type))

    def __call__(self, *args, **kwds):
        return self.call(*args, **kwds)
        
    def pre_call(self, *args, **kwds):
        pass
        
    def call(self, *args, **kwds):
        return self.func(*args, **kwds)

    def post_call(self, *args, **kwds):
        pass

    def error(self, retval, *args, **kwds):
        self.log.exception("")

#------------------------------------------------------------
#------------------------------------------------------------
class Safe(PreAndPost):
    def __init__(self, func):
        super(Safe, self).__init__(func)

    def __call__(self, *args, **kwds):
        retval = None
        try:
            self.pre_call(*args, **kwds)
            retval = self.call(*args, **kwds)
        except KeyboardInterrupt:
            raise Exception("Keyboard interruption detected")
        except:
            self.error(retval, *args, **kwds)
        finally:
            try:
                self.post_call(retval, *args, **kwds)
            except:
                try:
                    self.error(retval, *args, **kwds)
                except:
                    pass
            return retval

    def error(self, retval, *args, **kwds):
        if self.log.handlers :
            self.log.exception("")
        

#------------------------------------------------------------
#------------------------------------------------------------
class Timer(Safe):
    """A decorator which times a callable but also provides some timing functions
    to the func through itself being passed as a param to the function call"""
    def __init__(self, func):
        super(Timer, self).__init__(func)
        self._name = str(self.func.__name__)
        self.reset()
        
    def reset(self):
        self._starttime = datetime.datetime.now()
        self._lapStack = []
        self._records	= []
        self._laps	= []
        
    def recordLap(self, elapsed, message):
        self._records.append('\tlap: {0} | {1}'.format(elapsed, message))
        
    def startLap(self, message):
        self._lapStack.append((message,datetime.datetime.now()))
        return True
    
    def stopLap(self):
        if not self._lapStack:
            return False

        curr = datetime.datetime.now()
        message, start = self._lapStack.pop()

        #process the elapsed time
        elapsed	= str(curr - start)
        if not '.' in elapsed:
            elapsed += '.'

        while len(elapsed) < 14 :
            elapsed += '0'

        self.recordLap(elapsed, message)
        
    def newLap(self, message):
        """ Convenience method to stop the current lap and create a new lap """
        self.stopLap()
        self.startLap(message)
        
    def stop(self):
        #stop all the laps if not stopped
        while self._lapStack:
            self.stopLap()

        total = str(datetime.datetime.now() - self._starttime)

        #output the logs
        self.log.info('Time:{0} | {1} Stopwatch'.format(total,self._name))
        for record in self._records :
            self.log.info(record)
        
        return True

    def pre_call(self, *args, **kwds):
        self.startLap(self.func.__name__)
        
    def call(self, *args, **kwds):
        return self.func(timer=self, *args, **kwds)

    def post_call(self, *args, **kwds):
        self.stop()


#------------------------------------------------------------
#------------------------------------------------------------
class CommandTicker(Safe):
    TICKS = ['[.  ]', '[.. ]', '[...]', '[ ..]', '[  .]', '[   ]']
    def __init__(self, func, *args, **kwds):
        """A decorater that shows a command line progress bar for commandline operations that will take a long time"""
        super(CommandTicker, self).__init__(func, *args, **kwds)
        self.ticker_thread = threadlib.ThreadedProcess(*args, **kwds)
        self.ticker_thread.run = self.run
        
    def run(self):
        i = 0
        first = True        
        while self.ticker_thread.isMainloopAlive:
            time.sleep(.25)
            if i == len(self.TICKS):
                first = False
                i = 0
            if not first:
                sys.stderr.write("\r{0}\r".format(self.TICKS[i]))
                sys.stderr.flush()
            i += 1
        
        sys.stderr.flush()
    
    def pre_call(self, *args, **kwds):
        self.ticker_thread.start()
        
    def post_call(self, retval, *args, **kwds):
        self.ticker_thread.stop()
        sys.stderr.flush()
        sys.stderr.write("       ")
        sys.stderr.flush()
        


#------------------------------------------------------------
class Profile(Safe):
    """A decorator which profiles a callable."""
    def __init__(self, func, sort='cumulative', strip_dirs=False):
        super(Profile, self).__init__(func)
        self.sort = sort
        self.strip_dirs = strip_dirs
        base_path = Path.getTempPath().join('profile')
        base_path.makedirs()
        self.profile_path = base_path.join('{0}.{1}.profile'.format(func.__module__, func.__name__))
        self.stats_path = base_path.join('{0}.{1}.log'.format(func.__module__, func.__name__))
        self.profile = cProfile.Profile()
        
    def call(self, *args, **kwds):
        return self.profile.runcall(self.func, *args, **kwds)
    
    def post_call(self, retval, *args, **kwds):
        stream = open(self.stats_path, 'w')
        self.profile.dump_stats(self.profile_path)
        stats = pstats.Stats(self.profile_path, stream=stream)
        if self.strip_dirs:
            stats.strip_dirs()
        if isinstance(self.sort, (tuple, list)):
            stats.sort_stats(*self.sort)
        else:
            stats.sort_stats(self.sort)
        
        stats.print_stats()
        self.profile_path.remove()