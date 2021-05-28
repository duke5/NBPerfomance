# Create by Tony Che at 2020-01

# EnableGoldenBaselineDynamicCalculation.py
# Feature description

import json
from NetBrainIE import NetBrainIE, PrintMessage
from Utils.NetBrainUtils import NetBrainUtils, CurrentMethodName, CreateGuid

ConfigFile = r'.\conf\EnableGoldenBaselineDynamicCalculation31200.conf'


def EnableGoldenBaselineDynamicCalculation(configFile=''):
    configFile = ConfigFile if configFile == '' else configFile
    config = NetBrainUtils.GetConfig(configFile)
    if len(config) == 0:
        PrintMessage('Failed to load the configuration file: ' + configFile, 'Error')
        return False

    try:
        ret = True
        app = NetBrainIE(config['Url'], config['Username'], config['Password'])
        if app.Login():
            domainName = config.get('Domain Name', None)
            if domainName is None:
                domainName = config.get('DomainInfo', {}).get('Domain Name', None)
            if domainName is None:
                PrintMessage('Domain Name is not existed.', 'Error')
                return False
            app.ApplyTenantAndDomain(config['Tenant Name'], domainName)
            ret = app.GoldenBaselineCustomerEnabled()
    except Exception as e:
        print('Exception raised: ', str(e))
        ret = False
    finally:
        app.Logout()
        return ret


if __name__ == "__main__":
    EnableGoldenBaselineDynamicCalculation()

