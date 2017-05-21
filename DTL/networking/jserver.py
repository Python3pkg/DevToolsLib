import time
import threading
import socket
import json

from DTL.networking.jsocket import JsonSocket
from DTL.api import ThreadedProcess, ThreadedProcessWithPrompt


#------------------------------------------------------------
#------------------------------------------------------------
class JsonServer(JsonSocket):
    #------------------------------------------------------------
    def __init__(self, **kwds):
        JsonSocket.__init__(self, *kwds)
        self._bind()
    
    #------------------------------------------------------------
    def _bind(self):
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(self.networkAddress)
        self.log.info('Server running on {0}'.format(self.networkAddress))
    
    #------------------------------------------------------------
    def _listen(self):
        self.socket.listen(1)
    
    #------------------------------------------------------------
    def _accept(self):
        return self.socket.accept()
    
    #------------------------------------------------------------
    def accept_connection(self):
        self._listen()
        self.conn, addr = self._accept()
        self.conn.settimeout(self.timeout())
        self.log.info("connection accepted from ({0}:{1})".format(addr[0] ,addr[1]))


#------------------------------------------------------------
#------------------------------------------------------------
class JsonServerThreaded(ThreadedProcessWithPrompt, JsonServer):
    #------------------------------------------------------------
    def __init__(self, **kwargs):
        ThreadedProcessWithPrompt.__init__(self)
        JsonServer.__init__(self, **kwargs)
        self.setDaemon(True)
    
    #------------------------------------------------------------
    def _process_message(self, obj):
        """This method is called every time a JSON object is received from a client
        	@param	obj	JSON "key: value" object received from client
        	@retval	None
        """
        pass
    
    #------------------------------------------------------------
    def main_loop(self):
        while self.isMainloopAlive():
            try:
                self.accept_connection()
            except socket.timeout as e:
                self.log.info("socket.timeout: %s" % e)
                continue
            except Exception as e:
                self.log.exception(e)
                continue

            while self.isMainloopAlive:
                try:
                    obj = self.recv()
                    self._process_message(obj)
                except socket.timeout as e:
                    self.log.info("socket.timeout: %s" % e)
                    continue
                except Exception as e:
                    self.log.exception(e)
                    self._close_connection()
                    break
            self.close()

#------------------------------------------------------------
class ServerFactoryThread(ThreadedProcess, JsonSocket):
    #------------------------------------------------------------
    def __init__(self, **kwds):
        ThreadedProcess.__init__(self, **kwds)
        JsonSocket.__init__(self, **kwds)
    
    #------------------------------------------------------------
    def run(self):
        while self.isAlive():
            try:
                obj = self.recv()
                self._process_message(obj)
            except socket.timeout as e:
                self.log.info("socket.timeout: %s" % e)
                continue
            except Exception as e:
                #This helps when debugging
                #self.log.exception(e)
                self.log.info("client connection broken, closing socket")
                self._close_connection()
                break
        self.close()

#------------------------------------------------------------
#------------------------------------------------------------
class ServerFactory(JsonServerThreaded):
    #------------------------------------------------------------
    def __init__(self, server_thread, **kwargs):
        JsonServerThreaded.__init__(self, **kwargs)
        if not issubclass(server_thread, ServerFactoryThread):
            raise TypeError("serverThread not of type", ServerFactoryThread)
        self._thread_type = server_thread
        self._threads = []
    
    #------------------------------------------------------------
    def run(self):
        while self.isMainloopAlive:
            tmp = self._thread_type()
            self._purge_threads()
            while self.conn and self.isMainloopAlive:
                try:
                    self.accept_connection()
                except socket.timeout as e:
                    self.log.info("socket.timeout: %s" % e)
                    continue
                except Exception as e:
                    self.log.exception(e)
                    continue
                else:
                    tmp.swap_socket(self.conn)
                    tmp.start()
                    self._threads.append(tmp)
                    break

        self._wait_to_exit()		
        self.close()
    
    #------------------------------------------------------------
    def stop_all(self):
        for t in self._threads:
            if t.isAlive():
                t.exit()
                t.join()
    
    #------------------------------------------------------------
    def _purge_threads(self):
        for t in self._threads:
            if not t.isAlive():
                self._threads.remove(t)
    
    #------------------------------------------------------------
    def _wait_to_exit(self):
        while self._get_num_of_active_threads():
            time.sleep(0.2)
    
    #------------------------------------------------------------
    def _get_num_of_active_threads(self):
        return len([True for x in self._threads if x.isAlive()])
    
    #------------------------------------------------------------
    active = property(_get_num_of_active_threads, doc="number of active threads")


#------------------------------------------------------------
#------------------------------------------------------------
if __name__ == '__main__':
    class MyFactoryThread(ServerFactoryThread):
        """	This is an example factory thread, which the server factory will
        instantiate for each new connection.
        """
        def __init__(self, **kwds):
            super(MyFactoryThread, self).__init__(**kwds)
            self.setTimeout(2.0)
    
        def _process_message(self, obj):
            """ virtual method - Implementer must define protocol """
            if obj != '':
                if obj['message'] == "new connection":
                    self.send({'action':'new connections'})
                
                self.log.info("Received: {0}".format(obj))
    
    #------------------------------------------------------------
    class MyServerFactory(ServerFactory):
        def __init__(self, **kwds):
            ServerFactory.__init__(self, **kwds)
            
        #------------------------------------------------------------
        def handle_input(self, user_input):
            if user_input == 'show threads':
                for thread in [x for x in self._threads if x.isActive()]:
                    print(thread)
            return False
    
    server = MyServerFactory(server_thread=MyFactoryThread)
    server.start()