import sys
import threading
import time

myLock = threading.Lock()

def message_loop():
    while True:
        with myLock:
            time.sleep(1)
            print("Interrupting text!")

def handle_input():
    myLock.acquire()
    msg = input('Prompt>>>')
    if msg == 'stop' :
        return
    if msg == 'restart' :
        myLock.release()
        loop()
        return
    print("Received {0}".format(msg))
    myLock.release()
    loop()

def loop():
    try:
        while True:
            time.sleep(100)
    except KeyboardInterrupt:
        handle_input()


thread = threading.Thread(target = message_loop)
thread.daemon=True
thread.start()
loop()
