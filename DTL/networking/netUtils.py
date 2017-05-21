import urllib.request, urllib.error, urllib.parse
from urllib.parse import urlsplit

from DTL.api import Path, apiUtils

def download_file(url, local_dir=None):
    url_file_name = Path(urlsplit(url)[2]).name
    if local_dir is None:
        local_dir = apiUtils.getTempDir()
    url_local_path = Path(local_dir).join(url_file_name)
    fullurl = urllib.parse.quote(url, safe="%/:=&?~#+!$,;'@()*[]")
    url_file_handle = urllib.request.urlopen(fullurl)
    print(url_local_path)
    with open(url_local_path,'wb') as file_handle :
        file_handle.write(url_file_handle.read())
    
    return url_local_path
    
if __name__ == '__main__':
    download_file('http://genlinux.ciaus.local/patchdata/SC_main/Installer/Star Citizen Install-SC_main.exe')