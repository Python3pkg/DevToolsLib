import os
import sys
import logging
from functools import partial
from argparse import ArgumentParser

from DTL.api import loggingUtils, apiUtils, ImportModule

class pycisArgumentParser(ArgumentParser):
    """ArgumentParser that doesn't exit on error"""
    class ArgParseError(Exception):
        pass

    def parse_args(self, args=None, namespace=None):
        if not args: return None
        try: return ArgumentParser.parse_args(self, args, namespace)
        except self.__class__.ArgParseError : return None

    def exit(self, status=0, message=None):
        """Override exit function to prevent exiting the program"""
        if message:
            self._print_message(message, sys.stderr)
        raise self.__class__.ArgParseError()

class pyCis(object, metaclass=loggingUtils.LoggingMetaclass):
    '''pyCis - Python Console Intelligence System'''
    
    #------------------------------------------------------------
    def __init__(self):
        apiUtils.synthesize(self, 'commands', None)
        apiUtils.synthesize(self, 'parser', None)
        
        self._setupLogging()
        self._setupParser()
        self._setupCommands()
        
    #------------------------------------------------------------
    def _setupLogging(self):
        loggingUtils.setupStreamLogger(formatter=logging.Formatter('\t%(message)s'))
    
    #------------------------------------------------------------
    def _setupParser(self):
        main_parser = pycisArgumentParser(prog='', add_help=False)
        self.setParser(main_parser)
    
    #------------------------------------------------------------
    def loadCommandClass(self, name, module_name):
        """
        Given a command name and an application name, returns the Command
        class instance. All errors raised by the import process
        (ImportError, AttributeError) are allowed to propagate.
        """
        module = ImportModule('%s.%s' % (module_name, name))
        return module.Command()
    
    #------------------------------------------------------------
    def _findCommands(self, management_dir):
        """
        Given a path to a commands directory, returns a list of all the command
        names that are available.
    
        Returns an empty list if no commands are defined.
        """
        command_dir = os.path.join(management_dir, 'commands')
        try:
            return [f[:-3] for f in os.listdir(command_dir) if not f.startswith('_') and f.endswith('.py')]
        except OSError:
            return []
        
    #------------------------------------------------------------
    def _getCommands(self):
        _commands = self.commands()
        if _commands is None :
            _commands = dict([(name, 'DTL.pycis.commands') for name in self._findCommands(apiUtils.getMainDir())])
            
            #Handle other pycis sub app commands
        
        self.setCommands(_commands)
        return _commands
    
    #------------------------------------------------------------
    def _setupCommands(self):
        subparsers = self.parser().add_subparsers()
        for name, module_name in list(self._getCommands().items()):
            
            instance = self.loadCommandClass(name, module_name)
            parser = subparsers.add_parser(name, add_help=instance.helpFlag(), description=instance.__doc__)
            instance.setupParser(parser)
    
    #------------------------------------------------------------
    def _mainloop(self):
        while True:
            line = input('pyCis >> ')
            args = self.parser().parse_args(line.split())
            if args:
                args.func(args)
    
    #------------------------------------------------------------
    def print_help(self):
        self.parser().print_help()
        
    #------------------------------------------------------------
    def print_command_help(self, commandName):
        for name, module_name in list(self.commands().items()):
            if name == commandName :
                instance = self.loadCommandClass(name, module_name)
                print(instance.__doc__)
    
    #------------------------------------------------------------
    def run(self):
        self._mainloop()
    

if __name__ == '__main__':
    main = pyCis()
    main.run()