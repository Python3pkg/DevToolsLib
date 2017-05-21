import json
from xml.parsers import expat
from xml.sax.saxutils import XMLGenerator
from xml.sax.xmlreader import AttributesImpl
from xml.dom.minidom import parseString
try:
    from io import StringIO
except ImportError:
    try:
        from io import StringIO
    except ImportError:
        from io import StringIO
try:
    from collections import OrderedDict
except ImportError :
    OrderedDict = dict

try:
    _basestring = str
except NameError:
    _basestring = str
try:
    _unicode = str
except NameError:
    _unicode = str

from DTL.api import Path, Document, DotifyDict


#------------------------------------------------------------
#------------------------------------------------------------
class ParsingInterrupted(Exception): pass


#------------------------------------------------------------
#------------------------------------------------------------
class _DictSAXHandler(object):
    """Written by: Martin Blech  -  Integrated by: Kyle Rockman"""
    def __init__(self,
                 item_depth=0,
                 item_callback=lambda *args: True,
                 xml_attribs=True,
                 attr_prefix='@',
                 cdata_key='#text',
                 force_cdata=True,
                 cdata_separator='',
                 postprocessor=None,
                 dict_constructor=OrderedDict,
                 strip_whitespace=True):
        self.path = []
        self.stack = []
        self.data = None
        self.item = None
        self.item_depth = item_depth
        self.xml_attribs = xml_attribs
        self.item_callback = item_callback
        self.attr_prefix = attr_prefix
        self.cdata_key = cdata_key
        self.force_cdata = force_cdata
        self.cdata_separator = cdata_separator
        self.postprocessor = postprocessor
        self.dict_constructor = dict_constructor
        self.strip_whitespace = strip_whitespace
    
    #------------------------------------------------------------
    def startElement(self, name, attrs):
        attrs = self.dict_constructor(list(zip(attrs[0::2], attrs[1::2])))
        self.path.append((name, attrs or None))
        if len(self.path) > self.item_depth:
            self.stack.append((self.item, self.data))
            if self.xml_attribs:
                attrs = self.dict_constructor(
                    (self.attr_prefix+key, value)
                    for (key, value) in list(attrs.items()))
            else:
                attrs = None
            self.item = attrs or None
            self.data = None
    
    #------------------------------------------------------------
    def endElement(self, name):
        if len(self.path) == self.item_depth:
            item = self.item
            if item is None:
                item = self.data
            should_continue = self.item_callback(self.path, item)
            if not should_continue:
                raise ParsingInterrupted()
        if len(self.stack):
            item, data = self.item, self.data
            self.item, self.data = self.stack.pop()
            if self.strip_whitespace and data is not None:
                data = data.strip() or None
            if data and self.force_cdata and item is None:
                item = self.dict_constructor()
            if item is not None:
                if data:
                    self.push_data(item, self.cdata_key, data)
                self.item = self.push_data(self.item, name, item)
            else:
                self.item = self.push_data(self.item, name, data)
        else:
            self.item = self.data = None
        self.path.pop()
    
    #------------------------------------------------------------
    def characters(self, data):
        if not self.data:
            self.data = data
        else:
            self.data += self.cdata_separator + data
    
    #------------------------------------------------------------
    def push_data(self, item, key, data):
        if self.postprocessor is not None:
            result = self.postprocessor(self.path, key, data)
            if result is None:
                return item
            key, data = result
        if item is None:
            item = self.dict_constructor()
        try:
            value = item[key]
            if isinstance(value, list):
                value.append(data)
            else:
                item[key] = [value, data]
        except KeyError:
            item[key] = data
        return item


