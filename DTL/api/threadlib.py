import time
import threading

from DTL.api import apiUtils

#------------------------------------------------------------
class Process(object):
    #------------------------------------------------------------
    def __init__(self):
        apiUtils.synthesize(self, 'isMainloopAlive', False)
        apiUtils.synthesize(self, 'isPromptloopAlive', False)
    
    #------------------------------------------------------------
    def run(self):
        while self.isMainloopAlive:
            self.main_loop()
        
    #------------------------------------------------------------
    def main_loop(self):
        pass
    
    #------------------------------------------------------------
    def prompt_loop(self):
        while self.isPromptloopAlive:
            user_input = input('Prompt>>>')
            
            #DEBUG
            print("UserInput: {0}".format(user_input))
            #DEBUG
            
            if self.handle_input_defaults(user_input):
                break
            if self.handle_input(user_input):
                break
        
    #------------------------------------------------------------
    def handle_input_defaults(self, user_input):
        if user_input == 'restart' :
            self.stop()
            return True
        if user_input == 'stop' :
            self.stop()
            return True
        if user_input == 'end' :
            self.stop()
            return True
        if user_input == 'exit' :
            self.setIsPromptloopAlive(False)
            return True
        return False
        
    #------------------------------------------------------------
    def handle_input(self, user_input):
        return False
    
    #------------------------------------------------------------
    def start(self):
        """The newly living know nothing of the dead"""
        self.setIsMainloopAlive(True)
        self.run()
    
    #------------------------------------------------------------
    def stop(self):
        """The life of the dead is in the memory of the living"""
        self.setIsMainloopAlive(False)
        self.setIsPromptloopAlive(False)


#------------------------------------------------------------
#------------------------------------------------------------
class ThreadedProcess(threading.Thread, Process):
    #------------------------------------------------------------
    def __init__(self, daemon=True, **kwds):
        threading.Thread.__init__(self, **kwds)
        Process.__init__(self)
        apiUtils.synthesize(self, 'threadLock', threading.Lock())
        self.setDaemon(daemon)

    #------------------------------------------------------------
    def start(self):
        '''we override the start because we want the thread to handle calling run'''
        self.setIsMainloopAlive(True)        
        super(ThreadedProcess, self).start()


#------------------------------------------------------------
#------------------------------------------------------------
class ThreadedProcessWithPrompt(ThreadedProcess):
    #------------------------------------------------------------
    def __init__(self, daemon=True, **kwds):
        super(ThreadedProcessWithPrompt, self).__init__(**kwds)
        self.setDaemon(daemon)
    
    #------------------------------------------------------------
    def start(self):
        '''we override the start because we want the thread to handle calling run and we want to start our hidden prompt loop'''
        super(ThreadedProcessWithPrompt, self).start()
        while self.isMainloopAlive:
            try:
                while True:
                    time.sleep(100)
            except KeyboardInterrupt:
                self.setIsPromptloopAlive(True)
                self.threadLock.acquire()
                self.prompt_loop()
                self.threadLock.release()



            

    