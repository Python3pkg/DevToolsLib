"""
Python based enumartion type

Usage Example
=============
    >>> Colors = Enum("Red","Yellow","Blue")
    >>> print Colors.Red
    0
    >>> print Colors.Yellow
    1
    >>> print 2 == Colors.Blue
    True
    >>> print Colors.names[2]
    Blue
    >>> print Colors.names.index('Blue')
    2
    
"""
__all__ = ['Enum']

def Enum(*enumerated):
    enums = dict(list(zip(enumerated, list(range(len(enumerated))))))
    enums["names"] = enumerated
    return type('Enum', (), enums)

if __name__ == "__main__":
    print("here")
    Colors = Enum("Red","Yellow","Blue")
    print(Colors.Red)
    print(Colors.Yellow)
    print(2 == Colors.Blue)
    print(Colors.names[2])
    print(Colors.names.index('Blue'))

