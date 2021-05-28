import requests
import rsa
import logging
from random import randint
import re
import json
import uuid
import base64
import csv
import threading
import time
import os
import struct
import urllib
from time import localtime, gmtime, strftime, sleep
from datetime import datetime, timedelta
from colorama import Fore, Back, Style
import inspect
from Utils.NetBrainUtils import NetBrainUtils

requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)
CurrentMethodName = lambda: inspect.stack()[1][3]
# CurrentMethodName = sys._getframe().f_code.co_name
PrintJsonObject = lambda jsonObject: PrintMessage(json.dumps(jsonObject, indent=4, sort_keys=True))
CreateGuid = lambda: str(uuid.uuid4())
HTTP_TIMEOUT = 3600

HttpReturn = {
    'statusCode': -1,
    'resultCode': -1,
    'resultDescription': '',
    'data': []
}
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
DefaultFscInfo = {
    'uniqueName': 'FSC',
    'ipOrHostname': '',
    'port': '9095',
    'userName': 'admin',
    'password': '',
    'timeout': 5,
    'desc': ''
}
DefaultFSCDetailInfo = {
    'id': '',
    'deployMode': 1,  # 1: Standalone, 2:Group
    'groupName': 'FSC',
    'fscInfo': [
        DefaultFscInfo.copy()
    ],
    'useSSL': False,
    'conductCertAuthVerify': False,
    'certificateType': 2,
    'certificate': '',
    'certificateName': '',
    'tenants': []
}
# in V8.02, 0: Public; 1: My Device Groups; 2: System; 3: Media; 4: Policy Device Group
DeviceGroupType = ('Public', 'My Device Groups', 'System', 'Media', 'Policy Device Group')
DiscoverAccessOrder = (
    '', 'SNMP and Telnet', 'SNMP and SSH', 'SNMP and Telnet/SSH', 'SNMP and SSH/Telnet', 'SNMP Only')

def PrintMessage(message, level='Info'):
    currenttime = localtime()  # gmtime(): UTC time
    if re.search('Error', level, re.IGNORECASE):
        print(Fore.LIGHTYELLOW_EX + Back.RED, strftime("%Y-%m-%d %H:%M:%S", currenttime), message + Style.RESET_ALL)
    elif re.search('Warning', level, re.IGNORECASE):
        print(Fore.LIGHTWHITE_EX + Back.YELLOW, strftime("%Y-%m-%d %H:%M:%S", currenttime), message + Style.RESET_ALL)
    else:
        print(strftime("%Y-%m-%d %H:%M:%S", currenttime), message)

def isJson(objValue):
    try:
        if isinstance(objValue, dict):
            return True
        json.loads(objValue)
    except Exception as e:  # ValueError
        return False
    return True

