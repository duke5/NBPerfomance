# NetBrain
Python tools

# System
## Login and Logout
Login(self)  
Logout(self)
```python
from NetBrainIE import NetBrainIE

app = NetBrainIE('https://192.168.1.1', 'yourUsername', 'yourPassword')
if app.Login():
    # do your task
    ...
    app.Logout()
```

## Encrypt Password
EncrpytPassword(self, plainPassword)
```python
from NetBrainIE import NetBrainIE

app = NetBrainIE('https://192.168.1.1', 'yourUsername', 'yourPassword')
encrpytPassword = app.PasswordEncrypt('yourPlainPassword')
print(encrpytPassword)
```

## Create Tenant
AddTenant(self, tenantInfo)
```python
from NetBrainIE import NetBrainIE

tenantInfo = {
    'name': 'Your Tenant',
    'nodeSize': 1000,
    'description': 'This is your tenant'
}

app = NetBrainIE('https://192.168.1.1', 'yourUsername', 'yourPassword')
if app.Login():
    app.AddTenant(tenantInfo)
    app.Logout()
```

## Email Setting
SetEmailSetting(self, emailSetting)
```python
from NetBrainIE import NetBrainIE

emailSetting = {
    'Enable Email Server Settings': True,
    'SMTP Server': 'Your SMTP Server',
    'SMTP Port': 111,
    'Encryption': 'Your Encryption',
    'Sender Email Address': 'Your Email Address',
    'Password': 'xxx',
    'Send Email Frequency': {'duration': 5}
}

app = NetBrainIE('https://192.168.1.1', 'yourUsername', 'yourPassword')
if app.Login():
    app.SetEmailSetting(emailSetting)
    app.Logout()
```

## Create Front Server Controller
AddFrontServerController(self, fscDetailInfo)
```python
from NetBrainIE import NetBrainIE

fscInfo = {
    'Name': 'FSC',
    'Hostname or IP Address': '192.168.1.1',
    'Port': '9095',
    'Username': 'user',
    'Password': 'password',
    'Timeout': 5,
    'Description': '',
    'Allocated Tenants': ['Initial Tenant'],
    'useSSL': True
}

app = NetBrainIE('https://192.168.1.1', 'yourUsername', 'yourPassword')
if app.Login():
    app.AddFrontServerController(fscInfo)
    app.Logout()
```

## Edit Front Server Controller
EditFrontServerController(self, fscName, fscInfo)
```python
from NetBrainIE import NetBrainIE

fscInfo = {
    'Name': 'FSC2',
    'Hostname or IP Address': '192.168.1.1',
    'Port': '9095',
    'Username': 'user',
    'Password': 'password',
    'Timeout': 5,
    'Description': '',
    'Allocated Tenants': ['Initial Tenant'],
    'useSSL': True
}

app = NetBrainIE('https://192.168.1.1', 'yourUsername', 'yourPassword')
if app.Login():
    app.EditFrontServerController('fscName', fscInfo)
    app.Logout()
```

## Delete Front Server Controller
DeleteFrontServerController(self, fscName)
```python
from NetBrainIE import NetBrainIE

app = NetBrainIE('https://192.168.1.1', 'yourUsername', 'yourPassword')
if app.Login():
    app.DeleteFrontServerController('Your FSC Name')
    app.Logout()
```

## Create Front Server Group
CreateFrontServerGroup(self, fsgName)
```python
from NetBrainIE import NetBrainIE

app = NetBrainIE('https://192.168.1.1', 'yourUsername', 'yourPassword')
if app.Login():
    app.CreateFrontServerGroup('Your Front Server Group Name')
    app.Logout()
```

## Create Front Server
AddFrontServer(self, fsInfo)
```python
from NetBrainIE import NetBrainIE

FSInfo = {
    "Front Server ID": "FS3",
    "Authentication Key": "netbrain",
    "Front Server Group": "",
    "Tenant Name": "Initial Tenant"
}

app = NetBrainIE('https://192.168.1.1', 'yourUsername', 'yourPassword')
if app.Login():
    app.AddFrontServer(FSInfo)
    app.Logout()
```

