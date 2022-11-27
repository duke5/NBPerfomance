# Create by Tony Che at 2020-02

# NetBrainUtils.py
# Feature description

import configparser
import csv
import json
import inspect
#import logging
import os
import queue
import random, string
import re
import requests
import subprocess
import tempfile
import time
import uuid
import tarfile
import zipfile
import threading
from colorama import Fore, Back, Style
from datetime import datetime, timedelta
from time import localtime, gmtime, strftime, sleep

CreateGuid = lambda: str(uuid.uuid4())
CurrentMethodName = lambda: inspect.stack()[1][3]
PrintJsonObject = lambda jsonObject: NetBrainUtils.PrintMessage(json.dumps(jsonObject, indent=4, sort_keys=True))
requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)

DefaultHeaders = {
    "Content-Type": "application/x-www-form-urlencoded",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "Accept": "application/json, text/plain, */*",
    "User-Agent": "Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.132 Safari/537.36",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": '',
    "Origin": '',
    "Host": ''
}
HttpReturn = {
    'statusCode': -1,
    'resultCode': -1,
    'resultDescription': '',
    'data': []
}

class NetBrainUtils():
    def __init__(self):
        self.Descriptions = 'This is my utility api.'

    @staticmethod
    def PrintMessage(message, level='Info', logger=None):
        currenttime = strftime("%Y-%m-%d %H:%M:%S", localtime())  # localtime(),  gmtime(): UTC time
        if re.search('Error', level, re.IGNORECASE):
            output_message = ' '.join([currenttime, '[ERROR]', message])
            print(Fore.LIGHTYELLOW_EX + Back.RED, output_message + Style.RESET_ALL)
        elif re.search('Warning', level, re.IGNORECASE):
            output_message = ' '.join([currenttime, '[WARN]', message])
            print(Fore.LIGHTWHITE_EX + Back.YELLOW, output_message + Style.RESET_ALL)
        else:
            output_message = ' '.join([currenttime, '[INFO]', message])
            print(output_message)
        if logger is not None:
            logger.write(f'{output_message}\n')
            logger.flush()

    @staticmethod
    def GetConfig(configFile):
        if type(configFile) is str:
            with open(configFile, 'r') as config:
                config = json.load(config)
        else:
            config = configFile
        return config

    @staticmethod
    def isJson(objValue):
        try:
            if isinstance(objValue, dict):
                return True
            json.loads(objValue)
        except Exception as e:  # ValueError
            return False
        return True

    @staticmethod
    def GetDateTimeString(value=datetime.utcnow()):
        if type(value) is datetime:
            strDatetime = value.strftime(r'%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        else:
            dt = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
            strDatetime = dt.strftime(r'%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        return strDatetime

    @staticmethod
    def HttpGet(url, httpHeaders, httpVerify=False, httpAllowRedirects=False, httpTimeout=60):
        ret = HttpReturn.copy()
        try:
            httpResponse = requests.get(url, headers=httpHeaders, verify=httpVerify, allow_redirects=httpAllowRedirects, timeout=httpTimeout)
            statusCode = httpResponse.status_code
            ret['statusCode'] = statusCode

            if statusCode == 200:
                jsonResponse = httpResponse.json()
                ret['resultCode'] = jsonResponse.get('operationResult', {}).get('ResultCode', -1)
                ret['resultDescription'] = jsonResponse.get('operationResult', {}).get('ResultDesc', '')
                ret['data'] = jsonResponse.get('data', {})
            elif statusCode == 400:
                jsonResponse = httpResponse.json()
                ret['resultCode'] = jsonResponse.get('error', -1)
                ret['resultDescription'] = jsonResponse.get('error_description', '')
                ret['data'] = jsonResponse
            else:
                ret['data'] = httpResponse.text
        except json.JSONDecodeError:
            ret['resultCode'] = 0
            ret['resultDescription'] = httpResponse.text
        # except InvalidHeader:
        except Exception as e:
            ret['resultDescription'] = str(e)
            NetBrainUtils.PrintMessage(''.join([CurrentMethodName(), ' Exception: ', ret['resultDescription']]), 'Error')
        finally:
            return ret

    @staticmethod
    def HttpPut(url, httpHeaders, httpData, httpVerify=False, httpAllowRedirects=False, httpTimeout=60):
        ret = HttpReturn.copy()
        try:
            httpResponse = requests.put(url, headers=httpHeaders, data=json.dumps(httpData), verify=httpVerify, allow_redirects=httpAllowRedirects, timeout=httpTimeout)
            statusCode = httpResponse.status_code
            ret['statusCode'] = statusCode

            if statusCode == 200:
                jsonResponse = httpResponse.json()
                ret['resultCode'] = jsonResponse.get('operationResult', {}).get('ResultCode', -1)
                ret['resultDescription'] = jsonResponse.get('operationResult', {}).get('ResultDesc', '')
                ret['data'] = jsonResponse.get('data', {})
            elif statusCode == 400:
                jsonResponse = httpResponse.json()
                ret['resultCode'] = jsonResponse.get('error', -1)
                ret['resultDescription'] = jsonResponse.get('error_description', '')
                ret['data'] = jsonResponse
            else:
                ret['data'] = httpResponse.text
        except Exception as e:
            ret['resultDescription'] = str(e)
            NetBrainUtils.PrintMessage(''.join([CurrentMethodName(), ' Exception: ', str(e)]), 'Error')
        finally:
            return ret

    @staticmethod
    def HttpPost(url, httpHeaders, httpData, httpVerify=False, httpAllowRedirects=False, httpTimeout=60):
        ret = HttpReturn.copy()
        try:
            httpResponse = requests.post(url, headers=httpHeaders, data=json.dumps(httpData), verify=httpVerify, allow_redirects=httpAllowRedirects, timeout=httpTimeout)
            statusCode = httpResponse.status_code
            ret['statusCode'] = statusCode

            if statusCode == 200:
                jsonResponse = httpResponse.json()
                ret['resultCode'] = jsonResponse.get('operationResult', {}).get('ResultCode', -1)
                ret['resultDescription'] = jsonResponse.get('operationResult', {}).get('ResultDesc', '')
                ret['data'] = jsonResponse.get('data', {})
            elif statusCode == 400:
                jsonResponse = httpResponse.json()
                ret['resultCode'] = jsonResponse.get('error', -1)
                ret['resultDescription'] = jsonResponse.get('error_description', '')
                ret['data'] = jsonResponse
            else:
                ret['data'] = httpResponse.text
        except Exception as e:
            ret['resultDescription'] = str(e)
            NetBrainUtils.PrintMessage(''.join([CurrentMethodName(), ' Exception: ', str(e)]), 'Error')
        finally:
            return ret

    @staticmethod
    def HttpDelete(url, httpHeaders, httpData, httpVerify=False, httpAllowRedirects=False, httpTimeout=60):
        ret = HttpReturn.copy()
        try:
            httpResponse = requests.delete(url, headers=httpHeaders, data=json.dumps(httpData), verify=httpVerify, allow_redirects=httpAllowRedirects, timeout=httpTimeout)
            statusCode = httpResponse.status_code
            ret['statusCode'] = statusCode

            if statusCode == 200:
                jsonResponse = httpResponse.json()
                ret['resultCode'] = jsonResponse.get('operationResult', {}).get('ResultCode', -1)
                ret['resultDescription'] = jsonResponse.get('operationResult', {}).get('ResultDesc', '')
                ret['data'] = jsonResponse.get('data', {})
            elif statusCode == 400:
                jsonResponse = httpResponse.json()
                ret['resultCode'] = jsonResponse.get('error', -1)
                ret['resultDescription'] = jsonResponse.get('error_description', '')
                ret['data'] = jsonResponse
            else:
                ret['data'] = httpResponse.text
        except Exception as e:
            ret['resultDescription'] = str(e)
            NetBrainUtils.PrintMessage(''.join([CurrentMethodName(), ' Exception: ', str(e)]), 'Error')
        finally:
            return ret

    @staticmethod
    def GenerateRandomString(length):
        return ''.join(random.choice(string.letters) for i in range(length))

    @staticmethod
    def GetTenantAndDomainName(config):
        tenantName = config.get('Tenant Name', None)
        if tenantName is None:
            tenantName = config.get('DomainInfo', {}).get('Tenant Name', None)
        domainName = config.get('Domain Name', None)
        if domainName is None:
            domainName = config.get('DomainInfo', {}).get('Domain Name', None)
        return tenantName, domainName

    @staticmethod
    def GetLocalTime():
        return datetime.now()

    @staticmethod
    def GetUtcTime():
        return datetime.utcnow()

    @staticmethod
    def LocalTimeToUTCTime(localTime:datetime, offsetTimeZone:int=None):
        if offsetTimeZone is None:
            offsetTimeZone = datetime.now() - datetime.utcnow()
        else:
            offsetTimeZone = timedelta(hours=offsetTimeZone)
        utcTime = localTime - offsetTimeZone
        return utcTime

    @staticmethod
    def UTCTimeToLocalTime(utcTime, offsetTimeZone=None):
        if offsetTimeZone is None:
            offsetTimeZone = datetime.now() - datetime.utcnow()
        else:
            offsetTimeZone = timedelta(hours=offsetTimeZone)
        localTime = utcTime + offsetTimeZone
        return localTime

    @staticmethod
    def DateTimeToString(dt, format=0):
        if isinstance(dt, timedelta):
            return str(dt)
        if format == 1:
            dtString = dt.strftime(r'%Y-%m-%d %H:%M:%S.%f')
        elif format == 2:
            dtString = dt.strftime(r'%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        elif format == 3:
            dtString = dt.strftime(r'%Y%m%d_%H%M%S')
        elif format == 4:
            dtString = dt.strftime(r'%Y-%m-%d')
        elif format == 5:
            dtString = dt.strftime(r'%H:%M:%S')
        elif format == 6:
            dtString = dt.strftime(r'%Y-%m-%dT%H:%M:%SZ')
        else:
            dtString = dt.strftime(r'%Y-%m-%d %H:%M:%S')
        return dtString

    @staticmethod
    def StringToDateTime(dtString, format='%Y/%m/%d %H:%M:%S'):
        # datetime.strptime('01/01/20 01:01:01.123', '%d/%m/%y %H:%M:%S.%f')
        dt = datetime.strptime(dtString, format)
        return dt

    @staticmethod
    def DateAddDays(dt:datetime, days:int):
        result = dt + timedelta(days=days)
        return result

    @staticmethod
    def DatetimeAddHours(dt:datetime, hours:int):
        result = dt + timedelta(hours=hours)
        return result

    @staticmethod
    def DatetimeAddMinutes(dt:datetime, minutes:int):
        result = dt + timedelta(minutes=minutes)
        return result

    @staticmethod
    def DatetimeAddSeconds(dt:datetime, seconds:int):
        result = dt + timedelta(seconds=seconds)
        return result

    @staticmethod
    def GetDayOfWeek(day_of_week:int):
        day_of_weeks = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
        result = 'Sunday' if day_of_week >= 7 or day_of_week < 0 else day_of_weeks[day_of_week]
        return result

    @staticmethod
    def DictionaryToCSVFile(dictData, filename, header):
        with open(filename, 'w', newline='') as csvFile:
            writer = csv.DictWriter(csvFile, fieldnames=header)
            writer.writeheader()
            if type(dictData) is list:
                writer.writerows(row for row in dictData)
            else:
                writer.writerows(dictData)

    @staticmethod
    def CSVFileToDictionary(filename, header):
        dictData=[]
        with open(filename, 'r', newline='') as csvFile:
            reader = csv.DictReader(csvFile, fieldnames=header)
            dictData = [row for row in reader]
            del dictData[0]

        return dictData

    @staticmethod
    def JsonToFile(dictData, filename):
        with open(filename, 'w', newline='') as fp:
            #for row in dictData:
            json.dump(dictData, fp)

    @staticmethod
    def FileToJson(filename):
        dictData=[]
        with open(filename, 'r', newline='') as fp:
            dictData = json.load(fp)

        return dictData

    @staticmethod
    def LoadIniFile(filename):
        ini_config = configparser.ConfigParser(allow_no_value=True)
        ini_config.read(filename)
        for section in ini_config.sections():
            print(section)
            for name, value in ini_config.items(section):
                print('  %s = %r' % (name, value))
        return ini_config

    @staticmethod
    def SaveIniFile(filename, ini_config):
        with open(filename, 'w') as fp:
            ini_config.write(fp)
        return True

    @staticmethod
    def DeleteFile(filename):
        if os.path.exists(filename):
            os.remove(filename)

    @staticmethod
    def RunCommandOnLocalServer(command):
        print(command)
        with os.popen(command, 'r') as fp:
            result = fp.read().strip()
        return result

    @staticmethod
    def RunCommandOnRemoteServer(command, remote_server, username, password, operationSystem='Windows', userInput=[]):
        if operationSystem == 'Windows':
            if False and remote_server is not None:
                if not remote_server.startswith('\\'):
                    remote_server = '\\\\' + remote_server
                result = re.match('([a-zA-z]*)\s*(.*)', command, re.I).groups()
                if len(result) == 2:
                    cmd = ' '.join([result[0], remote_server, result[1]])
                else:
                    NetBrainUtils.PrintMessage(''.join(['Failed to parse the command: ', command]), 'Warning')
                    cmd = command
            else:
                cmd = command
            cmd = f'psexec \\\\{remote_server} -u {username} -p {password} -s -nobanner {command}'
        elif operationSystem == 'Linux':
            cmd = f'plink -ssh {username}@{remote_server} -pw {password} -no-antispoof "{command}"'
        #print(command)
        remote_shell = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                        stderr=subprocess.STDOUT, universal_newlines=True, shell=False)
        for input in userInput:
            remote_shell.stdin.write(input)
        remote_shell.stdin.close()
        remote_output = remote_shell.stdout.read()
        #sleep(3)
        return remote_output

    @staticmethod
    def ParseFilename(fullFileName):
        directory = os.path.dirname(fullFileName)
        basename = os.path.basename(fullFileName)
        filename = os.path.splitext(basename)
        fileInfo = {
            "FullFilename": fullFileName,
            "Directory": directory,
            "Filename": basename,
            "FilenameWithOutExtension": filename[0],
            "ExtensionName": filename[1]
        }
        return fileInfo

    @staticmethod
    def CopyFileToLinuxServer(remoteServer, username, password, srcFile, destFile, unzip=True, outputQueue=None):
        logContents = list()
        fileInfo = NetBrainUtils.ParseFilename(destFile)
        command = ''.join(['mkdir -p ', fileInfo['Directory'], ' 2>/dev/nul \n'])
        #print(command) if outputQueue is None else logContents.append(command)
        NetBrainUtils.RunCommandOnRemoteServer(command, remoteServer, username, password, 'Linux')
        command = ''.join(['echo y | pscp -scp -pw ', password, ' "', srcFile, '" "', username, '@', remoteServer,
                          ':', destFile, '"\n'])
        #print(command) if outputQueue is None else logContents.append(command)
        logContent = ''.join(['copy file "', srcFile, '" to "', remoteServer, ':', destFile, '", please wait ...'])
        print(logContent)
        with os.popen(command, 'r') as fp:
            result = fp.readlines()
            if len(result) > 1:
                result = result[-1]
        print(result, '\tCopy complete.') if outputQueue is None else logContents.append(result)
        if unzip and fileInfo['ExtensionName'].lower() == '.gz':
            logContent = 'unzip: ' + fileInfo['FullFilename'] + '\n'
            print(logContent) if outputQueue is None else logContents.append(logContent)
            command = ''.join(['cd ', fileInfo['Directory'], '; tar -zxvf ', fileInfo['Filename']])
            NetBrainUtils.RunCommandOnRemoteServer(command, remoteServer, username, password, 'Linux')
        if outputQueue is not None:
            outputQueue.put({'logLevel': 'Info', 'message': '\n'.join(line for line in logContents)})
        return True if result.endswith('100%\n') else False

    @staticmethod
    def CopyFileToWindowsServer(remoteServer, username, password, srcFile, destFile, unzip=True, outputQueue=None):
        logContents = list()
        if destFile[1] != ':' and destFile[1] != '$':
            logContent = ''.join(['Unknown destination folder: ', destFile])
            print(logContent) if outputQueue is None else outputQueue.put({'logLevel': 'Error', 'message': logContent})
            return False
        destDrive = ''.join(['\\\\', remoteServer, '\\', destFile[0], '$'])
        tempFilename = ''.join(['\\\\', remoteServer, '\\', destFile]).replace(':', '$')
        fileInfo = NetBrainUtils.ParseFilename(tempFilename)
        command = ''.join(['NET USE ', destDrive, ' /USER:', username, ' ', password, ' & ',
                           'MKDIR "', fileInfo['Directory'], '" & COPY /Y "', srcFile, '" "', tempFilename, '"'])
        #print(command) if outputQueue is None else logContents.append(command)
        logContent = ''.join(['copy file "', srcFile, '" to "', tempFilename, '", please wait ...'])
        print(logContent)
        with os.popen(command, 'r') as fp:
            result = fp.read().strip()
        #print(result) if outputQueue is None else logContents.append(result)
        print('Windows file copy completed.')
        if unzip and fileInfo['ExtensionName'].lower() == '.zip':
            print(logContent)
            logContent = 'unzip: ' + tempFilename + '\n'
            print(logContent) if outputQueue is None else logContents.append(logContent)
            NetBrainUtils.UnzipFile(tempFilename, fileInfo['Directory'])
        #os.remove(tempFilename) if os.path.exists(tempFilename) else None
        #print('unzip completed.')
        command = ''.join(['NET USE ', destDrive, ' DELETE'])
        with os.popen(command, 'r') as fp:
            fp.read().strip()
        if len(logContents):
            outputQueue.put({'logLevel': 'Info', 'message': '\n'.join(line for line in logContents)})
        result = re.search('[\w\W]*?( file\(s\) copied).*', result, re.I)
        return False if result is None else True

    @staticmethod
    def UnzipFile(zipFilename, targetFolder=None):
        fileInfo = NetBrainUtils.ParseFilename(zipFilename)
        if targetFolder is None:
            targetFolder = fileInfo['Directory']
        if fileInfo['ExtensionName'].lower() == '.zip':
            with zipfile.ZipFile(zipFilename, 'r') as fpZip:
                fpZip.extractall(targetFolder)
        elif fileInfo['ExtensionName'].lower() == '.gz':
            with tarfile.open(zipFilename) as fpZip:
                def is_within_directory(directory, target):
                    
                    abs_directory = os.path.abspath(directory)
                    abs_target = os.path.abspath(target)
                
                    prefix = os.path.commonprefix([abs_directory, abs_target])
                    
                    return prefix == abs_directory
                
                def safe_extract(tar, path=".", members=None, *, numeric_owner=False):
                
                    for member in tar.getmembers():
                        member_path = os.path.join(path, member.name)
                        if not is_within_directory(path, member_path):
                            raise Exception("Attempted Path Traversal in Tar File")
                
                    tar.extractall(path, members, numeric_owner=numeric_owner) 
                    
                
                safe_extract(fpZip, targetFolder)

    @staticmethod
    def PrettyHumanSize(size, kb=1024, reserve=2):
        i = 0
        unit = {0 : 'B', 1: 'KB', 2: 'MB', 3: 'GB', 4: 'TB'}
        while size > kb:
            size /= kb
            i += 1
        format = ''.join(['{:.', str(reserve), 'f}'])
        size = float(format.format(size))
        return ''.join([str(size), ' ', unit[i]])

    @staticmethod
    def ReadFileFromRemoteServer(remote_server, username, password, fileFullPath, operationSystem='Windows'):
        contents = ''
        if operationSystem == 'Windows':
            uncPath = ''.join(['\\\\', remote_server, '\\', fileFullPath]).replace(':', '$')
            shareFolder = ''.join(['\\\\', remote_server, '\\', fileFullPath[0], '$'])  # '\\192.168.31.200'\c$
            command = ''.join(['NET USE ', shareFolder, ' /USER:', username, ' ', password,
                               ' & NET USE ', shareFolder, ' DELETE'])
            with os.popen(command, 'r') as fp:
                fp.read().strip()
            f = open(uncPath, "r+")
            contents = f.readlines()
        elif operationSystem == 'Linux':
            command = f'plink -ssh {username}@{remote_server} -pw {password} -no-antispoof "cat {fileFullPath}"'
            #print(command)
            remote_shell = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                            stderr=subprocess.STDOUT, universal_newlines=True, shell=False)
            remote_shell.stdin.close()
            contents = remote_shell.stdout.read()
            #sleep(3)
        return contents

    @staticmethod
    def ReplaceSpecialCharacters(text, special_chars=['\\\\','/',':','*','?','"','<','>','\|','.',' ','$','”'], replaced_char='_'):
        # SpecialCharacters：\ / : * ? ” < > | . $
        regex_str = '|'.join(special_chars)
        content = re.sub(f'[{regex_str}]', replaced_char, text)
        return content


class ProducerThread(threading.Thread):
    def __init__(self, queue=None, name=None, worker_func={'function': None, 'parameter': None}):
        super(ProducerThread, self).__init__()
        self.name = 'Producer Thread' if name is None else name
        self.task_queue = queue if queue == None else queue.Queue()
        self.output_message_queue = queue.Queue()
        self.worker_func = worker_func['function']
        self.worker_func_param = worker_func['parameter']

    def run(self):
        return self.worker_func(self.worker_func_param)


class ConsumerThread(threading.Thread):
    def __init__(self, queue, name=None, worker_func={'func': None, 'param': None}):
        super(ConsumerThread, self).__init__()
        self.name = 'Consumer Thread' if name is None else name
        self.task_queue = queue
        self.output_message_queue = queue.Queue()
        self.worker_func = worker_func['function']
        self.worker_func_param = worker_func['parameter']

    def __del__(self):
        # Destructor called
        pass

    # To use the with statement, create a class with the following two methods:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        pass

    def run(self):
        # while True:
        #     if not self.task_queue.empty():
        #         item = self.task_queue.get()
        #         self.task_queue.task_done()
        #         time.sleep(random.random())
        return self.worker_func(self.worker_func_param)
