#!python2
import os
import sys
import traceback

SITECUSTOMIZE = '''#!python
import os
import site

site.addsitedir(os.environ.get('PYTHON_ENVIRONMENT',''))
'''

def main(*argv):
    env = input('Enter environment name:')
    local_path = os.path.normpath(os.path.dirname(argv[0]))
    environment_path = os.path.join(local_path, env)
    if not os.path.exists(environment_path):
        raise ValueError('Environment does not exists! {0}'.format(environment_path))
    
    if sys.platform == 'win32':
        cmd = 'SETX {0} "{1}"'
    else:
        cmd = 'export {0}={1}'
    
    print("Setting: {0}".format('PYTHON_ENVIRONMENT'))
    cmd = cmd.format('PYTHON_ENVIRONMENT',
                     environment_path)
    os.system(cmd)
    
    if input('Overwrite sitecustomize.py? y/n:') == 'y':
        with open(os.path.join(sys.prefix, 'Lib', 'site-packages', 'sitecustomize.py'), 'w') as file_handle:
            file_handle.write(SITECUSTOMIZE)

if __name__ == '__main__':
    try:
        main(sys.argv)
    except:
        traceback.print_exc()
        input("Failed!")