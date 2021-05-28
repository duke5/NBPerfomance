# Create by Tony Che at 2020-01

# EmailSetting.py
# Set Email configuration

import json
from NetBrainIE import NetBrainIE

ConfigFile = r'.\conf\EmailSetting31200.conf'


def main():
    with open(ConfigFile, 'r') as configFile:
        config = json.load(configFile)
    try:
        app = NetBrainIE(config['Url'], config['Username'], config['Password'])
        if app.Login():
            app.SetEmailSetting(config['EmailSetting'])
    except Exception as e:
        print('Exception raised: ', str(e))
    finally:
        app.Logout()
        return True


if __name__ == "__main__":
    main()