#------------------------------------------------------------
#------------------------------------------------------------
class XmlDocument(Document):
    '''Custom Dictionary class that has an associated xml file for easy saving/reading'''
    #------------------------------------------------------------
    def __init__(self, *args, **kwds):
        super(XmlDocument, self).__init__(*args, **kwds)
    
    #------------------------------------------------------------
    def _emit(self, key, value, content_handler,
              attr_prefix='@',
              cdata_key='#text',
              root=True,
              preprocessor=None):
        if preprocessor is not None:
            result = preprocessor(key, value)
            if result is None:
                return
            key, value = result
        if not isinstance(value, (list, tuple)):
            value = [value]
        if root and len(value) > 1:
            raise ValueError('document with multiple roots')
        for v in value:
            if v is None:
                v = OrderedDict()
            elif not isinstance(v, dict):
                v = _unicode(v)
            if isinstance(v, _basestring):
                v = OrderedDict(((cdata_key, v),))
            cdata = None
            attrs = OrderedDict()
            children = []
            for ik, iv in list(v.items()):
                if ik == cdata_key:
                    cdata = iv
                    continue
                if ik.startswith(attr_prefix):
                    attrs[ik[len(attr_prefix):]] = iv
                    continue
                children.append((ik, iv))
            content_handler.startElement(key, AttributesImpl(attrs))
            for child_key, child_value in children:
                self._emit(child_key, child_value, content_handler,
                      attr_prefix, cdata_key, False, preprocessor)
            if cdata is not None:
                content_handler.characters(cdata)
            content_handler.endElement(key)
                
    #------------------------------------------------------------
    def parse(self, file_handle, **kwds):
        data_stream = file_handle.read()
        handler = _DictSAXHandler(**kwds)
        parser = expat.ParserCreate()
        parser.ordered_attributes = True
        parser.StartElementHandler = handler.startElement
        parser.EndElementHandler = handler.endElement
        parser.CharacterDataHandler = handler.characters
        try:
            parser.ParseFile(data_stream)
        except (TypeError, AttributeError):
            if isinstance(data_stream, _unicode):
                data_stream = data_stream.encode('utf-8')
            parser.Parse(data_stream, True)
        return handler.item   
    
    #------------------------------------------------------------
    def unparse(self, data_dict, **kwds):
        ((key, value),) = list(data_dict.items())
        output = StringIO()
        content_handler = XMLGenerator(output, 'utf-8')
        content_handler.startDocument()
        self._emit(key, value, content_handler, **kwds)
        content_handler.endDocument()
        value = output.getvalue()
        try:
            value = value.decode('utf-8')
        except AttributeError:
            pass
        return parseString(value).toprettyxml(indent="\t")
    
    #------------------------------------------------------------
    @staticmethod
    def getValuesAsList(dictionary, keyList, allowNone=True, keyErrorMsg='Unable to find key'):
        dotified = DotifyDict(dictionary)
        dot_key = '.'.join(keyList[:-1])
        if len(keyList) == 1 :
            data = dictionary
        else:
            data = dotified.get(dot_key, None)
            if data is None:
                if allowNone :
                    return []
                raise KeyError(keyErrorMsg)
        if keyList[-1] in data and not isinstance(data[keyList[-1]], list):
            data = [data[keyList[-1]]]
        else:
            data = data.get(keyList[-1],[])
        
        return data
    
    def print_json(self):
        print(json.dumps(self.serialize()[0], sort_keys=True, indent=4, cls=self.encoder))



def remove_whilespace_nodes(node, unlink=False):
    """Removes all of the whitespace-only text decendants of a DOM node.

    When creating a DOM from an XML source, XML parsers are required to
    consider several conditions when deciding whether to include
    whitespace-only text nodes. This function ignores all of those
    conditions and removes all whitespace-only text decendants of the
    specified node. If the unlink flag is specified, the removed text
    nodes are unlinked so that their storage can be reclaimed. If the
    specified node is a whitespace-only text node then it is left
    unmodified."""

    remove_list = []
    for child in node.childNodes:
        if child.nodeType == Node.TEXT_NODE and \
           not child.data.strip():
            remove_list.append(child)
        elif child.hasChildNodes():
            remove_whilespace_nodes(child, unlink)
    for node in remove_list:
        node.parentNode.removeChild(node)
        if unlink:
            node.unlink()
