from DTL.db.base import BaseProperty

#------------------------------------------------------------
def typename(obj):
    """Returns the type of obj as a string. More descriptive and specific than
    type(obj), and safe for any object, unlike __class__."""
    if hasattr(obj, '__class__'):
        return getattr(obj, '__class__').__name__
    else:
        return type(obj).__name__

#------------------------------------------------------------
def validateString(value,
                   name='unused',
                   empty_ok=False):
    """Raises an exception if value is not a valid string or a subclass thereof.

    A string is valid if it's not empty, no more than _MAX_STRING_LENGTH bytes,
    and not a Blob.

    Args:
      value: the value to validate.
      name: the name of this value; used in the exception message.
      empty_ok: allow empty value.
    """
    if value is None and empty_ok:
        return
    if not isinstance(value, str):
        raise ValueError('%s should be a string; received %s (a %s):' %
                         (name, value, typename(value)))
    if not value and not empty_ok:
        raise ValueError('%s must not be empty.' % name)

#------------------------------------------------------------
def validateInteger(value,
                    name='unused',
                    empty_ok=False,
                    zero_ok=True,
                    negative_ok=True):
    """Raises an exception if value is not a valid integer.

    An integer is valid if it's not negative or empty and is an integer
    (either int or long).

    Args:
      value: the value to validate.
      name: the name of this value; used in the exception message.
      empty_ok: allow None value.
      zero_ok: allow zero value.
      negative_ok: allow negative value.
    """
    if value is None and empty_ok:
        return
    if not isinstance(value, int):
        raise ValueError('%s should be an integer; received %s (a %s).' %
                         (name, value, typename(value)))
    if not value and not zero_ok:
        raise ValueError('%s must not be 0 (zero)' % name)
    if value < 0 and not negative_ok:
        raise ValueError('%s must not be negative.' % name)
    if not (-0x8000000000000000 <= value <= 0x7fffffffffffffff):
        raise OverflowError('%d is out of bounds for int64' % value)   


#------------------------------------------------------------
#------------------------------------------------------------
class _CoercingProperty(BaseProperty):
    """A BaseProperty subclass that extends validate() to coerce to self.data_type."""
    #------------------------------------------------------------
    def validate(self, value):
        """Coerce values (except None) to self.data_type."""
        value = super(_CoercingProperty, self).validate(value)
        if value is not None and not isinstance(value, self.data_type):
            if self.data_type == str :
                value = str(value)
            else:
                value = self.data_type(value)
        return value

#------------------------------------------------------------
#------------------------------------------------------------
class StringProperty(_CoercingProperty):
    """A textual property, which can be multi- or single-line."""
    data_type = str
    #------------------------------------------------------------
    def __init__(self, multiline=False, **kwds):
        super(StringProperty, self).__init__(**kwds)
        self.multiline = multiline

    #------------------------------------------------------------
    def validate(self, value):
        value = super(StringProperty, self).validate(value)
        validateString(value, self.name, True)
        if not self.multiline and value and value.find('\n') != -1:
            raise ValueError('Property %s is not multi-line' % self.name)
        return value


#------------------------------------------------------------
#------------------------------------------------------------
class IntegerProperty(_CoercingProperty):
    data_type = int
    #------------------------------------------------------------
    def validate(self, value):
        value = super(IntegerProperty, self).validate(value)
        validateInteger(value, self.name)
        return value

    #------------------------------------------------------------
    def empty(self, value):
        """0 is not an empty value."""
        return value is None


#------------------------------------------------------------
#------------------------------------------------------------
class FloatProperty(_CoercingProperty):
    data_type = float
    #------------------------------------------------------------
    def validate(self, value):
        value = super(FloatProperty, self).validate(value)
        if value is not None and not isinstance(value, float):
            raise ValueError('Property %s must be a float' % self.name)
        return value

    #------------------------------------------------------------
    def empty(self, value):
        """0.0 is not an empty value."""
        return value is None


#------------------------------------------------------------
#------------------------------------------------------------
class BooleanProperty(_CoercingProperty):
    data_type = bool
    #------------------------------------------------------------
    def validate(self, value):
        value = super(BooleanProperty, self).validate(value)
        if value is not None and not isinstance(value, bool):
            raise ValueError('Property %s must be a bool' % self.name)
        return value

    #------------------------------------------------------------
    def empty(self, value):
        """False is not an empty value."""
        return value is None


#------------------------------------------------------------
#------------------------------------------------------------
class ListProperty(BaseProperty):
    data_type = list
    allowed_types = set([str,str,str,bool,int,int,float,list,tuple])
    #------------------------------------------------------------
    def __init__(self, item_type, default=None, **kwds):
        if item_type is str:
            item_type = str
        if not isinstance(item_type, type):
            raise TypeError('Item type should be a type object')       
        if item_type not in self.allowed_types:
            raise ValueError('Item type %s is not acceptable' % item_type.__name__)   

        if default is None:
            default = []        

        self.item_type = item_type
        super(ListProperty, self).__init__(default=default,
                                           **kwds)

    #------------------------------------------------------------
    def __set__(self, model_instance, value):
        if not isinstance(value, list):
            if self.__get__(model_instance, model_instance.__class__):
                new_value = [value] + self.__get__(model_instance, model_instance.__class__)
            else:
                new_value = [value]
        else:
            new_value = value

        super(ListProperty, self).__set__(model_instance, new_value)

    #------------------------------------------------------------
    def validate(self, value):
        """
        Raises:
          ValueError if property is not a list whose items are instances of
          the reference_class given to the constructor.
        """
        value = super(ListProperty, self).validate(value)
        if value is not None:
            if not isinstance(value, list):
                raise ValueError('Property %s must be a list' % self.name)

            value = self.validate_list_contents(value)
        return value

    #------------------------------------------------------------
    def validate_list_contents(self, value):
        """Validates that all items in the list are of the correct type.
        Raises:
          ValueError if the list has items are not instances of the
          reference_class given to the constructor.
        """
        if self.item_type in (int, int):
            item_type = (int, int)
        else:
            item_type = self.item_type

        for item in value:
            if not isinstance(item, item_type):
                if item_type == (int, int):
                    raise BadValueError('Items in the %s list must all be integers.' %
                                        self.name)
                else:
                    raise BadValueError('Items in the %s list must all be %s instances' %
                                        (self.name, self.item_type.__name__))

    #------------------------------------------------------------
    def empty(self, value):
        """[] is not an empty value."""
        return value is None

    #------------------------------------------------------------
    def default_value(self):
        """Because the property supplied to 'default' is a static value,
        that value must be shallow copied to prevent all fields with
        default values from sharing the same instance.

        Returns:
          Copy of the default value.
        """
        return list(super(ListProperty, self).default_value())


#------------------------------------------------------------
#------------------------------------------------------------
class CustomDataProperty(BaseProperty):
    """A Property that can be given values of the constructors data_type value"""
    data_type = str
    #------------------------------------------------------------
    def __init__(self, item_type, **kwds):
        self.data_type = item_type
        super(CustomDataProperty, self).__init__(**kwds)

    #------------------------------------------------------------
    def validate(self, value):
        """Coerce values (except None) to self.data_type(which is set by the ctor).
        If the value given to the property is not of the data_type it will coerced to that type during validate

        Actual value Validation is left up to the type to handle constructor values of any type incoming

        """
        value = super(_CoercingProperty, self).validate(value)
        if value is not None and not isinstance(value, self.data_type):
            value = self.data_type(value)

        return value