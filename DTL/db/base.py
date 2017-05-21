import sys
import json
import re
from copy import deepcopy
from DTL.qt import QtXml
from DTL.api import InternalError, Path, apiUtils

RESERVED_PROPERTY_NAME = re.compile('^__.*__$')

RESERVED_WORDS = ['addChild',
                  'asJson',
                  'asXml',
                  'child',
                  'childCount',
                  'insertChild',
                  'parent',
                  'properties',
                  'removeChild',
                  'resource',
                  'row',
                  'typeInfo',
                  '']

#------------------------------------------------------------
#------------------------------------------------------------
class ReservedWordError(InternalError):
    """Raised when a property is defined for a reserved word."""


#------------------------------------------------------------
def obj_for_name(module_name, class_name):
    try:
        return getattr(sys.modules[module_name], class_name)
    except KeyError:
        module = __import__(module_name, globals(), locals(), class_name)
        return getattr(module, class_name)
    except Exception as e:
        raise Exception(e)

#------------------------------------------------------------
def check_reserved_word(attr_name):
    """Raise an exception if attribute name is a reserved word.

    Args:
      attr_name: Name to check to see if it is a reserved word.

    Raises:
      ReservedWordError when attr_name is determined to be a reserved word.
    """
    if RESERVED_PROPERTY_NAME.match(attr_name):
        raise ReservedWordError(
            "Cannot define property.  All names both beginning and "
            "ending with '__' are reserved.")

    if attr_name in RESERVED_WORDS or attr_name in dir(BaseData):
        raise ReservedWordError(
            "Cannot define property using reserved word '%(attr_name)s'. "
            "If you would like to use this name in the datastore consider "
            "using a different name like %(attr_name)s_ and adding "
            "name='%(attr_name)s' to the parameter list of the property "
            "definition." % locals())


#------------------------------------------------------------
#------------------------------------------------------------
class BaseProperty(object):
    #------------------------------------------------------------
    def __init__(self, default=None, name=None, required=False, choices=None):
        apiUtils.synthesize(self, 'default', default)
        apiUtils.synthesize(self, 'name', name)
        apiUtils.synthesize(self, 'required', required)
        apiUtils.synthesize(self, 'choices', choices)
    
    #------------------------------------------------------------
    def __property_config__(self, property_name):
        """Configure property, connecting it to its data instance."""
        super(BaseProperty, self).__init__()
        if self._name is None:
            self._name = property_name
        
    #------------------------------------------------------------
    def __get__(self, instance, cls):
        if instance is None:
            return self
        try:
            return getattr(instance, self._attr_name())
        except AttributeError:
            self.__set__(instance, self._default)
            return self._default       
    
    #------------------------------------------------------------
    def __set__(self, instance, new_value):
        new_value = self.validate(new_value)
        setattr(instance, self._attr_name(), new_value)
        
    #------------------------------------------------------------
    def empty(self, value):
        """Determine if value is empty in the context of this property.
        For most kinds, this is equivalent to "not value", but for kinds like
        bool, the test is more subtle, so subclasses can override this method
        if necessary."""
        return not value
    
    #------------------------------------------------------------
    def validate(self, value):
        """Assert that provided value is compatible with this property."""
        if self.empty(value):
            if self._required:
                raise InternalError('Property {0} is required'.format(self._name))
        else:
            if self.choices():
                if value not in self.choices():
                    raise InternalError('Property {0} is {1}; must be one of {2}'.format(self._name, value, self._choices))
        return value
    
    #------------------------------------------------------------
    def default_value(self):
        return self._default
    
    #------------------------------------------------------------
    def _attr_name(self):
        """Attribute name we use for this property in model instances."""
        return '_' + self._name


#------------------------------------------------------------
#------------------------------------------------------------
class PropertiedClass(type):
    #------------------------------------------------------------
    def __init__(cls, name, bases, dct):
        super(PropertiedClass, cls).__init__(name, bases, dct)
        cls._properties = {}
        for base in bases:
            if hasattr(base, '_properties'):
                property_keys = set(base._properties.keys())
                if property_keys:
                    cls._properties.update(base.properties())
                    
        for name, attr in list(dct.items()):
            if isinstance(attr, BaseProperty) or issubclass(attr.__class__, BaseProperty):
                check_reserved_word(name)
                cls._properties[name] = attr
                attr.__property_config__(name)


#------------------------------------------------------------
#------------------------------------------------------------
class JsonBaseDataEncoder(json.JSONEncoder):
    #------------------------------------------------------------
    def default(self, obj):
        if issubclass(obj.__class__, BaseData):
            return obj.properties()
        return json.JSONEncoder.default(self, obj)


