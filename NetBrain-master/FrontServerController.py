import json
from NetBrainIE import NetBrainIE, PrintMessage
from Utils.NetBrainUtils import NetBrainUtils, CurrentMethodName, CreateGuid

ConfigFile = r'.\conf\FrontServerController31200.conf'

def AddFrontServerController(application=None, configFile=''):
    configFile = ConfigFile if configFile == '' else configFile
    config = NetBrainUtils.GetConfig(configFile)
    if len(config) == 0:
        PrintMessage('Failed to load the configuration file: ' + configFile, 'Error')
        return False

    try:
        ret = True
        print('Add Front Server Controller')
        if application is None:
            app = NetBrainIE(config['Url'], config['Username'], config['Password'])
            logined = app.Login()
        else:
            app = application
            logined = True
        if logined:
            app.AddFrontServerController(config['FSCInfo'])
    except Exception as e:
        print('AddFrontServerController Exception raised: ', str(e))
        ret = False
    finally:
        if application is None and logined:
            app.Logout()
        return ret

def EditFrontServerController(application=None, configFile=''):
    configFile = ConfigFile if configFile == '' else configFile
    config = NetBrainUtils.GetConfig(configFile)
    if len(config) == 0:
        PrintMessage('Failed to load the configuration file: ' + configFile, 'Error')
        return False

    try:
        ret = True
        print('Edit Front Server Controller')
        if application is None:
            app = NetBrainIE(config['Url'], config['Username'], config['Password'])
            logined = app.Login()
        else:
            app = application
            logined = True
        if logined:
            app.EditFrontServerController('FSC1', config['FSCInfo'])
    except Exception as e:
        print('EditFrontServerController Exception raised: ', str(e))
        ret = False
    finally:
        if application is None and logined:
            app.Logout()
        return ret

def DeleteFrontServerController(application=None, configFile=''):
    configFile = ConfigFile if configFile == '' else configFile
    config = NetBrainUtils.GetConfig(configFile)
    if len(config) == 0:
        PrintMessage('Failed to load the configuration file: ' + configFile, 'Error')
        return False

    try:
        ret = True
        print('Delete Front Server Controller')
        if application is None:
            app = NetBrainIE(config['Url'], config['Username'], config['Password'])
            logined = app.Login()
        else:
            app = application
            logined = True
        if logined:
            app.DeleteFrontServerController(config['FSCInfo']['Name'])
            ret = False
    except Exception as e:
        print('DeleteFrontServerController Exception raised: ', str(e))
    finally:
        if application is None and logined:
            app.Logout()
        return ret


if __name__ == '__main__':
    AddFrontServerController()
    #EditFrontServerController()
    #DeleteFrontServerController()
