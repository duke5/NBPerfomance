# Create by Tony Che at 2020-01

# AddUser
# Add User

import json
from NetBrainIE import NetBrainIE, PrintMessage
from Utils.NetBrainUtils import NetBrainUtils, CurrentMethodName, CreateGuid

ConfigFile = r'.\conf\User31200.conf'

def AddUser(application=None, configFile=''):
    configFile = ConfigFile if configFile == '' else configFile
    config = NetBrainUtils.GetConfig(configFile)
    if len(config) == 0:
        PrintMessage('Failed to load the configuration file: ' + configFile, 'Error')
        return False

    try:
        ret = True
        if application is None:
            app = NetBrainIE(config['Url'], config['Username'], config['Password'])
            logined = app.Login()
        else:
            app = application
            logined = True
        if logined:
            userCount = config.get('UserCount', 1) + 1
            tenantList = app._getDisplayTenantList()
            userList = app._getAllUsers()
            if userCount > 2:
                for i in range(1, userCount):
                    userInfo = config['UserInfo'].copy()
                    value = userInfo['First Name']
                    userInfo['First Name'] = f'{value}{i:02}'
                    value = userInfo['Username']
                    userInfo['Username'] = f'{value}{i:02}'
                    value = userInfo['Email'].split('@')
                    userInfo['Email'] = f'{value[0]}{i:02}@{value[1]}'
                    ret = app.AddUser(userInfo, tenantList, userList)
                    if ret:
                        userList.append({'name': userInfo['Username']})
            else:
                ret = app.AddUser(config['UserInfo'], tenantList, userList)
    except Exception as e:
        print('Exception raised: ', str(e))
        ret = False
    finally:
        if application is None and logined:
            app.Logout()
        return ret


if __name__ == "__main__":
    AddUser()