#------------------------------------------------------------
#------------------------------------------------------------
class BaseData(object, metaclass=PropertiedClass):
    def __init__(self, parent=None, *args, **kwds):
        super(BaseData, self).__init__()
        apiUtils.synthesize(self, 'parent', parent)
        apiUtils.synthesize(self, 'children', [])
        apiUtils.synthesize(self, 'columnMap', [])
        
        if parent is not None:
            parent.addChild(self)
            
        if args or kwds :
            raise Exception('Unhandled Args:\n{0}\n{1}'.format(str(args), str(kwds)))
    
    #------------------------------------------------------------
    def __repr__(self):
        output = '{0}( '.format(self.__class__.__name__)
        for key, prop in sorted(self.properties().items()):
            output += '{0}={1}, '.format(key, prop.__get__(self))
        output = output[:-2] + ' )'
        return str(output)
    
    #------------------------------------------------------------
    def copy(self):
        return deepcopy(self)
            
    #------------------------------------------------------------
    def addChild(self, child):
        self.children().append(child)
        child.setParent(self)
        
    #------------------------------------------------------------
    def insertChild(self, position, child):
        if position < 0 or position > self.childCount():
            return False
        
        self.children().insert(position, child)
        child.setParent(self)
        return True
    
    #------------------------------------------------------------
    def removeChild(self, position):
        if position < 0 or position > self.childCount():
            return False
        
        child = self.children().pop(position)
        child.setParent(None)

        return True
    
    #------------------------------------------------------------
    def child(self, row):
        return self.children()[row]
    
    #------------------------------------------------------------
    def childCount(self):
        return len(self.children())
    
    #------------------------------------------------------------
    def typeInfo(self):
        return self.__class__.__name__
    
    #------------------------------------------------------------
    def moduleInfo(self):
        return self.__class__.__module__
    
    #------------------------------------------------------------
    def row(self):
        if self.parent is not None:
            return self.parent.children.index(self)
        
    #------------------------------------------------------------
    def resource(self):
        return None
    
    #------------------------------------------------------------
    def data(self, column):
        try:
            attr = self.columnMap[column]
            return attr.__get__(self)
        except IndexError :
            pass
        except Exception as e :
            raise Exception(e)
    
    #------------------------------------------------------------
    def setData(self, column, value):
        try :
            attr = self.columnMap[column]
            attr.__set__(self,value.toPyObject())
        except IndexError :
            pass
        except Exception as e:
            raise Exception(e)
    
    #------------------------------------------------------------
    def readXml(self, filepath):
        with open(filepath,'r') as xml_file :
            xml_data = xml_file.read()
        
        xml_doc = QtXml.QDomDocument()
        xml_doc.setContent(xml_data)
        xml_doc = xml_doc.documentElement()
        
        self._readXml(xml_doc)
        
    #------------------------------------------------------------
    def saveXml(self, filepath):
        xml_data = self._asXml(QtXml.QDomDocument(), None)
        with open(filepath,'wb') as xml_file :
            xml_file.write(xml_data)
    
    #------------------------------------------------------------
    def readJson(self, filepath):     
        with open(filepath,'r') as json_file :
            json_data = json.load(json_file)
        
        self._readJson(json_data)
        
    #------------------------------------------------------------
    def saveJson(self, filepath):
        with open(filepath,'wb') as json_file :
            json_data = json.dumps(self._asJson(), sort_keys=True, indent=4, cls=JsonBaseDataEncoder)
            json_file.write(json_data)
    
    #------------------------------------------------------------
    def _readXml(self, current_node):
        for prop in list(self.properties().values()):
            if current_node.hasAttribute(prop.name()):
                attr_value = current_node.attribute(prop.name())
                prop.__set__(self, attr_value)        
        
        nodeList = current_node.childNodes()
        for child in [nodeList.item(i).toElement() for i in range(nodeList.count())]:
            module_name = str(child.attribute('module_name'))
            class_name = str(child.attribute('class_name'))
            node_name = str(child.attribute('name'))
            child_class = obj_for_name(module_name, class_name)
            new_child = child_class(name=node_name, parent=self)
            new_child._readXml(child)        
    
    #------------------------------------------------------------
    def _asXml(self, xml_doc, parent):
        node = xml_doc.createElement(self.typeInfo())
        if parent :
            parent.appendChild(node)
        else:
            xml_doc.appendChild(node)
       
        for k, v in list(self.properties().items()):
            node.setAttribute(k, v)
        
        node.setAttribute('module_name', self.moduleInfo())
        node.setAttribute('class_name', self.typeInfo())

        for i in self._children:
            i._asXml(xml_doc, node)

        return xml_doc.toString(indent=4)
    
    #------------------------------------------------------------
    def _readJson(self, json_data):
        for prop in list(self.properties().values()):
            if prop.name in json_data:
                prop_data = json_data[prop.name()]
                prop.__set__(self, prop_data)        

        for child in json_data.get('children',[]):
            module_name = child.pop('module_name')
            class_name = child.pop('class_name')
            child_class = obj_for_name(module_name, class_name)
            new_child = child_class(parent=self)
            new_child._readJson(child)
    
    #------------------------------------------------------------
    def _asJson(self):
        dictionary = self.properties()
        dictionary['class_name'] = self.typeInfo()
        dictionary['module_name'] = self.moduleInfo()
        children_data = list()
        for i in self._children:
            children_data.append(i._asJson())
        
        dictionary['children'] = children_data

        return dictionary
    
    #------------------------------------------------------------
    @classmethod
    def properties(cls):
        """Returns a dictionary of all the properties defined for this data object."""
        return dict(cls._properties)
