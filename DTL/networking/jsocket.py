"""
Contains JsonSocket, JsonServer and JsonClient implementations (json object message passing server and client).

This file is part of the jsocket package.
Copyright (C) 2011 by 
Christopher Piekarski <chris@cpiekarski.com>

The jsocket_base module is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

The jsocket package is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with jsocket_base module.  If not, see <http://www.gnu.org/licenses/>.


Modified by Kyle Rockman

"""
import json
import socket
import struct
import time

from DTL.api import apiUtils, loggingUtils



RESPONSE_TEST = 'response test'
RESPONSE_TEST_FAIL = 'False'
RESPONSE_TEST_SUCCESS = 'True'

RESPONSE_TIMEOUT = 'timeout'
RESPONSE_CLOSED_SOCKET = 'closed'

#------------------------------------------------------------
def getLocalIP():
    '''A helper function that will try to get the local IP address in a multiplatform way'''
    addr = socket.gethostbyname(socket.gethostname())
    if addr == "127.0.0.1" : #Try internet connection method
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('google.com',0))
        addr = s.getsockname()[0]
    return addr


#------------------------------------------------------------
#------------------------------------------------------------
class BaseSocket(object, metaclass=loggingUtils.LoggingMetaclass):
    ADDRESS_FAMILY = socket.AF_INET
    SOCKET_TYPE = socket.SOCK_STREAM
    DEFAULT_PORT = 5000
    CONN_RETRY = 1
    
    #------------------------------------------------------------
    def __init__(self, address=None, port=None):
        self.socket = socket.socket(self.ADDRESS_FAMILY, self.SOCKET_TYPE)
        self.conn = self.socket
        apiUtils.synthesize(self, 'timeout', None)
        apiUtils.synthesize(self, 'address', address or getLocalIP(), True)
        apiUtils.synthesize(self, 'port', port or self.DEFAULT_PORT, True)
        apiUtils.synthesize(self, 'networkAddress', (self.address, self.port), True)
        
    #------------------------------------------------------------
    def setTimeout(self, timeout):
        self._timeout = timeout
        self.socket.settimeout(timeout)
    
    #------------------------------------------------------------
    def pack(self, data):
        frmt = "=%ds" % len(data)
        packed_hdr = struct.pack('!I', len(data))
        packed_msg = struct.pack(frmt, data)
        
        return packed_hdr, packed_msg
        
    #------------------------------------------------------------
    def unpack(self, frmt, data):
        return struct.unpack(frmt, data)[0]
        
    #------------------------------------------------------------
    def send_handshake(self):
        try:
            packed_hdr, packed_msg = self.pack(RESPONSE_TEST)
            self._send(packed_hdr)
            self._send(packed_msg)

            response = self.recv_handler()
            if response != RESPONSE_TEST_SUCCESS :
                return False
        except socket.timeout as e:
            self.log.info("socket.timeout: {0}".format(e))
            return False
        except Exception as e:
            #This helps when debugging
            #self.log.exception(e)
            self.log.info("send handshake failed: {0}".format(e))
            self._close_connection()
            return False
        return True
        
    #------------------------------------------------------------
    def recv_handshake(self, data):
        if data == RESPONSE_TEST :
            try:
                self._send(RESPONSE_TEST_SUCCESS)
                data = self.recv_handler()
            except socket.timeout as e:
                self.log.info("socket.timeout: {0}".format(e))
                return ''
            except Exception as e:
                #This helps when debugging
                #self.log.exception(e)
                self.log.info("recv handshake failed: {0}".format(e))
                self._close_connection()
                return ''
        return data
        
    #------------------------------------------------------------
    def _send(self, data):
        sent = 0
        while sent < len(data):
            sent += self.conn.send(data[sent:])
    
    #------------------------------------------------------------
    def send_handler(self, data):
        if self.socket:
            if self.send_handshake():
                packed_hdr, packed_msg = self.pack(data)
                self._send(packed_hdr)
                self._send(packed_msg)
            
    #------------------------------------------------------------
    def _recv(self, size):
        data = ''
        while len(data) < size:
            data_tmp = self.conn.recv(size-len(data))
            data += data_tmp
            if data_tmp == '':
                raise RuntimeError("socket connection broken")
        return data
    
    #------------------------------------------------------------
    def recv_handler(self):
        data = ''
        try:
            msg_size = self.unpack('!I', self._recv(4))
            frmt = "=%ds" % msg_size
            data = self.unpack(frmt, self._recv(msg_size))
            data = self.recv_handshake(data)
            return data
        except Exception as e:
            #This helps when debugging
            #self.log.exception(e)
            self.log.info("connection broken")
            self._close_connection()
        
        return data
    
    #------------------------------------------------------------
    def _close_socket(self):
        self.log.info("closing main socket")
        self.socket.close()
    
    #------------------------------------------------------------
    def _close_connection(self):
        self.log.info("closing the connection socket")
        self.conn.close()
    
    #------------------------------------------------------------
    def connect(self):
        for i in range(self.CONN_RETRY):
            try:
                self.socket.connect(self.networkAddress)
            except socket.error as msg:
                self.log.error("SockThread Error: %s" % msg)
                time.sleep(3)
                continue
            self.log.info("...Socket Connected")
            return True
        return False
    
    #------------------------------------------------------------
    def close(self):
        self._close_socket()
        if self.socket is not self.conn:
            self._close_connection()
            
    #------------------------------------------------------------
    def swap_socket(self, new_sock):
        """ Swaps the existing socket with a new one. Useful for setting socket after a new connection.
                @param - new_sock - socket to replace the existing default JsonSocket object"""
        del self.socket
        self.socket = new_sock
        self.conn = self.socket
        
    # Subclass methods to override
    #------------------------------------------------------------
    def send(self, data):
        self.send_handler(data)
        
    #------------------------------------------------------------
    def recv(self):
        return self.recv_handler()


#------------------------------------------------------------
#------------------------------------------------------------
class JsonSocket(BaseSocket):
    CONN_RETRY = 1
    
    #------------------------------------------------------------
    def __init__(self, **kwds):
        BaseSocket.__init__(self, **kwds)
    
    #------------------------------------------------------------
    def send(self, obj):
        data = json.dumps(obj)
        self.send_handler(data)
    
    #------------------------------------------------------------
    def read(self):
        data = self.recv_handler()
        obj = json.loads(data)
        return obj
