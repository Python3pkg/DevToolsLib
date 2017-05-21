import os
import sys
import imp
import getpass

#------------------------------------------------------------
def mainIsFrozen():
    """Returns whether we are frozen via py2exe.
    This will affect how we find out where we are located."""
    return (hasattr(sys, "frozen") or # new py2exe
            hasattr(sys, "importers") # old py2exe
            or imp.is_frozen("__main__")) # tools/freeze

#------------------------------------------------------------
def getPkgDir():
    """ This will get us the program's directory,
    even if we are frozen using py2exe"""
    if mainIsFrozen():
        return os.path.dirname(sys.executable)
    if '__file__' in globals():
        return os.path.dirname(__file__)
    if sys.argv[0] == '' :
        return os.getcwd()
    return os.path.dirname(sys.argv[0])

SECRET_KEY = '11131986dtl11131986dtl'
PKG_DIR = os.path.dirname(getPkgDir())
PKG_NAME = os.path.basename(PKG_DIR)

PKG_DATA_DIR = os.path.join(os.path.expanduser('~'),('.' + PKG_NAME))
if not os.path.exists(PKG_DATA_DIR) :
    try:
        os.makedirs(PKG_DATA_DIR)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise

PKG_RESOURCE_PATH = os.path.join(PKG_DIR, 'resources')

if os.name == 'posix':
    OS_TYPE = 'Linux'
elif os.name == 'nt':
    OS_TYPE = 'Windows'
elif os.name == 'osx':
    OS_TYPE = 'MacOS'
else :
    OS_TYPE = None
    
COMPANY = ''