## Edit Front Server
EditFrontServer(self, fsName, fsInfo)
```python
from NetBrainIE import NetBrainIE

FSInfo = {
    "Authentication Key": "netbrain1",
    "Front Server Group": ""
}

app = NetBrainIE('https://192.168.1.1', 'yourUsername', 'yourPassword')
if app.Login():
    app.EditFrontServer('Your Front Server Name', FSInfo)
    app.Logout()
```

## Delete Front Server
DeleteFrontServer(self, fsName)
```python
from NetBrainIE import NetBrainIE

app = NetBrainIE('https://192.168.1.1', 'yourUsername', 'yourPassword')
if app.Login():
    app.DeleteFrontServer('Your Front Server Name')
    app.Logout()
```

## Add User
AddUser(self, userInfo)
```python
from NetBrainIE import NetBrainIE

userInfo = {
    'Email': 'xxx@yyy.com',
    'First Name': 'firstname',
    'Last Name': 'lastname',
    'Username': 'firstname lastname',
    'Password': 'password',
}

app = NetBrainIE('https://192.168.1.1', 'yourUsername', 'yourPassword')
if app.Login():
    app.AddUser(userInfo)
    app.Logout()
```








# Domain

## Apply Tenant and Domain
ApplyTenantAndDomain(self, tenantName, domainName)
```python
from NetBrainIE import NetBrainIE

app = NetBrainIE('https://192.168.1.1', 'yourUsername', 'yourPassword')
if app.Login():
    app.ApplyTenantAndDomain('tenantName', 'domainName')
    # do your task
    ...
    app.Logout()
```

## Get Tenant and Domain ID
GetTenantDomainID(self, tenantName, domainName='')
```python
from NetBrainIE import NetBrainIE

app = NetBrainIE('https://192.168.1.1', 'yourUsername', 'yourPassword')
if app.Login():
    tenantID, domainID = app.GetTenantDomainID('tenantName', 'domainName')
    # do your task
    ...
    app.Logout()
```

## Create Domain
CreateDomain(self, domainInfo)
```python
from NetBrainIE import NetBrainIE

domainInfo = {
    "Tenant Name": "Initial Tenant",
    'Domain Name': 'Your Domain',
    'Maximum Nodes': '1000',
    'Description': 'This is your domain.'
}

app = NetBrainIE('https://192.168.1.1', 'yourUsername', 'yourPassword')
if app.Login():
    app.CreateDomain(domainInfo)
    app.Logout()
```

## Update Telnet/SSH Login
def UpdateTelnetInfo(self, telnetInfo)
```python
from NetBrainIE import NetBrainIE

domainInfo = {
    "Tenant Name": "Initial Tenant",
    'Domain Name': 'Your Domain',
    'Maximum Nodes': '1000',
    'Description': 'This is your domain.'
}
telnetInfo = {
    'Alias': 'xxx',
    'Username': 'xxx',
    'Password': 'xxx'
}

app = NetBrainIE('https://192.168.1.1', 'yourUsername', 'yourPassword')
if app.Login():
    app.CreateDomain(domainInfo)
    app.UpdateTelnetInfo(telnetInfo)
    app.Logout()
```

## Update Privillege Login
UpdateEnablePasswd(self, enablePasswordInfo)
```python
from NetBrainIE import NetBrainIE

enablePasswdInfo = {
    'Alias': 'xxx',
    'Username': 'xxx',
    'Password': 'xxx'
}

app = NetBrainIE('https://192.168.1.1', 'yourUsername', 'yourPassword')
if app.Login():
    app.ApplyTenantAndDomain('yourTenantName', 'yourDomainName')
    app.UpdateEnablePasswd(enablePasswdInfo)
    app.Logout()
```

## Update SNMP String
UpdateSnmpRoInfo(self, SnmpRoInfoInfo)
```python
from NetBrainIE import NetBrainIE

snmpRoInfo ={
    'Alias': 'xxx',
    'SNMP Read Only Community String': 'xxx'
}

app = NetBrainIE('https://192.168.1.1', 'yourUsername', 'yourDomainName')
if app.Login():
    app.ApplyTenantAndDomain('yourTenantName', 'domainName')
    app.UpdateSnmpRoInfo(snmpRoInfo)
    app.Logout()
```