def GetDateTimeString(value=datetime.utcnow()):
    if type(value) is datetime:
        strDatetime = value.strftime(r'%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
    else:
        dt = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
        strDatetime = dt.strftime(r'%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
    return strDatetime

def HttpGet(url, httpHeaders, httpVerify=False, httpAllowRedirects=False, httpTimeout=3600):
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
        PrintMessage(''.join([CurrentMethodName(), ' Exception: ', ret['resultDescription']]), 'Error')
    finally:
        return ret

def HttpPut(url, httpHeaders, httpData, httpVerify=False, httpAllowRedirects=False, httpTimeout=3600):
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
        PrintMessage(''.join([CurrentMethodName(), ' Exception: ', str(e)]), 'Error')
    finally:
        return ret

def HttpPost(url, httpHeaders, httpData, httpVerify=False, httpAllowRedirects=False, httpTimeout=3600):
    ret = HttpReturn.copy()
    try:
        httpResponse = requests.post(url, headers=httpHeaders, data=json.dumps(httpData), verify=httpVerify,
                                     allow_redirects=httpAllowRedirects, timeout=httpTimeout)
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
        PrintMessage(''.join([CurrentMethodName(), ' Exception: ', str(e)]), 'Error')
    finally:
        return ret

def HttpPatch(url, httpHeaders, httpData, httpVerify=False, httpAllowRedirects=False, httpTimeout=3600):
    ret = HttpReturn.copy()
    try:
        httpResponse = requests.patch(url, headers=httpHeaders, data=json.dumps(httpData), verify=httpVerify,
                                     allow_redirects=httpAllowRedirects, timeout=httpTimeout)
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
        PrintMessage(''.join([CurrentMethodName(), ' Exception: ', str(e)]), 'Error')
    finally:
        return ret

def HttpDelete(url, httpHeaders, httpData, httpVerify=False, httpAllowRedirects=False, httpTimeout=3600):
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
        PrintMessage(''.join([CurrentMethodName(), ' Exception: ', str(e)]), 'Error')
    finally:
        return ret

class NetBrainIE():
    def __init__(self, url, username='admin', password='Netbrain1!', tenantName='Initial Tenant', domainName='',
                 scope='mainUI'):
        if(url.endswith('/')):
            self.Url = url
        else:
            self.Url = url + '/'
        findIt = re.match("(\w*)\W*([\w\.]*).*", self.Url)
        if (findIt):
            # print(findIt.group(0), findIt.group(1), findIt.group(2))
            referer = ''.join([findIt[1], '://', findIt[2]])
            host = findIt[2]
        else:
            referer = ''
            host = ''

        self.Username = username
        self.Password = password
        self.TenantName = tenantName
        self.DomainName = domainName
        self.Scope = scope
        self.Headers = DefaultHeaders.copy()
        self.Headers['Referer'] = referer
        self.Headers['Origin'] = referer
        self.Headers['Host'] = host
        self.Payload = {
            "grant_type": "password",
            "client_id": "ngAuthApp",
            "scope": scope,
            "username": username,
            "password": '',
            "login_type": "kick_login"
        }
        self.AccessToken = ''
        self.AccessTokenType = ''
        self.AccessScope = ''
        self.TenantID = ''
        self.DomainID = ''
        self.UserID = ''
        self.DefaultFscInfo = DefaultFscInfo.copy()
        self.DefaultFSCDetailInfo = DefaultFSCDetailInfo.copy()
        self.FreeNodeSize = 1000
        self.Logined = False
        self.SiteLocked = False
        self.Logger = None
        self.CurrentVersion = self.GetVersion()
        '''
        # Create and configure logger
        logging.basicConfig(filename="NetBrainIE.log",
                            format='%(asctime)s %(message)s',
                            filemode='w')
        # Creating an object
        self.Logger = logging.getLogger()
        # Setting the threshold of logger to DEBUG
        self.Logger.setLevel(logging.DEBUG)
        '''

    def __del__(self):
        if self.Logined:
            self.Logout()
        if self.Logger is not None:
            self.Logger.close()

    def _getUrl(self, functionName, serviceUrl, referer='', tenantID='', domainID=''):
        url = self.Url + serviceUrl
        headers = self.Headers.copy()
        if referer != '':
            headers['Referer'] = headers['Origin'] + referer
        if tenantID == '':
            headers['TenantGuid'] = self.TenantID
        else:
            headers['TenantGuid'] = tenantID
        if domainID == '':
            headers['DomainGuid'] = self.DomainID
        else:
            headers['DomainGuid'] = domainID
        httpReponse = HttpGet(url, headers)
        if httpReponse['statusCode'] != 200:
            PrintMessage(''.join([functionName, ' failed: ', json.dumps(httpReponse)]), 'Error')
            return {}
        # print(json.dumps(httpReponse, indent=4, sort_keys=True))
        resultCode = httpReponse.get('resultCode', -1)
        if resultCode != 0:
            PrintMessage(''.join([functionName, ' failed. ', httpReponse['resultDescription']]), 'Error')
            return {}
        info = httpReponse.get('data', [])
        # PrintJsonObject(info)

        return info

    def _putUrl(self, functionName, serviceUrl, payload, referer='', tenantID='', domainID=''):
        url = self.Url + serviceUrl
        headers = self.Headers.copy()
        if referer != '':
            headers['Referer'] = headers['Origin'] + referer
        if tenantID == '':
            headers['TenantGuid'] = self.TenantID
        else:
            headers['TenantGuid'] = tenantID
        if domainID == '':
            headers['DomainGuid'] = self.DomainID
        else:
            headers['DomainGuid'] = domainID
        httpReponse = HttpPut(url, headers, payload)
        if httpReponse['statusCode'] != 200:
            PrintMessage(''.join([functionName, ' failed: ', json.dumps(httpReponse)]), 'Error')
            return {}
        # print(json.dumps(httpReponse, indent=4, sort_keys=True))
        resultCode = httpReponse.get('resultCode', -1)
        if resultCode != 0:
            PrintMessage(''.join([functionName, ' failed. ', httpReponse['resultDescription']]), 'Error')
            return {}
        info = httpReponse.get('data', [])
        # PrintJsonObject(info)

        return info

    def _postUrl(self, functionName, serviceUrl, payload, referer='', tenantID='', domainID=''):
        url = self.Url + serviceUrl
        headers = self.Headers.copy()
        if referer != '':
            headers['Referer'] = headers['Origin'] + referer
        if tenantID == '':
            headers['TenantGuid'] = self.TenantID
        else:
            headers['TenantGuid'] = tenantID
        if domainID == '':
            headers['DomainGuid'] = self.DomainID
        else:
            headers['DomainGuid'] = domainID
        httpReponse = HttpPost(url, headers, payload)
        # print(json.dumps(httpReponse, indent=4, sort_keys=True))
        resultCode = httpReponse['statusCode']
        if resultCode != 200:
            PrintMessage(''.join([functionName, ' failed (', str(resultCode), '): ', json.dumps(httpReponse)]), 'Error')
            return {}
        resultCode = httpReponse.get('resultCode', -1)
        if resultCode == 500 and httpReponse['resultDescription'].endswith('already activated.'):
            #license activate
            httpReponse['resultCode'] = 0
            info = {'status' : True}
        elif resultCode != 0:
            PrintMessage(''.join([functionName, ' failed (', str(resultCode), '): ', httpReponse['resultDescription']]), 'Error')
            return {}
        else:
            info = httpReponse.get('data', [])
        # PrintJsonObject(info)
        if type(info) is bool or type(info) is int:
            ret = True
        else:
            ret = True if len(info) else False
        if ret:
            resultCode = httpReponse.get('resultCode', -1)
            if resultCode != 0:
                PrintMessage(''.join([functionName, ' failed (', str(resultCode), '): ', httpReponse['resultDescription']]), 'Error')
                return {}

        return info

    def _postUrlUpload(self, functionName, serviceUrl, files, referer='', tenantID='', domainID='', payload=''):
        url = self.Url + serviceUrl
        headers = self.Headers.copy()
        #headers['Content-Type'] = 'multipart/form-data' #'multipart/form-data'  # 'application/octet-stream'
        #headers['Content-Length'] = '%d' % os.path.getsize(files['FilePath'])
        if referer != '':
            headers['Referer'] = headers['Origin'] + referer
        if tenantID == '':
            headers['TenantGuid'] = self.TenantID
        else:
            headers['TenantGuid'] = tenantID
        if domainID == '':
            headers['DomainGuid'] = self.DomainID
        else:
            headers['DomainGuid'] = domainID
        headers.pop('Content-Type', None)
        headers.pop('Cookie', None)
        headers.pop('Sec-Fetch-Mode', None)
        headers.pop('Sec-Fetch-Site', None)

        if payload == '':
            httpResponse = requests.post(url, headers=headers, files=files, verify=False)
        else:
            httpResponse = requests.post(url, headers=headers, data=payload, files=files, verify=False)
        theRequest = httpResponse.request
        statusCode = httpResponse.status_code
        ret = HttpReturn.copy()
        ret['statusCode'] = statusCode
        if (statusCode == 200):
            jsonResponse = httpResponse.json()
            resultCode = jsonResponse.get('operationResult', {}).get('ResultCode', None)
            if resultCode is None:
                ret['resultCode'] = 0
                ret['resultDescription'] = ''
                ret['data'] = jsonResponse
            else:
                ret['resultCode'] = resultCode
                ret['resultDescription'] = jsonResponse.get('operationResult', {}).get('ResultDesc', '')
                ret['data'] = jsonResponse.get('data', [])
        elif (statusCode == 400):
            jsonResponse = httpResponse.json()
            ret['resultCode'] = jsonResponse.get('error', -1)
            ret['resultDescription'] = jsonResponse.get('error_description', '')
            ret['data'] = jsonResponse
        else:
            ret['data'] = httpResponse.text
        resultCode =ret['resultCode']
        if resultCode != 0:
            PrintMessage(''.join([functionName, ' failed (', str(resultCode), '): ', ret['resultDescription']]),
                         'Error')
            return {}
        info = ret.get('data', [])

        return info

    def _deleteUrl(self, functionName, serviceUrl, payload, referer='', tenantID='', domainID=''):
        url = self.Url + serviceUrl
        headers = self.Headers.copy()
        if referer != '':
            headers['Referer'] = headers['Origin'] + referer
        if tenantID == '':
            headers['TenantGuid'] = self.TenantID
        else:
            headers['TenantGuid'] = tenantID
        if domainID == '':
            headers['DomainGuid'] = self.DomainID
        else:
            headers['DomainGuid'] = domainID
        httpReponse = HttpDelete(url, headers, payload)
        resultCode = httpReponse['statusCode']
        if resultCode != 200:
            PrintMessage(''.join([functionName, ' failed (', str(resultCode), '): ', json.dumps(httpReponse)]), 'Error')
            return {}
        # print(json.dumps(httpReponse, indent=4, sort_keys=True))
        resultCode = httpReponse.get('resultCode', -1)
        if resultCode != 0:
            PrintMessage(''.join([functionName, ' failed (', str(resultCode), '): ', httpReponse['resultDescription']]), 'Error')
            return {}
        info = httpReponse.get('data', [])
        # PrintJsonObject(info)

        return info

    def _patchUrl(self, functionName, serviceUrl, payload, referer='', tenantID='', domainID=''):
        url = self.Url + serviceUrl
        headers = self.Headers.copy()
        if referer != '':
            headers['Referer'] = headers['Origin'] + referer
        if tenantID == '':
            headers['TenantGuid'] = self.TenantID
        else:
            headers['TenantGuid'] = tenantID
        if domainID == '':
            headers['DomainGuid'] = self.DomainID
        else:
            headers['DomainGuid'] = domainID
        httpReponse = HttpPatch(url, headers, payload)
        # print(json.dumps(httpReponse, indent=4, sort_keys=True))
        resultCode = httpReponse['statusCode']
        if resultCode != 200:
            PrintMessage(''.join([functionName, ' failed (', str(resultCode), '): ', json.dumps(httpReponse)]), 'Error')
            return {}
        resultCode = httpReponse.get('resultCode', -1)
        if resultCode == 500 and httpReponse['resultDescription'].endswith('already activated.'):
            #license activate
            httpReponse['resultCode'] = 0
            info = {'status' : True}
        elif resultCode != 0:
            PrintMessage(''.join([functionName, ' failed (', str(resultCode), '): ', httpReponse['resultDescription']]), 'Error')
            return {}
        else:
            info = httpReponse.get('data', [])
        # PrintJsonObject(info)
        if type(info) is bool or type(info) is int:
            ret = True
        else:
            ret = True if len(info) else False
        if ret:
            resultCode = httpReponse.get('resultCode', -1)
            if resultCode != 0:
                PrintMessage(''.join([functionName, ' failed (', str(resultCode), '): ', httpReponse['resultDescription']]), 'Error')
                return {}

        return info

    def _getJsonObject(self, jsonItems, key, value, ignoreCase=True):
        # return json object that key equal value
        if ignoreCase:
            reIngoreCase = re.IGNORECASE
        else:
            reIngoreCase = 0
        for item in jsonItems:
            currentValue = item.get(key, '')
            if type(value) is not str:
                value = str(value)
            if type(currentValue) is not str:
                currentValue = str(currentValue)
            #PrintMessage(''.join(['name=', key, ', current value=', currentValue, ', new value=', value]))
            if(re.fullmatch(value, currentValue, reIngoreCase)):
                return item
        return {}

    def set_logger(self, log_filename:str, over_written=False):
        if over_written:
            self.Logger = open(log_filename, 'w+')
        else:
            self.Logger = open(log_filename, 'a+')
        return True

    def PrintMessage(self, message, level='Info'):
        NetBrainUtils.PrintMessage(message, level, self.Logger)
        return True

    def SetScope(self, scope):
        # Set scope: system, mainUI
        self.Scope = scope

    def SetVersion(self, version : float):
        # Set current version
        self.CurrentVersion = version

    def GetVersion(self):
        url = self.Url + r'ServicesAPI/conf/fix_releaseinfo.txt'
        info = requests.get(url, headers=self.Headers, verify=False, allow_redirects=False, timeout=HTTP_TIMEOUT)
        if info.status_code == 200:
            self.version_info = info.json()
        else:
            self.version_info = {}
        version = self.version_info.get('ProductVersion', '8.0')
        if version == '10.0a':
            version = 10.001
        return float(version)

    def PasswordEncrypt(self, plainPassword=''):
        # Encrypt password
        if plainPassword == '':
            pwd = self.Password.encode()
        else:
            pwd = plainPassword.encode()
        serviceUrl = r"ServicesAPI/admin/getPublicKey"
        #original_pass = requests.post(self.Url + serviceUrl, verify=False)
        info = self._postUrl(CurrentMethodName(), serviceUrl, {})
        if len(info):
            modules = int(info[1], 16)
            exponent = int(info[0], 16)
            encrypt_key = rsa.PublicKey(modules, exponent)
            pwd = rsa.encrypt(pwd, encrypt_key)
            #encapPasswd = ''.join(["%02X" % x for x in pwd]).strip()
            encryptPassword = pwd.hex()
            #print(encryptPassword)
            return encryptPassword

        return ''

    def PasswordDecrypt(self, encryptPassword):
        # Decrypt password
        return False
        serviceUrl = r"ServicesAPI/admin/getPublicKey"
        info = self._postUrl(CurrentMethodName(), serviceUrl, {})
        if len(info):
            modules = int(info[1], 16)
            exponent = int(info[0], 16)
            private_key = ''   # rsa.PrivateKey(modules, exponent, d, p, q)
            pwd = encryptPassword.decode()
            plainPassword = rsa.decrypt(pwd, private_key)
            #plainPassword = pwd.hex()
            # print(plainPassword)
            return plainPassword

        return ''

    def GenerateAccessToken(self, username, password, loginType='normal_login'):
        # Log into system and generate access token
        encryptPassword = self.PasswordEncrypt(password)
        if encryptPassword == '':
            PrintMessage('GenerateAccessToken failed', 'Error')
            return False

        serviceUrl = r'ServicesAPI/GenerateAccessToken'
        url = self.Url + serviceUrl
        headers = self.Headers.copy()
        headers['Referer'] += '/admin.html'
        payload = {
            'grant_type': 'password',
            'username': username,
            'password': encryptPassword,
            'client_id': 'ngAuthApp',
            'scope': self.Scope,
            "login_type": loginType
        }
        if loginType == '':
            payload.pop('login_type', None)
        #payload['scope'] = 'system'

        html = requests.post(url, headers=headers, data=payload, verify=False, allow_redirects=False, timeout=60)
        #PrintMessage(html.text)
        if (html.status_code == 400):
            result = html.json()
            # PrintJsonObject(result)
            errorCode = result.get('error', '')
            if (errorCode == '100075'):
                userID = result.get('error_description', '').split(',')
                if (len(userID) > 1):
                    self.UserID = userID[1]
                    self.Headers['Content-Type'] = r'application/json;charset=UTF-8'
                    PrintMessage('GenerateAccessToken passed.')
                    return True
            elif (errorCode == '100071'):
                PrintMessage(''.join([CurrentMethodName(), ': ', result['error_description']]), 'Warning')
                return self.GenerateAccessToken(username, password, 'kick_login')
            PrintMessage(''.join([CurrentMethodName(), ' failed.\n', json.dumps(result)]), 'Error')
            return False
        elif(html.status_code == 200):
            result = html.json()
            # print(json.dumps(result, indent=4, sort_keys=True))
            # print(html.cookies)
            #self.Logger.info(result)
            self.AccessToken = result['access_token']
            self.AccessTokenType = result['token_type']
            self.AccessScope = result['scope']
            self.UserID = result['userId']
            self.Username = username

            if (self.AccessToken != None):
                self.Headers['Authorization'] = result['token_type'] + ' ' + result['access_token']
                self.Headers['Content-Type'] = r'application/json;charset=UTF-8'
                self.Headers['Cookie'] = ''.join([r'system_signalrHubClientId=system_', CreateGuid(),
                                                  r'; mainUI_signalrHubClientId=mainUI_', CreateGuid()])
                #self.Headers['Accept'] = r'*/*'
                self.Headers['Accept'] = 'application/json, text/plain, */*'
                if(self.Scope == 'system'):
                    self.Headers['Referer'] += '/admin.html'
                else:
                    self.Headers['Referer'] += '/desktop.html'

                PrintMessage('GenerateAccessToken passed')
                return True
            else:
                PrintMessage(''.join([CurrentMethodName(), ' failed.\n', json.dumps(result)]), 'Error')
                return False
        else:
            PrintMessage(''.join([CurrentMethodName(), ' failed.\n', html.text]), 'Error')
            return False

    def _login(self, username, password, clientAppID='IE', strategies=['KickOtherSession']):
        # Log into system and generate access token
        encryptPassword = self.PasswordEncrypt(password)
        if encryptPassword == '':
            PrintMessage(''.join([CurrentMethodName(), ' failed.'], 'Error'))
            return False

        serviceUrl = r'ServicesAPI/auth/login'
        url = self.Url + serviceUrl
        headers = self.Headers.copy()
        headers['Referer'] += '/admin.html'
        payload = {
            'clientAppId': clientAppID,
            'principal': username,
            'credential': encryptPassword,
            "strategies": strategies
        }
        if strategies is None or len(strategies) <= 0:
            payload.pop('strategies')

        html = requests.post(url, headers=headers, data=payload, verify=False, allow_redirects=False, timeout=3000)
        # PrintMessage(html.text)
        if (html.status_code == 400):
            result = html.json()
            # PrintJsonObject(result)
            errorCode = result.get('operationResult', {}).get('ResultCode', '')
            if (errorCode == 100000111100075):
                userID = result.get('operationResult', {}).get('ResultDesc', '').split(',')
                if (len(userID) > 1):
                    self.UserID = userID[1]
                    self.AccessTokenType = 'Bearer'
                    self.AccessToken = result.get('data', {}).get('accessToken', '')
                    self.Headers['Content-Type'] = r'application/json;charset=UTF-8'
                    self.Headers['Authorization'] = ' '.join([self.AccessTokenType, self.AccessToken])
                    #PrintMessage('GenerateAccessToken passed.')
                    return True
            elif (errorCode == '100071'):
                PrintMessage(''.join([CurrentMethodName(), ': ', result['error_description']]), 'Warning')
                return self.GenerateAccessToken(username, password, 'kick_login')
            PrintMessage(''.join([CurrentMethodName(), ' failed.\n', json.dumps(result)]), 'Error')
            return False
        elif (html.status_code == 200):
            result = html.json()
            # print(json.dumps(result, indent=4, sort_keys=True))
            # print(html.cookies)
            # self.Logger.info(result)
            self.AccessToken = result['data']['accessToken']
            self.AccessTokenType = 'Bearer'
            self.AccessScope = None
            self.Username = username

            if (self.AccessToken != None):
                self.Headers['Authorization'] = ' '.join([self.AccessTokenType, self.AccessToken])
                self.Headers['Content-Type'] = r'application/json;charset=UTF-8'
                self.Headers['Cookie'] = ''.join([r'system_signalrHubClientId=system_', CreateGuid(),
                                                  r'; mainUI_signalrHubClientId=mainUI_', CreateGuid()])
                # self.Headers['Accept'] = r'*/*'
                self.Headers['Accept'] = 'application/json, text/plain, */*'
                if (self.Scope == 'system'):
                    self.Headers['Referer'] += '/admin.html'
                else:
                    self.Headers['Referer'] += '/desktop.html'
                self.UserID = self._getUserAdditionalInfo()['userId']  # result['userId']  # GetUserAdditionalInfo

                PrintMessage(''.join([CurrentMethodName(), '  passed']))
                return True
            else:
                PrintMessage(''.join([CurrentMethodName(), ' failed.\n', json.dumps(result)]), 'Error')
                return False
        else:
            PrintMessage(''.join([CurrentMethodName(), ' failed.\n', html.text]), 'Error')
            return False

    def Login(self, username=None, password=None, clientAppID='IE'):
        # Log into system and apply tenant/domain
        if username is not None:
            self.Username = username
        if password is not None:
            self.Password = password
        if self.CurrentVersion >= 8.03:
            login = self._login(self.Username, self.Password, clientAppID)
        else:
            login = self.GenerateAccessToken(self.Username, self.Password)
        if login:
            PrintMessage('Login passed')
            if len(self.TenantName) and len(self.DomainName):
                self.ApplyTenantAndDomain(self.TenantName, self.DomainName)
        else:
            PrintMessage('Login failed', 'Error')
        self.Logined = login
        return login

    def Logout(self):
        # Logout system
        serviceUrl = r"ServicesAPI/Session/Logout"
        url = self.Url + serviceUrl
        headers = self.Headers.copy()
        headers['Accept'] = 'application/json, text/plain, */*'
        headers.pop('TenantGuid', None)
        headers.pop('DomainGuid', None)
        if self.Scope == 'system':
            payload = {'scope': 'system'}
        else:
            payload = {'scope': 'mainUI'}
        html = requests.post(url, headers=headers, data=json.dumps(payload), verify=False)
        result = html.json()
        #self.Logger.info(result)
        if self.SiteLocked:
            self._unlockSite()
            self.SiteLocked = False

        if(result['data'] == True):
            self.Logined = False
            PrintMessage('Logout passed.')
            return True
        else:
            PrintMessage('Logout failed', 'Error')
            return False

    def GetTenantDomainID(self, tenantName, domainName=''):
        # Get Tanant and Domain ID
        if self.CurrentVersion <= 8.01:
            serviceUrl = r'ServicesAPI/Admin/User/GetUserInfo/mainUI/' + self.UserID   # 8.01
        # elif self.CurrentVersion in ['8.02', '8.03', '8.1']:
        else:
            serviceUrl = r'ServicesAPI/Admin/User/GetUserInfo/system'  # 8.02 and later
        info = self._getUrl(CurrentMethodName(), serviceUrl)
        if len(info) == 0:
            return '', ''

        tenants = info['tenant']
        #print(json.dumps(tenants, indent=4, sort_keys=True))
        tenant = self._getJsonObject(tenants, 'name', tenantName)
        domain = self._getJsonObject(tenant.get('domains', []), 'name', domainName)
        tenantID = tenant.get('ID', '')
        domainID = domain.get('guid', '')
        if len(tenantName) and tenantID == '':
            PrintMessage(''.join([CurrentMethodName(), ' failed: the tenant name "',
                                  tenantName, '" do NOT existed.']), 'Error')
            return '', ''
        if len(domainName) and domainID == '':
            PrintMessage(''.join([CurrentMethodName(), ' failed: the domain name "',
                                  domainName, '" do NOT existed.']), 'Warning')
            return tenantID, ''

        PrintMessage('GetTenantDomainID passed.')
        return tenantID, domainID

    def ApplyTenantAndDomain(self, tenantName, domainName):
        # Apply Tenant and Domain
        tenantID, domainID = self.GetTenantDomainID(tenantName, domainName)
        self.TenantID = self.Headers['TenantGuid'] = tenantID
        self.TenantName = tenantName
        self.DomainID = self.Headers['DomainGuid'] = domainID
        self.DomainName = domainName

        if len(tenantName) and len(tenantID):
            if len(domainName) and len(domainID):
                #info = self._getDomainSummary()
                PrintMessage(''.join([CurrentMethodName(), ' passed. Tenant Name=', tenantName,
                             ', TenantGuid=', tenantID, '; Domain Name=', domainName, ', DomainGuid=', domainID]))
            else:
                PrintMessage(''.join([CurrentMethodName(), ' passed. Tenant Name=', tenantName,
                             ', TenantGuid=', tenantID]))
            return True
        else:
            PrintMessage(''.join([CurrentMethodName(),' failed: Tenant=' ,tenantName, ', Domain=', domainName]), 'Error')
            return False

    def AddTenant(self, tenantInfo):
        serviceUrl = r'ServicesAPI/Admin/Tenant/upInsertTenant'
        tenantId = CreateGuid()
        tenantName = tenantInfo.get('Tenant Name', '')
        if tenantName == '':
            PrintMessage(''.join([CurrentMethodName(), ' failed. Please define Tenant Name.']), 'Error')
            return False
        nodeSize = tenantInfo.get('Maximum Nodes', self.FreeNodeSize)
        if type(nodeSize) is not int:
            PrintMessage(''.join([CurrentMethodName(), ' failed. Maximum Nodes must be a integer.']), 'Error')
            return False

        if self.CurrentVersion > 8.03:
            payload = {
                'decodeTenantObj': {
                    'ID': tenantId,
                    'name': tenantName,
                    'description': tenantInfo.get('Description', ''),
                    'dbName': tenantName.replace(' ', '_'),
                    'nodeSize': None,  # nodeSize,
                    'auths': {
                        'groups': [],
                        'users': []
                    },
                    'isCustomizedDBConn': False,
                    'isCustomizedLiveDBConn': False,
                    'storeUniqueKey': 'default',
                    # 'fsc_port': 0,
                    # 'fsc_isssl': False,
                    # 'IsPocRequest': False,
                    'forNewTenant': True
                },
                'tenantConnection': None,
                'lsDisplayUser': [
                    {
                        'userId': self.UserID,
                        'userName': self.Username,
                        'isSystemAdmin': True,
                        'isTenantAdmin': True,
                        'isDomainAdmin': True,
                        'canCreateDomain': True,
                        'isTenantUser': True,
                        'isDomainUser': True,
                        'authentication': {
                            'id': '',
                            'alias': 'NetBrain',
                            'type': 0
                        },
                        'externalGroup': []
                    }
                ],
                'forNewTenant': True,
                'licenseInfo': {
                    'Module': [
                        {
                            'Type': 0,
                            'IsChecked': True,
                            'IsDisable': False,
                            'Nodes': nodeSize,
                            'IsMSP': False
                        },
                        {
                            'Type': 1,
                            'IsChecked': True,
                            'IsDisable': False,
                            'Nodes': int(nodeSize * 4.5),
                            'IsMSP': False
                        },
                        {
                            'Type': 2,
                            'IsChecked': True,
                            'IsDisable': False,
                            'Nodes': int(nodeSize * 6.6),
                            'IsMSP': False
                        },
                        {
                            'Type': 3,
                            'IsChecked': True,
                            'IsDisable': False,
                            'Nodes': int(nodeSize * 6.6),
                            'IsMSP': False
                        }
                    ],
                    'NewTech': [
                        {
                            'Key': 'ACI',
                            'Name': 'Cisco ACI',
                            'Type': 1,
                            'IsDisabled': False,
                            'Parameter': [
                                {
                                    'Type': 'port',
                                    'Name': 'Ports',
                                    'Value': nodeSize
                                }
                            ]
                        },
                        {
                            'Key': '1047',
                            'Name': 'WAP',
                            'Type': 0,
                            'IsDisabled': False,
                            'Parameter': [
                                {
                                    'Type': 'node',
                                    'Name': 'Nodes',
                                    'Value': nodeSize
                                }
                            ]
                        },
                        {
                            'Key': 'ESXI',
                            'Name': 'vCenter',
                            'Type': 1,
                            'IsDisabled': False,
                            'Parameter': [
                                {
                                    'Type': 'cpu',
                                    'Name': 'CPU Processers',
                                    'Value': nodeSize
                                }
                            ]
                        },
                        {
                            'Key': 'NSX',
                            'Name': 'NSX-v',
                            'Type': 1,
                            'IsDisabled': False,
                            'Parameter': [
                                {
                                    'Type': 'cpu',
                                    'Name': 'CPU Processers',
                                    'Value': nodeSize
                                }
                            ]
                        },
                        {
                            'Key': 'AWS',
                            'Name': 'Amazon AWS',
                            'Type': 1,
                            'IsDisabled': False,
                            'Parameter': [
                                {
                                    'Type': 'vpc',
                                    'Name': 'VPCs',
                                    'Value': nodeSize
                                }
                            ]
                        },
                        {
                            'Key': 'Azure',
                            'Name': 'Microsoft Azure',
                            'Type': 1,
                            'IsDisabled': False,
                            'Parameter': [
                                {
                                    'Type': 'vnet',
                                    'Name': 'VNets',
                                    'Value': nodeSize
                                }
                            ]
                        },
                        {
                            'Key': 'performance',
                            'Name': 'performance',
                            'Type': 1,
                            'IsDisabled': False,
                            'Parameter': [
                                {
                                    'Type': 'cup',
                                    'Name': 'performance',
                                    'Value': nodeSize
                                }
                            ]
                        },
                        {
                            "Key": "aaa",
                            "Name": "aaa",
                            "Type": 1,
                            "IsDisabled": True,
                            "Parameter": [
                                {
                                    "Type": "aaa",
                                    "Name": "aaa",
                                    "Value": nodeSize
                                }
                            ]
                        }
                    ]
                },
                'isInitTenant': False
            }
        else:
            payload = {
                'decodeTenantObj': {
                    'ID': tenantId,
                    'name': tenantName,
                    'description': tenantInfo.get('Description', ''),
                    'allowedUser': 1,
                    'dbName': tenantName.replace(' ', '_'),
                    'nodeSize': nodeSize,
                    'isMaxUserUnlimited': 'true',
                    'maxUserCount': 1,
                    'forNewTenant': True,
                    'featureInfo':{
                        'tenantId': tenantId,
                        'nodeSize': nodeSize
                    }
                },
                'tenantConnection': None,
                'lsDisplayUser':[
                    {
                        'userId': self.UserID,
                        'userName': self.Username,
                        'isTenantAdmin': True
                    }
                ],
                'forNewTenant': True
            }
        info = self._postUrl(CurrentMethodName(), serviceUrl, payload, r'/admin.html')
        if not info:
            PrintMessage(''.join([CurrentMethodName(), ' failed.']), 'Error')
        else:
            PrintMessage(''.join([CurrentMethodName(), ' passed.']))
        return info

    # Active License start
    def _resetLoginPassword(self, oldPwd, newPwd):
        serviceUrl = r'ServicesAPI/Admin/User/resetLoginPassword'
        payload = {
            'userId': self.UserID,
            'oldPwd': self.PasswordEncrypt(oldPwd),
            'newPwd': self.PasswordEncrypt(newPwd)
        }
        '''
        header = self.Headers.copy()
        header['Content-Type'] = 'application/json;charset=UTF-8'
        header['Referer'] = header['Origin'] + r'/admin.html'
        header.pop('Sec-Fetch-Mode')
        header.pop('Sec-Fetch-Site')
        header['TenantGuid'] = ''
        header['DomainGuid'] = ''
        '''
        info = self._postUrl(CurrentMethodName(), serviceUrl, payload, r'/admin.html')
        if info:
            PrintMessage(''.join([CurrentMethodName(), ' passed.']))
        else:
            info = False
            print(''.join(['user: ', self.Username, ', old password:', oldPwd, ', new password: ', newPwd]))
        return info

    def _getUserAdditionalInfo(self):
        serviceUrl = r'ServicesAPI/Admin/User/GetUserAdditionalInfo'
        info = self._getUrl(CurrentMethodName(), serviceUrl, r'/admin.html')
        PrintMessage(''.join([CurrentMethodName(), ' passed.']))
        return info

    def _updateUserInfo(self, userInfo):
        serviceUrl = r'ServicesAPI/admin/updateUserInfo'
        payload = userInfo
        info = self._postUrl(CurrentMethodName(), serviceUrl, payload, r'/admin.html')
        if len(info) < 1:
            PrintMessage(''.join([CurrentMethodName(), ' failed: No data return.']), 'Error')
            return False
        success = info.get('success', False)
        if not success:
            PrintMessage(''.join(['_updateUserInfo failed: ', info.get('reasons', 'No reasons return.')]), 'Error')
        else:
            PrintMessage('_updateUserInfo passed.')
        return success

    def _getLicenseInfo(self):
        serviceUrl = r'ServicesAPI/License/RefreshInformation'
        info = self._getUrl(CurrentMethodName(), serviceUrl, r'/admin.html')
        isActivate = info.get('isActivate', False)
        if not isActivate:
            PrintMessage(''.join([CurrentMethodName(), ' failed: ', json.dumps(info)]), 'Error')
            return False
        self.FreeNodeSize = info.get('modules', {}).get('Essential', {}).get('currentTerm', {}).get('freeNodeSize', 0)
        return isActivate

    def _siteConfiguration(self, url):
        serviceUrl = r'ServicesAPI/AdvancedSettings/siteConfiguration'
        payload = url
        info = self._postUrl(CurrentMethodName(), serviceUrl, payload, '/admin.html')
        return info

    def ActivateOnline(self, newpwd, userInfo, licenseInfo, tenantInfo={}, emailSetting={},
                       username='admin', oldpwd='admin'):
        self.Username = username
        self.Password = oldpwd
        self.Scope = 'system'
        print('ActivateOnline:\nLog in with old password.')
        #if self.GenerateAccessToken(username, oldpwd):
        if self.Login(username, oldpwd, 'IEAdmin'):
            self.Scope = 'mainUI'
            print('Change old password to new password.')
            if not self._resetLoginPassword(oldpwd, newpwd):
                PrintMessage(''.join([CurrentMethodName(), ' failed to reset password.', 'Error']))
                return False
        if not self.Logined:
            self.Password = newpwd
            self.Scope = 'system'
            print('Log in with new password.')
            #if not self.GenerateAccessToken(username, newpwd, 'resetPwd_login'):  #
            if not self.Login(username, newpwd, 'IEAdmin'):
                PrintMessage(''.join([CurrentMethodName(), ' failed to log into system with new password.', 'Error']))
                return False
        print('Update user info.')
        currentUserInfo = self._getUserAdditionalInfo()
        # PrintJsonObject(currentUserInfo)
        if len(currentUserInfo) < 1:
            PrintMessage(''.join([CurrentMethodName(), ' failed. No user found.', 'Error']))
            self.Logout()
            return False
        userInfo['authId'] = currentUserInfo['authId']
        userInfo['userId'] = currentUserInfo['userId']
        # userInfo['userName'] = currentUserInfo['userName']
        self._updateUserInfo(userInfo)

        print('Update license info.')
        serviceUrl = r'ServicesAPI/License/Activate/Permanent/Online'
        licenseInfo['password'] = self.PasswordEncrypt(licenseInfo['password'])
        payload = licenseInfo
        info = self._postUrl(CurrentMethodName(), serviceUrl, payload, '/admin.html')
        if len(info) < 1:
            PrintMessage(''.join([CurrentMethodName(), ' failed: No data return.']), 'Error')
            self.Logout()
            return False
        # verify if the activatation is success
        success = info.get('status', False)
        # success = True
        if not success:
            PrintMessage(''.join([CurrentMethodName(), ' failed: ', info.get('error', 'No reasons return.')]), 'Error')
            self.Logout()
            return False

        # verify if the license is Actived
        value = self._getLicenseInfo()
        if len(tenantInfo) > 0:
            print('Add Tenant.')
            self.AddTenant(tenantInfo)

        if len(emailSetting) > 0:
            print('Set Email Setting.')
            self.SetEmailSetting(emailSetting)

        if self.CurrentVersion >= 8.03:
            self._siteConfiguration({'ie': self.Url, 'portal': self.Url + 'portal/'})
        else:
            self._siteConfiguration(self.Url)
        PrintMessage(''.join([CurrentMethodName(), ' passed']))
        self.Scope = 'mainUI'
        self.Logout()
        return True
    # Active License end

    # Email Settings start
    def _getEmailSetting(self):
        serviceUrl = r'ServicesAPI/Admin/EmailSetting'
        info = self._getUrl(CurrentMethodName(), serviceUrl, r'/admin.html')
        if len(info) < 1:
            self.PrintMessage(''.join([CurrentMethodName(), ' failed.']), 'Error')
            return []

        return info

    def TestEmailSetting(self):
        serviceUrl = r'ServicesAPI/Admin/EmailSetting/TestEmailSetting'
        payload = self._getEmailSetting()
        payload['isPwdEmpty'] = True
        info = self._postUrl(CurrentMethodName(), serviceUrl, payload, r'/admin.html')

        return info

    def SetEmailSetting(self, emailSetting):
        defaultSetting = self._getEmailSetting()
        if len(defaultSetting) < 1:
            PrintMessage(''.join(['SetEmailSetting Failed: Fail to retrieve Email Setting.']), 'Error')
            return False

        password = emailSetting['Password']
        if (password == ''):
            isPwdEmpty = True
        else:
            isPwdEmpty = False
        if self.CurrentVersion <= 8.01:
            serviceUrl = r'ServicesAPI/Admin/EmailSetting/UpInsert'  # v8.01
        else:
            serviceUrl = r'ServicesAPI/Admin/EmailSetting/settings'  # v8.02 and later
        emailSetting['Send Email Frequency'].update({'unit': 1})
        payload = {
            'ID': defaultSetting['ID'],
            'isPwdEmpty': isPwdEmpty,
            'enable': emailSetting['Enable Email Server Settings'],
            'smtpServer': emailSetting['SMTP Server'],
            'smtpPort': emailSetting['SMTP Port'],
            'encryption': emailSetting['Encryption'],
            'smtpSender': emailSetting['Sender Email Address'],
            'smtpSenderPassword': self.PasswordEncrypt(password),
            'sendEmailFreq': emailSetting['Send Email Frequency'] ,
            'operateInfo': {'operateUserName': self.Username}
        }

        info = self._postUrl(CurrentMethodName(), serviceUrl, payload, r'/admin.html')
        if not self.TestEmailSetting() :
            PrintMessage('TestEmailSetting failed.', 'Warning')
        PrintMessage('SetEmailSetting passed.')
        return True
    # Email Settings end

    # Front Server Controller start
    def _getFSCTenantList(self):
        # Retrieve FSC's Tenant list
        serviceUrl = r'ServicesAPI/FSCManager/TenantList'
        info = self._getUrl(CurrentMethodName(), serviceUrl, '/admin.html')
        if len(info) == 0:
            PrintMessage('Failed to retrieve Front Server Controller TenantList info.', 'Error')
            info = []

        return info

    def _getFrontServerControllerInfo(self):
        # Retrieve FSC info
        serviceUrl = r'ServicesAPI/FSCManager'
        info = self._getUrl(CurrentMethodName(), serviceUrl, '/admin.html')
        if len(info) == 0:
            PrintMessage('Failed to retrieve Front Server Controller info.', 'Error')

        return info

    def _getFrontServerControllerDetailInfo(self, fscName):
        # Retrieve FSC detail info
        fscLists = self._getFrontServerControllerInfo()
        fsc = self._getJsonObject(fscLists, 'name', fscName)
        fscID = fsc.get('id', '')
        if fscID == '':
            PrintMessage(''.join(['Front Server Controller "', fscName, '" does NOT existed.']), 'Error')
            return {}

        serviceUrl = r'ServicesAPI/FSCManager/' + fscID
        info = self._getUrl(CurrentMethodName(), serviceUrl, '/admin.html')
        if len(info) == 0:
            PrintMessage('Failed to retrieve Front Server Controller info.', 'Error')

        return info

    def VerifyFrontServerControllerConnected(self, fscName):
        # Verify if the FSC is connected
        fscInfos = self._getFrontServerControllerInfo()
        if len(fscInfos) == 0:
            PrintMessage(''.join([CurrentMethodName(), ': There is NO Front Server Controller existed.']), 'Error')
            return False

        fscInfo = self._getJsonObject(fscInfos, 'name', fscName)
        fscID = fscInfo.get('id', '')
        if fscID == '':
            PrintMessage(''.join(['Front Server Controller "', fscName, '" does NOT existed.']), 'Error')
            return False

        serviceUrl = r'ServicesAPI/FSCManager/FSCAndFSStatus'
        payload = {'withFsStatus': True}
        fscInfos = self._postUrl(CurrentMethodName(), serviceUrl, payload, '/admin.html')
        if len(fscInfos) < 1:
            PrintMessage(''.join([CurrentMethodName(), ' "', fscName, '" failed.\n']), 'Error')
            return False
        else:
            fscInfo = self._getJsonObject(fscInfos, 'id', fscID)
            if len(fscInfo) < 1:
                PrintMessage(''.join([CurrentMethodName(), ' "', fscName, '" failed.\n', json.dumps(fscInfos)]), 'Error')
                return False

            fscConnected = fscInfo.get('fscInfo', [])[0].get('fscConnected', False)
            if fscConnected:
                PrintMessage(''.join([CurrentMethodName(), ' passed.\nThe Front Server Controller "',
                                      fscName, '" is connected.']))
                return True

        PrintMessage(
            ''.join([CurrentMethodName(), ' failed.\nThe Front Server Controller "', fscName, '" is NOT connected. ',
                     json.dumps(fscInfos)]), 'Error')
        return False

    def AddFrontServerController(self, fscDetailInfo):
        # Add FSC
        deployMode = fscDetailInfo.get('Deployment Mode', 1)
        if deployMode == 'Standalone':
            deployMode = 1
            fscName = fscDetailInfo['FSCInfo'][0].get('Name', 'FSC')
        else:
            deployMode = 2  # Group
            fscName = fscDetailInfo.get('Group Name', 'FSC')
        fscTenants = list()
        tenantLists = self._getFSCTenantList()
        for tenantList in tenantLists:
            if tenantList['name'] in fscDetailInfo.get('Allocated Tenants', []):
                tenantList['isSelected'] = True
                fscTenants.append(tenantList.copy())
        fscInfo = list()
        for item in fscDetailInfo['FSCInfo']:
            fscInfo.append({
                        'uniqueName': item.get('Name', ''),
                        'ipOrHostname': item.get('Hostname or IP Address', ''),
                        'port': item.get('Port', '9095'),
                        'userName': item.get('Username', 'admin'),
                        'password': self.PasswordEncrypt(item.get('Password', '')),
                        'timeout': item.get('Timeout', 5),
                        'desc': item.get('Description', '')
                    })
        serviceUrl = r'ServicesAPI/FSCManager'
        payload = {
            'id': CreateGuid(),
            'deployMode': deployMode,
            'groupName': fscName,
            'fscInfo': fscInfo,
            'useSSL': fscDetailInfo.get('useSSL', False),
            'conductCertAuthVerify': fscDetailInfo.get('Conduct Certificate Authority verification', False),
            'certificateType': fscDetailInfo.get('certificateType', 2),
            'certificate': fscDetailInfo.get('certificate', ''),
            'certificateName': fscDetailInfo.get('certificateName', ''),
            'tenants': fscTenants
        }
        info = self._postUrl(CurrentMethodName(), serviceUrl, payload, '/admin.html')
        if not isJson(info):
            PrintMessage(info, 'Warning')

        info = self.VerifyFrontServerControllerConnected(fscName)
        msg = '" passed.' if info else '" failed.'
        PrintMessage(''.join([CurrentMethodName(), ' "', fscName, msg]))
        return info

    def EditFrontServerController(self, fscName, fscDetailInfo):
        serviceUrl = r'ServicesAPI/FSCManager'

        payload = self._getFrontServerControllerDetailInfo(fscName)
        if len(payload) == 0:
            PrintMessage(''.join([CurrentMethodName(), ' Failed.\n', 'Failed to retrieve Front Server Controller "',
                                  fscName, '" info.']), 'Error')
            return False

        index = 0
        fscInfo = fscDetailInfo['FSCInfo']
        for item in payload['fscInfo']:
            item['uniqueName'] = fscInfo[index]['Name']
            item['ipOrHostname'] = fscInfo[index]['Hostname or IP Address']
            item['port'] = fscInfo[index]['Port']
            item['userName'] = fscInfo[index]['Username']
            item['password'] = self.PasswordEncrypt(fscInfo[index]['Password'])
            item['timeout'] = fscInfo[index]['Timeout']
            item['desc'] = fscInfo[index]['Description']

        '''
        info = payload['fscInfo'][0]
        if fscInfo.get('Name', '') != '':
            fscName = fscInfo['Name']
            info['uniqueName'] = fscName
        if len(fscInfo['Hostname or IP Address']):
            info['ipOrHostname'] = fscInfo['Hostname or IP Address']
        if len(fscInfo['Port']):
            info['port'] = fscInfo['Port']
        if len(fscInfo['Username']):
            info['userName'] = fscInfo['Username']
        if len(fscInfo['Password']):
            info['password'] = fscInfo['Password']
        if fscInfo.get('Timeout', None) is not None:
            info['timeout'] = fscInfo['Timeout']
        if len(fscInfo['Description']):
            info['desc'] = fscInfo['Description']
        '''

        info = self._putUrl(CurrentMethodName(), serviceUrl, payload, '/admin.html')
        if len(info) == 0:
            PrintMessage(''.join([CurrentMethodName(), ' failed.']), 'Error')
            return False
        if not isJson(info):
            PrintMessage(info, 'Warning')

        self.VerifyFrontServerControllerConnected(fscName)
        PrintMessage(''.join([CurrentMethodName(), ' "', fscName, '" passed.']))
        return True

    def DeleteFrontServerController(self, fscName):
        # Delete FSC
        fscInfos = self._getFrontServerControllerInfo()
        if len(fscInfos) == 0:
            PrintMessage('DeleteFrontServerController: No Front Server Controller existed.', 'Warning')
            return True

        fscInfo = self._getJsonObject(fscInfos, 'name', fscName)
        if len(fscInfo) == 0:
            PrintMessage('DeleteFrontServerController failed.', 'Error')
            PrintMessage(' '.join(['The Front Server Controller"', fscName, '" does NOT existed.', 'Error']))
            PrintMessage(json.dumps(fscInfos))
            return False

        fscID = fscInfo.get('id', '')
        # print(fscID)

        serviceUrl = r'ServicesAPI/FSCManager/' + fscID
        info = self._deleteUrl(CurrentMethodName(), serviceUrl, {}, r'/admin.html')
        if not info:
            PrintMessage('DeleteFrontServerController failed.', 'Error')
            return False

        PrintMessage('DeleteFrontServerController passed.')
        return True

    # Front Server Controller end

    # Front Server Group start
    def _getFrontServerGroupInfo(self):
        serviceUrl = r'ServicesAPI/FSManager/fsg/' + self.TenantID
        info = self._getUrl(CurrentMethodName(), serviceUrl, '/admin.html')
        if len(info):
            PrintMessage(''.join([CurrentMethodName(), ' passed.']))
        else:
            PrintMessage(''.join([CurrentMethodName(), ' failed to retrieve Front Server Group info.']), 'Error')

        return info

    def GetFrontServerGroupID(self, fsgName):
        if (fsgName == ''):
            return ''

        fsgroup = self._getFrontServerGroupInfo()
        fsgroup = self._getJsonObject(fsgroup, 'alias', fsgName)
        fsgID = fsgroup.get('id', '')
        # if(fsgID != ''):
        #     PrintMessage('Front Server Group "' + fsgName + '" exist.', 'Warning')
        return fsgID

    def GetFrontServerGroupName(self, fsgID):
        if (fsgID == ''):
            return ''

        fsgroup = self._getFrontServerGroupInfo()
        fsgroup = self._getJsonObject(fsgroup, 'id', fsgID)
        return fsgroup.get('alias', '')

    def CreateFrontServerGroup(self, fsgName, tenantName='Initial Tenant'):
        tenantLists = self._getFSCTenantList()
        tenantInfo = self._getJsonObject(tenantLists, 'name', tenantName)
        if len(tenantInfo):
            PrintMessage(''.join([CurrentMethodName(), ' failed: cannot find Tenant "', tenantName, ' ".']), 'Error')
            return ''

        serviceUrl = r'ServicesAPI/FSManager/fsg'
        fsgID = CreateGuid()
        payload = {
            'alias': fsgName,
            'id': fsgID,
            'isFSG': True,
            'tenantInfo': {
                'id': tenantInfo['id'],
                'name': tenantInfo['name']
            }
        }

        info = self._postUrl(CurrentMethodName(), serviceUrl, payload, r'/admin.html')
        if len(info) == 0:
            PrintMessage(''.join([CurrentMethodName(), ' failed.']), 'Error')
            return ''

        PrintMessage(''.join([CurrentMethodName(), ' "', fsgName, '" passed.']))
        return fsgID

    def EditFrontServerGroup(self, fsgName, fsgNewName):
        serviceUrl = r'ServicesAPI/FSManager/fsg'
        payload = self._getFrontServerGroupInfo()
        payload = self._getJsonObject(payload, 'alias', fsgName)
        payload['alias'] = fsgNewName

        info = self._putUrl(CurrentMethodName(), serviceUrl, payload, r'/admin.html')
        if len(info) == 0:
            PrintMessage(''.join([CurrentMethodName(), ' failed.']), 'Error')
            return ''

        PrintMessage(''.join([CurrentMethodName(), ' passed: "', fsgName, '" ==> "', fsgNewName, '".']))
        return True

    def DeleteFrontServerGroup(self, fsgName):
        payload = self._getFrontServerGroupInfo()
        payload = self._getJsonObject(payload, 'alias', fsgName)
        # PrintJsonObject(payload)
        fsgID = payload.get('id', '')
        if fsgID == '':
            PrintMessage(''.join([CurrentMethodName(), ' failed:', ' Failed to retrieve the ID of Front Server Group.\n',
                                  json.dumps(payload)]), 'Error')
            return False

        serviceUrl = r'ServicesAPI/FSManager/fsg/' + fsgID
        info = self._deleteUrl(CurrentMethodName(), serviceUrl, payload, r'/admin.html')
        if len(info) == 0:
            PrintMessage(''.join([CurrentMethodName(), ' failed.']), 'Error')
            return False

        PrintMessage(''.join([CurrentMethodName(), ' "', fsgName, '" passed.']))
        return True

    # Front Server Group end

    # Front Server start
    def _getFrontServerInfo(self, fsName):
        serviceUrl = r'ServicesAPI/FSManager/fs/' + fsName
        info = self._getUrl(CurrentMethodName(), serviceUrl, '/admin.html')
        if len(info):
            PrintMessage(''.join([CurrentMethodName(), ' passed.']))
        else:
            PrintMessage(''.join([CurrentMethodName(), ' failed: ', json.dumps(info)]), 'Error')

        return info

    def _verifyFrontServerInfo(self, fsName, fsgName):
        fsInfo = self._getFrontServerInfo(fsName)
        # PrintJsonObject(fsInfo)
        if fsName != '':
            value = fsInfo.get('id', '')
            if (re.search(fsName, value, re.IGNORECASE) == None):
                PrintMessage('The name of Front Server is wrong. Set "' + fsName + '" and return "' + value + '".',
                             'Error')
                return False
        if fsgName != '':
            value = fsInfo.get('group', '')
            if (re.search(fsgName, value, re.IGNORECASE) == None):  # or fsInfo.get('fsgId', '') == ''):
                PrintMessage(
                    'The name of Front Server Group is wrong. Set "' + fsgName + '" and return "' + value + '".',
                    'Error')
                return False
            value = fsInfo.get('fsgId', '')
            if value == '':
                PrintMessage('The ID of Front Server Group is NULL.', 'Error')
                return False
        if self.CurrentVersion >= 8.03:
            return True
        value = fsInfo.get('key', '')
        if value != '':
            PrintMessage('The Authentication Key exist in response data.', 'Error')
            return False

        return True

    def AddFrontServer(self, fsInfo): # Name, fsAuthKey, tenantName='', fsgName=''):
        tenantName = fsInfo.get('Tenant Name', '')
        tenantID, domainID = self.GetTenantDomainID(tenantName)
        if len(tenantID) <= 0:
            PrintMessage('Failed to retrieve the Tenant ID.', 'Error')
            return False
        fsInfo['Tenant ID'] = tenantID
        fsName = fsInfo.get('Front Server ID', '')
        fsgName = fsInfo.get('Front Server Group', '')
        fsgID = self.GetFrontServerGroupID(fsgName)
        if fsgID == '' and fsgName != '':
            PrintMessage('Front Group Name "' + fsgName + '" does NOT exist.', 'Warning')
            fsgID = self.CreateFrontServerGroup(fsgName)

        serviceUrl = r'ServicesAPI/FSManager/fs'
        payload = {
            'ipOrHostname': '',
            'id': fsName,
            'key': self.PasswordEncrypt(fsInfo.get('Authentication Key', '')),
            'isFSG': False,
            'fsgId': fsgID,
            'registered': False,
            'tenantInfo': {
                'name': tenantName,
                'id': tenantID
            }
        }
        info = self._postUrl(CurrentMethodName(), serviceUrl, payload, r'/admin.html')
        if len(info) == 0:
            PrintMessage(''.join([CurrentMethodName(), ' failed. The name of Front Server is "', fsName, '".']), 'Error')
            return False
        if self._verifyFrontServerInfo(fsName, fsgName):
            PrintMessage(''.join([CurrentMethodName(), ' passed. The name of Front Server is "', fsName, '".']))
            return True
        else:
            PrintMessage('AddFrontServer failed.', 'Error')
            return False

    def EditFrontServer(self, fsName, fsInfo):
        payload = self._getFrontServerInfo(fsName)
        fsgName = payload.get('group', '')
        fsgNewName = fsInfo.get('Front Server Group', '')
        if fsgNewName != '':
            if re.search(fsgNewName, fsgName, re.IGNORECASE) == None:
                fsgID = self.GetFrontServerGroupID(fsgNewName)
                if (fsgID == ''):
                    PrintMessage('Front Group Name "' + fsgNewName + '" does NOT exist.', 'Warning')
                    fsgID = self.CreateFrontServerGroup(fsgNewName)
                payload['fsgId'] = fsgID
                payload['group'] = fsgNewName
        else:
            if payload.get('fsgId', '') != '':
                payload['fsgId'] = ''
            if payload.get('group', '') != '':
                del payload['group']
        fsNewAuthKey = fsInfo.get('Authentication Key', '')
        if fsNewAuthKey != '':
            payload['key'] = self.PasswordEncrypt(fsNewAuthKey)

        serviceUrl = 'ServicesAPI/FSManager/fs/'
        info = self._putUrl(CurrentMethodName(), serviceUrl, payload, r'/admin.html')
        if len(info) == 0:
            PrintMessage(''.join([CurrentMethodName(), ' failed. The name of Front Server is "', fsName, '".']),
                         'Error')
            return False
        if self._verifyFrontServerInfo(fsName, fsgNewName):
            PrintMessage('EditFrontServer passed.')
            return True
        else:
            PrintMessage('EditFrontServer failed.', 'Error')
            return False

    def DeleteFrontServer(self, fsName):
        serviceUrl = r'ServicesAPI/FSManager/fs/' + fsName
        info = self._deleteUrl(CurrentMethodName(), serviceUrl, {}, r'/admin.html')
        if info:
            PrintMessage('DeleteFrontServer passed.')
            return True
        else:
            PrintMessage('DeleteFrontServer failed.', 'Error')
            return False

    # Front Server end

    # Add User Account start
    def _getDisplayTenantList(self):
        serviceUrl = r'ServicesAPI/Admin/Tenant/getDisplayTenantList'
        info = self._getUrl(CurrentMethodName(), serviceUrl, '/admin.html')
        if len(info):
            PrintMessage(''.join([CurrentMethodName(), ' passed.']))
        else:
            PrintMessage(''.join([CurrentMethodName(), ' failed: ', json.dumps(info)]), 'Error')

        return info

    def _getUserByName(self, username):
        serviceUrl = r'ServicesAPI/Admin/User/getUserByName'
        payload = {'authId': '', 'userName': username}
        info = self._postUrl(CurrentMethodName(), serviceUrl, payload, r'/admin.html')
        if len(info):
            PrintMessage(''.join([CurrentMethodName(), ' passed.']))
        else:
            PrintMessage(''.join([CurrentMethodName(), ' failed: ', json.dumps(info)]), 'Error')

        return info

    def _getAllUsers(self):
        serviceUrl = r'ServicesAPI/Admin/User/getAllUsers'
        info = self._getUrl(CurrentMethodName(), serviceUrl, r'/admin.html')
        if len(info):
            PrintMessage(''.join([CurrentMethodName(), ' passed.']))
        else:
            PrintMessage(''.join([CurrentMethodName(), ' failed: ', json.dumps(info)]), 'Error')

        return info

    def _analysisUserInfo(self, userInfo, tenantList=None, userList=None):
        # make up User and TenentRoles
        ret = dict()
        username = userInfo.get('Username', '')
        if username == '':
            PrintMessage('AddUser Failed: Please set the username.', 'Error')
            return ret
        password = userInfo.get('Password', '')
        if password == '':
            PrintMessage('AddUser Failed: Please set the password.', 'Error')
            return ret
        if userList is None:
            userList = self._getAllUsers()
        user = self._getJsonObject(userList, 'name', username)
        if len(user):
            PrintMessage(''.join(['AddUser skipped: the username "', username, '" existed.']), 'Warning')
            return ret
        if tenantList is None:
            tenantList = self._getDisplayTenantList()
        tenentRoles = list()
        for tenantAccess in userInfo.get('Tenant Access', []):
            tenantName = tenantAccess.get('Name', '')
            if tenantName == '':
                continue
            tenant = self._getJsonObject(tenantList, 'name', tenantName)
            domainList = tenant['decodeTenant']['domains']
            domains = list()
            domainAccesses = userInfo.get('Domain Access', [])
            if len(domainAccesses) <= 0:
                for item in domainList:
                    domainAccesses.append({"Name": item['name'], "Domain Privileges": []})
            for domainAccess in domainAccesses:
                domainName = domainAccess.get('Name', '')
                if domainName == '':
                    for item in domainList:
                        domain = {'id': item['guid'], 'roles': ['domainAdmin'], 'devicePolicies': []} # !!!unfininshed
                        domains.append(domain)
                else:
                    item = self._getJsonObject(domainList, 'name', domainName)
                    if len(item):
                        domain = {'id': item['guid'], 'roles': ['domainAdmin'], 'devicePolicies': []}  # !!!unfininshed
                        domains.append(domain)
            tenentRoles.append({
                'tenantId': tenant['ID'],
                'isAdmin': tenantAccess.get('Tenant Admin', ''),
                'canAddDomain': tenantAccess.get('Allowed to Create Domain', ''),
                'domains': domains
            })

        hashKey = randint(1000, 9999)
        user = {
            'canResetPassword': userInfo.get('Allowed to change individual password', False),
            'authentication': {'id': '', 'alias': 'NetBrain', 'type': 0, '$$hashKey': f'object:{hashKey}'},
            'matchField': 'password',
            'email': userInfo.get('Email', ''),
            'firstName': userInfo.get('First Name', ''),
            'lastName': userInfo.get('Last Name', ''),
            'name': userInfo.get('Username', ''),
            'password': self.PasswordEncrypt(password),
            'phoneNumber': userInfo.get('Phone Number', ''),
            'department': userInfo.get('Department', ''),
            'description': userInfo.get('Description', ''),
            'expireDate': userInfo.get('Expired after', None),  # !!! unfininshed
        }
        ret['User'] = user
        ret['TenentRoles'] = tenentRoles

        return ret

    def AddUser(self, userInfo, tenantList=None, userList=None):
        user = self._analysisUserInfo(userInfo, tenantList, userList)
        if len(user) == 0:
            return False

        username = userInfo['Username']
        serviceUrl = r'ServicesAPI/Admin/User/upInsertUserTenantRole'
        url = self.Url + serviceUrl
        headers = self.Headers.copy()
        headers['Referer'] += '/admin.html'
        payload = {
            'userTenantRole': {
                'user': user['User'],
                'isSystemManager': userInfo.get('System Admin', True),
                'isSystemUser': userInfo.get('System Management', True),
                'isUserManager': userInfo.get('User Management', True),
                'tenantRole': user['TenentRoles']
            },
            'pageUrl': self.Url + 'admin.html#/systemAdmin'
        }
        #PrintJsonObject(payload)
        html = requests.post(url, headers=headers, data=json.dumps(payload), verify=False, allow_redirects=False,
                             timeout=HTTP_TIMEOUT)
        if html.status_code != 200:
            PrintMessage(''.join(['AddUser failed.\n', html.text]), 'Error')
            return []
        result = html.json()
        resultCode = result.get('operationResult', {}).get('ResultCode', -1)
        if resultCode == 100096:
            PrintMessage(''.join(['AddUser "', username, '" passed. ', result['operationResult']['ResultDesc']]), 'Warning')
        #PrintJsonObject(result)
        else:
            user = self._getUserByName(username)
            if len(user) == 0:
                self.PrintMessage(''.join(['AddUser "', username, '" failed.']), 'Error')
                return False
            PrintMessage(''.join(['AddUser "', username, '" passed.']))
        return True

    # Add User Account end

    # domain start
    def _upInsertUserSystemConf(self, domainID=''):
        serviceUrl = r'ServicesAPI/User/System/Config/upInsertUserSystemConf'
        if domainID != '':
            self.DomainID = domainID
        payload = {
            "userConf": {
                "conf": {
                    "selectedTenantGuid": self.TenantID,
                    "selectedDomainGuids": [self.DomainID]
                }
            }
        }
        info = self._postUrl(CurrentMethodName(), serviceUrl, payload, r'/domainAdmin.html')
        if info is not None:
            PrintMessage(''.join([CurrentMethodName(), ' passed.']))
        else:
            PrintMessage(''.join([CurrentMethodName(), ' failed: ', json.dumps(info)]), 'Error')

        return info

    def CreateDomain(self, domainInfo):
        if len(domainInfo) == 0:
            PrintMessage(CurrentMethodName() + ' failed to load Domain info.', 'Error')
            return {}
        tenantName = domainInfo.get('Tenant Name', '')
        if tenantName == '':
            PrintMessage(CurrentMethodName() + ' failed to load Tenant Name.', 'Error')
            return {}
        domainName = domainInfo.get('Domain Name', '')
        if domainName == '':
            PrintMessage(CurrentMethodName() + ' failed to load Domain Name.', 'Error')
            return {}
        maxNodes = domainInfo.get('Maximum Nodes', '')
        if maxNodes == '':
            PrintMessage(CurrentMethodName() + ' failed to load Maximum Nodes.', 'Error')
            return {}
        tenantID, domainID = self.GetTenantDomainID(tenantName, domainName)
        if tenantID != '':
            self.TenantID = tenantID
        if domainID != '':
            PrintMessage(''.join([CurrentMethodName(), ': Domain Name "', domainName, '" is existed.']), 'Warning')
            return {}

        serviceUrl = r'ServicesAPI/Admin/Domain/createDomain'
        if self.CurrentVersion > 8.03:
            payload = {
                'userGuid': self.UserID,
                'companyGuid': tenantID,
                'displayName': domainName,
                'nodeSize': 0,
                'descr': domainInfo.get('Description', ''),
                'licenseInfo': {
                    'Module': [
                        {
                            'Type': 0,
                            'IsChecked': True,
                            'IsDisable': False,
                            'Nodes': maxNodes
                        },
                        {
                            'Type': 1,
                            'IsChecked': True,
                            'Nodes': int(maxNodes * 4.5),
                            'IsDisable': False
                        },
                        {
                            'Type': 2,
                            'IsChecked': True,
                            'Nodes': int(maxNodes * 6.6),
                            'IsDisable': False
                        },
                        {
                            'Type': 3,
                            'IsChecked': True,
                            'IsDisable': True,
                            'Nodes': int(maxNodes * 6.6),
                            'IsDisable': False
                        }
                    ],
                    'NewTech': [
                        {
                            'Key': 'ACI',
                            'Name': 'Cisco ACI',
                            'Type': 1,
                            'IsDisabled': False,
                            'Parameter': [
                                {
                                    'Type': 'port',
                                    'Name': 'Ports',
                                    'Value': maxNodes
                                }
                            ]
                        },
                        {
                            'Key': '1047',
                            'Name': 'WAP',
                            'Type': 0,
                            'IsDisabled': False,
                            'Parameter': [
                                {
                                    'Type': 'node',
                                    'Name': 'Nodes',
                                    'Value': maxNodes
                                }
                            ]
                        },
                        {
                            'Key': 'ESXI',
                            'Name': 'vCenter',
                            'Type': 1,
                            'IsDisabled': False,
                            'Parameter': [
                                {
                                    'Type': 'cpu',
                                    'Name': 'CPU Processers',
                                    'Value': maxNodes
                                }
                            ]
                        },
                        {
                            'Key': 'NSX',
                            'Name': 'NSX-v',
                            'Type': 1,
                            'IsDisabled': False,
                            'Parameter': [
                                {
                                    'Type': 'cpu',
                                    'Name': 'CPU Processers',
                                    'Value': maxNodes
                                }
                            ]
                        },
                        {
                            'Key': 'AWS',
                            'Name': 'Amazon AWS',
                            'Type': 1,
                            'IsDisabled': False,
                            'Parameter': [
                                {
                                    'Type': 'vpc',
                                    'Name': 'VPCs',
                                    'Value': maxNodes
                                }
                            ]
                        },
                        {
                            'Key': 'Azure',
                            'Name': 'Microsoft Azure',
                            'Type': 1,
                            'IsDisabled': False,
                            'Parameter': [
                                {
                                    'Type': 'vnet',
                                    'Name': 'VNets',
                                    'Value': maxNodes
                                }
                            ]
                        },
                        {
                            'Key': 'performance',
                            'Name': 'performance',
                            'Type': 1,
                            'IsDisabled': False,
                            'Parameter': [
                                {
                                    'Type': 'cup',
                                    'Name': 'performance',
                                    'Value': maxNodes
                                }
                            ]
                        },
                        {
                            "Key": "aaa",
                            "Name": "aaa",
                            "Type": 1,
                            "IsDisabled": True,
                            "Parameter": [
                                {
                                    "Type": "aaa",
                                    "Name": "aaa",
                                    "Value": maxNodes
                                }
                            ]
                        }
                    ]
                }
            }
        else:
            payload = {
                'userGuid': self.UserID,
                'companyGuid': tenantID,
                'displayName': domainName,
                'nodeSize': maxNodes,
                'descr': domainInfo.get('Description', '')
            }
        info = self._postUrl(CurrentMethodName(), serviceUrl, payload, r'/domainAdmin.html')
        if len(info):
            PrintMessage(''.join([CurrentMethodName(), ' passed. Tenant=', tenantName, ', Domain=', domainName]))
            self.ApplyTenantAndDomain(tenantName, domainName)
            self._upInsertUserSystemConf()
            self._getAllNetworkSetting()
        else:
            PrintMessage(''.join([CurrentMethodName(), ' failed: ', json.dumps(info)]), 'Error')

        return info

    def CreateDomainWithNetworkSetting(self, domainInfo, telnetInfo={}, enablePasswdInfo={}, snmpRoInfo={}):
        if len(domainInfo) == 0:
            PrintMessage(CurrentMethodName() + ' failed to load Domain info.', 'Error')
            return False
        info = self.CreateDomain(domainInfo)
        if len(info):
            if len(telnetInfo):
                info = self.UpdateTelnetInfo(telnetInfo)
            if len(enablePasswdInfo):
                info = self.UpdateEnablePasswd(enablePasswdInfo)
            if len(snmpRoInfo):
                info = self.UpdateSnmpRoInfo(snmpRoInfo)

        return info

    def DeleteDomain(self, domainInfo):
        if len(domainInfo) == 0:
            PrintMessage(CurrentMethodName() + ' failed to load Domain info.', 'Error')
            return {}

        serviceUrl = r'ServicesAPI/Admin/Domain/deleteDomain'
        payload = domainInfo
        # {
        #     'userGuid': self.UserID,
        #     'companyGuid': domainInfo['companyGuid'],
        #     'domainGuid': domainInfo['domainGuid'],
        #     'dbName': domainInfo['dbName']
        # }
        info = self._postUrl(CurrentMethodName(), serviceUrl, payload, r'/domainAdmin.html')
        if info:
            PrintMessage(''.join([CurrentMethodName(), ' passed. dbName=', domainInfo['dbName']]))
        else:
            PrintMessage(''.join([CurrentMethodName(), ' failed: ', json.dumps(info)]), 'Error')

        return info

    def _getDomainSummary(self):
        serviceUrl = r'ServicesAPI/system/domain/domainsummary'
        payload = {
            "domainId": self.DomainID,
            "tenantId": self.TenantID
        }
        info = self._postUrl(CurrentMethodName(), serviceUrl, payload, r'/domainAdmin.html')
        if len(info):
            PrintMessage(''.join([CurrentMethodName(), ' passed.']))
        else:
            PrintMessage(''.join([CurrentMethodName(), ' failed: ', json.dumps(info)]), 'Error')

        return info

    def GetWorkspaceSummaryAndLicenseUsage(self):
        return self._getDomainSummary()

    def _getAllNetworkSetting(self):
        serviceUrl = r'ServicesAPI/networksetting/getAllNetworkSetting'
        info = self._getUrl(CurrentMethodName(), serviceUrl, r'/domainAdmin.html')
        PrintMessage(''.join([CurrentMethodName(), ' passed.']))

        return info

    def GetDiscoverNetworkSetting(self):
        return self._getAllNetworkSetting()

    def _checkDeviceCountSSHPrivateKey(self):
        serviceUrl = r'ServicesAPI/networksetting/checkDeviceCount/SSHPrivateKey'
        info = self._getUrl(CurrentMethodName(), serviceUrl, r'/domainAdmin.html')
        PrintMessage(''.join([CurrentMethodName(), ' passed.']))

        return info

    def _checkDeviceCountJumpbox(self):
        serviceUrl = r'ServicesAPI/networksetting/checkDeviceCount/Jumpbox'
        info = self._getUrl(CurrentMethodName(), serviceUrl, r'/domainAdmin.html')
        PrintMessage(''.join([CurrentMethodName(), ' passed.']))

        return info

    def _checkDeviceCountTelnetInfo(self):
        serviceUrl = r'ServicesAPI/networksetting/checkDeviceCount/TelnetInfo'
        info = self._getUrl(CurrentMethodName(), serviceUrl, r'/domainAdmin.html')
        PrintMessage(''.join([CurrentMethodName(), ' passed.']))

        return info

    def _checkDeviceCountEnablePassword(self):
        serviceUrl = r'ServicesAPI/networksetting/checkDeviceCount/EnablePassword'
        info = self._getUrl(CurrentMethodName(), serviceUrl, r'/domainAdmin.html')
        PrintMessage(''.join([CurrentMethodName(), ' passed.']))

        return info

    def _checkDeviceCountSnmpRoInfo(self):
        serviceUrl = r'ServicesAPI/networksetting/checkDeviceCount/SnmpRoInfo'
        info = self._getUrl(CurrentMethodName(), serviceUrl, r'/domainAdmin.html')
        PrintMessage(''.join([CurrentMethodName(), ' passed.']))

        return info

    def CheckDeviceCount(self):
        self._checkDeviceCountSSHPrivateKey()
        self._checkDeviceCountJumpbox()
        self._checkDeviceCountTelnetInfo()
        self._checkDeviceCountEnablePassword()
        self._checkDeviceCountSnmpRoInfo()

    def _domainAdmin(self):
        serviceUrl = r'domainAdmin.html'
        url = self.Url + serviceUrl
        headers = self.Headers.copy()
        headers[
            'Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3'
        headers['Sec-Fetch-Mode'] = 'navigate'
        headers['Sec-Fetch-User'] = '?1'
        headers['Upgrade-Insecure-Requests'] = '1'
        headers.pop('Origin')
        headers.pop('Host')
        headers.pop('Referer')
        headers.pop('TenantGuid')
        headers.pop('DomainGuid')
        headers.pop('Authorization')
        httpReponse = HttpGet(url, headers)
        if (httpReponse['statusCode'] != 200):
            PrintMessage(''.join([CurrentMethodName(), ' failed: ', json.dumps(httpReponse)]), 'Error')
            return {}
        # print(json.dumps(httpReponse, indent=4, sort_keys=True))
        resultCode = httpReponse.get('resultCode', -1)
        if (resultCode != 0):
            PrintMessage(''.join([CurrentMethodName(), ' failed. ', httpReponse['resultDescription']]), 'Error')
            return {}
        info = httpReponse.get('data', [])
        # PrintJsonObject(info)

        return info

    def _getDomainPermissionListByUserId(self):
        serviceUrl = r'ServicesAPI/Admin/Domain/GetDomainPermissionListByUserId'
        payload = {
            self.UserID
        }
        info = self._postUrl(CurrentMethodName(), serviceUrl, payload, r'/domainAdmin.html')
        if len(info):
            PrintMessage(''.join([CurrentMethodName(), ' passed.']))
        else:
            PrintMessage(''.join([CurrentMethodName(), ' failed: ', json.dumps(info)]), 'Error')

        return info

    def _getAllBaseData(self):
        serviceUrl = r'ServicesAPI/SystemModel/getAllBaseData'
        info = self._getUrl(CurrentMethodName(), serviceUrl, r'/domainAdmin.html')
        if len(info):
            PrintMessage(''.join([CurrentMethodName(), ' passed.']))
        else:
            PrintMessage(''.join([CurrentMethodName(), ' failed: ', json.dumps(info)]), 'Error')

        return info

    def _getAllNetworkSettingIds(self):
        serviceUrl = r'ServicesAPI/networksetting/getAllNetworkSettingIds'
        info = self._getUrl(CurrentMethodName(), serviceUrl, r'/domainAdmin.html')
        if len(info):
            PrintMessage(''.join([CurrentMethodName(), ' passed.']))
        else:
            PrintMessage(''.join([CurrentMethodName(), ' failed: ', json.dumps(info)]), 'Error')

        return info

    def _getLiveSetting(self):
        serviceUrl = r'ServicesAPI/Discovery/Options/getLiveSetting'
        info = self._getUrl(CurrentMethodName(), serviceUrl, r'/domainAdmin.html')
        if len(info):
            PrintMessage(''.join([CurrentMethodName(), ' passed.']))
        else:
            PrintMessage(''.join([CurrentMethodName(), ' failed: ', json.dumps(info)]), 'Error')

        return info

    def _getAllNetworkServer(self):
        serviceUrl = r'ServicesAPI/networksetting/getAllNetworkServer'
        info = self._getUrl(CurrentMethodName(), serviceUrl, r'/domainAdmin.html')
        if len(info):
            PrintMessage(''.join([CurrentMethodName(), ' passed.']))
        else:
            PrintMessage(''.join([CurrentMethodName(), ' failed: ', json.dumps(info)]), 'Error')

        return info

    def _deviceAccessControlSetting(self):
        serviceUrl = r'ServicesAPI/AdvancedSettings/DeviceAccessControlSetting'
        info = self._getUrl(CurrentMethodName(), serviceUrl, r'/domainAdmin.html')
        if len(info):
            PrintMessage(''.join([CurrentMethodName(), ' passed.']))
        else:
            PrintMessage(''.join([CurrentMethodName(), ' failed: ', json.dumps(info)]), 'Error')

        return info

    def _getFrontServerRefDevice(self, fsID):
        serviceUrl = r'ServicesAPI/networksetting/getFrontServerRefDevice'
        payload = {
            'frontServerId': fsID,
            'searchKey': '',
            'pageIndex': 1,
            'pageCapacity': 50000
        }
        info = self._postUrl(CurrentMethodName(), serviceUrl, payload, r'/domainAdmin.html')
        if len(info):
            PrintMessage(''.join([CurrentMethodName(), ' passed.']))
        else:
            PrintMessage(''.join([CurrentMethodName(), ' failed: ', json.dumps(info)]), 'Error')

        return info

    def _getOnlineUsers(self):
        serviceUrl = r'ServicesAPI/Admin/User/GetOnlineUsers'
        info = self._getUrl(CurrentMethodName(), serviceUrl, r'/domainAdmin.html')
        if len(info):
            PrintMessage(''.join([CurrentMethodName(), ' passed.']))
        else:
            PrintMessage(''.join([CurrentMethodName(), ' failed: ', json.dumps(info)]), 'Error')

        return info

    def _getUserInfoMainUI(self):
        serviceUrl = r'ServicesAPI/Admin/User/GetUserInfo/mainUI'
        info = self._getUrl(CurrentMethodName(), serviceUrl, r'/domainAdmin.html')
        if len(info):
            PrintMessage(''.join([CurrentMethodName(), ' passed.']))
        else:
            PrintMessage(''.join([CurrentMethodName(), ' failed: ', json.dumps(info)]), 'Error')

        return info

    def _getCMSetting(self):
        serviceUrl = r'ServicesAPI/changemgmtsetting/getCMSetting'
        info = self._getUrl(CurrentMethodName(), serviceUrl, r'/domainAdmin.html')
        if len(info):
            PrintMessage(''.join([CurrentMethodName(), ' passed.']))
        else:
            PrintMessage(''.join([CurrentMethodName(), ' failed: ', json.dumps(info)]), 'Error')

        return info

    def _lastDiscoverSummaryInfo(self):
        serviceUrl = r'ServicesAPI/deviceManagement/lastDiscoverSummaryInfo'
        info = self._getUrl(CurrentMethodName(), serviceUrl, r'/domainAdmin.html')
        if len(info):
            PrintMessage(''.join([CurrentMethodName(), ' passed.']))
        else:
            PrintMessage(''.join([CurrentMethodName(), ' failed: ', json.dumps(info)]), 'Error')

        return info

    def _fineTuneSummaryInfo(self):
        serviceUrl = r'ServicesAPI/deviceManagement/fineTuneSummaryInfo'
        info = self._getUrl(CurrentMethodName(), serviceUrl, r'/domainAdmin.html')
        if len(info):
            PrintMessage(''.join([CurrentMethodName(), ' passed.']))
        else:
            PrintMessage(''.join([CurrentMethodName(), ' failed: ', json.dumps(info)]), 'Error')

        return info

    def _deviceCountList(self):
        serviceUrl = r'ServicesAPI/deviceManagement/deviceCountList'
        info = self._getUrl(CurrentMethodName(), serviceUrl, r'/domainAdmin.html')
        if len(info):
            PrintMessage(''.join([CurrentMethodName(), ' passed.']))
        else:
            PrintMessage(''.join([CurrentMethodName(), ' failed: ', json.dumps(info)]), 'Error')

        return info.get('deviceCountList', [])

    def discoveredDevicesByPaging(self, type):
        serviceUrl = r'ServicesAPI/deviceManagement/discoveredDevicesByPaging'
        payload = {
            'pageNumber': 0,
            'pageSize': 10000,
            'sortField': 'name',
            'sortOrder': 'asc',
            'filterFields': [
                'name',
                'mgmtIP',
                'devTypeName',
                'oid',
                'vendor',
                'model',
                'reason',
                'ftime',
                'ctime'
            ],
            'filter': '',
            'accessType': type,  # SNMP Only Devices: 2
            'reason': ''
        }
        info = self._pstUrl(CurrentMethodName(), payload, serviceUrl, r'/domainAdmin.html')
        if len(info):
            PrintMessage(''.join([CurrentMethodName(), ' passed.']))
        else:
            PrintMessage(''.join([CurrentMethodName(), ' failed: ', json.dumps(info)]), 'Error')

        return info  # .get('deviceList', [])

    def _getSiteSummaryInfo(self):
        serviceUrl = r'ServicesAPI/site/siteSummaryInfo'
        info = self._getUrl(CurrentMethodName(), serviceUrl, r'/domainAdmin.html')
        if len(info):
            PrintMessage(''.join([CurrentMethodName(), ' passed.']))
        else:
            PrintMessage(''.join([CurrentMethodName(), ' failed: ', json.dumps(info)]), 'Error')

        return info

    def _schedulerSummary(self):
        serviceUrl = r'ServicesAPI/scheduler/summary'
        info = self._getUrl(CurrentMethodName(), serviceUrl, r'/domainAdmin.html')
        if len(info):
            PrintMessage(''.join([CurrentMethodName(), ' passed.']))
        else:
            PrintMessage(''.join([CurrentMethodName(), ' failed: ', json.dumps(info)]), 'Error')

        return info

    def _getUserConfByUserId(self):
        serviceUrl = r'ServicesAPI/User/Config/getUserConfByUserId'
        payload = {
            "userId": self.UserID
        }
        info = self._postUrl(CurrentMethodName(), serviceUrl, payload, r'/domainAdmin.html')
        if len(info):
            PrintMessage(''.join([CurrentMethodName(), ' passed.']))
        else:
            PrintMessage(''.join([CurrentMethodName(), ' failed: ', json.dumps(info)]), 'Error')

        return info

    def ImportNetworkSetting(self, settingInfo):
        serviceUrl = r'ServicesAPI/networksetting/importNetworkSetting'
        encodeZip = ''
        with open(settingInfo['filePath'], 'rb') as f:
            encodeZip = base64.b64encode((f.read()))
        payload = {
            "info": encodeZip.decode(),
            "password": self.PasswordEncrypt(settingInfo['password'])
        }
        info = self._postUrl(CurrentMethodName(), serviceUrl, payload, r'/domainAdmin.html')
        if len(info):
            PrintMessage(''.join([CurrentMethodName(), ' passed.']))
        else:
            PrintMessage(''.join([CurrentMethodName(), ' failed: ', json.dumps(info)]), 'Error')
        self._getAllNetworkSetting()
        sleep(3)

        return info

    def ImportAPIServersV2(self, settingInfo):
        serviceUrl = r'ServicesAPI/externalAPIServer/importAPIServersV2'
        encodeZip = ''
        with open(settingInfo['filePath'], 'rb') as f:
            encodeZip = base64.b64encode((f.read()))
        payload = {
            "info": encodeZip.decode(),
            "password": self.PasswordEncrypt(settingInfo['password'])
        }
        info = self._postUrl(CurrentMethodName(), serviceUrl, payload, r'/domainAdmin.html')
        if len(info):
            PrintMessage(''.join([CurrentMethodName(), ' passed.']))
        else:
            PrintMessage(''.join([CurrentMethodName(), ' failed: ', json.dumps(info)]), 'Error')
        self._getAllAPIServers()
        sleep(3)
        return info

    def _getAllNetworkDef(self):
        serviceUrl = r'ServicesAPI/Admin/Domain/getAllNetworkDef'
        info = self._getUrl(CurrentMethodName(), serviceUrl, r'/domainAdmin.html')
        if len(info):
            PrintMessage(''.join([CurrentMethodName(), ' passed.']))
        else:
            PrintMessage(''.join([CurrentMethodName(), ' failed: ', json.dumps(info)]), 'Error')

        return info

    def _getAllAPIServers(self):
        serviceUrl = r'ServicesAPI/externalAPIServer/getAllAPIServers'
        info = self._getUrl(CurrentMethodName(), serviceUrl, '/domainAdmin.html')
        PrintMessage(''.join([CurrentMethodName(), ' passed.']))
        return info

    def GetExternalAPIServer(self):
        return self._getAllAPIServers()

    def ImportNetworkDefineTable(self, networkDefineTableFilePath):
        serviceUrl = r'ServicesAPI/Admin/Domain/upInsertNetworkDef'
        payload = list()
        with open(networkDefineTableFilePath) as csvFile:
            csvReader = csv.DictReader(csvFile)
            for row in csvReader:
                item = {
                    'ID': str(uuid.uuid4()),
                    'devNameExp': row['Hostname'],
                    'isRegx': row['Is Regular Match'],
                    'ipAddrRange': row['IP Address'],
                    'devSubTypeName': row['Device Type'],
                    'devSubType': row['Device Type ID'],
                    'devDriverName': row['Driver'],
                    'driverId': row['Driver ID']
                }
                payload.append(item)

        info = self._postUrl(CurrentMethodName(), serviceUrl, payload, r'/domainAdmin.html')
        if info:
            info = self._getAllNetworkDef()
            if len(info) >= len(payload):
                PrintMessage(''.join([CurrentMethodName(), ' passed. ']))
                return True
        PrintMessage(''.join([CurrentMethodName(), ' failed: ', json.dumps(info)]), 'Error')

        return info

    def UpdateTelnetInfo(self, telnetInfo):
        serviceUrl = r'ServicesAPI/networksetting/updateTelnetInfo'
        payload = {
            "ID": telnetInfo['Username'],
            "alias": telnetInfo['Alias'],
            "cliMode": 0,
            "userName": telnetInfo['Username'],
            "password": self.PasswordEncrypt(telnetInfo['Password']),
            "sshKeyID": '',
            "refCount": 0,
            "order": 0,
            "isChangePassword": False
        }
        info = self._postUrl(CurrentMethodName(), serviceUrl, payload, r'/domainAdmin.html')
        if info['result']:
            PrintMessage(''.join([CurrentMethodName(), ' passed. ']))
        else:
            PrintMessage(''.join([CurrentMethodName(), ' failed. ', json.dumps(info)]), 'Error')

        return info

    def UpdateEnablePasswd(self, enablePasswordInfo):
        serviceUrl = r'ServicesAPI/networksetting/updateEnablePasswd'
        payload = {
            "ID": enablePasswordInfo['Username'],
            "alias": enablePasswordInfo['Alias'],
            "enableUserName": enablePasswordInfo['Username'],
            "enablePassword": self.PasswordEncrypt(enablePasswordInfo['Password']),
            "refCount": 0,
            "order": 0,
            "isChangePassword": False
        }
        info = self._postUrl(CurrentMethodName(), serviceUrl, payload, r'/domainAdmin.html')
        if info['result']:
            PrintMessage(''.join([CurrentMethodName(), ' passed. ']))
        else:
            PrintMessage(''.join([CurrentMethodName(), ' failed. ', json.dumps(info)]), 'Error')

        return info

    def UpdateSnmpRoInfo(self, snmpRoInfoInfo):
        serviceUrl = r'ServicesAPI/networksetting/updateSnmpRoInfo'
        payload = {
            "ID": snmpRoInfoInfo['SNMP Read Only Community String'],
            "alias": snmpRoInfoInfo['Alias'],
            "snmpPort": 0,
            "roString": snmpRoInfoInfo['SNMP Read Only Community String'],
            "snmpVersion": 1,
            "v3": {"encryptPassword": "", "userName": "", "authPro": 1, "authMode": 1, "encryptPro": 1,
                   "authPassword": "", "contextName": "", "isChangeAuthPassword": False,
                   "isChangeEncryptPassword": False},
            "refCount": 0,
            "order": 0
        }
        if self.CurrentVersion >= 8.03:
            payload.update({"isChangeRoString": False, "roConfirmString": payload['roString'],
                            "roString": self.PasswordEncrypt(payload['roString'])})
        info = self._postUrl(CurrentMethodName(), serviceUrl, payload, r'/domainAdmin.html')
        if info['result']:
            PrintMessage(''.join([CurrentMethodName(), ' passed. ']))
        else:
            PrintMessage(''.join([CurrentMethodName(), ' failed. ', json.dumps(info)]), 'Error')

        return info

    def _removeElement(self, elementInfo):
        serviceUrl = r'ServicesAPI/networksetting/removeElement'
        info = self._postUrl(CurrentMethodName(), serviceUrl, elementInfo, r'/domainAdmin.html')
        return info

    def DeleteTelnetInfo(self, name):
        item = {'tab': 'TelnetInfo', 'strGuid': [name]}
        info = self._removeElement(item)
        return info

    def DeleteEnablePasswd(self, name):
        item = {'tab': 'EnablePassword', 'strGuid': [name]}
        info = self._removeElement(item)
        return info

    def DeleteSnmpRoInfo(self, name):
        item = {'tab': 'SnmpRoInfo', 'strGuid': [name]}
        info = self._removeElement(item)
        return info

    def DeleteAPIServer(self, apiServerID):
        serviceUrl = r'ServicesAPI/externalAPIServer/deleteAPIServer'
        payload = [apiServerID]
        info = self._postUrl(CurrentMethodName(), serviceUrl, payload, r'/domainAdmin.html')
        return info

    def _getAllDeviceTypes(self):
        serviceUrl = r'ServicesAPI/SystemModel/getAllDeviceTypes'
        info = self._getUrl(CurrentMethodName(), serviceUrl, r'/domainAdmin.html')
        if len(info):
            PrintMessage(''.join([CurrentMethodName(), ' passed.']))
        else:
            PrintMessage(''.join([CurrentMethodName(), ' failed: ', json.dumps(info)]), 'Error')

        return info

    def _getDiscoverSummaryLogByTaskId(self, taskID, timeOut=3600):
        serviceUrl = r'ServicesAPI/discovery/getDiscoverSummaryLogByTaskId/0/' + taskID
        tick = 0
        sleepTime = 90
        while True:
            info = self._getUrl(CurrentMethodName(), serviceUrl, r'/domainAdmin.html')
            if info.get('isFinished', False):
                break;
            log = info.get('log', '')
            if log != '':
                print(log, info['statusLog'])
            sleep(sleepTime)
            tick += sleepTime
            if tick >= timeOut:
                PrintMessage(''.join([CurrentMethodName(), ' timeout. ', info]), 'Warning')
                return {}
        PrintMessage(''.join([CurrentMethodName(), ' passed. ']))

        return info

    def _licenseDetailsResult(self):
        serviceUrl = r'ServicesAPI/system/domain/licenseDetailsResult'
        payload = {
            "tenantId": self.TenantID,
            "domainId": self.DomainID
        }
        info = self._postUrl(CurrentMethodName(), serviceUrl, payload, r'/domainAdmin.html')
        PrintMessage(''.join([CurrentMethodName(), ' passed. ']))

        return info

    def _getDiscoverResultByTaskId(self, taskID):
        serviceUrl = r'ServicesAPI/discovery/getDiscoverResultByTaskId'
        payload = {
                'taskId': taskID,
                'pageSize': 50000,
                'pageNumber': 0
            }
        info = self._postUrl(CurrentMethodName(), serviceUrl, payload, r'/domainAdmin.html')
        if len(info):
            PrintMessage(''.join([CurrentMethodName(), ' passed. ']))
        else:
            PrintMessage(''.join([CurrentMethodName(), ' failed. ', json.dumps(info)]), 'Error')

        return info

    def StartDiscover(self, discoverInfo):
        '''
        discoverOptionEnum = {
            ViaProxy: 2,
            ViaLocal: 4,
            GetCdpTable: 8,
            GetRoutingTable: 16,
            // 'ScanAfterDiscover': 32,
            FindRPNViaSnmp: 64,
            ScanDestinationSubnet: 128,
            ScanAllConnectedSubnet: 256,
            GetDeviceInfo: 512,
            GetInterfaceInfo: 1024,
            RunAdditionalOperation: 2048
            //Rebuild: 2048, ??? not used, removed
            //Rebuild2: 4096 ??? not used, removed
            };
        :param discoverInfo:
        :return:
        '''
        serviceUrl = r'ServicesAPI/discovery/startDiscover'
        discoverTaskID = CreateGuid()
        currenttime = datetime.utcnow().strftime(r'%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        fromScan = discoverInfo.get('Scan IP Range', False)
        hostips = discoverInfo['HostIPs']
        if type(hostips) is list:
            hostips = list(filter(None, hostips))
        else:
            with open(hostips, 'r') as txtFile:
                hostips = list(filter(None, txtFile.read().split(';')))
        allNetworkSetting = self._getAllNetworkSetting()
        networkServer = discoverInfo.get('Front Server', None)
        if networkServer is not None and len(networkServer) == 0:
            # networkServer = list()
            for item in allNetworkSetting.get('networkServer', []):
                networkServer.append(item['id'])
        telnetInfo = discoverInfo.get('Telnet/SSH Login', None)
        if telnetInfo is not None and len(telnetInfo) == 0:
            # telnetInfo = list()
            for item in allNetworkSetting.get('telnetInfo', []):
                telnetInfo.append(item['ID'])
        enablePasswd = discoverInfo.get('Privilege Login', [])
        if enablePasswd is not None and len(enablePasswd) == 0:
            # enablePasswd = list()
            for item in allNetworkSetting.get('enablePasswd', []):
                enablePasswd.append(item['ID'])
        snmpRoInfo = discoverInfo.get('SNMP String', None)
        if snmpRoInfo is not None and len(snmpRoInfo) == 0:
            # snmpRoInfo = list()
            for item in allNetworkSetting.get('snmpRoInfo', []):
                snmpRoInfo.append(item['ID'])
        sshPrivateKey = discoverInfo.get('Private Key', [])
        if sshPrivateKey is not None and len(sshPrivateKey) == 0:
            # sshPrivateKey = list()
            for item in allNetworkSetting.get('sshPrivateKey', []):
                sshPrivateKey.append(item['ID'])
        jumpbox = discoverInfo.get('Jumpbox', [])
        if jumpbox is not None and len(jumpbox) == 0:
            # jumpbox = list()
            for item in allNetworkSetting.get('jumpbox', []):
                jumpbox.append(item['ID'])
        payload = {
            "_id": discoverTaskID,
            "startTime": currenttime,
            "srcType": "ondemand discover task",
            "discoverOption": {
                "useAllNap": True, "discoverOption": 90, "snmpIfPingFailed": True, "snmpOnly": False,
                "telnetIfPingFailed": False, "updateDeviceSetting": True, "pingTimeout": 2, "pingTryTimes": 2,
                "jumpboxOnly": False, "skipPing": False, "pollingOrder": 3,
                "fromScan": fromScan,
                "accessOrder": DiscoverAccessOrder.index(discoverInfo.get('Access Mode', 'SNMP and Telnet/SSH')),
                "maxDepth": discoverInfo.get('Discovery Depth', 0),
                "domainOption": 1, "domainName": "", "scanMaskLength": 24, "cliForceTimeout": 600,
                "discoverInfo": {
                    "proxy": "", "orignalProxy": "", "comefrom": "", "comefromMask": "", "ifname": "", "desc": "",
                    "depth": 0, "ipSrc": 0, "subnetList": []
                },
                "hostips": hostips,
                "isAllDevices": False, "limitRunTimeMinutes": 0,
                "checkedObjs": {
                    "networkServer": networkServer, "sshPrivateKey": sshPrivateKey, "jumpbox": jumpbox,
                    "telnetInfo": telnetInfo, "enablePasswd": enablePasswd, "snmpRoInfo": snmpRoInfo
                }
            },
            "pluginExecPoints": []
        }
        if self.CurrentVersion >= 8.03:
            payload['discoverOption']['discoverOption'] = 2138
            payload['discoverOption']['apiServers'] = discoverInfo.get('apiServers', [])
        else:
            payload['discoverOption']['discoverOption'] = 90
        info = self._postUrl(CurrentMethodName(), serviceUrl, payload, r'/domainAdmin.html')
        info['DiscoverTaskID'] = discoverTaskID
        # PrintJsonObject(info)
        if info.get('result', False):
            self._getDiscoverSummaryLogByTaskId(discoverTaskID)
            self._licenseDetailsResult()
            PrintMessage(''.join([CurrentMethodName(), ' passed. ']))
            return discoverTaskID
        else:
            PrintMessage(''.join([CurrentMethodName(), ' failed. ', json.dumps(info)]), 'Error')
            return ''

    def DeviceIPtoID(self, deviceIPs):
        if type(deviceIPs) is str:
            with open(deviceIPs, 'r') as f:
                deviceIDs = f.read()  # list(filter(None, f.read().split(';')))
        else:
            deviceIDs = ';'.join(id for id in deviceIPs)
        # info = self._getAllDevicesByPaging(255, '31.31.0.1')
        info = self._calcDySearchDevice(deviceIDs)
        return info

    def SaveDeviceGroup(self, groupInfo, discoverTaskID=''):
        serviceUrl = r'ServicesAPI/DeviceGroup/SaveDeviceGroup/false'
        deviceGroupNames = self._getAllDeviceGroupInfo()
        name = groupInfo['Name']
        item = self._getJsonObject(deviceGroupNames, 'Name', name)
        if len(item):
            groupID = item['ID']
            PrintMessage(''.join(['The name of device group "', name, '" is existed.']), "Warning")
        else:
            groupID = CreateGuid()
        allItems = list()
        if discoverTaskID != '':
            deviceIDs = self._getDiscoverResultByTaskId(discoverTaskID)
            deviceCount = 0
            for item in deviceIDs:
                config = item.get('tuneState', {}).get('config', '')
                if config.startswith('Succeeded'):
                    deviceID = item.get('deviceId', '')
                    if deviceID != '':
                        allItems.append({'ID': deviceID, 'type': 'Static'})
        else:
            deviceIDs = groupInfo.get('DeviceID', [])
            deviceCount = groupInfo.get('DeviceCount', 0)
            # info = self._getAllDevicesByPaging(255, '31.31.0.1')
            info = self.DeviceIPtoID(deviceIDs)
            for item in info:
                deviceID = item.get('ID', '')
                if deviceID != '':
                    allItems.append({'ID': deviceID, 'type': 'Static'})
        payload = {
            'ID': groupID,
            'Name': name,
            'Description': groupInfo['Description'],
            'UserGuid': self.UserID,
            'HasInterface': True,
            'AutoLink': False,
            'Type': DeviceGroupType.index(groupInfo.get('Type', 'Public')),
            'RangeOption': 0,
            'DeviceGroupRange': [],
            'SiteRange': [],
            'Filter': {'Expression': '', 'Conditions': []},
            'DynamicInterfaceCondition': {
                'DeviceCondition': {
                    'Scope': {'RangeOption': 0, 'DeviceGroupRange': [], 'SiteRange': []},
                    'Filter': {'Expression': '', 'Conditions': []}
                },
                'InterfaceFilter': {'Expression': '', 'Conditions': []}
            },
            'AllItems': allItems
        }
        if deviceCount <= 0:
            self._postUrl(CurrentMethodName(), serviceUrl, payload, '/domainAdmin.html')
            item = len(allItems)
            if item > 0:
                PrintMessage(''.join([CurrentMethodName(), ' passed. Device group name is ', name,
                                      ', the count of devices is ', str(item), '. The first ID is ',
                                      allItems[0]['ID'], '.']))
            else:
                PrintMessage(''.join([CurrentMethodName(), ' completed. Device group name is ', name,
                                      ', the count of devices is ', str(item), '.']), 'Warning')
        else:
            deviceGroupCount = groupInfo.get('DeviceGroupCount', 1)
            index = 1
            indexFrom = 0
            while indexFrom < deviceGroupCount:
                indexTo = indexFrom + deviceCount
                name = groupInfo['Name'] + f'{index:05}'
                item = self._getJsonObject(deviceGroupNames, 'Name', name)
                if len(item):
                    groupID = item['ID']
                    PrintMessage(''.join(['The name of device group "', name, '" is existed.']), "Warning")
                else:
                    groupID = CreateGuid()
                payload['ID'] = groupID
                payload['Name'] = name
                payload['AllItems'] = allItems[indexFrom:indexTo]
                self._postUrl(CurrentMethodName(), serviceUrl, payload, '/domainAdmin.html')
                item = len(payload['AllItems'])
                if item > 0:
                    PrintMessage(''.join([CurrentMethodName(), ' passed. Device group name is ', name,
                                          ', the count of devices is ', str(item), '. The first ID is ',
                                          allItems[0]['ID'], '.']))
                else:
                    PrintMessage(''.join([CurrentMethodName(), ' passed. Device group name is ', name,
                                          ', the count of devices is ', str(item), '.']), 'Warning')
                index += 1
                indexFrom += deviceCount
        return True

    def setDataCleanOption(self, data_engine_data:dict):
        serviceUrl = r'ServicesAPI/dataEngine/setDataCleanOption'
        payload = {
            'ID': 'DataEngineClean',
            'jobId': '',
            'shrink': {
                'checked': True,
                'keepMonth': data_engine_data['Keep Data Month'],
                'keepCount': data_engine_data['Keep Data Point']
            },
            'remove': {
                'checked': True,
                'keepMonth': data_engine_data['Delete Data Month']
            },
            'operateInfo': {
                'opUserId': self.UserID,
                'opUser': self.Username,
                'opTime': NetBrainUtils.GetDateTimeString()
            }
        }
        info = self._postUrl(CurrentMethodName(), serviceUrl, payload, r'/domainAdmin.html')

        PrintMessage(''.join([CurrentMethodName(), ' passed. ' if info else ' failed']))

        return info

    def DataCleanOption(self, other_data:dict):
        serviceUrl = r'ServicesAPI/GlobalDataClean'
        unit = ['days', 'weeks', 'months']
        current_time = NetBrainUtils.GetDateTimeString()
        payload = [
            {
                'id': 'QappExecutionLog',
                'name': 'Qapp/Gapp Execution Logs',
                'description': '',
                'order': 1,
                'supportDataSize': False,
                'rules': [
                    {
                        'amount': other_data['Qapp/Gapp Execution Logs']['Value'],
                        'unit': unit.index(other_data['Qapp/Gapp Execution Logs']['Unit'].lower()),
                        'supportedUnits': [
                            0,
                            1,
                            2
                        ],
                        'enabled': other_data['Qapp/Gapp Execution Logs']['Enabled'],
                        'type': 0
                    }
                ],
                'operateInfo': {
                    'opUser': 'NetBrain',
                    'opTime': current_time
                }
            },
            {
                'id': 'OneIPTableEntry',
                'name': 'One-IP Table Entries',
                'description': '',
                'order': 2,
                'supportDataSize': True,
                'rules': [
                    {
                        'amount': other_data['One-IP Table Entries']['Value'],
                        'unit': unit.index(other_data['One-IP Table Entries']['Unit'].lower()),
                        'supportedUnits': [
                            0,
                            1,
                            2
                        ],
                        'enabled': other_data['One-IP Table Entries']['Enabled'],
                        'type': 0
                    }
                ],
                'operateInfo': {
                    'opUser': 'NetBrain',
                    'opTime': current_time
                }
            },
            {
                'id': 'DiscoverBenchmarkTaskLogs',
                'name': 'Discovery/Benchmark Logs',
                'description': 'The deleted logs for a discovery task include: Execution Logs, Device Logs, Report and Plugin Logs.\r\nThe deleted logs for a benchmark task include: Execution Logs, Device Logs and Plugin Logs.',
                'order': 3,
                'supportDataSize': False,
                'rules': [
                    {
                        'amount': other_data['Discovery/Benchmark Logs']['Value'],
                        'unit': unit.index(other_data['Discovery/Benchmark Logs']['Unit'].lower()),
                        'supportedUnits': [
                            0,
                            1,
                            2
                        ],
                        'enabled': other_data['Discovery/Benchmark Logs']['Enabled'],
                        'type': 0
                    }
                ],
                'operateInfo': {
                    'opUser': 'NetBrain',
                    'opTime': current_time
                }
            },
            {
                'id': 'AAMPathData',
                'name': 'Application Path History Data',
                'description': '',
                'order': 4,
                'supportDataSize': False,
                'rules': [
                    {
                        'amount': other_data['Application Path History Data']['Value'],
                        'unit': unit.index(other_data['Application Path History Data']['Unit'].lower()),
                        'supportedUnits': [
                            0,
                            1,
                            2
                        ],
                        'enabled': other_data['Application Path History Data']['Enabled'],
                        'type': 0
                    }
                ],
                'operateInfo': {
                    'opUser': 'NetBrain',
                    'opTime': current_time
                }
            },
            {
                'id': 'DataUnitStorage',
                'name': 'Data Unit Storage',
                'description': 'Clear the (data view) data generated by Qapps being executed in the Shedule Qapp, Dashboard and Map functions.',
                'order': 5,
                'supportDataSize': True,
                'rules': [
                    {
                        'amount': other_data['Data Unit Storage']['Value'],
                        'unit': unit.index(other_data['Data Unit Storage']['Unit'].lower()),
                        'supportedUnits': [
                            0,
                            1,
                            2
                        ],
                        'enabled': other_data['Data Unit Storage']['Enabled'],
                        'type': 0
                    },
                    {
                        'amount': 1,
                        'unit': 1,
                        'supportedUnits': [
                            0,
                            1,
                            2
                        ],
                        'enabled': True,
                        'type': 1
                    },
                    {
                        'keepCount': 8640,
                        'enabled': True,
                        'type': 2
                    }
                ],
                'operateInfo': {
                    'opUser': 'NetBrain',
                    'opTime': current_time
                }
            },
            {
                'id': 'BenchmakBackupMap',
                'name': 'Backup Maps',
                'description': '',
                'order': 6,
                'supportDataSize': True,
                'rules': [
                    {
                        'amount': other_data['Backup Maps']['Value'],
                        'unit': unit.index(other_data['Backup Maps']['Unit'].lower()),
                        'supportedUnits': [
                            0,
                            1,
                            2
                        ],
                        'enabled': other_data['Backup Maps']['Enabled'],
                        'type': 0
                    }
                ]
            },
            {
                'id': 'APITriggerTask',
                'name': 'API Triggered Automation Task',
                'description': '',
                'order': 7,
                'supportDataSize': False,
                'rules': [
                    {
                        'amount': other_data['API Triggered Automation Task']['Value'],
                        'unit': unit.index(other_data['API Triggered Automation Task']['Unit'].lower()),
                        'supportedUnits': [
                            0,
                            1,
                            2
                        ],
                        'enabled': other_data['API Triggered Automation Task']['Enabled'],
                        'type': 0
                    }
                ],
                'operateInfo': {
                    'opUser': 'NetBrain',
                    'opTime': current_time
                }
            },
            {
                'id': 'TriggeredIncident',
                'name': 'Triggered Incidents',
                'description': '',
                'order': 8,
                'supportDataSize': False,
                'rules': [
                    {
                        'amount': other_data['Triggered Incidents']['Value'],
                        'unit': unit.index(other_data['Triggered Incidents']['Unit'].lower()),
                        'supportedUnits': [
                            0,
                            1,
                            2
                        ],
                        'enabled': other_data['Triggered Incidents']['Enabled'],
                        'type': 0
                    }
                ],
                'operateInfo': {
                    'opUser': 'NetBrain',
                    'opTime': current_time
                }
            },
            {
                'id': 'EventConsoleEntry',
                'name': 'Event Entries in Event Console',
                'description': '',
                'order': 9,
                'supportDataSize': True,
                'rules': [
                    {
                        'amount': other_data['Event Entries in Event Console']['Value'],
                        'unit': unit.index(other_data['Event Entries in Event Console']['Unit'].lower()),
                        'supportedUnits': [
                            0,
                            1,
                            2
                        ],
                        'enabled': other_data['Event Entries in Event Console']['Enabled'],
                        'type': 0
                    }
                ],
                'operateInfo': {
                    'opUser': 'NetBrain',
                    'opTime': current_time
                }
            },
            {
                'id': 'ScheduleDVTLog',
                'name': 'Execution Logs for Scheduled Data View Template & Parser Tasks',
                'description': '',
                'order': 10,
                'supportDataSize': False,
                'rules': [
                    {
                        'amount': other_data['Execution Logs for Scheduled Data View Template & Parser Tasks']['Value'],
                        'unit': unit.index(other_data['Execution Logs for Scheduled Data View Template & Parser Tasks']['Unit'].lower()),
                        'supportedUnits': [
                            0,
                            1,
                            2
                        ],
                        'enabled': other_data['Execution Logs for Scheduled Data View Template & Parser Tasks']['Enabled'],
                        'type': 0
                    }
                ],
                'operateInfo': {
                    'opUser': 'NetBrain',
                    'opTime': current_time
                }
            },
            {
                'id': 'DashboardActivityDataTable',
                'name': 'Dashboard Activity Data Table',
                'description': 'Activity data table refers to the device data tables generated by running a Qapp in a Dashboard widget.<br/>By default, the data tables older than 30 days will be deleted, which means only the data tables in the latest 30 days can be archived for each Dashboard.',
                'order': 11,
                'supportDataSize': False,
                'rules': [
                    {
                        'amount': other_data['Dashboard Activity Data Table']['Value'],
                        'unit': unit.index(other_data['Dashboard Activity Data Table']['Unit'].lower()),
                        'supportedUnits': [
                            0,
                            1,
                            2
                        ],
                        'enabled': other_data['Dashboard Activity Data Table']['Enabled'],
                        'type': 0
                    }
                ],
                'operateInfo': {
                    'opUser': 'NetBrain',
                    'opTime': current_time
                }
            },
            {
                'id': 'CompareResults',
                'name': 'Compare Results',
                'description': '',
                'order': 12,
                'supportDataSize': False,
                'rules': [
                    {
                        'amount': other_data['Compare Results']['Value'],
                        'unit': unit.index(other_data['Compare Results']['Unit'].lower()),
                        'supportedUnits': [
                            0,
                            1,
                            2
                        ],
                        'enabled': other_data['Compare Results']['Enabled'],
                        'type': 0
                    }
                ],
                'operateInfo': {
                    'opUser': 'NetBrain',
                    'opTime': current_time
                }
            },
            {
                'id': 'ThirdPartyFlashAlert',
                'name': 'Third Party Flash Alert',
                'description': 'Third Party Flash Alert',
                'order': 13,
                'supportDataSize': False,
                'rules': [
                    {
                        'amount': other_data['Third Party Flash Alert']['Value'],
                        'unit': unit.index(other_data['Third Party Flash Alert']['Unit'].lower()),
                        'supportedUnits': [
                            0,
                            1,
                            2
                        ],
                        'enabled': other_data['Third Party Flash Alert']['Enabled'],
                        'type': 0
                    }
                ],
                'operateInfo': {
                    'opUser': 'NetBrain',
                    'opTime': current_time
                }
            },
            {
                'id': 'FIDExecutionLog',
                'name': 'Feature Intent Template Execution Logs',
                'description': 'Feature Intent Template Execution Logs',
                'order': 14,
                'supportDataSize': True,
                'rules': [
                    {
                        'amount': other_data['Feature Intent Template Execution Logs']['Value'],
                        'unit': unit.index(other_data['Feature Intent Template Execution Logs']['Unit'].lower()),
                        'supportedUnits': [
                            0,
                            1,
                            2
                        ],
                        'enabled': other_data['Feature Intent Template Execution Logs']['Enabled'],
                        'type': 0
                    }
                ],
                'operateInfo': {
                    'opUser': 'NetBrain',
                    'opTime': current_time
                }
            },
            {
                'id': 'AdaptivePollingFlashAlert',
                'name': 'Adaptive Polling Result and Flash Alert',
                'description': '',
                'order': 15,
                'supportDataSize': True,
                'rules': [
                    {
                        'amount': other_data['Adaptive Polling Result and Flash Alert']['Value'],
                        'unit': unit.index(other_data['Adaptive Polling Result and Flash Alert']['Unit'].lower()),
                        'supportedUnits': [
                            0,
                            1,
                            2
                        ],
                        'enabled': other_data['Adaptive Polling Result and Flash Alert']['Enabled'],
                        'type': 0
                    }
                ],
                'operateInfo': {
                    'opUser': 'NetBrain',
                    'opTime': current_time
                }
            }
        ]
        info = self._postUrl(CurrentMethodName(), serviceUrl, payload, r'/domainAdmin.html')
        PrintMessage(''.join([CurrentMethodName(), ' completed. ']))

        return True

    # domain end

    # Device Group start
    def _getAllDeviceGroupInfo(self):
        serviceUrl = r'ServicesAPI/DeviceGroup/getAllDeviceGroupInfo/true'
        info = self._getUrl(CurrentMethodName(), serviceUrl)
        PrintMessage(''.join([CurrentMethodName(), ' passed.']))

        return info

    def _getDeviceGroupInfo(self):
        serviceUrl = r'ServicesAPI/DeviceGroup/DeviceGroupInfo'
        info = self._postUrl(CurrentMethodName(), serviceUrl, {}, '/domainAdmin.html')
        if len(info):
            PrintMessage(''.join([CurrentMethodName(), ' passed.']))
        else:
            PrintMessage(''.join([CurrentMethodName(), ' failed: ', json.dumps(info)]), 'Error')

        return info

    def _deleteDeviceGroupByGuid(self, groupID, deleteAll=False):
        serviceUrl = r'ServicesAPI/DeviceGroup/deleteDeviceGroupByGuid'
        payload = {
                'deleteAllDevicesFromDomain': deleteAll,
                'deviceGroupGuid': groupID
            }
        info = self._postUrl(CurrentMethodName(), serviceUrl, payload, r'/desktop.html')
        if info:
            PrintMessage(''.join([CurrentMethodName(), ' passed. ']))
        else:
            PrintMessage(''.join([CurrentMethodName(), ' failed. ', json.dumps(info)]), 'Error')

    def DeleteDeviceGroup(self, groupNames, deleteAll=False):
        groups = self._getAllDeviceGroupInfo()
        for name in groupNames:
            item = self._getJsonObject(groups, 'Name', name)
            if len(item):
                self._deleteDeviceGroupByGuid(item['ID'], True)

        return True

    def _getAllTechnologySpecs(self):
        serviceUrl = r'ServicesAPI/visualspace/getAllTechnologySpecs'
        info = self._getUrl(CurrentMethodName(), serviceUrl)
        if len(info):
            PrintMessage(''.join([CurrentMethodName(), ' passed.']))
        else:
            PrintMessage(''.join([CurrentMethodName(), ' failed: ', json.dumps(info)]), 'Error')

        return info

    def _getBuildInRunBookActions(self):
        serviceUrl = r'ServicesAPI/runbook/actionfavorite/getBuildInRunBookActions'
        info = self._getUrl(CurrentMethodName(), serviceUrl)
        if len(info):
            PrintMessage(''.join([CurrentMethodName(), ' passed.']))
        else:
            PrintMessage(''.join([CurrentMethodName(), ' failed: ', json.dumps(info)]), 'Error')

        return info

    def _getDevicesAndInterfacesByCondition(self, condition):
        serviceUrl = r'ServicesAPI/DeviceGroup/DevicesAndInterfacesByCondition'
        payload = {
            'filterContent': '',
            'filterField': 'name',
            'guid': condition.get('GroupGuid', ''),
            'pageNumber': 1,
            'pageSize': condition.get('PageSize', 50000),  # 50,
            'sortField': condition.get('Sort', 'name'),  # 'name',
            'sortOrder': condition.get('SortOrder', 'ASC'),  # 'ASC'
        }
        info = self._postUrl(CurrentMethodName(), serviceUrl, payload)
        if len(info):
            PrintMessage(''.join([CurrentMethodName(), ' passed.']))
        else:
            PrintMessage(''.join([CurrentMethodName(), ' failed: ', json.dumps(info)]), 'Error')

        return info

    def _isMapExist(self, groupGuid):
        serviceUrl = r'ServicesAPI/map/isMapExist/' + groupGuid
        info = self._postUrl(CurrentMethodName(), serviceUrl, {})
        if len(info):
            PrintMessage(''.join([CurrentMethodName(), ' passed.']))
        else:
            PrintMessage(''.join([CurrentMethodName(), ' failed: ', json.dumps(info)]), 'Error')

        return info

    def _getSystemMapByKey(self, groupGuid):
        serviceUrl = ''.join([r'ServicesAPI/map/getSystemMapByKey/', groupGuid, '/4/false'])
        info = self._postUrl(CurrentMethodName(), serviceUrl, {})
        if len(info):
            PrintMessage(''.join([CurrentMethodName(), ' passed.']))
        else:
            PrintMessage(''.join([CurrentMethodName(), ' failed: ', json.dumps(info)]), 'Error')

        return info

    def _getAllDevicesByPaging(self, pageSize=100, filterContent=''):
        serviceUrl = r'ServicesAPI/DataModel/getAllDevicesByPaging'
        payload = {
            'pageSize': pageSize,
            'pageNumber': 0,
            'filterFields': ['name', 'mgmtIP', 'model', 'vendor'],
            'filterContent': filterContent,
            'isNeedSdnDevice': True,
            'sortField': 'name',
            'sortOrder': 'asc'
        }
        info = self._postUrl(CurrentMethodName(), serviceUrl, payload)
        if len(info):
            PrintMessage(''.join([CurrentMethodName(), ' passed.']))
        else:
            PrintMessage(''.join([CurrentMethodName(), ' failed: ', json.dumps(info)]), 'Error')

        return info

    def _calcDySearchDevice(self, deviceIPs=[]):
        serviceUrl = r'ServicesAPI/DataModel/calcDySearchDevice'
        payload = {
            'RangeOption': 0,
            'DeviceGroupRange': [],
            'SiteRange': [],
            'Filter': {
                'Expression': 'A',
                'Conditions': [
                    {'Operator': 0, 'Expression': deviceIPs, 'Schema': 'mgmtIP'}
                ]
            }
        }
        info = self._postUrl(CurrentMethodName(), serviceUrl, payload)
        if len(info):
            PrintMessage(''.join([CurrentMethodName(), ' passed.']))
        else:
            PrintMessage(''.join([CurrentMethodName(), ' failed: ', json.dumps(info)]), 'Error')

        return info

    # Device Group end

    # Schedule Task start
    def _getDiscoveryBenchmarkDefinition(self, name='', isDiscovery=True):
        info = self._getAllBenchmarkDefinitions()
        if name:
            definitionInfo = self._getJsonObject(info, 'name', name)
        if len(definitionInfo) <= 0: # new
            startDate = str(datetime.today().date())
            endDate = str((datetime.today() + timedelta(days=1)).date())
            strNow = GetDateTimeString()
            id = CreateGuid()
            if isDiscovery:
                defaultDefinitionInfo = self._getJsonObject(info, 'name', 'Scheduled System Discovery')
            else:
                defaultDefinitionInfo = self._getJsonObject(info, 'name', 'Basic System Benchmark')
            definitionInfo = {
                'ID': id,
                'name': name,
                'description': '',
                'isEnable': True,
                'isEnableDisplay': 'Enable',
                'jobId': id,
                '$isNew': False,
                'author': self.Username,
                'currentRunStatus': '',
                'currentStatusDisplay': '',
                'lastResultDisplay': '',
                'lastResultHasError': False,
                'lastRunStatus': '',
                'lastRunTime': '0001-01-01T00:00:00',
                'lastRunTimeDisplay': '',
                'lastRunTimeSpan': '00:00:00',
                'lastRunTimeSpanDisplay': '',
                'nextRunTime': '3000-01-02T00:00:00-05:00',
                'rangeOptionDisplay': 'All Devices',
                'showStopButton': True,
                'schedule': {
                    'start': ''.join([startDate, 'T05:00:01.285Z']),
                    'frequency': defaultDefinitionInfo['schedule']['frequency'],
                    'end': ''.join([endDate, 'T04:59:01.285Z']),
                    'enableEnd': False,
                    'timeZone': defaultDefinitionInfo['schedule']['timeZone'],
                    'startDate': startDate,
                    'endDate': endDate
                },
                'sendEmailInfo': defaultDefinitionInfo.get('sendEmailInfo', {}),
                'operateInfo': {
                    'opTime': strNow,
                    'opUser': self.Username,
                    'operateTime': strNow,
                    'operateUserName': self.Username
                },
                'pluginExecPoints':[]
            }
            if isDiscovery:
                definitionInfo['type'] = 1 #defaultDefinitionInfo['type'], # 0: Benchmark, 1: Discovery
                definitionInfo['typeDisplay'] = 'Discovery Task'
                definitionInfo['discoverOption'] = {} #defaultDefinitionInfo['discoverOption']
            else:
                process = defaultDefinitionInfo['retrieveOption']['additionalProcess']['process'][:13]
                for item in process:
                    item['isChecked'] = False
                definitionInfo['type'] = 0 #defaultDefinitionInfo['type'], # 0: Benchmark, 1: Discovery
                definitionInfo['typeDisplay'] = 'Benchmark Task'
                definitionInfo['retrieveOption'] = {
                    'devScope': {
                        'isRetrieveLegacy': True,
                        'scopeType': 0, # 0: AllDevices, 1: Device Group, 2: Site
                        'scopeRange': [],
                        'excludedDeviceGroups': None},
                    'retrieveData':{},
                    'retrieveParam': defaultDefinitionInfo['retrieveOption']['retrieveParam'],
                    'additionalProcess': {'process': process},
                    'sdnScope': {'isRetrieveSDN': False, 'isSelectAllController': False, 'scopeRange': []},
                    'scheduleTasks': []
                }
        return definitionInfo

    def _getAllBenchmarkDefinitions(self):
        serviceUrl = r'ServicesAPI/snapshot/getAllBenchmarkDefinitions'
        info = self._getUrl(CurrentMethodName(), serviceUrl, '/domainAdmin.html')
        if len(info):
            PrintMessage(''.join([CurrentMethodName(), ' passed.']))
        else:
            PrintMessage(''.join([CurrentMethodName(), ' failed: ', json.dumps(info)]), 'Error')
        return info

    def _getTimeZones(self):
        serviceUrl = r'ServicesAPI/scheduleqapps/timezones'
        info = self._getUrl(CurrentMethodName(), serviceUrl, '/domainAdmin.html')
        if len(info):
            PrintMessage(''.join([CurrentMethodName(), ' passed.']))
        else:
            PrintMessage(''.join([CurrentMethodName(), ' failed: ', json.dumps(info)]), 'Error')
        return info

    def _getWebServerTimeZone(self):
        serviceUrl = r'ServicesAPI/snapshot/getWebServerTimeZone'
        info = self._getUrl(CurrentMethodName(), serviceUrl, '/domainAdmin.html')
        if len(info):
            PrintMessage(''.join([CurrentMethodName(), ' passed.']))
        else:
            PrintMessage(''.join([CurrentMethodName(), ' failed: ', json.dumps(info)]), 'Error')
        return info

    def _getNctTableNames(self):
        serviceUrl = r'ServicesAPI/SystemModel/getNctTableNames'
        info = self._getUrl(CurrentMethodName(), serviceUrl, '/domainAdmin.html')
        if len(info):
            PrintMessage(''.join([CurrentMethodName(), ' passed.']))
        else:
            PrintMessage(''.join([CurrentMethodName(), ' failed: ', json.dumps(info)]), 'Error')
        return info

    def _getAllTechnologySpecs(self):
        serviceUrl = r'ServicesAPI/visualspace/getAllTechnologySpecs'
        info = self._getUrl(CurrentMethodName(), serviceUrl, '/domainAdmin.html')
        if len(info):
            PrintMessage(''.join([CurrentMethodName(), ' passed.']))
        else:
            PrintMessage(''.join([CurrentMethodName(), ' failed: ', json.dumps(info)]), 'Error')
        return info

    def _getAllVsdefnBaseInfo(self):
        serviceUrl = r'ServicesAPI/visualspace/getAllVsdefnBaseInfo'
        info = self._getUrl(CurrentMethodName(), serviceUrl, '/domainAdmin.html')
        if len(info):
            PrintMessage(''.join([CurrentMethodName(), ' passed.']))
        else:
            PrintMessage(''.join([CurrentMethodName(), ' failed: ', json.dumps(info)]), 'Error')
        return info

    def _getAllTopoLinkTypes(self):
        serviceUrl = r'ServicesAPI/topology/getAllTopoLinkTypes'
        info = self._getUrl(CurrentMethodName(), serviceUrl, '/domainAdmin.html')
        if len(info):
            PrintMessage(''.join([CurrentMethodName(), ' passed.']))
        else:
            PrintMessage(''.join([CurrentMethodName(), ' failed: ', json.dumps(info)]), 'Error')
        return info

    def _getAllSdnControllerDefs(self):
        serviceUrl = r'ServicesAPI/externalAPIServer/getAllSdnControllerDefs/1'
        info = self._getUrl(CurrentMethodName(), serviceUrl, '/domainAdmin.html')
        PrintMessage(''.join([CurrentMethodName(), ' passed.']))
        return info

    def _getParserLib(self):
        serviceUrl = r'ServicesAPI/ParserLib/Category?parserType=2'
        info = self._getUrl(CurrentMethodName(), serviceUrl, '/domainAdmin.html')
        if len(info):
            PrintMessage(''.join([CurrentMethodName(), ' passed.']))
        else:
            PrintMessage(''.join([CurrentMethodName(), ' failed: ', json.dumps(info)]), 'Error')
        return info

    def _getSitePath(self):
        serviceUrl = r'ServicesAPI/site/sitePath'
        info = self._getUrl(CurrentMethodName(), serviceUrl, '/domainAdmin.html')
        if len(info):
            PrintMessage(''.join([CurrentMethodName(), ' passed.']))
        else:
            PrintMessage(''.join([CurrentMethodName(), ' failed: ', json.dumps(info)]), 'Error')
        return info

    def _getParseConfigurationFiles(self, parserLib):
        item = dict()
        for level1 in parserLib.get('nodes', []):
            for level2 in level1.get('nodes', []):
                for level3 in level2.get('nodes', []):
                    for parser in level3.get('parsers', []):
                        item['parentId'] = level3['id']
                        item['cIndex'] = level3['accessType']
                        item['parentPath'] = '/'.join(['All Parsers', level1['name'], level2['name'], level3['name']])
                        item['parserId'] = parser['id']
                        item['parserName'] = parser['name']
                        item['parserPath'] = parser['parserPath']
                        yield item
                for parser in level2.get('parsers', []):
                    item['parentId'] = level2['id']
                    item['cIndex'] = level2['accessType']
                    item['parentPath'] = '/'.join(['All Parsers', level1['name'], level2['name']])
                    item['parserId'] = parser['id']
                    item['parserName'] = parser['name']
                    item['parserPath'] = parser['parserPath']
                    yield item
            for parser in level1.get('parsers', []):
                item['parentId'] = level1['id']
                item['cIndex'] = level1['accessType']
                item['parentPath'] = '/'.join(['All Parsers', level1['name']])
                item['parserId'] = parser['id']
                item['parserName'] = parser['name']
                item['parserPath'] = parser['parserPath']
                yield item

        return item

    def _getBasicAamAndPath(self):
        serviceUrl = r'ServicesAPI/aam/application/query/basicaamandpath'
        info = self._postUrl(CurrentMethodName(), serviceUrl, {}, '/domainAdmin.html')
        if len(info):
            PrintMessage(''.join([CurrentMethodName(), ' passed.']))
        else:
            PrintMessage(''.join([CurrentMethodName(), ' failed: ', json.dumps(info)]), 'Error')
        return info

    def _getChildrenSiteByParentSiteID(self, siteID):
        serviceUrl = r'ServicesAPI/site/getChildrenSiteByParentSiteID'
        payload = {
            'siteId': siteID,
            'returnSpecialSite': False
        }
        info = self._postUrl(CurrentMethodName(), serviceUrl, payload, '/domainAdmin.html')
        if len(info):
            PrintMessage(''.join([CurrentMethodName(), ' passed.']))
        else:
            PrintMessage(''.join([CurrentMethodName(), ' failed: ', json.dumps(info)]), 'Error')
        return info

    def _getSiteMapCountByBechmarkId(self, benchmarkID):
        serviceUrl = r'ServicesAPI/updatemapmgr/getSiteMapCountByBechmarkId'
        payload = {
            'isCascade': True,
            'mapId': benchmarkID,
            'mapType': 3
        }
        info = self._postUrl(CurrentMethodName(), serviceUrl, payload, '/domainAdmin.html')
        if len(info):
            PrintMessage(''.join([CurrentMethodName(), ' passed.']))
        else:
            PrintMessage(''.join([CurrentMethodName(), ' failed: ', json.dumps(info)]), 'Error')
        return info

    def _upInsertDiscoveryDefinition(self, definitionInfo):
        serviceUrl = r'ServicesAPI/snapshot/upInsertDiscoveryDefinition'
        info = self._postUrl(CurrentMethodName(), serviceUrl, definitionInfo, '/domainAdmin.html')
        if len(info):
            PrintMessage(''.join([CurrentMethodName(), ' passed.']))
        else:
            PrintMessage(''.join([CurrentMethodName(), ' failed: ', json.dumps(info)]), 'Error')
        return True

    def _upInsertBenchmarkDefinition(self, definitionInfo):
        serviceUrl = r'ServicesAPI/snapshot/upInsertBenchmarkDefinition'
        info = self._postUrl(CurrentMethodName(), serviceUrl, definitionInfo, '/domainAdmin.html')
        if len(info):
            PrintMessage(''.join([CurrentMethodName(), ' passed.']))
        else:
            PrintMessage(''.join([CurrentMethodName(), ' failed: ', json.dumps(info)]), 'Error')
        return True

    def EnableDiscoveryBenchmark(self, discoverybenchmarkName, definitionInfo=None, isDiscovery=True, enable=True):
        if definitionInfo is None:
            info = self._getAllBenchmarkDefinitions()
            definitionInfo = self._getJsonObject(info, 'name', discoverybenchmarkName)
        if len(definitionInfo) == 0:
            return True
        definitionInfo['isEnable'] = enable
        definitionInfo['isEnableDisplay'] = 'Enable' if enable else 'Disable'
        definitionInfo['$$hashKey'] = '-'.join(['uiGrid', str(randint(1000, 9999))])
        definitionInfo['showStopButton'] = True
        info = definitionInfo['schedule'].get('startDate', '')
        if info == '':
            info = definitionInfo['schedule']['start'].split('T')[0]
            definitionInfo['schedule']['startDate'] = info
            definitionInfo['schedule']['endDate'] = definitionInfo['schedule']['end'].split('T')[0]
        definitionInfo['schedule']['startDisplay'] = ', '.join([info, '12:00:00 AM'])
        definitionInfo['schedule']['nextRunTimeDisplay'] = ''
        definitionInfo['schedule']['frequency']['typeDisplay'] = 'Once'
        if isDiscovery:
            definitionInfo['typeDisplay'] = 'Discovery Task'
            info = self._upInsertDiscoveryDefinition(definitionInfo)
        else:
            definitionInfo['typeDisplay'] = 'Benchmark Task'
            info = self._upInsertBenchmarkDefinition(definitionInfo)
        if info:
            PrintMessage(''.join([CurrentMethodName(), ' passed.']))
        else:
            PrintMessage(''.join([CurrentMethodName(), ' failed: ', json.dumps(info)]), 'Error')
        return info

    def EnableDiscovery(self, discoveryName):
        return self.EnableDiscoveryBenchmark(discoveryName, None)

    def EnableBenchmark(self, benchmarkName):
        return self.EnableDiscoveryBenchmark(benchmarkName, None, False)

    def SaveScheduleDiscovery(self, ScheduleDiscoveryInfo, enable=True):
        info = self._getAllBenchmarkDefinitions()
        discoveryName = ScheduleDiscoveryInfo['Task Name']
        discoveryName2 = ScheduleDiscoveryInfo.get('Task Name Duplicate', None)
        definitionInfo = self._getJsonObject(info, 'name', discoveryName)
        if len(definitionInfo) == 0: # new discovery
            definitionInfo = self._getJsonObject(info, 'name', 'Scheduled System Discovery') # default Discovery
            definitionInfo['ID'] = CreateGuid()
            definitionInfo['name'] = discoveryName
            if discoveryName != 'Scheduled System Discovery':
                definitionInfo['isFixed'] = False
        if discoveryName2: # duplicate
            discoveryName = discoveryName2
            definitionInfo['ID'] = CreateGuid()
            definitionInfo['name'] = discoveryName
            definitionInfo['author'] = self.Username
            definitionInfo['isEnable'] = True
            definitionInfo['isFixed'] = False
            info = self.EnableDiscoveryBenchmark(discoveryName, definitionInfo, True, enable)
            return info
        if ScheduleDiscoveryInfo.get('Description', None) is not None:
            definitionInfo['description'] = ScheduleDiscoveryInfo['Description']
        discoverInfo = ScheduleDiscoveryInfo['Discovery Seed']
        if (discoverInfo['FromFile']):
            with open(discoverInfo['HostIPs'], 'r') as txtFile:
                hostips = list(filter(None, txtFile.read().split(';')))
        else:
            hostips = list(filter(None, discoverInfo['HostIPs']))
        accessMode = discoverInfo['Access Mode']
        if type(accessMode) is str:
            accessMode = DiscoverAccessOrder.index(accessMode)
        definitionInfo['discoverOption']['accessOrder'] = accessMode
        definitionInfo['discoverOption']['maxDepth'] = discoverInfo['Discovery Depth']
        definitionInfo['discoverOption']['isAllDevices'] = False
        definitionInfo['discoverOption']['fromScan'] = False
        definitionInfo['discoverOption']['hostips'] = hostips
        networkSetting = definitionInfo['discoverOption']['checkedObjs']
        networkSetting['networkServer'] = ScheduleDiscoveryInfo['Network Settings']['Front Server']
        networkSetting['sshPrivateKey'] = ScheduleDiscoveryInfo['Network Settings']['Private Key']
        networkSetting['jumpbox'] = ScheduleDiscoveryInfo['Network Settings']['Jumpbox']
        networkSetting['telnetInfo'] = ScheduleDiscoveryInfo['Network Settings']['Telnet/SSH Login']
        networkSetting['enablePasswd'] = ScheduleDiscoveryInfo['Network Settings']['Privilege Login']
        networkSetting['snmpRoInfo'] = ScheduleDiscoveryInfo['Network Settings']['SNMP String']

        info = self.EnableDiscoveryBenchmark(discoveryName, definitionInfo, True, enable)
        if info:
            PrintMessage(''.join([CurrentMethodName(), ' passed.']))
        else:
            PrintMessage(''.join([CurrentMethodName(), ' failed: ', json.dumps(info)]), 'Error')
        return info

    def _getDeviceScopeItem(self, retrieveInfo, definitionInfo):
        dest = definitionInfo.get('retrieveOption', {}).get('devScope', None)
        deviceGroups = list()
        excludedDeviceGroups = list()
        allDeviveGroups = self._getAllDeviceGroupInfo()
        for deviceGroup in allDeviveGroups:
            if deviceGroup['Name'] in retrieveInfo.get('Select Device', []):
                deviceGroups.append(deviceGroup['ID'])
            if deviceGroup['Name'] in retrieveInfo.get('Exclude Device Groups', []):
                excludedDeviceGroups.append(deviceGroup['ID'])
        if retrieveInfo.get('Select Device Type', '') == 'All Devices':
            dest['scopeType'] = '0'
        elif retrieveInfo.get('Select Device Type', '') == 'Device Group':
            dest['scopeType'] = '1'
        elif retrieveInfo.get('Select Device Type', '') == 'Site':
            dest['scopeType'] = '2'
        dest['scopeRange'] = deviceGroups
        dest['excludedDeviceGroups'] = excludedDeviceGroups

        dest = definitionInfo['retrieveOption'].get('additionalProcess', {}).get('process', None)
        if dest is None:
            definitionInfo['retrieveOption']['additionalProcess'] = {'process': []}
            dest = definitionInfo['retrieveOption']['additionalProcess']['process']
        for process in dest:
            name = process['name']
            if name in ['Recalculate Dynamic CE List', 'Recalculate MPLS Virtual Route Tables']:
                src = retrieveInfo.get('Update MPLS Cloud', {})
            elif name in ['IPv4 L3 Topology', 'IPv6 L3 Topology', 'L2 Topology', 'L3 VPN Tunnel',
                          'Logical Topology', 'L2 Overlay Topology']:
                src = retrieveInfo.get('Build Topology', {})
            elif name in ['Recalculate Dynamic Device Groups', 'Recalculate Site', 'Build Default Device Data View',
                          'Qualify Data View Templates', 'Build Network Tree']:
                src = retrieveInfo.get('System Operations', {})
            elif name in ['Recalculate AWS Virtual Route Table', 'Recalculate Azure Virtual Route Table']:
                src = retrieveInfo.get('Update Public Cloud', {})
            else:
                continue
            if len(src):
                isChecked = True if name in src.get('selected', []) else False
                process['isChecked'] = True if src.get('allSelected', []) else isChecked
                process['$$hashKey'] = 'uiGrid-' + str(randint(1000, 9999))
        return dest

    def _getUpdateMapsItem(self, src):
        item = {
            'ID': 7, 'type': 7, 'name': 'Schedule Update Maps', 'tip': 'Update Maps', 'action': 'onUpdateMap',
            'isChecked': True, 'dataViewTaskParam': {}, 'autoUpdateMapParam': {}
        }
        selectQmap = {
                'isCascade': True, 'mapId': '', 'mapType': 2,
                'isExportMapVisio': True, 'isCascade': True, 'isKeepHistoryVersion': False
            }
        updateConfigItemTemplate = {
            'isBackup': True, 'isEnable': False, 'isExportVisio': True, 'isKeepHistoryVersion': True,
            'targetMapFolders': [], 'targetMapType': 1, 'targetMaps': [],
            'exportVisioOptions': {
                'toIEFolder': {'isEnabled': True, 'folderPath': 'Public'},
                'toExternalDrive': {'isEnabled': False, 'networkPath': '', 'userName': '', 'password': ''}
            }
        }
        name = 'Update Context Maps'
        isChecked = True if name in src.get('selected', []) else False
        item['autoUpdateMapParam']['updateContextQmap'] = True if src['allSelected'] else isChecked
        selectQmaps = []
        updateConfigItems = []
        name = 'Update Site Maps'
        isChecked = True if name in src.get('selected', []) else False
        updateConfigItem = updateConfigItemTemplate.copy()
        updateConfigItem['targetMapType'] = 3
        updateConfigItem['isEnable'] = True if src['allSelected'] else isChecked
        updateConfigItem['targetMapFolders'] = []
        if src['allSelected'] or updateConfigItem['isEnable']:
            sitePath = self._getSitePath()
            for key, value in sitePath.items():
                if value['siteName'] == 'My Network':
                    selectQmap['mapId'] = key  # list(sitePath.keys())[0]
                    selectQmaps.append(selectQmap)
                    break
        item['autoUpdateMapParam']['selectQmaps'] = selectQmaps
        updateConfigItems.append(updateConfigItem)
        name = 'Update Shared Device Group Maps'
        isChecked = True if name in src.get('selected', []) else False
        updateConfigItem = updateConfigItemTemplate.copy()
        updateConfigItem['targetMapType'] = 4
        updateConfigItem['isEnable'] = True if src['allSelected'] else isChecked
        updateConfigItem['targetMapFolders'] = ['Public', 'Policy Device Group', 'System'] if updateConfigItem['isEnable'] else []
        updateConfigItems.append(updateConfigItem)
        name = 'Update Public Maps'
        isChecked = True if name in src.get('selected', []) else False
        updateConfigItem = updateConfigItemTemplate.copy()
        updateConfigItem['targetMapType'] = 1
        updateConfigItem['isEnable'] = True if src['allSelected'] else isChecked
        updateConfigItem['targetMapFolders'] = ['Public'] if updateConfigItem['isEnable'] else []
        updateConfigItems.append(updateConfigItem)
        item['autoUpdateMapParam']['updateConfigItems'] = updateConfigItems
        return item

    def _getRetrieveLiveDataItem(self, retrieveInfo, definitionInfo):
        dest = definitionInfo.get('retrieveOption', {}).get('retrieveData', None)
        if dest is None:
            definitionInfo['retrieveOption']['retrieveData'] = {}
            dest = definitionInfo['retrieveOption']['retrieveData']
        if retrieveInfo.get('Built-in Live Data', {}).get('allSelected', False):
            dest['config'] = True
            dest['routingTable'] = True
            dest['arpTable'] = True
            dest['macTable'] = True
            dest['cdpTable'] = True
            dest['stpTable'] = True
            dest['bgpNbr'] = True
            dest['deviceInfo'] = True
            dest['interfaceInfo'] = True
        else:
            selected = retrieveInfo.get('Built-in Live Data', {}).get('selected', [])
            dest['config'] = True if 'Configuration File' in selected else False
            dest['routingTable'] = True if 'Route Table' in selected else False
            dest['arpTable'] = True if 'ARP Table' in selected else False
            dest['macTable'] = True if 'MAC Table' in selected else False
            dest['cdpTable'] = True if 'NDP Table' in selected else False
            dest['stpTable'] = True if 'STP Table' in selected else False
            dest['bgpNbr'] = True if 'BGP Advertised-route Table' in selected else False
            dest['deviceInfo'] = True if 'Inventory Information of Device/Interface/Module' in selected else False
            dest['interfaceInfo'] = True if 'Inventory Information of Device/Interface/Module' in selected else False
        nctTableNames = self._getNctTableNames()
        if retrieveInfo.get('NCT TABLE', {}).get('allSelected', False):
            dest['isAllNctSelected'] = True
            dest['nctTable'] = nctTableNames.get('ncts', [])
            dest['extentedParser'] = nctTableNames.get('extentedParser', [])
        else:
            dest['isAllNctSelected'] = False
            dest['nctTable'] = retrieveInfo.get('NCT TABLE', {}).get('selected', [])
            dest['extentedParser'] = nctTableNames.get('extentedParser', [])
        technoloySpecs = self._getAllTechnologySpecs().get('result', [])
        original_techData = dest['techData'].copy()
        dest['techData'] = []
        names = retrieveInfo.keys()
        for spec in technoloySpecs:
            name = spec['name']
            if name not in names:
                continue
            item = dict()
            item['techName'] = name
            item['techId'] = spec['id']
            if retrieveInfo.get('VMware vCenter', {}).get('allSelected', False):
                selected = ['Basic Data', 'Node Properties', 'Topology Data']
            else:
                selected = retrieveInfo.get(name, {}).get('selected', [])
            item['basicInfo'] = True if 'Basic Data' in selected else False
            item['detailInfo'] = True if 'Node Properties' in selected else False
            item['topologyInfo'] = True if 'Topology Data' in selected else False
            tech_data = next((item for item in original_techData if item.get('techName') and item['techName'] == name), None)
            if tech_data is not None:
                system_table = tech_data.get('systemTable', None)
                if system_table is not None:
                    item['systemTable'] = system_table.copy()
            dest['techData'].append(item)
        return dest

    def _getAdditionalProcessItem(self, retrieveInfo, definitionInfo):
        dest = definitionInfo['retrieveOption'].get('additionalProcess', {}).get('process', None)
        if dest is None:
            definitionInfo['retrieveOption']['additionalProcess'] = {'process': []}
            dest = definitionInfo['retrieveOption']['additionalProcess']['process']
        for process in dest:
            name = process['name']
            if name in ['Recalculate Dynamic CE List', 'Recalculate MPLS Virtual Route Tables']:
                src = retrieveInfo.get('Update MPLS Cloud', {})
            elif name in ['IPv4 L3 Topology', 'IPv6 L3 Topology', 'L2 Topology', 'L3 VPN Tunnel',
                          'Logical Topology', 'L2 Overlay Topology']:
                src = retrieveInfo.get('Build Topology', {})
            elif name in ['Recalculate Dynamic Device Groups', 'Recalculate Site', 'Build Default Device Data View',
                          'Qualify Data View Templates', 'Build Network Tree']:
                src = retrieveInfo.get('System Operations', {})
            elif name in ['Recalculate AWS Virtual Route Table', 'Recalculate Azure Virtual Route Table']:
                src = retrieveInfo.get('Update Public Cloud', {})
            else:
                continue
            if len(src):
                isChecked = True if name in src.get('selected', []) else False
                process['isChecked'] = True if src.get('allSelected', []) else isChecked
                process['$$hashKey'] = 'uiGrid-' + str(randint(1000, 9999))
        return dest

    def _getRebuildVisualSpaceItem(self, src, definitionInfo):
        dest = definitionInfo['retrieveOption'].get('additionalProcess', {}).get('process', None)
        rebuildVisualSpace = self._getAllVsdefnBaseInfo()
        for visualSpace in rebuildVisualSpace:
            name = visualSpace['path']
            isChecked = True if name in src.get('selected', []) else False
            item = dict()
            item['isChecked'] = True if src['allSelected'] else isChecked
            if item['isChecked']:
                obj = self._getJsonObject(dest, 'name', name.replace('\\', '\\\\'))
                if obj:
                    dest.remove(obj)
                item['ID'] = visualSpace['id']
                item['name'] = name
                item['tip'] = name
                item['type'] = 11
                item['$$hashKey'] = 'uiGrid-' + str(randint(1000, 9999))
                dest.append(item)
        return dest

    def _getParseConfigurationFilesItem(self, src, definitionInfo):
        dest = definitionInfo['retrieveOption'].get('additionalProcess', {}).get('process', None)
        obj = self._getJsonObject(dest, 'type', 12)
        if obj:
            dest.remove(obj)
        configParsers = list()
        parserFiles = self._getParserLib()
        for parserFile in self._getParseConfigurationFiles(parserFiles):
            name = parserFile['parserPath']
            isChecked = True if name in src.get('selected', []) else False
            parserFile['$$hashKey'] = 'uiGrid-' + str(randint(1000, 9999))
            parserFile['isChecked'] = True  # if src['allSelected'] else isChecked
            configParsers.append(parserFile.copy())
        item = {
            'ID': 12,
            'name': 'Configuration Parser',
            'type': 12,
            'action': '',
            'tip': '',
            'isChecked': True,
            'configParsersParam': {'configParsers': configParsers}
        }
        dest.append(item)
        return dest

    def _getApplicationAssuranceItem(self, retrieveInfo, definitionInfo):
        dest = definitionInfo['retrieveOption'].get('applicationAssurance', None)
        if dest is None:
            definitionInfo['retrieveOption']['applicationAssurance'] = {
                'autoSetGoldenThreshold': 3,
                'clientUrl': self.Url,
                'enable': False,
                'enableAutoSetGoldenPath': False,
                'restartAutoSetGoldenPath': False,
                'applications': [],
                'shareAlert': {'alertUsers': [], 'selectedAllUsers': "False", 'sendEmailTo': [],
                               'levels': [1, 2]}
            }
            dest = definitionInfo['retrieveOption']['applicationAssurance']
        name = 'Auto Set Golden Path'
        src = retrieveInfo.get(name, {})
        if len(src):
            dest['enableAutoSetGoldenPath'] = src.get('Enable', False)
            dest['autoSetGoldenThreshold'] = src.get('Run Benchmarks to set up Golden Paths', 3)
            dest['restartAutoSetGoldenPath'] = src.get('restartAutoSetGoldenPath', False)
        name = 'Application Verification'
        src = retrieveInfo.get(name, {})
        if len(src):
            dest['enable'] = src['allSelected']
            application = self._getBasicAamAndPath()
            name = application[0].get('name', '')
            obj = self._getJsonObject(dest['applications'], 'name', name)
            if obj:
                dest['applications'].remove(obj)
            item = {
                'id': application[0]['id'],
                'name': name,
                'paths': [],
                '$$hashKey': 'uiGrid-' + str(randint(1000, 9999))
            }
            dest['applications'].append(item)
        return dest

    def SaveScheduleBenchmark(self, ScheduleBenchmarkInfo, enable=True): #v8.02
        name = ScheduleBenchmarkInfo['Task Name']
        name2 = ScheduleBenchmarkInfo.get('Task Name Duplicate', None)
        definitionInfo = self._getDiscoveryBenchmarkDefinition(name, False)
        if ScheduleBenchmarkInfo.get('Description', None) is not None:
            definitionInfo['description'] = ScheduleBenchmarkInfo['Description']
        if name2: # duplicate
            name = name2
            definitionInfo['ID'] = CreateGuid()
            definitionInfo['name'] = name
            definitionInfo['author'] = self.Username
            definitionInfo['isEnable'] = True
            definitionInfo['isFixed'] = False
            info = self.EnableDiscoveryBenchmark(name, definitionInfo, True, enable)
            return info
        #Schedule
        definitionInfo['schedule']['frequency'] = {
            'type': 0, 'runOnce': {'startTime': 33360}, 'byHour': None, 'byDay': None, 'byWeek': None, 'byMonth': None
        }
        #Device Scope
        retrieveInfo = ScheduleBenchmarkInfo.get('Device Scope', {})
        if len(retrieveInfo):
            self._getDeviceScopeItem(retrieveInfo, definitionInfo)

        #Retrieve Live Data
        retrieveInfo = ScheduleBenchmarkInfo.get('Retrieve Live Data', {})
        if len(retrieveInfo):
            self._getRetrieveLiveDataItem(retrieveInfo, definitionInfo)
        #Additional Operations after Benchmark
        retrieveInfo = ScheduleBenchmarkInfo.get('Additional Operations after Benchmark', {})
        if len(retrieveInfo):
            dest = definitionInfo['retrieveOption'].get('additionalProcess', {}).get('process', None)
            self._getAdditionalProcessItem(retrieveInfo, definitionInfo)
            #Rebuild Visual Space
            src = retrieveInfo.get('Rebuild Visual Space', {})
            if len(src):
                self._getRebuildVisualSpaceItem(src, definitionInfo)
            #Parse Configuration Files
            src = retrieveInfo.get('Parse Configuration Files', {})
            if src.get('allSelected', False):
                self._getParseConfigurationFilesItem(src, definitionInfo)
            #Schedule Update Maps
            name = 'Update Maps'
            src = retrieveInfo.get(name, {})
            if len(src):
                while True:
                    obj = self._getJsonObject(dest, 'type', '7')
                    if obj:
                        dest.remove(obj)
                    else:
                        break;
                item = self._getUpdateMapsItem(src)
                dest.append(item)
            # application Assurance
            self._getApplicationAssuranceItem(retrieveInfo, definitionInfo)

        info = self.EnableDiscoveryBenchmark(name, definitionInfo, False, enable)
        if info:
            PrintMessage(''.join([CurrentMethodName(), ' passed.']))
        else:
            PrintMessage(''.join([CurrentMethodName(), ' failed: ', json.dumps(info)]), 'Error')
        return info

    def RemoveBenchmarkDefinitionByGuid(self, guid):
        serviceUrl = r'ServicesAPI/snapshot/removeBenchmarkDefinitionByGuid'
        payload = {
            'ID': guid,
            'deleteDataFolder': True
        }
        info = self._postUrl(CurrentMethodName(), serviceUrl, payload, '/domainAdmin.html')
        if len(info):
            PrintMessage(''.join([CurrentMethodName(), ' passed.']))
        else:
            PrintMessage(''.join([CurrentMethodName(), ' failed: ', json.dumps(info)]), 'Error')
        return info

    def RemoveBenchmarkDefinitionByName(self, name):
        info = self._getAllBenchmarkDefinitions()
        item = self._getJsonObject(info, 'name', name)
        guid = item.get('ID', '0')
        info = self.RemoveBenchmarkDefinitionByGuid(guid)
        return info

    def StartBenchmarkTask(self, name, maxTimeout=86400): # 43200 = 12*3600s, 864000 = 24*3600s
        info = self._getAllBenchmarkDefinitions()
        item = self._getJsonObject(info, 'name', name)
        if len(item) <=0:
            PrintMessage(''.join([CurrentMethodName(), ' failed to find the name "', name, '". \n',
                                  json.dumps(info)]), 'Error')
            return False
        if not item['isEnable']:
            PrintMessage(''.join([CurrentMethodName(), ' failed: please enable "', name, '" firstly.']), 'Error')
            return False
        index = 0
        sleepTime = 90
        if item['currentRunStatus'] == 'Running' :
            PrintMessage(''.join([CurrentMethodName(), ' : the task "', name, '" is running.']), 'Warning')
            while True:
                info = self._getAllBenchmarkDefinitions()
                item = self._getJsonObject(info, 'name', name)
                if len(item) <= 0:
                    PrintMessage('Failed to retrieve task status.', 'Warning')
                    continue
                print(''.join([str(1+index/sleepTime), ': ', item['currentRunStatus']]))
                if item['currentRunStatus'] != 'Running':
                    break
                sleep(sleepTime)
                if maxTimeout < 0:
                    continue
                index += sleepTime
                if index >= maxTimeout:
                    break
            if index >= maxTimeout:
                PrintMessage(''.join([CurrentMethodName(), ' failed: the task "', name, '" is running more than ',
                                      str(maxTimeout/3600), ' hours (', str(maxTimeout), ' seconds).']), 'Error')
                return False
            else:
                PrintMessage(''.join([CurrentMethodName(), ': "', name, '" passed.']))
                return True

        serviceUrl = r'ServicesAPI/snapshot/startBenchmarkTask'
        payload = {
            'ID': item['ID'],
            'type': item['type']
        }
        info = self._postUrl(CurrentMethodName(), serviceUrl, payload, '/domainAdmin.html')
        if len(info) <= 0 or not info['result']:
            PrintMessage(''.join([CurrentMethodName(), ' failed.']), 'Error')
            return False
        for index in range(3):
            info = self._getAllBenchmarkDefinitions()
            item = self._getJsonObject(info, 'name', name)
            if item['currentRunStatus'] == 'Running':
                break
            sleep(sleepTime)
        if item['currentRunStatus'] != 'Running':
            PrintMessage(''.join([CurrentMethodName(), ' failed to start "', name, '".']), 'Error')
            return False
        index = 0
        while True:
            info = self._getAllBenchmarkDefinitions()
            item = self._getJsonObject(info, 'name', name)
            if len(item) <= 0:
                PrintMessage('Failed to retrieve task status.', 'Warning')
                continue
            print(''.join([str(1+index/sleepTime), ': ', item['currentRunStatus']]))
            if item['currentRunStatus'] != 'Running':
                break
            sleep(sleepTime)
            if maxTimeout < 0:
                continue
            index += sleepTime
            if index >= maxTimeout:
                break
        if index >= maxTimeout:
            PrintMessage(''.join([CurrentMethodName(), ' failed: the task "', name, '" is running more than ',
                                  str(maxTimeout/3600), ' hours (', str(maxTimeout), ' seconds).']), 'Error')
            return False
        else:
            PrintMessage(''.join([CurrentMethodName(), ': "', name, '" passed.']))
            return True

    #Schedule Data View Template
    def _getRootSite(self):
        serviceUrl = r'ServicesAPI/site/root-site'
        info = self._getUrl(CurrentMethodName(), serviceUrl, '/domainAdmin.html')
        if len(info):
            PrintMessage(''.join([CurrentMethodName(), ' passed.']))
        else:
            PrintMessage(''.join([CurrentMethodName(), ' failed: ', json.dumps(info)]), 'Error')
        return info

    def _getParserLibCategoryCrawl(self):
        serviceUrl = r'ServicesAPI/ParserLib/Category/Crawl'
        info = self._getUrl(CurrentMethodName(), serviceUrl, '/domainAdmin.html')
        if len(info):
            PrintMessage(''.join([CurrentMethodName(), ' passed.']))
        else:
            PrintMessage(''.join([CurrentMethodName(), ' failed: ', json.dumps(info)]), 'Error')
        return info

    def _getDataViewTemplateTree(self):
        serviceUrl = r'ServicesAPI/dataViewTemplate/tree/getTree'
        info = self._getUrl(CurrentMethodName(), serviceUrl, '/domainAdmin.html')
        if len(info):
            PrintMessage(''.join([CurrentMethodName(), ' passed.']))
        else:
            PrintMessage(''.join([CurrentMethodName(), ' failed: ', json.dumps(info)]), 'Error')
        return info

    def _getSchedulerDataViewTemplate(self):
        serviceUrl = r'ServicesAPI/scheduler/search'
        payload = {
            'keyword': '',
            'pageNumber': 0,
            'pageSize': 50000,
            'creators': [],
            'statuses': []
        }
        info = self._postUrl(CurrentMethodName(), serviceUrl, payload, '/domainAdmin.html')
        if len(info):
            PrintMessage(''.join([CurrentMethodName(), ' passed.']))
        else:
            PrintMessage(''.join([CurrentMethodName(), ' failed: ', json.dumps(info)]), 'Error')
        return info

    def _getAllDisplayUsersOnDomain(self):
        serviceUrl = r'ServicesAPI/Admin/User/getAllDisplayUsersOnDomain'
        info = self._postUrl(CurrentMethodName(), serviceUrl, {}, '/domainAdmin.html')
        if len(info):
            PrintMessage(''.join([CurrentMethodName(), ' passed.']))
        else:
            PrintMessage(''.join([CurrentMethodName(), ' failed: ', json.dumps(info)]), 'Error')
        return info

    def _checkSchedulerDataViewTemplate(self, name):
        serviceUrl = r'ServicesAPI/scheduler/check'
        payload = {
            'name': name,
            'scheduleObjectType': 1
        }
        info = self._postUrl(CurrentMethodName(), serviceUrl, payload, '/domainAdmin.html')
        return info

    def _schedulerSearch(self):
        serviceUrl = r'ServicesAPI/scheduler/search'
        payload = {
            'keyword': '', 'pageNumber': 0, 'pageSize': 100, 'creators': [], 'statuses': []
        }
        info = self._postUrl(CurrentMethodName(), serviceUrl, payload, '/domainAdmin.html')
        if len(info):
            PrintMessage(''.join([CurrentMethodName(), ' passed.']))
        else:
            PrintMessage(''.join([CurrentMethodName(), ' failed: ', json.dumps(info)]), 'Error')
        return info

    def GetScheduleDataViewTemplateTask(self, dvtName=''):
        info = self._schedulerSearch()
        if dvtName != '':
            info = self._getJsonObject(info, 'name', dvtName)
        return info

    def _schedulerLogDvt(self, taskID, startTime='', endTime=''):
        serviceUrl = r'ServicesAPI/scheduler/log/dvt'
        if startTime == '':
            today = datetime.today().replace(hour=0,minute=0,second=0,microsecond=327000)
            today = NetBrainUtils.LocalTimeToUTCTime(today)
            firstDay = today.replace(day=1)
            lastMonth = firstDay - timedelta(days=1)
            startTime = lastMonth.replace(day=today.day)
            startTime = NetBrainUtils.DateTimeToString(startTime, 2)
        if endTime == '':
            today += timedelta(days=1)
            today -= timedelta(seconds=1)
            endTime = NetBrainUtils.DateTimeToString(today, 2)
        payload = {'taskId': taskID, 'startTime': startTime, 'endTime': endTime, 'skip': 0, 'take': 50000}
        info = self._postUrl(CurrentMethodName(), serviceUrl, payload, '/domainAdmin.html')
        if len(info):
            PrintMessage(''.join([CurrentMethodName(), ' passed.']))
        else:
            PrintMessage(''.join([CurrentMethodName(), ' failed: ', json.dumps(info)]), 'Error')
        return info

    def _schedulerLogDvtExecution(self, taskExecutionID):
        serviceUrl = r'ServicesAPI/scheduler/log/dvt/execution'
        payload = {'taskExecutionId': taskExecutionID, 'skip': 0, 'take': 50000}
        info = self._postUrl(CurrentMethodName(), serviceUrl, payload, '/domainAdmin.html')
        if len(info):
            PrintMessage(''.join([CurrentMethodName(), ' passed.']))
        else:
            PrintMessage(''.join([CurrentMethodName(), ' failed: ', json.dumps(info)]), 'Error')
        return info

    def _schedulerLogDvtQualification(self, taskExecutionID):
        serviceUrl = r'ServicesAPI/scheduler/log/dvt/qualification/' + taskExecutionID
        info = self._getUrl(CurrentMethodName(), serviceUrl, '/domainAdmin.html')
        if len(info):
            PrintMessage(''.join([CurrentMethodName(), ' passed.']))
        else:
            PrintMessage(''.join([CurrentMethodName(), ' failed: ', json.dumps(info)]), 'Error')
        return info

    def GetScheduleDataViewTemplateTaskViewLogs(self, dvtName, startTime=''):
        info = self.GetScheduleDataViewTemplateTask(dvtName)
        if len(info) <= 0:
            PrintMessage(''.join([CurrentMethodName(), ' failed to find the task "', dvtName, '".']), 'Error')
            return {}
        if startTime != '':
            startTime = NetBrainUtils.StringToDateTime(startTime, '%m/%d/%Y, %I:%M:%S %p')
            startTime = NetBrainUtils.LocalTimeToUTCTime(startTime)
            info = self._schedulerLogDvt(info['id'])
            for item in info:
                startExecuteTime = NetBrainUtils.StringToDateTime(item['startExecuteTime'], '%Y-%m-%dT%H:%M:%S.%fZ')
                startExecuteTime = startExecuteTime.replace(microsecond=0)
                if startTime == startExecuteTime:
                    info = item
                    break
        return info

    def GetScheduleDataViewTemplateTaskExecutionLog(self, taskExecutionID):
        return self._schedulerLogDvtExecution(taskExecutionID)

    def GetScheduleDataViewTemplateTaskQualification(self, taskExecutionID):
        return self._schedulerLogDvtQualification(taskExecutionID)

    def SaveScheduleDataViewTemplate(self, scheduleDVTInfo):
        serviceUrl = r'ServicesAPI/scheduler'
        name = scheduleDVTInfo['Task Name']
        names = self._schedulerSearch()
        info = self._getJsonObject(names, 'name', name)
        if len(info):
            PrintMessage(''.join([CurrentMethodName(), ': the Schedule DVT name "', name, '" is existed. Abort!!!']), 'Warning')
            #sdvtID = info['id']
            return {}
        else:
            sdvtID = CreateGuid()
        targetDeviceSite = targetDeviceDeviceGroups = targetDeviceDevices = targetDeviceNode = list()
        info = scheduleDVTInfo.get('Device Scope', {})
        if len(info.get('Site', [])):
            rootSite = self._getRootSite()
            for name in info.get('Site', []):
                item = self._getJsonObject(rootSite, 'name', name) if type(rootSite) is list else rootSite
                if len(item):
                    targetDeviceSite.append({
                        'ID': item['ID'],
                        'name': name,
                        'deviceCount': item['deviceCount'],
                        'location': name
                    })
        elif len(info.get('Device Group', [])):
            deviceGroup = self.DeviceGroupInfo()
            for name in info.get('Device Group', []):
                item = self._getJsonObject(deviceGroup, 'name', name)
                if len(item):
                    targetDeviceDeviceGroups.append({
                        'ID': item['ID'],
                        'name': name,
                        'deviceCount': item['deviceCount'],
                        'location': name
                    })
        elif len(info.get('Device', [])):
            targetDeviceDevices = info['Device']
        elif len(info.get('Node', [])):
            targetDeviceNode = info['Node']
        dvtTemplates = list()
        info = self._getDataViewTemplateTree()
        names = scheduleDVTInfo.get('Select Data View Template/Parser', {}).get('Data View Template', '')
        for name in names:
            dvtInfo = self._getJsonObject(info, 'name', name) if type(info) is list else info
            if len(name) and len(dvtInfo):
                item = {
                    'ID': dvtInfo['ID'],
                    'name': dvtInfo['name'],
                    'type': dvtInfo['nodeType'],
                    'path': dvtInfo['name']
                }
                dvtTemplates.append(item)
        parsers = list()
        info = self._getParserLibCategoryCrawl()
        names = scheduleDVTInfo.get('Select Data View Template/Parser', {}).get('Parser', '')
        for name in names:
            parserInfo = self._getJsonObject(info, 'name', name) if type(info) is list else info
            if len(name) and len(parserInfo):
                item = {
                    'ID': parserInfo['id'],
                    'name': parserInfo['name'],
                    'type': parserInfo['accessType'],
                    'path': parserInfo['path'],
                    'command': ''
                }
                parsers.append(item)
        alertUser = list()
        info = self._getAllDisplayUsersOnDomain()
        names = scheduleDVTInfo.get('Notification', {}).get('Share Alert with', [])
        for name in names:
            parserInfo = self._getJsonObject(info, 'userName', name) if type(info) is list else info
            if len(name) and len(parserInfo):
                item = {
                    'userId': parserInfo['userId'],
                    'userName': parserInfo['userName']
                }
                alertUser.append(item)
            else:
                PrintMessage(''.join(['The user "', name, '" does not exist.']), 'Warning')
        payload = {
            'id': sdvtID,
            'name': scheduleDVTInfo.get('Task Name', ''),
            'description': scheduleDVTInfo.get('Description', ''),
            'scheduleObjectType': 1,
            'setting': {
                'scheduleTime': {
                    'frequency': {
                        'runOnce': {},
                        'byDay': {'timeRange': [{'startTime': '', 'endTime': ''}]},
                        'byWeek': {'day': [6], 'timeRange': [{'startTime': 25860}], 'interval': 1},
                        'type': 4
                    },
                    'qappFrequency': {},
                    'selectedTimeZone': 'Eastern Standard Time',
                    'start': '2019-12-29T05:00:00.000Z'
                },
                'targetDevice': {
                    'sites': targetDeviceSite,
                    'deviceGroups': targetDeviceDeviceGroups,
                    'devices': targetDeviceDevices,
                    'nodes': targetDeviceNode,
                },
                'dataViewTemplate': {
                    'templates': dvtTemplates
                },
                'visibleInDataView': False,
                'parsers': parsers,
                'maxCmdForOneParser': scheduleDVTInfo.get('Select Data View Template/Parser', {}).get('Max Command Instances of a Parameterized Parser for Each Device', 32),
                'qapp': {'name': '', 'path': ''},
                'qappGroup': {'name': '', 'path': ''},
                'alertUser': alertUser,
                'levels': [2],
                'sendEmailTo': scheduleDVTInfo.get('Notification', {}).get('Send Email to', [])
            },
            'createInfo': {'userName': self.Username},
            'active': True,
            'isRunNow': False,
            'firstExecuteTime': '',
            'scheduleQappExecutionId': ''
        }
        info = self._putUrl(CurrentMethodName(), serviceUrl, payload, '/domainAdmin.html')
        if len(info):
            PrintMessage(''.join([CurrentMethodName(), ' passed.']))
        else:
            PrintMessage(''.join([CurrentMethodName(), ' failed: ', json.dumps(info)]), 'Error')
        return info

    def _schedulerRunnow(self, name):
        info = self._schedulerSearch()
        item = self._getJsonObject(info, 'name', name)
        if len(item) <= 0:
            PrintMessage(''.join([CurrentMethodName(), ' failed to find the name "', name, '". \n',
                                  json.dumps(info)]), 'Error')
            return False
        serviceUrl = r'ServicesAPI/scheduler/runnow'
        payload = {'id': item['id']}
        info = self._postUrl(CurrentMethodName(), serviceUrl, payload, '/domainAdmin.html')
        if info:
            PrintMessage(''.join([CurrentMethodName(), ' passed.']))
        else:
            PrintMessage(''.join([CurrentMethodName(), ' failed: ', json.dumps(info)]), 'Error')
        return info

    def StartScheduleDVT(self, name, maxTimeout=43200):  # 43200 = 12*3600s
        info = self._schedulerSearch()
        item = self._getJsonObject(info, 'name', name)
        if len(item) <= 0:
            PrintMessage(''.join([CurrentMethodName(), ' failed to find the name "', name, '". \n',
                                  json.dumps(info)]), 'Error')
            return False
        index = 0
        if item['status'] == 'Running':
            PrintMessage(''.join([CurrentMethodName(), ' : the task "', name, '" is running.']), 'Warning')
            while True:
                info = self._schedulerSearch()
                item = self._getJsonObject(info, 'name', name)
                if len(item) <= 0:
                    PrintMessage('Failed to retrieve task status.', 'Warning')
                    continue
                print(''.join([str(1+index/30), ': ', item['status']]))
                if item['status'] != 'Running':
                    break
                sleep(30)
                if maxTimeout < 0:
                    continue
                index += 30
                if index >= maxTimeout:
                    break
            if index >= maxTimeout:
                PrintMessage(''.join([CurrentMethodName(), ' failed: the task "', name, '" is running more than ',
                                      str(maxTimeout / 3600), ' hours (', str(maxTimeout), ' seconds).']), 'Error')
                return False
            else:
                PrintMessage(''.join([CurrentMethodName(), ': "', name, '" passed.']))
                return True

        serviceUrl = r'ServicesAPI/scheduler/runnow'
        payload = {'id': item['id']}
        info = self._schedulerRunnow(name)   # _postUrl(CurrentMethodName(), serviceUrl, payload, '/domainAdmin.html')
        if not info:
            PrintMessage(''.join([CurrentMethodName(), ' failed.']), 'Error')
            return False
        index = 0
        sleep(60)
        info = self._schedulerSearch()
        item = self._getJsonObject(info, 'name', name)
        if item['status'] != 'Running':
            PrintMessage(''.join([CurrentMethodName(), ' failed to start "', name, '".']), 'Error')
            return False
        while True:
            info = self._schedulerSearch()
            item = self._getJsonObject(info, 'name', name)
            if len(item) <= 0:
                PrintMessage('Failed to retrieve task status.', 'Warning')
                continue
            print(''.join([str(1+index/30), ': ', item['status']]))
            if item['status'] != 'Running':
                break
            sleep(30)
            if maxTimeout < 0:
                continue
            index += 30
            if index >= maxTimeout:
                break
        if index >= maxTimeout:
            PrintMessage(''.join([CurrentMethodName(), ' failed: the task "', name, '" is running more than ',
                                  str(maxTimeout/3600), ' hours (', str(maxTimeout), ' seconds).']), 'Error')
            return False
        else:
            PrintMessage(''.join([CurrentMethodName(), ': "', name, '" passed.']))
            return True

    # Schedule Task end

    # Golden Baseline start
    def _getGvTree(self, name):
        serviceUrl = r'ServicesAPI/globalVariable/gvTree'
        info = self._getUrl(CurrentMethodName(), serviceUrl, '/VariableMapping.html')
        if len(name) and len(info):
            info = self._getJsonObject(info.get('child', []), 'name', name)
        return info

    def _customerEnabled(self, globalVariableID, enabled):
        serviceUrl = r'ServicesAPI/goldenBaseline/gbVariableRule/customerEnabled'
        payload = {
            'gvId': globalVariableID,
            'isCustomerEnabled': enabled
        }
        info = self._postUrl(CurrentMethodName(), serviceUrl, payload, '/VariableMapping.html')
        return info

    def _getGlobalVariableID(self, input, output):
        if len(input) <= 0:
            return True
        for item in input:
            id = item.get('id', None)
            if id is not None:
                value = {
                    'id': id,
                    'name': item['name'],
                    'nodeType': item['nodeType'],
                    'isBuiltIn': item['isBuiltIn']
                }
                output.append(value)
            child = item.get('child', [])
            if len(child):
                self._getGlobalVariableID(child, output)

        return True

    def GoldenBaselineCustomerEnabled(self, name='Built-in Variables', enabled=True):
        globalVariableIDs = list()
        info = self._getGvTree(name)
        self._getGlobalVariableID(info.get('child', []), globalVariableIDs)
        index = 1
        length = len(globalVariableIDs)
        print(f'Global Variable count: {length}', sep='\n')
        length = 0
        for item in globalVariableIDs:
            id = item['id']
            name = item['name']
            type = item['nodeType']
            if type in [2, 3, 4]:
                info = self._customerEnabled(id, enabled)
                strEnabled = True if info.get('isCustomerEnable', -1) == 1 else False
                print(f'{index}: id={id}, name={name}, type={type}, enable={strEnabled}.', sep='\n')
                length += 1
            else:
                print(f'{index}: id={id}, name={name}, type={type} skipped.', sep='\n')
            index += 1
        print(f'Global Variable enabled: {length}', sep='\n')
        return info
    # Golden Baseline end

    # Site Manager start
    def _lockSite(self):
        serviceUrl = r'ServicesAPI/Admin/Domain/lock-site'
        info = self._postUrl(CurrentMethodName(), serviceUrl, {}, '/domainAdmin.html')
        if len(info):
            PrintMessage(''.join([CurrentMethodName(), ' failed: ', json.dumps(info)]), 'Error')
            return False
        else:
            self.SiteLocked = True
            PrintMessage(''.join([CurrentMethodName(), ' passed.']))
            return True

    def _environmentInit(self):
        serviceUrl = r'ServicesAPI/site-manager/environment-init'
        info = self._postUrl(CurrentMethodName(), serviceUrl, {}, '/domainAdmin.html')
        return True

    def _getChildrenSitesByParentAndSelected(self, parentSiteID=0, selectedSiteIds=[]):
        serviceUrl = r'ServicesAPI/site/getChildrenSitesByParentAndSelected'
        payload = {'parentSiteId': parentSiteID, 'selectedSiteIds': selectedSiteIds}
        info = self._postUrl(CurrentMethodName(), serviceUrl, payload, '/domainAdmin.html')
        if len(info):
            PrintMessage(''.join([CurrentMethodName(), ' passed.']))
        else:
            PrintMessage(''.join([CurrentMethodName(), ' failed: ', json.dumps(info)]), 'Error')
        return info

    def _getChildrenSiteByParentSiteID(self, siteID=0):
        serviceUrl = r'ServicesAPI/site-manager/getChildrenSiteByParentSiteID'
        payload = {'siteId': siteID, 'useTemporaryStorage': True, 'ignoreSpecialSite': False}
        info = self._postUrl(CurrentMethodName(), serviceUrl, payload, '/domainAdmin.html')
        if len(info):
            PrintMessage(''.join([CurrentMethodName(), ' passed.']))
        else:
            PrintMessage(''.join([CurrentMethodName(), ' failed: ', json.dumps(info)]), 'Error')
        return info

    def _getSiteDefinitionBySiteID(self, siteID):
        serviceUrl = r'ServicesAPI/site-manager/getSiteDefinitionBySiteID'
        payload = {'siteId': siteID, 'useTemporaryStorage': True}
        info = self._postUrl(CurrentMethodName(), serviceUrl, payload, '/domainAdmin.html')
        if len(info):
            PrintMessage(''.join([CurrentMethodName(), ' passed.']))
        else:
            PrintMessage(''.join([CurrentMethodName(), ': No Site Definition is found.', json.dumps(info)]), 'Error')
        return info

    def _loadSiteFromFile(self, directoryPath):
        serviceUrl = r'ServicesAPI/site-manager/loadSiteFromFile'
        payload = {'directoryPath': urllib.parse.quote_plus(directoryPath)}
        info = self._postUrl(CurrentMethodName(), serviceUrl, payload, '/domainAdmin.html')
        if info:
            PrintMessage(''.join([CurrentMethodName(), ' passed.']))
        else:
            PrintMessage(''.join([CurrentMethodName(), ' failed: ', json.dumps(info)]), 'Error')
        return info

    def _uploadAndLoadSite(self, fileFullName):
        serviceUrl = r'ServicesAPI/ngloadsite/uploadAndLoadSite?access_token='
        url = self.Url + serviceUrl
        headers = self.Headers.copy()
        headers['Referer'] = headers['Origin'] + '/domainAdmin.html'
        #headers['Content-Disposition'] = 'form-data'
        #headers['Content-Type'] = 'multipart/form-data'
        headers['TenantGuid'] = self.TenantID
        headers['DomainGuid'] = self.DomainID
        filename = os.path.basename(fileFullName)
        filesize = os.path.getsize(fileFullName)
        with open(fileFullName, 'rb') as fp:
            fileContent = fp.read()
        files = {'fileName': (None, filename), 'file': (filename, fileContent, 'application/x-zip-compressed')}
        #files = {'file': (filename, fileContent, 'application/x-zip-compressed')}
        info = self._postUrlUpload(CurrentMethodName(), serviceUrl, files, '/desktop.html')
        if len(info):
            PrintMessage(''.join([CurrentMethodName(), ' passed.']))
        '''
        httpResponse = requests.post(url, headers=headers, files=files, verify=False)
        data = httpResponse.request.body
        size = len(data)
        statusCode = httpResponse.status_code
        directoryPath = ''
        ret = HttpReturn.copy()
        ret['statusCode'] = statusCode
        if (statusCode == 200):
            jsonResponse = httpResponse.json()
            ret['resultCode'] = jsonResponse.get('operationResult', {}).get('ResultCode', -1)
            ret['resultDescription'] = jsonResponse.get('operationResult', {}).get('ResultDesc', '')
            ret['data'] = jsonResponse.get('data', {})
            directoryPath = ret['data'].get('directoryPath', '')
        elif (statusCode == 400):
            jsonResponse = httpResponse.json()
            ret['resultCode'] = jsonResponse.get('error', -1)
            ret['resultDescription'] = jsonResponse.get('error_description', '')
            ret['data'] = jsonResponse
        else:
            ret['data'] = httpResponse.text
        '''
        directoryPath = info.get('directoryPath', '')
        if len(directoryPath):
            info = self._loadSiteFromFile(directoryPath)
            PrintMessage(''.join([CurrentMethodName(), ' passed.']))
        else:
            info = False
            PrintMessage(''.join([CurrentMethodName(), ' failed: ', json.dumps(info)]), 'Error')
        return info

    def _commitSite(self, needRebuild=False):
        serviceUrl = r'ServicesAPI/site-manager/commitSite'
        payload = {'useTemporaryStorage': True, 'needToRebuild': needRebuild}
        info = self._postUrl(CurrentMethodName(), serviceUrl, payload, '/domainAdmin.html')
        if type(info) is bool:
            PrintMessage(''.join([CurrentMethodName(), ' passed.']))
            return True
        else:
            PrintMessage(''.join([CurrentMethodName(), ' failed: ', json.dumps(info)]), 'Error')
            return False

    def _unlockSite(self):
        serviceUrl = r'ServicesAPI/site-manager/unlock-site'
        info = self._postUrl(CurrentMethodName(), serviceUrl, {}, '/domainAdmin.html')
        if type(info) is bool:
            self.SiteLocked = False
            PrintMessage(''.join([CurrentMethodName(), ' passed.']))
            return True
        else:
            PrintMessage(''.join([CurrentMethodName(), ' failed: ', json.dumps(info)]), 'Error')
            return False

    def LoadSiteDefinition(self, fileFullName, needRebuild=False):
        info = self._lockSite()
        if info:
            info = self._environmentInit()
            #info = self._getChildrenSitesByParentAndSelected()
            #info = self._getChildrenSiteByParentSiteID()
            #item = self._getJsonObject(info, 'name', 'My Network')
            #info = self._getSiteDefinitionBySiteID(item['ID'])
        if info:
                info = self._uploadAndLoadSite(fileFullName)
        if info:
            info = self._commitSite(needRebuild)
            info = self._unlockSite()
        else:
            info = False
        if info:
            PrintMessage(''.join([CurrentMethodName(), ' passed.']))
        else:
            PrintMessage(''.join([CurrentMethodName(), ' failed.']), 'Error')
        return info

    def _getSiteID(self, siteName, siteID=0):
        info = self._getChildrenSitesByParentAndSelected(siteID)
        info = self._getJsonObject(info, 'name', siteName)
        siteID = info['ID'] if len(info) else ''
        return siteID

    def _addNewSite(self, name, category, parentID):
        serviceUrl = r'ServicesAPI/site-manager/addNewSite'
        #parentID = self._getSiteID(parentName)
        payload = {
            'site':{'ID': CreateGuid(), 'name': name, 'siteCategory': category, 'deviceCount': 0, 'parentId': parentID},
            'useTemporaryStorage': True
        }
        info = self._postUrl(CurrentMethodName(), serviceUrl, payload, '/domainAdmin.html')
        if len(info):
            PrintMessage(''.join([CurrentMethodName(), ' passed.']))
            return info
        else:
            PrintMessage(''.join([CurrentMethodName(), ' failed: ']), 'Error')
            return ''

    def _modifySite(self, name, siteID):
        serviceUrl = r'ServicesAPI/site-manager/commitSite'
        #parentID = self._getSiteID(parentName)
        payload = {'site': {'ID': siteID, 'name': name}, 'useTemporaryStorage': True}
        info = self._postUrl(CurrentMethodName(), serviceUrl, payload, '/domainAdmin.html')
        if type(info) is bool and info:
            PrintMessage(''.join([CurrentMethodName(), ' passed.']))
        else:
            PrintMessage(''.join([CurrentMethodName(), ' failed: ', json.dumps(info)]), 'Error')
        return info

    def _removeSite(self, siteID):
        serviceUrl = r'ServicesAPI/site-manager/removeSite'
        payload = {'siteID': siteID, 'useTemporaryStorage': True}
        info = self._postUrl(CurrentMethodName(), serviceUrl, payload, '/domainAdmin.html')
        if type(info) is bool and info:
            PrintMessage(''.join([CurrentMethodName(), ' passed.']))
        else:
            PrintMessage(''.join([CurrentMethodName(), ' failed: ', json.dumps(info)]), 'Error')
        return info

    def _addManuallyAddedMember(self, siteID, deviceIDs):
        serviceUrl = r'ServicesAPI/site-manager/addManuallyAddedMember'
        payload = {'siteId': siteID, 'deviceIds': deviceIDs, 'useTemporaryStorage': True}
        info = self._postUrl(CurrentMethodName(), serviceUrl, payload, '/domainAdmin.html')
        if type(info) is bool and info:
            PrintMessage(''.join([CurrentMethodName(), ' passed.']))
        else:
            PrintMessage(''.join([CurrentMethodName(), ' failed: ', json.dumps(info)]), 'Error')
        return info

    def AddSite(self, siteInfo):
        name = siteInfo['Name']
        category = siteInfo['Category']
        if type(category) is str:
            category = 1 if category.lower() == 'container' else 2 # leaf
        parentPath = siteInfo['Parent Path'].split('\\')
        if len(parentPath) < 1:
            PrintMessage('AddSite: Please define the parent name.', 'Error')
            return False
        parentID = 0
        for parentName in parentPath:
            parentID = self._getSiteID(parentName, parentID)
        info = self._addNewSite(name, category, parentID)
        if len(info):
            # add devices
            self._addManuallyAddedMember(info, siteInfo['DeviceIPs'])
            return True
        else:
            return False

    def getSiteDevicesBySiteIDWithFilter(self, site_id, device_name):
        if device_name is None or device_name == '':
            return {}
        serviceUrl = r'ServicesAPI/site/getSiteDevicesBySiteIDWithFilter'
        payload = {
            'siteId': site_id,
            'filterFields': ['name', 'model', 'mgmtIP', 'vendor'],
            'filterValue': device_name,
            'sortField': 'deviceName',
            'sortOrder': 'asc',
            'pageNumber': 1,
            'pageSize': 100,
            'type': 4}
        info = self._postUrl(CurrentMethodName(), serviceUrl, payload, '/desktop.html')
        if len(info):
            PrintMessage(''.join([CurrentMethodName(), ' passed.']))
        else:
            PrintMessage(''.join([CurrentMethodName(), ' failed.']))
        return info

    # Site Manager  end

    # Import Map start
    def _desktopAll(self):
        serviceUrl = r'ServicesAPI/networkos/desktop/all'
        payload = {'h': 16, 'v': 7}
        info = self._postUrl(CurrentMethodName(), serviceUrl, payload, '/desktop.html')
        if len(info):
            PrintMessage(''.join([CurrentMethodName(), ' passed.']))
        else:
            PrintMessage(''.join([CurrentMethodName(), ' failed: ', json.dumps(info)]), 'Error')
        return info

    def _getDesktopFolderID(self):
        info = self._desktopAll()
        for item in info['desktopItems']:
            if item.get('folder', {}).get('name', '') == 'Desktop':
                folderId = item.get('folder', {}).get('id', '')
                break
        if len(folderId) <= 0:
            PrintMessage(''.join([CurrentMethodName(), ': failed to get Desktop ID.']), 'Error')
            return ''
        return folderId

    def _getServerUploadLimitSize(self):
        serviceUrl = r'ServicesAPI/networkos/files/getServerUploadLimitSize'
        info = self._getUrl(CurrentMethodName(), serviceUrl, '/desktop.html')
        if len(info):
            PrintMessage(''.join([CurrentMethodName(), ' passed.']))
        else:
            PrintMessage(''.join([CurrentMethodName(), ' failed: ', json.dumps(info)]), 'Error')
        return info

    def _checkMapNameExist(self, mapNames, desktopFolderID=None):
        serviceUrl = r'ServicesAPI/map/checkMapNameExist'
        folderID = self._getDesktopFolderID() if desktopFolderID is None else desktopFolderID
        if folderID == '':
            PrintMessage(''.join([CurrentMethodName(), ' failed.']), 'Error')
            return {}
        mapNameList = list()
        for mapName in mapNames:
            mapNameList.append({'mapName': os.path.splitext(mapName)[0], 'mapId': CreateGuid(), 'isExisted': False})
        payload = {'FolderId': folderID, 'CheckMapNameList': mapNameList}
        info = self._postUrl(CurrentMethodName(), serviceUrl, payload, '/desktop.html')
        if len(info):
            PrintMessage(''.join([CurrentMethodName(), ' passed.']))
        else:
            PrintMessage(''.join([CurrentMethodName(), ' failed: ', json.dumps(info)]), 'Error')
        return info

    def _fileUploadRestrictionToken(self, source='1'):
        serviceUrl = r'ServicesAPI/FileUploadRestriction/token/1' + source
        info = self._getUrl(CurrentMethodName(), serviceUrl, '/desktop.html')
        if len(info):
            PrintMessage(''.join([CurrentMethodName(), ' passed.']))
        else:
            PrintMessage(''.join([CurrentMethodName(), ' failed: ', json.dumps(info)]), 'Error')
        return info

    def ImportMap(self, fileFullName, renameDuplicated=False):
        folderId = self._getDesktopFolderID()
        if folderId == '':
            PrintMessage(''.join([CurrentMethodName(), ' failed.']), 'Error')
            return {}
        filename = os.path.basename(fileFullName)
        self._checkMapNameExist([filename], folderId)
        self.UploadToken = self._fileUploadRestrictionToken()
        with open(fileFullName, 'rb') as fp:
            fileContent = fp.read()

        if renameDuplicated:
            serviceUrl = ''.join([r'ServicesAPI/map/importMap/', folderId, r'/true'])
        else:
            serviceUrl = ''.join([r'ServicesAPI/map/importMap/', folderId, r'/false'])
        if self.CurrentVersion > 8.02:  # in ['8.03', '8.1-G']:
            serviceUrl += f'?uploadToken={self.UploadToken}';
        files = {'file': (filename, fileContent, 'application/octet-stream')}
        info = self._postUrlUpload(CurrentMethodName(), serviceUrl, files, '/desktop.html')
        if len(info):
            PrintMessage(''.join([CurrentMethodName(), ' passed.']))
        return info
    # Import Map end

    # Change Analysis start
    def _getChangeAnalysisSetting(self):
        serviceUrl = r'ServicesAPI/Admin/Domain/getChangeAnalysisSetting'
        info = self._getUrl(CurrentMethodName(), serviceUrl, '/desktop.html')
        if len(info):
            PrintMessage(''.join([CurrentMethodName(), ' passed.']))
        else:
            PrintMessage(''.join([CurrentMethodName(), ' failed: ', json.dumps(info)]), 'Error')
        return info

    def _updateChangeAnalysisSetting(self, caSetting):
        serviceUrl = r'ServicesAPI/Admin/Domain/updateChangeAnalysisSetting'
        info = self._postUrl(CurrentMethodName(), serviceUrl, caSetting, '/domainAdmin.html')
        if info:
            PrintMessage(''.join([CurrentMethodName(), ' passed.']))
        else:
            PrintMessage(''.join([CurrentMethodName(), ' failed: ', json.dumps(info)]), 'Error')
        return info

    def EnableChangeAnalysis(self, config):
        # Operations->Domain Settings->Change Analysis Setting
        nctTableNames = self._getNctTableNames()
        caSetting = self._getChangeAnalysisSetting()
        if len(caSetting):
            caSetting['caEnabled'] = config.get('Enable Change Analysis', True)
            liveData = config['Built-in Live Data']
            if 'Configuration File' in liveData:
                caSetting['configurationFile'] = True
                liveData.remove('Configuration File')
            else:
                caSetting['configurationFile'] = False
            caSetting['systemTable'] = liveData
            caSetting['nctTable'] = nctTableNames.get('ncts', [])
            info = self._updateChangeAnalysisSetting(caSetting)
        else:
            PrintMessage(''.join([CurrentMethodName(), ' failed to get Change Analysis Setting.']), 'Error')
            return False
        PrintMessage(''.join([CurrentMethodName(), ' passed']))
        return True

    # Change Analysis end

    # Service Monitor start
    def PublicKey(self):
        serviceUrl = r"ServicesAPI/ServiceMonitor/publicKey"
        info = self._postUrl(CurrentMethodName(), serviceUrl, {})

        return info

    def ServiceMonitorLogin(self, username, password):
        # Log into system and generate access token
        encryptPassword = self.PasswordEncrypt(password)
        if encryptPassword == '':
            PrintMessage('GenerateAccessToken failed', 'Error')
            return {}

        serviceUrl = r'ServicesAPI/ServiceMonitor/login'
        url = self.Url + serviceUrl
        payload = {
            'grant_type': 'password',
            'username': username,
            'password': encryptPassword,
            'client_id': 'service_monitor',
            'scope': 'service_monitor_ui'
        }

        info = self._postUrl(CurrentMethodName(), serviceUrl, payload, '/monitor.html')
        if len(info) <= 0:
            PrintMessage(''.join([CurrentMethodName(), ' failed.']), 'Error')
        return info

    # Service Monitor end

    # Domain Health Report start
    def DomainHealthReport(self):
        serviceUrl = r"ServicesAPI/DomainHealthReport/report"
        info = self._getUrl(CurrentMethodName(), serviceUrl, '/domainAdmin.html')

        return info
    # Domain Health Report end

    # CheckPoint OPSEC Manager start
    def _getOpsec(self):
        serviceUrl = r'ServicesAPI/opsec'
        info = self._getUrl(CurrentMethodName(), serviceUrl, '/domainAdmin.html')
        if len(info):
            PrintMessage(''.join([CurrentMethodName(), ' passed.']))
        else:
            PrintMessage(''.join([CurrentMethodName(), ' failed.']), 'Error')
        return info

    def _getZones(self):
        serviceUrl = r'ServicesAPI/topology/zones'
        info = self._getUrl(CurrentMethodName(), serviceUrl, '/domainAdmin.html')
        if len(info):
            PrintMessage(''.join([CurrentMethodName(), ' passed.']))
        else:
            PrintMessage(''.join([CurrentMethodName(), ' failed.']), 'Error')
        return info

    def _getSubnets(self):
        serviceUrl = r'ServicesAPI/topology/subnets'
        payload = {'zoneId': '', 'begin': 0, 'count': 5000, 'sortOrder': 'asc', 'onlyGetIpConflicted': True,
                   'filterFields': ['subnet', 'deviceName', 'ipInterfaceName', 'ip', 'vrf', 'description'],
                   'filterString': ''}
        info = self._postUrl(CurrentMethodName(), serviceUrl, payload, '/domainAdmin.html')
        if len(info):
            PrintMessage(''.join([CurrentMethodName(), ' passed.']))
        else:
            PrintMessage(''.join([CurrentMethodName(), ' failed.']), 'Error')
        return info

    def GetCheckPointOPSEC(self):
        return self._getOpsec()

    def GetDiscoveryStatusInDomainHealthReport(self):
        domain_summary = self._getDomainSummary()
        device_count_list = self._deviceCountList()
        zones = self._getZones()
        subnets = self._getSubnets()
        return {'Domain Summary': domain_summary, 'Device Count List': device_count_list, 'Zones': zones,
                'Subnets': subnets}

    # CheckPoint OPSEC Manager end

    # Feature Device Setting start
    def getSafeDeviceSettingByGuid(self, guid):
        if guid is None or guid == '':
            return {}
        serviceUrl = r'ServicesAPI/DataModel/getSafeDeviceSettingByGuid/' + guid
        info = self._getUrl(CurrentMethodName(), serviceUrl, '/desktop.html')
        if len(info):
            PrintMessage(''.join([CurrentMethodName(), ' passed.']))
        else:
            PrintMessage(''.join([CurrentMethodName(), ' failed.']), 'Error')
        return info

    def tuneDeviceSetting(self, device_setting):
        serviceUrl = r'ServicesAPI/DataModel/tuneDeviceSetting'
        task_id = CreateGuid()
        client_id = CreateGuid()
        payload = {
            'deviceSetting': device_setting,
            'taskId': task_id,
            'hubClientId': 'mainUI_' + client_id
        }
        payload['deviceSetting'].update({'taskId': task_id})
        info = self._postUrl(CurrentMethodName(), serviceUrl, payload, '/desktop.html')
        if len(info):
            PrintMessage(''.join([CurrentMethodName(), ' passed.']))
        else:
            PrintMessage(''.join([CurrentMethodName(), ' failed.']), 'Error')
        return info

    # Feature Device Settingend

    # FID start
    def fid_tree(self):
        serviceUrl = r'ServicesAPI/fid/tree'
        info = self._getUrl(CurrentMethodName(), serviceUrl, '/fidManager.html')
        if len(info):
            PrintMessage(''.join([CurrentMethodName(), ' passed.']))
        else:
            PrintMessage(''.join([CurrentMethodName(), ' failed.']), 'Error')
        return info

    def get_fid_by_name(self, name:str, fid_tree=None):
        # name: MyFID
        if fid_tree is None:
            fid_tree = self.fid_tree()
        fid = next((item for item in fid_tree['results'] if item.get("name") and item["name"] == name), {})
        return fid

    def get_fid_folder(self, path:str, fid_tree=None):
        # path： Shared Feature Intent Template/MyFID
        if fid_tree is None:
            fid_tree = self.fid_tree()
        path_split = path.replace('\\', '/').split('/')
        if len(path_split) <= 1:
            parent_folder = 'Built-in Feature Intent Template'
            name = path
        else:
            parent_folder = path_split[-2]
            name = path_split[-1]
        fid_parent = next((item for item in fid_tree['results'] if item.get("name") and item["name"] == parent_folder), None)
        if fid_parent is None:
            PrintMessage(f'the folder "{parent_folder}" is not exist.', 'Error')
            return None
        fid_parent_id = fid_parent['_id']
        # fid = {}
        # for item in fid_tree['results']:
        #     if item['name'] == name and item['parentId'] == fid_parent_id:
        #         fid = item
        #         break
        fid = next((item for item in fid_tree['results'] if item["name"] == name and item["parentId"] == fid_parent_id), None)
        return fid

    def fid_add_tree_folder_by_id(self, folder_name, parent_id):
        serviceUrl = r'ServicesAPI/fid/tree/folder'
        payload = {
            'folderName': folder_name,
            'parentId': parent_id
        }
        info = self._postUrl(CurrentMethodName(), serviceUrl, payload, '/fidManager.html')
        if len(info):
            PrintMessage(''.join([CurrentMethodName(), ' passed.']))
        else:
            PrintMessage(''.join([CurrentMethodName(), ' failed.']), 'Error')
        return info

    def fid_add_tree_folder_by_name(self, folder_name, parent_name):
        fid = self.get_fid_by_name(parent_name)
        return self.fid_add_tree_folder_by_id(folder_name, fid.get('_id', 4))

    def fid_import(self, folder_name, import_fullname):
        serviceUrl = r'ServicesAPI/fid/import'
        fid = self.get_fid_by_name(folder_name)
        filename = os.path.basename(import_fullname)
        with open(import_fullname, 'rb') as fp:
            fileContent = fp.read()
        payload = ''.join(['{"parentId":"', fid.get('_id', 4), '"}'])
        files = {'payload': (None, payload), 'file': (filename, fileContent, 'application/octet-stream')} #"{'parentId': '245ff6a7-246f-43a2-b72f-378de72f7f90'}"
        info = self._postUrlUpload(CurrentMethodName(), serviceUrl, files, '/fidManager.html', '', '')
        if len(info):
            PrintMessage(''.join([CurrentMethodName(), ' passed.']))
        else:
            PrintMessage(''.join([CurrentMethodName(), ' failed.']), 'Error')
        return info

    def fid_import_many(self, fid_folder:dict, import_fullnames:list):
        # fid_folder: {'_id': '37dcf85b-fc26-42f8-ba19-4e803769e129', 'name': 'MyFID', 'accessType': 4, 'type': 1, 'parentId': '4'}
        serviceUrl = r'ServicesAPI/fid/import'
        fid_all = self.fid_tree()
        # fid_folder = self.get_fid_by_name(folder_name)
        # if fid_folder is None:
        #     PrintMessage(''.join([CurrentMethodName(), f' the parent folder "{folder_name}" is not exist.']), 'Error')
        #     return {}
        file_contents = []
        for fullname in import_fullnames:
            name = NetBrainUtils.ParseFilename(fullname)
            fid = next((item for item in fid_all['results'] if item.get('name', None) == name['FilenameWithOutExtension']), None)
            if fid is None:
                with open(fullname, 'rb') as fp:
                    file_content = fp.read()
                file_contents.append((name['Filename'], file_content, 'application/octet-stream'))
            else:
                PrintMessage(f'{name["FilenameWithOutExtension"]} is exist, skipped.', 'Warning')
        item = ''.join(['{"parentId":"', fid_folder.get('_id', 4), '"}'])
        payload = {'payload': (None, item)}
        for i, item in enumerate(file_contents, start=1):
            payload[f'file{i}'] = item
        info = self._postUrlUpload(CurrentMethodName(), serviceUrl, payload, '/fidManager.html', '', '')
        if len(info):
            PrintMessage(''.join([CurrentMethodName(), ' passed.']))
        else:
            PrintMessage(''.join([CurrentMethodName(), ' failed.']), 'Error')
        return info

    def fid_delete_folder_by_id(self, folder_id):
        serviceUrl = r'ServicesAPI/fid/tree/folder/' + folder_id
        info = self._deleteUrl(CurrentMethodName(), serviceUrl, {}, r'/fidManager.html')
        if info:
            PrintMessage(CurrentMethodName() + ' passed.')
            return True
        else:
            PrintMessage(CurrentMethodName() + ' failed.', 'Error')
            return False

    def fid_delete_folder_by_name(self, folder_name):
        fid = self.get_fid_by_name(folder_name)
        return self.fid_delete_folder_by_id(fid.get('_id', 4))

    def fid_delete_fid_by_id(self, fid_id):
        serviceUrl = r'ServicesAPI/fid/' + fid_id
        info = self._deleteUrl(CurrentMethodName(), serviceUrl, {}, r'/fidManager.html')
        if info:
            PrintMessage(CurrentMethodName() + ' passed.')
            return True
        else:
            PrintMessage(CurrentMethodName() + ' failed.', 'Error')
            return False

    def fid_delete_fid_by_name(self, fid_name):
        fid = self.get_fid_by_name(fid_name)
        return self.fid_delete_fid_by_id(fid.get('_id', 4))

    def fid_current_status(self, fid_id):
        serviceUrl = r'ServicesAPI/fid/execution/current/' + fid_id
        info = self._getUrl(CurrentMethodName(), serviceUrl, '/fidManager.html')
        # if len(info):
        #     PrintMessage(''.join([CurrentMethodName(), ' passed.']))
        # else:
        #     PrintMessage(''.join([CurrentMethodName(), ' failed.']), 'Error')
        return info

    def wait_fid_execution_complete(self, fid_id):
        # wait 6 hours, 6*3600=21600
        check_interval = 5
        wait_duration = int( 6 * 3600 / check_interval)
        minute_tick = int(60 / check_interval)
        i = 0
        while i < wait_duration:
            sleep(check_interval)
            status = self.fid_current_status(fid_id)
            i += 1  # check_interval
            current_status = status.get('current', {})
            if current_status == {}:
                continue
            if current_status is None:
                break
            if i % minute_tick == 0:  # print message every minute
                current_status = status.get('current', {}).get('status', -1)
                if current_status > 0:
                    PrintMessage(f'status = {current_status}.')
        return status

    def fid_execution(self, fid_path:str, device_ids:list, debug_mode=False):
        serviceUrl = r'ServicesAPI/fid/execution'
        payload = {
            'debugMode': debug_mode,
            'deviceIds': device_ids,
            'fidPath': fid_path
        }
        info = self._postUrl(CurrentMethodName(), serviceUrl, payload, '/fidManager.html')
        PrintMessage(CurrentMethodName() + f' {fid_path} completed.')
        return True

    # FID end

    # ParseLibrary start
    def parserlib_category(self):
        serviceUrl = r'ServicesAPI/ParserLib/Category'
        info = self._getUrl(CurrentMethodName(), serviceUrl, '/desktop.html')
        if len(info):
            PrintMessage(''.join([CurrentMethodName(), ' passed.']))
        else:
            PrintMessage(''.join([CurrentMethodName(), ' failed.']), 'Error')
        return info

    def resourceio_inventory(self, inventory_info):
        serviceUrl = r'ServicesAPI/resourceIO/inventory'
        filename = os.path.basename(inventory_info['fullname'])
        with open(inventory_info['fullname'], 'rb') as fp:
            fileContent = base64.b64encode((fp.read()))
            fp.seek(4)
            len_summary, = struct.unpack('i', fp.read(4))
            len_list, = struct.unpack('i', fp.read(4))
        payload = {
            'packageVersion': 1,
            'summaryDataLength': len_summary,
            'listDataLength': len_list,
            'packageFileName': filename,
            'base64Data': fileContent.decode(),
            'expectedImportLocation': {'space': inventory_info['space'], 'location': inventory_info['location']},
            'options': {'dependencyType': 1, 'locationType': 1}
        }
        info = self._postUrl(CurrentMethodName(), serviceUrl, payload, '/desktop.html')
        if len(info):
            PrintMessage(''.join([CurrentMethodName(), ' passed.']))
        else:
            PrintMessage(''.join([CurrentMethodName(), ' failed.']), 'Error')
        #info['fileContent'] = payload['']
        return info

    def parser_create_folder(self, folder_info):
        serviceUrl = r'ServicesAPI/ParserLib/Category'
        payload = {
            'id': CreateGuid(),
            'name': folder_info['name'],
            'parentId': folder_info['parentId'],
            'accessType': folder_info['accessType']
        }
        info = self._postUrl(CurrentMethodName(), serviceUrl, payload, '/desktop.html')
        PrintMessage(''.join([CurrentMethodName(), ' passed.']))
        return True

    def parser_import(self, parser_fullname, parent_name, parser_lib=None, import_token=None):
        parent_name = parent_name.replace('Shared Parsers in Tenant', 'Shared Files in Tenant')
        if parser_lib is None:
            parser_lib = self.parserlib_category()
        parent_names = parent_name.split('\\')
        parent_node = next((item for item in parser_lib['nodes'] if item.get("name") and item["name"] == parent_names[0]), None)
        if parent_node is None:
            PrintMessage(''.join([CurrentMethodName(), ': ', parent_name, 'is not existed']), 'Warning')
            return False
        sub_node = next((item for item in parent_node['nodes'] if item.get("name") and item["name"] == parent_names[1]), None)
        if sub_node is None:
            folder_info = {
                'parentId': parent_node['id'],
                'accessType': parent_node['accessType'],
                'name': parent_names[1]
            }
            self.parser_create_folder(folder_info)
        if import_token is None:
            import_token = self._fileUploadRestrictionToken('1')
        location = '/' if len(parent_names) < 2 else ''.join(['/', parent_names[1], '/'])
        inventory_info = {
            'space': parent_node['accessType'],
            'location': location,
            'fullname': parser_fullname
        }
        inventory = self.resourceio_inventory(inventory_info)
        serviceUrl = r'ServicesAPI/resourceIO/import?uploadToken=' + import_token
        filename = os.path.basename(parser_fullname)
        parser_name = os.path.splitext(filename)[0]
        with open(parser_fullname, 'rb') as fp:
            fileContent = fp.read() # base64.b64encode((fp.read()))
        key = ''.join(['{"path":"Shared Files in Tenant/', parser_name, '","type":"Parser"}'])
        payload = {
            'expectedImportLocation': {'space': parent_node['accessType'], 'location': location},
            # 'resources': [
            #     {
            #         'size': os.path.getsize(parser_fullname),
            #         'dependencies': [],
            #         'counts': None,
            #         'key': urllib.parse.quote(key),
            #         'type': 'Parser',
            #         'isExists': False,
            #         'name': parser_name,
            #         'space': parent_node['accessType'], 'location': location
            #     }],
            'resources': inventory['resources'],
            'options': {'jobId': CreateGuid()}
        }
        #files = {'json': (None, json.dumps(payload).encode('utf-8')), 'file': (filename, fileContent, 'application/octet-stream')}
        files = {'json': (None, json.dumps(payload)),
                 'file': (filename, fileContent, 'application/octet-stream')}
        info = self._postUrlUpload(CurrentMethodName(), serviceUrl, files, '/desktop.html')
        if len(info):
            PrintMessage(''.join([CurrentMethodName(), ' passed.']))
            time.sleep(2)
        else:
            PrintMessage(''.join([CurrentMethodName(), ' failed.']), 'Error')
        time.sleep(1)
        return info

    def parser_delete_parser_by_id(self, parent_id:str, parser_id:str):
        serviceUrl = ''.join([r'ServicesAPI/ParserLib/Parser/', parent_id, '/', parser_id])
        info = self._deleteUrl(CurrentMethodName(), serviceUrl, {}, r'/desktop.html')
        if info:
            PrintMessage(CurrentMethodName() + ' passed.')
            return True
        else:
            PrintMessage(CurrentMethodName() + ' failed.', 'Error')
            return False

    def parser_delete_parser_by_name(self, parent_name:str, parser_name:str):
        parser_lib = self.parserlib_category()
        parent = next((item for item in parser_lib['nodes'] if item.get("name") and item["name"] == parent_name), None)
        if parent is None:
            PrintMessage(''.join([CurrentMethodName(), ': ', parent_name, 'is not existed']), 'Warning')
            return True
        parser = next((item for item in parser_lib['nodes'] if item.get("name") and item["name"] == parent_name), None)
        if parser is None:
            PrintMessage(''.join([CurrentMethodName(), ': ', parser_name, 'is not existed']), 'Warning')
            return True
        return self.parser_delete_fid_by_id(parent.get('id'), parser['id'])

    def getAccessType(self, parser_id:str):
        serviceUrl = r'ServicesAPI/ParserLib/Category/getAccessType/' + parser_id
        info = self._getUrl(CurrentMethodName(), serviceUrl, '/parser.html')
        PrintMessage(''.join([CurrentMethodName(), ' passed.']))
        return info

    def KCVerification(self):
        serviceUrl = r'ServicesAPI/KCVerification'
        info = self._getUrl(CurrentMethodName(), serviceUrl, '/parser.html')
        if info:
            PrintMessage(''.join([CurrentMethodName(), ' passed.']))
        else:
            PrintMessage(''.join([CurrentMethodName(), ' failed.']), 'Error')
        return info

    def parser_get(self, parser_id:str):
        serviceUrl = r'ServicesAPI/ParserLib/Parser/' + parser_id
        info = self._getUrl(CurrentMethodName(), serviceUrl, '/desktop.html')
        if len(info):
            PrintMessage(''.join([CurrentMethodName(), ' passed.']))
        else:
            PrintMessage(''.join([CurrentMethodName(), ' failed.']), 'Error')
        return info

    def parser_save(self, payload:dict):
        serviceUrl = r'ServicesAPI/ParserLib/Parser/'
        info = self._putUrl(CurrentMethodName(), serviceUrl, payload, '/parser.html')
        PrintMessage(''.join([CurrentMethodName(), ' complete.']))
        return True

    def RemoveParsersQualify(self, parser_path, parser_category=None):
        if parser_category is None:
            parsers = self.parserlib_category()
        else:
            parsers = parser_category
        path = parser_path.split('/')
        level = len(path) - 1
        for i in range(0, level):
            parsers = next((item for item in parsers['nodes'] if item.get("name") and item["name"] == path[i]),
                           None)
            if parsers is None:
                PrintMessage(''.join(['The parser "', parser_path, '" do NOT exist.']), 'Warning')
                return True
        if parsers is not None:
            parser = next(
                (item for item in parsers['parsers'] if item.get("name") and item["name"] == path[level]), None)
        if parser is None:
            PrintMessage(''.join(['The parser "', parser_path, '" do NOT exist.']), 'Warning')
            return True
        parser = self.parser_get(parser['id'])
        if len(parser.get('qualify', {}).get('Conditions', [])) <= 0:
            PrintMessage(''.join([CurrentMethodName(), ': The qualify condition of "', parser_path, '" is skipped.']), 'Warning')
            return True
        #ret = self.getAccessType(parser['id'])
        ret = self.KCVerification()
        if not ret:
            PrintMessage('No permission to change parser', 'Error')
            return False
        payload = {
            'id': parser['id'],
            'name': parser['name'],
            'author': parser['author'],
            'accessType': parser['accessType'],
            'command': parser['command'],
            'devTypes': parser['devTypes'],
            'supportNodeType': parser['supportNodeType'],
            'params': parser['params'],
            'version': parser['version'],
            'description': parser['description'],
            'type': parser['type'],
            'subtype': '',
            'qualify': {'Expression': '', 'Conditions': []},
            'bizType': parser['bizType'],
            'samples': parser['samples'],
            'sequences': parser['sequences'],
            'variables': parser['variables'],
        }
        self.parser_save(payload)
        PrintMessage(''.join([CurrentMethodName(), ': The qualify condition of "', parser_path, '" is removed.']))
        time.sleep(1)
        return True

    # ParseLibrary end

    # FlashProbe start
    def flashprobe_add(self, payload):
        serviceUrl = r'ServicesAPI/AdaptiveMonitor/FlashProbes'
        info = self._postUrl(CurrentMethodName(), serviceUrl, payload, '/adaptiveAutomationManager.html')
        if info:
            PrintMessage(' '.join([CurrentMethodName(), payload['name'], 'passed.']))
        else:
            PrintMessage(' '.join([CurrentMethodName(), payload['name'],'failed.']), 'Error')
        return info

    def flashprobe_delete(self, flashprobe_ids):
        serviceUrl = r'ServicesAPI/AdaptiveMonitor/FlashProbes'
        payload = {'ids': flashprobe_ids, 'type': 0}
        info = self._deleteUrl(CurrentMethodName(), serviceUrl, payload, r'/adaptiveAutomationManager.html')
        if info:
            PrintMessage(CurrentMethodName() + ' passed.')
            return True
        else:
            PrintMessage(CurrentMethodName() + ' failed.', 'Error')
            return False

    def flashprobes_search(self, device_id):
        serviceUrl = r'ServicesAPI/AdaptiveMonitor/FlashProbes/Search'
        payload = {
            'nodePathSchema': 'Legacy',
            'nodePathValue': device_id,
            'type':1,
            'pageSize': 50000,
            'pageIndex': 1,
            'filterContent': '',
            'filterFields': ['displayName', 'intfName', 'desc', 'createSrc.name', 'operateInfo.opUser'],
            'sortField': 'displayName',
            'sortOrder': 'asc'
        }
        info = self._postUrl(CurrentMethodName(), serviceUrl, payload, '/adaptiveAutomationManager.html')
        if info:
            PrintMessage(''.join([CurrentMethodName(), ' passed.']))
        else:
            PrintMessage(''.join([CurrentMethodName(), ' failed.']), 'Error')
        return info

    def getDevicesByTypesByPaging(self, device_types=[2001]):
        serviceUrl = r'ServicesAPI/DataModel/getDevicesByTypesByPaging'
        payload = {
            'types': device_types,
            'pageSize': 5000,
            'pageNumber': 0,
            'filterField': ['name'],
            'filterContent': '',
            'isNeedSdnNetworkDevice': False,
            'sortField': 'name',
            'sortOrder': 'asc'
        }
        info = self._postUrl(CurrentMethodName(), serviceUrl, payload, '/adaptiveAutomationManager.html')
        if len(info) > 0:
            PrintMessage(''.join([CurrentMethodName(), ' passed.']))
        else:
            PrintMessage(''.join([CurrentMethodName(), ' failed.']), 'Error')
        return info

    def flashprobe_search_by_name(self, device_name):
        devices = self.getDevicesByTypesByPaging()
        if devices['count'] <= 0:
            PrintMessage('no device which subtype is 2001 is found.', 'Warning')
            return True
        device_id = next((item['ID'] for item in devices['deviceList'] if item.get("name") and item["name"] == device_name), None)
        if device_id is None:
            PrintMessage(f'the device "{device_name}" is found.', 'Warning')
            return True
        return self.flashprobe_search(device_id)

    def flashprobes_enable(self, probes:dict, enabled:bool):
        if len(probes.get('ids', [])) <= 0:
            PrintMessage(''.join([CurrentMethodName(), ': no flash probe need to be enabled/disabled.']), 'Warning')
            return True
        serviceUrl = r'ServicesAPI/AdaptiveMonitor/FlashProbes/EnableSetting'
        payload = {
            'type': probes['type'],
            'ids': probes['ids'],
            'isEnable': enabled,
            'resType': 0
        }
        info = self._patchUrl(CurrentMethodName(), serviceUrl, payload, '/adaptiveAutomationManager.html')
        if info == len(probes['ids']):
            PrintMessage(''.join([CurrentMethodName(), ' passed.']))
        else:
            PrintMessage(''.join([CurrentMethodName(), ' failed.']), 'Error')
        return info

    def flashprobes_apply(self, probe_id, apply_devices:list, apply_flashprobe_ids:list, probe_type=1):
        '''
        :param probe_id:
        :param apply_devices: [{
			"devId": "03f57a95-ae9a-426a-8471-f1000f0634ed",
			"devName": "ustb000000",
			"devTypeId": 2
		}]
		:param apply_devices: ['36d1352119d5707c134897a3eb235240']
        :param probe_type: 1 # primary probe
        :return: {"operationResult":{"ResultCode":0,"ResultDesc":"Operation Successful"},"data":{"count":123}}
        '''
        serviceUrl = r'ServicesAPI/AdaptiveMonitor/FlashProbes/Apply'
        payload = {
            'id': probe_id,
            'type': probe_type,
            'devAndIntfs': apply_devices,
            'duplicatedFPIds': apply_flashprobe_ids
        }
        info = self._postUrl(CurrentMethodName(), serviceUrl, payload, '/adaptiveAutomationManager.html')
        if info['count'] == len(apply_flashprobe_ids):
            PrintMessage(''.join([CurrentMethodName(), ' passed.']))
        else:
            PrintMessage(''.join([CurrentMethodName(), ' failed.']), 'Error')
        return info

    def DefaultPollingFrequency_Get(self):
        serviceUrl = r'ServicesAPI/AdaptiveMonitor/AMGlobalSettings/DefaultPollingFrequency'
        info = self._getUrl(CurrentMethodName(), serviceUrl, '/adaptiveAutomationManager.html')
        if len(info) > 0:
            PrintMessage(''.join([CurrentMethodName(), ' passed.']))
        else:
            PrintMessage(''.join([CurrentMethodName(), ' failed.']), 'Error')
        return info

    def DefaultPollingFrequency(self, default_frequency:int):
        serviceUrl = r'ServicesAPI/AdaptiveMonitor/AMGlobalSettings/DefaultPollingFrequency'
        payload = {
            'setting': default_frequency
        }
        info = self._putUrl(CurrentMethodName(), serviceUrl, payload, '/adaptiveAutomationManager.html')
        if info:
            PrintMessage(''.join([CurrentMethodName(), ' passed.']))
        else:
            PrintMessage(''.join([CurrentMethodName(), ' failed.']), 'Error')
        return info

    def PollingEnabledStatus(self, enabled:bool):
        serviceUrl = r'ServicesAPI/AdaptiveMonitor/AMGlobalSettings/PollingEnabledStatus'
        payload = {
            'setting': enabled
        }
        info = self._putUrl(CurrentMethodName(), serviceUrl, payload, '/adaptiveAutomationManager.html')
        if info:
            PrintMessage(''.join([CurrentMethodName(), ' passed.']))
        else:
            PrintMessage(''.join([CurrentMethodName(), ' failed.']), 'Error')
        return info

    def flashprobe_get(self, flashprobe_id:str):  # retrieve flashprobe
        serviceUrl = r'ServicesAPI/AdaptiveMonitor/FlashProbes/' + flashprobe_id
        info = self._getUrl(CurrentMethodName(), serviceUrl, r'/proactiveAutomationManager.html')
        if len(info) > 0:
            PrintMessage(CurrentMethodName() + ' passed.')
        else:
            PrintMessage(CurrentMethodName() + ' failed.', 'Error')
        return info

    def flashprobes_save(self, flashprobe_id, payload):
        serviceUrl = r'ServicesAPI/AdaptiveMonitor/FlashProbes/' + flashprobe_id
        info = self._putUrl(CurrentMethodName(), serviceUrl, payload, '/proactiveAutomationManager.html')
        if info:
            PrintMessage(''.join([CurrentMethodName(), ' passed.']))
        else:
            PrintMessage(''.join([CurrentMethodName(), ' failed.']), 'Error')
        return info

    # FlashProbe end

    # NetworkIntent start
    def NICategories(self, name):  # create NI Folder
        serviceUrl = r'ServicesAPI/NICategories'
        payload = {
            'nodeType': 0,
            'id': CreateGuid(),  # 'f896301e-afb2-86f9-0ff0-f260d46f3272',
            'type': 1,
            'accessType': 1,
            'parentId': '0',
            'name': name
        }
        info = self._postUrl(CurrentMethodName(), serviceUrl, payload, r'/adaptiveAutomationManager.html')
        if info['name'] == name:
            PrintMessage(CurrentMethodName() + ' passed.')
        else:
            PrintMessage(CurrentMethodName() + ' failed.', 'Error')
        return info

    def NICategories_get(self):  # retrieve NI Folder
        serviceUrl = r'ServicesAPI/NICategories'
        info = self._getUrl(CurrentMethodName(), serviceUrl, r'/adaptiveAutomationManager.html')
        if len(info) > 0:
            PrintMessage(CurrentMethodName() + ' passed.')
        else:
            PrintMessage(CurrentMethodName() + ' failed.', 'Error')
        return info

    def GetNIBasicData(self, folder_id:str):
        serviceUrl = r'ServicesAPI/NIs/GetNIBasicData/' + folder_id
        info = self._getUrl(CurrentMethodName(), serviceUrl, r'/adaptiveAutomationManager.html')
        if len(info) > 0:
            PrintMessage(CurrentMethodName() + ' passed.')
        else:
            PrintMessage(CurrentMethodName() + ' failed.', 'Error')
        return info

    def deleteNodes(self, folder_ids:list):  # delete NI Folders
        serviceUrl = r'ServicesAPI/NICategories/deleteNodes/'
        info = self._postUrl(CurrentMethodName(), serviceUrl, folder_ids, r'/adaptiveAutomationManager.html')
        if info:
            PrintMessage(CurrentMethodName() + ' passed.')
        else:
            PrintMessage(CurrentMethodName() + ' failed.', 'Error')
        return info

    def nis_delete(self, ni_id:str):  # delete ni
        serviceUrl = r'ServicesAPI/nis/' + ni_id
        info = self._deleteUrl(CurrentMethodName(), serviceUrl, {}, r'/adaptiveAutomationManager.html')
        if info:
            PrintMessage(CurrentMethodName() + ' passed.')
        else:
            PrintMessage(CurrentMethodName() + ' failed.', 'Error')
        return info

    def NICategories_rename(self, folder_name:str, old_name:str, new_name:str):
        # not finished yet
        folders = self.NICategories_get()
        folder = next((item for item in folders if item.get("name") and item["name"] == folder_name), None)
        if folder is None:
            PrintMessage(CurrentMethodName() + f': {folder_name} is not existed.', 'Warning')
            return {}
        # nis = self.GetNIBasicData(folder['id'])
        # folder = next((item for item in nis if item.get("name") and item["name"] == folder_name), None)
        # if folder is None:
        #     PrintMessage(CurrentMethodName() + f': {folder_name} is not existed.', 'Warning')
        #     return {}
        serviceUrl = r'ServicesAPI/NICategories/rename'
        payload = {
            'id': folder['id'],
            'name': new_name
        }
        info = self._postUrl(CurrentMethodName(), serviceUrl, payload, r'/adaptiveAutomationManager.html')
        if info['name'] == new_name:
            PrintMessage(CurrentMethodName() + ' passed.')
        else:
            PrintMessage(CurrentMethodName() + ' failed.', 'Error')
        return info

    def DoFullSearch_NI(self, device_ids:list):
        serviceUrl = r'ServicesAPI/Search/BasicSearch/DoFullSearch/NI'
        payload = {
            'keyword': '',
            'devScope': {
                'id': 2,
                'name': 'All Intents'  # 1: 'Intents for Current Map'
            },
            'categoryFilters': [],
            'allMatchedCount': 100000,
            'pageInfo': {
                'index': 1,
                'size': 100000
            },
            'statisticsCategories': None,
            'niMode': 1,
            'mapDeviceIds': device_ids,  # ['9078639c-31d6-4938-91b3-20b71ef9a32a'],
            'searchWithMapDevice': False  # True
        }
        info = self._postUrl(CurrentMethodName(), serviceUrl, payload, r'/adaptiveAutomationManager.html')
        if len(info) > 0:
            PrintMessage(CurrentMethodName() + ' passed.')
        else:
            PrintMessage(CurrentMethodName() + ' failed.', 'Error')
        return info

    def SaveNetworkIntent(self, folder_id:str, payload):
        serviceUrl = r'ServicesAPI/NIs/' + folder_id
        info = self._postUrl(CurrentMethodName(), serviceUrl, payload, r'/adaptiveAutomationManager.html')
        if payload['networkIntent']['name'] == info.get('name', None):
            PrintMessage(CurrentMethodName() + ' passed.')
        else:
            info = False
            PrintMessage(CurrentMethodName() + ' failed.', 'Error')
        return info

    def Save(self, payload):
        serviceUrl = r'ServicesAPI/NIs/Save'
        info = self._postUrl(CurrentMethodName(), serviceUrl, payload, r'/adaptiveAutomationManager.html')
        if payload['networkIntent']['name'] == info['name']:
            PrintMessage(CurrentMethodName() + ' passed.')
        else:
            PrintMessage(CurrentMethodName() + ' failed.', 'Error')
        return info

    def RetrieveCmd(self, device_id:str, command:str, command_type:int):
        serviceUrl = r'ServicesAPI/NIs/RetrieveCmd'
        payload = {
            'deviceId': device_id,
            'command': command,
            'commandType': command_type,
            'retrieveSource': 0  # command_type - 1
        }
        info = self._postUrl(CurrentMethodName(), serviceUrl, payload, r'/adaptiveAutomationManager.html')
        if len(info) > 0:
            PrintMessage(CurrentMethodName() + ' passed.')
        else:
            PrintMessage(CurrentMethodName() + ' failed.', 'Error')
        return info

    def GetNIS(self, payload=[]):
        serviceUrl = r'ServicesAPI/NIs/GetNIS'
        info = self._postUrl(CurrentMethodName(), serviceUrl, payload, r'/adaptiveAutomationManager.html')
        PrintMessage(CurrentMethodName() + ' completed.')
        return info

    # NetworkIntent end

    # Triggered Automation start
    def GetInstalledAutomationModelByTypeAndPath(self, ni_fullname):
        serviceUrl = r'ServicesAPI/AdaptiveMonitor/InstalledAutomation/GetInstalledAutomationModelByTypeAndPath'
        payload = {
            'installType': 1,
            'automationType': 'NI',
            'automationPath': ni_fullname
        }
        info = self._postUrl(CurrentMethodName(), serviceUrl, payload, r'/adaptiveAutomationManager.html')
        PrintMessage(CurrentMethodName() + ' completed.')
        return info

    def AddInstalledAutomation(self, device, network_intent, flash_probe_info:list):
        if type(network_intent) is str:
            nis = self.GetNIS()
            ni = next((item for item in nis if item.get("path") and item["path"] == network_intent), None)
        else:
            ni = network_intent
        if ni is None:
            PrintMessage(''.join([CurrentMethodName(), ' failed to find NI "', str(network_intent), '".']), 'Error')
            return False
        flash_probes = self.flashprobes_search(device['_id'])
        flash_probe_name = flash_probe_info[0]['Name']
        # flash_probe_fullname = '_'.join([NetBrainUtils.ReplaceSpecialCharacters(device['name']), flash_probe_name])
        flash_probe_fullname = flash_probe_name
        flash_probe = next((item for item in flash_probes['flashProbes'] if item["name"] == flash_probe_fullname), None)
        if flash_probe is None:
            PrintMessage(''.join([CurrentMethodName(), ' failed to find FlashProbe "', flash_probe_fullname, '".']), 'Error')
            return False
        playbook = flash_probe_info[0]['Playbook']
        tags = self.GetAllPlaybookTag()
        tag = next((item for item in tags if item.get('name') and item['name'] == playbook), None)
        if tag is None:
            tag_id = self.AddPlaybookTag(playbook)
            if tag_id is None or len(tag_id) == 0:
                PrintMessage(''.join([CurrentMethodName(), ' failed to create playbook tag "', playbook, '".']), 'Error')
                return False
            #tag = {'id': tag_id, 'name': playbook}
            tags = self.GetAllPlaybookTag()
            tag = next((item for item in tags if item.get('name') and item['name'] == playbook), None)
        payload = {
            'isEnable': True,
            'installType': 1,
            'automationNode': {
                'automationId': ni['id'],
                'automationName': ni['name'],
                'automationPath': ni['path'],
                'automationType': ni['type'],
                'automationSubType': 1
            },
            'description': '',
            'automationTargetDevice': 'pre-defined',
            'installedDTNodes': [
                {
                    'nodePathSchema': 'Legacy',
                    'nodePathValue': device['_id'],
                    'nodeName': device['name'],
                    'dTNode': {
                        'dTNodeType': 1,  # FlashProbeNode = 1,ScheduledFlashProbeNode = 2, ManuallyNode = 3, IncidentNode = 4,RelativeNode = 5
                        'dTNodeId': flash_probe['id'],  # '531ff95884a735917fe76e039513120e',  # FlashProbeID
                        'dTNodeName': flash_probe_fullname,  # 'test',  # FlashProbeName
                        'flashProbeType': flash_probe['type'],  # 只有flashProbe才有 ，Primary = 1, Secondary = 2, External = 3
                        'flashProbeCategory': flash_probe['category'],  # 1,
                        'icon': 'icons_flash_probe_primary_14'
                    },
                    'createSrc': {
                        'name': 'Manually',
                        'type': 'Manually'
                    },
                    'playbookTags': [{'playbookId': tag['id'], 'operateInfo': tag['operateInfo']}],
                    'playbookTagIds': [tag['id']],
                    'noteOnDecisionTree': flash_probe_info[0]['Note On Decision Tree'],
                    'triggerRule': {
                        'triggerRunType': 1,  # RunOnce = 1, RunContinously = 2
                        'runContinuously': {
                            'interval': {
                                'duration': 15,
                                'unit': 2
                            },
                            'isRepeat': True,
                            'repeatRunTimes': 3
                        },
                        'enableTriggerSeuppression': False,
                        'wontRunTwiceWithIn': {
                            'duration': 10,
                            'unit': 2
                        }
                    },
                    'imgIcon': 'img/icon/Unclassified Device.png',
                    'operateInfo': {
                        'opUserId': self.Username,  # '47162ba0-3099-4c2d-bb65-6b0194e28dce',
                        'opUser': self.UserID,  # 'loaduser08',
                        'opTime': NetBrainUtils.GetDateTimeString() # '2020-12-29T16:43:38.214Z'
                    },
                    '$$hashKey': 'uiGrid-00T8'
                }
            ]
        }
        if len(flash_probe_info) == 2:
            frequency_probe_name = flash_probe_info[1]['Name']
            frequency_probe = next((item for item in flash_probes['flashProbes'] if item["name"] == frequency_probe_name), None)  #
            if frequency_probe is None:
                PrintMessage(''.join([CurrentMethodName(), ' failed to find Frequency Probe - "', frequency_probe_name, '".']), 'Error')
                return False
            if playbook != flash_probe_info[1]['Playbook']:
                playbook = flash_probe_info[1]['Playbook']
                tags = self.GetAllPlaybookTag()
                tag = next((item for item in tags if item.get('name') and item['name'] == playbook), None)
                if tag is None:
                    tag_id = self.AddPlaybookTag(playbook)
                    if tag_id is None or len(tag_id) == 0:
                        PrintMessage(''.join([CurrentMethodName(), ' failed to create playbook tag "', playbook, '".']),
                                     'Error')
                        return False
                    #tag = {'id': tag_id, 'name': playbook}
                    tags = self.GetAllPlaybookTag()
                    tag = next((item for item in tags if item.get('name') and item['name'] == playbook), None)
            item = {
                'nodePathSchema': 'Legacy',
                'nodePathValue': device['_id'],
                'nodeName': device['name'],
                'dTNode': {
                    'dTNodeType': 2,
                    'dTNodeId': frequency_probe['id'],
                    'dTNodeName': frequency_probe['name'],
                    'flashProbeType': frequency_probe['type'],
                    'flashProbeCategory': frequency_probe['category'],
                    'icon': 'icon_nb_interactive_run'
                },
                'createSrc': {
                    'name': 'Manually',
                    'type': 'Manually'
                },
                'playbookTags': [{'playbookId': tag['id'], 'operateInfo': tag['operateInfo']}],
                'playbookTagIds': [tag['id']],
                'noteOnDecisionTree': flash_probe_info[1]['Note On Decision Tree'],
                'triggerRule': {
                    'triggerRunType': 1,
                    'runContinuously': {
                        'interval': {
                            'duration': 15,
                            'unit': 2
                        },
                        'isRepeat': True,
                        'repeatRunTimes': 3
                    },
                    'enableTriggerSeuppression': False,
                    'wontRunTwiceWithIn': {
                        'duration': 10,
                        'unit': 2
                    }
                },
                'imgIcon': 'img/icon/Unclassified Device.png',
                'operateInfo': frequency_probe['operateInfo'],
                '$$hashKey': 'uiGrid-0BU3'
            }
            payload['installedDTNodes'].append(item)
        serviceUrl = r'ServicesAPI/AdaptiveMonitor/InstalledAutomation/AddInstalledAutomation'
        info = self._postUrl(CurrentMethodName(), serviceUrl, payload, r'/adaptiveAutomationManager.html')
        # info = '9627cf2f-3d43-49f1-ae8f-0107cafeeec0'
        msg = ' '.join([CurrentMethodName(), ' for ', ni['name']])
        if len(info) == 0:
            PrintMessage(msg + ' failed.', 'Error')
        else:
            PrintMessage(msg + ' passed.')
        return info

    def InstalledAutomationGetList(self):
        serviceUrl = r'ServicesAPI/AdaptiveMonitor/InstalledAutomation/GetList'
        payload = {
            'installType': 1,
            'pageIndex': 1,
            'pageCapacity': 50000,
            'filter': {
                'searchKeyWord': '',
                'deviceIds': [],
                'playBookTagIds': [],
                'flashProbeId': ''
            },
            'sortField': '',
            'isAsc': True
        }
        info = self._postUrl(CurrentMethodName(), serviceUrl, payload, r'/adaptiveAutomationManager.html')
        if len(info) > 0:
            PrintMessage(CurrentMethodName() + ' passed.')
        else:
            PrintMessage(CurrentMethodName() + ' failed.', 'Error')
        return info

    def DeleteInstalledAutomationByID(self, installed_automation_id:str):
        serviceUrl = r'ServicesAPI/AdaptiveMonitor/InstalledAutomation/' + installed_automation_id
        info = self._deleteUrl(CurrentMethodName(), serviceUrl, {}, r'/adaptiveAutomationManager.html')
        if info:
            PrintMessage(CurrentMethodName() + ' passed.')
        else:
            PrintMessage(CurrentMethodName() + ' failed.', 'Error')
        return info

    def DeleteInstalledAutomation(self, installed_automation_ids:list):
        serviceUrl = r'ServicesAPI/AdaptiveMonitor/InstalledAutomation/Delete'
        payload = {'installAutomationIds': installed_automation_ids, 'isTriggerAutomation': True}
        info = self._postUrl(CurrentMethodName(), serviceUrl, payload, r'/adaptiveAutomationManager.html')
        if info:
            PrintMessage(CurrentMethodName() + ' passed.')
        else:
            PrintMessage(CurrentMethodName() + ' failed.', 'Error')
        return info

    def GetAllPlaybookTag(self):
        serviceUrl = r'ServicesAPI/AdaptiveMonitor/PlaybookTag/GetAllPlaybookTag/false'
        info = self._getUrl(CurrentMethodName(), serviceUrl, r'/adaptiveAutomationManager.html')
        PrintMessage(CurrentMethodName() + ' completed.')
        return info

    def AddPlaybookTag(self, tag_name):
        serviceUrl = r'ServicesAPI/AdaptiveMonitor/PlaybookTag/AddPlaybookTag'
        payload = {'name': tag_name}
        info = self._postUrl(CurrentMethodName(), serviceUrl, payload, r'/adaptiveAutomationManager.html')
        #info = '984941f7-fe68-4c6e-b2b1-60b8ccd64d45'
        if len(info) > 0:
            PrintMessage(CurrentMethodName() + ' passed.')
        else:
            PrintMessage(CurrentMethodName() + ' failed.', 'Error')
        return info

    # Triggered Automation end

    # Schedule CLI Commands start
    def getDevicesByTypes(self, types:list):
        serviceUrl = r'ServicesAPI/DataModel/getDevicesByTypes'
        payload = {
            'types': types,
            'limit': 50000, 'skip': 0
        }
        info = self._postUrl(CurrentMethodName(), serviceUrl, payload, r'/adaptiveAutomationManager.html')
        if len(info) > 0:
            PrintMessage(CurrentMethodName() + ' passed.')
        else:
            PrintMessage(CurrentMethodName() + ' failed.', 'Error')
        return info

    def GetList(self, device_id:str, search:str=''):
        serviceUrl = r'ServicesAPI/AdaptiveMonitor/ScheduleCliCommand/GetList'
        payload = {
            'deviceId': device_id,
            'pageSize': 50000, 'pageIndex': 0, 'search': search
        }
        info = self._postUrl(CurrentMethodName(), serviceUrl, payload, r'/adaptiveAutomationManager.html')
        if len(info) > 0:
            PrintMessage(CurrentMethodName() + ' passed.')
        else:
            PrintMessage(CurrentMethodName() + ' failed.', 'Error')
        return info

    def ScheduleCliCommand_Summary(self):
        serviceUrl = r'ServicesAPI/AdaptiveMonitor/ScheduleCliCommand/Summary'
        info = self._getUrl(CurrentMethodName(), serviceUrl, r'/adaptiveAutomationManager.html')
        if len(info) > 0:
            PrintMessage(CurrentMethodName() + ' passed.')
        else:
            PrintMessage(CurrentMethodName() + ' failed.', 'Error')
        return info

    def GetFullCommand1(self, command_infos:list):
        serviceUrl = r'ServicesAPI/AdaptiveMonitor/ScheduleCliCommand/GetFullCommand'
        payload = []
        for info in command_infos:
            payload.append({
                'devicetype': info['device type'],  # 2
                'command': info['command']
            })
        info = self._postUrl(CurrentMethodName(), serviceUrl, payload, r'/adaptiveAutomationManager.html')
        if len(info) > 0:
            PrintMessage(CurrentMethodName() + ' passed.')
        else:
            PrintMessage(CurrentMethodName() + ' failed.', 'Error')
        return info

    def GetFrequency(self, device_ids:list):
        serviceUrl = r'ServicesAPI/AdaptiveMonitor/ScheduleCliCommand/GetFrequency'
        info = self._postUrl(CurrentMethodName(), serviceUrl, device_ids, r'/adaptiveAutomationManager.html')
        if len(info) > 0:
            PrintMessage(CurrentMethodName() + ' passed.')
        else:
            PrintMessage(CurrentMethodName() + ' failed.', 'Error')
        return info

    def CheckConflict(self, command_infos:list):
        serviceUrl = r'ServicesAPI/AdaptiveMonitor/ScheduleCliCommand/CheckConflict'
        payload = []
        id = CreateGuid()
        index = 1
        for info in command_infos:
            device_id = info['device']['_id']
            frequencies = self.GetFrequency(device_id)
            frequency = frequencies[device_id][info['frequency name']]
            payload.append({
                'deviceId': info['device id'],
                'deviceType': info['device type'],
                'command': info['command'],
                'description': '',
                'frequency': frequency,
                '$$hashKey': 'uiGrid-{:4d}'.format(index),
                'showDeleteBtn': False
            })
            index += 1

        info = self._postUrl(CurrentMethodName(), serviceUrl, payload, r'/adaptiveAutomationManager.html')
        if len(info) > 0:
            PrintMessage(CurrentMethodName() + ' passed.')
        else:
            PrintMessage(CurrentMethodName() + ' failed.', 'Error')
        return info

    def GetFullCommand(self, payload):
        serviceUrl = r'ServicesAPI/AdaptiveMonitor/ScheduleCliCommand/GetFullCommand'
        info = self._postUrl(CurrentMethodName(), serviceUrl, payload, r'/adaptiveAutomationManager.html')
        # if len(info) > 0:
        #     PrintMessage(CurrentMethodName() + ' passed.')
        # else:
        #     PrintMessage(CurrentMethodName() + ' failed.', 'Error')
        PrintMessage(CurrentMethodName() + ' completed.')
        return info

    def ScheduleCliCommand_Upinsert(self, devices, command_infos:list):
        serviceUrl = r'ServicesAPI/AdaptiveMonitor/ScheduleCliCommand/Upinsert'
        unit = ['', 'hours', 'days', 'weeks']
        payload = []
        index = 1
        device_ids = [item['ID'] for item in devices]
        frequencies = self.GetFrequency(device_ids)
        icon_url = ''.join(['/ServicesAPI/DeviceIcon/stateIcon/', self.TenantID, '/2001/1.3.6.1.4.1.9.1.516/1.png'])
        for device in devices:
            device_id = device['ID']
            #frequencies = self.GetFrequency([device_id])
            #frequencies = self.GetFrequency([device_id])
            for info in command_infos:
                frequency = frequencies.get(device_id, {}).get(info['frequency']['name'], None)
                if frequency is None:
                    PrintMessage(''.join(['The device "', device['name'], '" do NOT have ', info['frequency']['name']]), 'Warning')
                    continue
                frequency['inteval'] = info['frequency']['inteval']
                frequency['unit'] = unit.index(info['frequency']['unit'])
                # full_command = self.GetFullCommand([{'devicetype': device['subType'], 'command': info['command']}])
                # if len(full_command) <= 0:
                #     full_command.append({'fullcommand':  info['command']})
                payload.append({
                    'deviceId': device_id,
                    'deviceType': device['subType'],
                    'command': info['command'],
                    'description': '',
                    'frequency': frequency,
                    '$$hashKey': 'uiGrid-{:4d}'.format(index),
                    'showDeleteBtn': False,
                    'fullcommand': info['command'],  # full_command[0]['fullcommand'],
                    'deviceName': device['name'],
                    'iconUrl': icon_url,
                    'id': '',
                    'isEnable': True
                })
                index += 1
        #item=next((item for item in payload if item.get("deviceName") and item["deviceName"] == "ustta000000"), None)
        info = self._postUrl(CurrentMethodName(), serviceUrl, payload, r'/adaptiveAutomationManager.html')
        if info:
            PrintMessage(CurrentMethodName() + ' passed.')
        else:
            PrintMessage(CurrentMethodName() + ' failed.', 'Error')
        return info

    def ScheduleCliCommand_GetList(self, device_id:str, search:str=''):
        # return: {count:3, data:[{"id":"", "deviceId":"", ...}]}
        serviceUrl = r'ServicesAPI/AdaptiveMonitor/ScheduleCliCommand/GetList'
        payload = {
            'deviceId': device_id,
            'pageIndex': 0,
            'pageSize': 50000,
            'search': search
        }
        info = self._postUrl(CurrentMethodName(), serviceUrl, payload, r'/adaptiveAutomationManager.html')
        if len(info) > 0:
            PrintMessage(CurrentMethodName() + ' passed.')
        else:
            PrintMessage(CurrentMethodName() + ' failed.', 'Error')
        return info

    def ScheduleCliCommand_Delete(self, id):
        serviceUrl = r'ServicesAPI/AdaptiveMonitor/ScheduleCliCommand/Delete/' + id
        info = self._getUrl(CurrentMethodName(), serviceUrl, r'/adaptiveAutomationManager.html')
        if info:
            PrintMessage(CurrentMethodName() + ' passed.')
        else:
            PrintMessage(CurrentMethodName() + ' failed.', 'Error')
        return info

    def ScheduleCliCommand_Summary(self, id):
        # return {"command_total":20,"device_total":10}
        serviceUrl = r'ServicesAPI/AdaptiveMonitor/ScheduleCliCommand/Summary/'
        info = self._getUrl(CurrentMethodName(), serviceUrl, r'/adaptiveAutomationManager.html')
        if info:
            PrintMessage(CurrentMethodName() + ' passed.')
        else:
            PrintMessage(CurrentMethodName() + ' failed.', 'Error')
        return info

    # Schedule CLI Commands  end

    def EnableAutoUpdate(self, enabled:bool):
        serviceUrl = r'ServicesAPI/AutoUpdate/Setting/EnableAutoUpdate'
        payload = {"enableAUCheck": enabled}
        info = self._putUrl(CurrentMethodName(), serviceUrl, payload, r'/admin.html')
        if info['enableAUCheck'] == enabled:
            PrintMessage(CurrentMethodName() + ' passed.')
        else:
            PrintMessage(CurrentMethodName() + ' failed.', 'Error')
        return info
    # Feature start
    # Feature end
