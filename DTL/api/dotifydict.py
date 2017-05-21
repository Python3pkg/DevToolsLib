from DTL.api import BaseDict

#------------------------------------------------------------
#------------------------------------------------------------
class DotifyDict(BaseDict):
    #------------------------------------------------------------
    def __eq__(self, other):
        return dict.__eq__(self, other)
    
    #------------------------------------------------------------
    def __setitem__(self, key, value):
        if '.' in key:
            myKey, restOfKey = key.split('.', 1)
            target = self.set_default(myKey, DotifyDict())
            if not isinstance(target, DotifyDict):
                raise KeyError('cannot set "{0}" in "{1}" ({2})'.format(restOfKey, myKey, repr(target)))
            target[restOfKey] = value
        else:
            if isinstance(value, dict) and not isinstance(value, DotifyDict):
                value = DotifyDict(value)
            dict.__setitem__(self, key, value)
    
    #------------------------------------------------------------
    def __getitem__(self, key):
        if '.' not in key:
            return dict.__getitem__(self, key)
        myKey, restOfKey = key.split('.', 1)
        target = dict.__getitem__(self, myKey)
        if not isinstance(target, DotifyDict):
            raise KeyError('cannot get "{0}" in "{1}" ({2})'.format(restOfKey, myKey, repr(target)))
        return target[restOfKey]
    
    #------------------------------------------------------------
    def __contains__(self, key):
        if '.' not in key:
            return dict.__contains__(self, key)
        myKey, restOfKey = key.split('.', 1)
        target = dict.__getitem__(self, myKey)
        if not isinstance(target, DotifyDict):
            return False
        return restOfKey in target
    
    #------------------------------------------------------------
    def get(self, key, default=None):
        try:
            return self.__getitem__(key)
        except KeyError:
            return default
        except Exception as e:
            raise Exception(e)
    
    #------------------------------------------------------------
    def set_default(self, key, default):
        if key not in self:
            self[key] = default
        return self[key]
    
    #------------------------------------------------------------
    __setattr__ = __setitem__
    __getattr__ = __getitem__