## Import Network Setting
ImportNetworkSetting(self, settingInfo)
```python
from NetBrainIE import NetBrainIE

networkSettingInfo = {
    'filePath': r'C:\xxx\NetworkSetting.zip',
    'password': 'password'
}

app = NetBrainIE('https://192.168.1.1', 'yourUsername', 'yourPassword')
if app.Login():
    app.ApplyTenantAndDomain('yourTenantName', 'yourDomainName')
    app.ImportNetworkSetting(networkSettingInfo)
    app.Logout()
```

## Import Network DefineTable
ImportNetworkDefineTable(self, networkDefineTableFilePath)
```python
from NetBrainIE import NetBrainIE

networkDefineTableFilePath = r'C:\xxx\NetworkDefineTable.csv'

app = NetBrainIE('https://192.168.1.1', 'yourUsername', 'yourPassword')
if app.Login():
    app.ApplyTenantAndDomain('yourTenantName', 'yourDomainName')
    app.ImportNetworkDefineTable(networkDefineTableFilePath)
    app.Logout()
```

## Start Discover
StartDiscover(self, discoverInfo)
```python
from NetBrainIE import NetBrainIE

discoverInfo = {
    'Access Mode': 'SNMP and Telnet/SSH',
    'Discovery Depth': 0,
    'Front Server':['FS1'],
    'Telnet/SSH Login':['xxx'],
    'Privillege Login':['xxx'],
    'SNMP String':['xxx'],
    'Scan IP Range ': False,
    'HostIPs': r'C:\ip\ip.txt'
}
discoverInfo2 = {
    'Access Mode': 'SNMP and Telnet/SSH',
    'Discovery Depth': 0,
    'Front Server':['FS1'],
    'Telnet/SSH Login':['xxx'],
    'Privillege Login':['xxx'],
    'SNMP String':['xxx'],
    'Scan IP Range ': True,
    'HostIPs': ['192.168.1.1-192.168.2.1']
}

app = NetBrainIE('https://192.168.1.1', 'yourUsername', 'yourPassword')
if app.Login():
    app.ApplyTenantAndDomain('yourTenantName', 'domainName')
    app.StartDiscover(discoverInfo)
    app.Logout()
```

## Save Device Group
SaveDeviceGroup(self, groupInfo)
```python
from NetBrainIE import NetBrainIE

groupInfo = {
    'Name': 'group name',
    'Description': '',
    'Type': 0, #in V8.02, 0: Public; 1: My Device Groups; 2: System; 3: Media; 4: Policy Device Group
    'DeviceID': ['192.168.1.1', '192.168.1.2', '192.168.1.3']
}

app = NetBrainIE('https://192.168.1.1', 'yourUsername', 'yourPassword')
if app.Login():
    app.ApplyTenantAndDomain('yourTenantName', 'domainName')
    app.SaveDeviceGroup(groupInfo)
    app.Logout()
```

## Golden Baseline Dynamic Calculation Enabled
GoldenBaselineCustomerEnabled(self, name='Built-in Variables', enabled=True)
```python
from NetBrainIE import NetBrainIE

app = NetBrainIE('https://192.168.1.1', 'yourUsername', 'yourPassword')
if app.Login():
    app.ApplyTenantAndDomain('yourTenantName', 'domainName')
    app.GoldenBaselineCustomerEnabled()
    app.Logout()
```









# Data Dictionary

## DefaultFscInfo
```python
DefaultFscInfo = {
    'uniqueName': 'FSC',
    'ipOrHostname': '',
    'port': '9095',
    'userName': 'admin',
    'password': '',
    'timeout': 5,
    'desc': ''
}
```

## DefaultFSCDetailInfo
```python
DefaultFSCDetailInfo = {
    'id': '',
    'deployMode': 1,
    'groupName': 'FSC',
    'fscInfo': [
        {} #fscInfo
    ],
    'useSSL': False,
    'conductCertAuthVerify': False,
    'certificateType': 2,
    'certificate': '',
    'certificateName': '',
    'tenants': []
}
```




