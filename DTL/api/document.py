import json

from DTL.api import BaseDict, Path, apiUtils

#------------------------------------------------------------
#------------------------------------------------------------
class Document(BaseDict):
    '''Custom Dictionary class that has an associated file for easy saving/reading/printing'''
    def __init__(self, *args, **kwds):
        super(Document, self).__init__( *args, **kwds)
        apiUtils.synthesize(self, 'encoder', None)
    
    def serialize(self):
        return (dict(self), self.add_quotes(self.filepath))
    
    def deserialize(self, datadict={}, filepath=''):
        apiUtils.synthesize(self, 'filepath', Path(filepath))
        self.read()
        self._set_data(datadict=datadict)

    def setFilepath(self, filepath):
        self._filepath = Path(filepath)

    def save(self):
        '''Writes the dict data to the file'''
        data_dict = self.serialize()[0]
        if self.filepath != '' :
            with open(self.filepath,'wb') as file_handle :
                file_handle.write(self.unparse(data_dict))
    
    def read(self):
        '''Reads file and stores the data in self as a dictionary'''
        if not self.filepath.exists() :
            return
        with open(self.filepath,'r') as file_handle :
            data_dict = self.parse(file_handle)
        self._set_data(data_dict)
        
    def unparse(self, data_dict):
        return json.dumps(data_dict, sort_keys=True, indent=4, cls=self.encoder)
            
    def parse(self, file_handle):
        return json.load(file_handle)
    
    def prettyprint(self):
        print(self.unparse(self.serialize()[0]))
    
