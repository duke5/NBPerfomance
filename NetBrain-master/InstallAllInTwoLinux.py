# Create by Tony Che at 2020-02

# InstallAllInTwoLinux.py
# Feature description

import os
import subprocess
from NetBrainIE import NetBrainIE, PrintMessage
from NetBrainDB import NetBrainDB
from Utils.NetBrainUtils import NetBrainUtils, CurrentMethodName, CreateGuid

ConfigFile = r'.\conf\InstallAllInTwoLinux31200.conf'
installInfo31200 = {
    'webServer': '192.168.31.200',
    'linuxServer': '192.168.31.186',
    'linuxUser': 'root',
    'linuxPassword': 'Netbrain1',
    'localPath': r'\\192.168.33.101\US_Package\8.0.2\2020-02-11-1\DEV\ALL-LINUX\netbrain-all-in-two-linux-x86_64-rhel7-8.0.2.tar.gz',
    'remotePath': r'/opt/netbraintemp/02-11-1',
    'servicePassword': 'netbrain',
    'useSSL': True,
    'certPath': '/etc/ssl/cert.pem',
    'keyPath': '/etc/ssl/key.pem',
    'cacertPath': '/etc/ssl/cacert.pem'
}

def InstallAllInTwoLinux(application=None, configFile=''):
    configFile = ConfigFile if configFile == '' else configFile
    config = NetBrainUtils.GetConfig(configFile)
    if len(config) == 0:
        PrintMessage(''.join([CurrentMethodName(), 'Failed to load the configuration file: ', configFile]), 'Error')
        return False
    installInfo = config  # installInfo31200
    remoteServer = ''.join([installInfo['linuxUser'], '@', installInfo['linuxServer']])
    remotePath = installInfo['remotePath']
    if (remotePath[-1] == '/'):
        remotePath = remotePath[:-1]
    pwd = installInfo['linuxPassword']
    servicePassword = installInfo['servicePassword']
    src = installInfo['localPath']
    dest = ''.join([remoteServer, ':', remotePath])
    # ' ''
    cmd = ' '.join(
        ['plink -ssh', remoteServer, '-pw', pwd, '-no-antispoof', '"mkdir -p', remotePath, '" 2>/dev/nul \n'])
    # print(cmd)
    # create dest folder
    remoteShell = subprocess.Popen(cmd)

    cmd = ''.join(['pscp -scp -pw ', pwd, ' "', src, '" ', dest, '\n'])
    print('copy file, please wait ...')
    # copy install file from src to dest
    remoteShell = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                   universal_newlines=True, shell=False)
    remoteOutput = remoteShell.stdout.readlines()
    # remoteOutput = ['',]
    # print(*remoteOutput)
    lastLine = remoteOutput[-1]
    if (not lastLine.endswith('100%\n')):
        print('Error: ', lastLine)
    else:
        print(' '.join(['copy "', src, '" to "', dest, '" success.\n', lastLine]))
    # ' ''
    # open remote shell
    cmd = ' '.join(['plink -ssh', remoteServer, '-pw', pwd, '-no-antispoof\n'])
    # print(cmd)
    # plink -ssh root@192.168.31.186 -pw Netbrain1 -no-antispoof "ls -lt"
    remoteShell = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                   universal_newlines=True, shell=True)
    filename = os.path.basename(src)
    filenameStart = filename[0:5] + '\t'
    # print('filenameStart:', filenameStart)
    cmd = ' '.join(['cd', remotePath, '\ntar -zxvf', filename, '\n[[ -d bak ]] || mkdir bak\nmv', filename, './bak\ncd',
                    filenameStart, '\n'])
    # print(cmd)
    remoteShell.stdin.write(cmd)
    '''
    read EULA: yes
    license: i accept
    data path: enter
    log path: enter
    ip address: enter
    service name: enter
    password: netbrain
    pwd confirm: netbrain
    ssl: yes
    cert: certpath
    key: keypath
    ca: capath
    customized port: enter
    service monitor: https://.../
    continue: enter
    install: enter
    '''
    if (installInfo['useSSL']):
        input = ''.join([r'"yes\ni accept\n\n\n\n\n',servicePassword, '\n', servicePassword, '\nyes\n',
                         installInfo['certPath'], '\n', installInfo['keyPath'], '\n', installInfo['cacertPath'],
                         '\n\nhttps://', installInfo['webServer'], '/\n\n\n"'])
    else:
        input = ''.join(
            [r'"yes\ni accept\n\n\n\n\n', servicePassword, '\n', servicePassword, '\nno\n\nhttps://',
             installInfo['webServer'], '/\n\n\n"'])
    cmd = ' '.join(['printf', input, '> input\n'])
    # unzip install file
    remoteShell.stdin.write(cmd)
    # run install file and exit
    cmd = '\n'.join(['./install.sh < input\n', 'rm -rf input\n', 'logout\n'])
    print('installing, please wait till the installation complete.')
    # type user input
    remoteShell.stdin.write(cmd)
    # remoteShell.stdin.write('logout\n')
    # remoteShell.stdin.flush()
    remoteShell.stdin.close()

    # remoteShell.wait()
    remoteOutput = remoteShell.stdout.readlines()
    # remoteOutput = remoteShell.communicate()
    print(*remoteOutput)


if __name__ == "__main__":
    InstallAllInTwoLinux()

