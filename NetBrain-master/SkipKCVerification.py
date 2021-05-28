# Create by Tony Che at 2020-01

# SkipKCVerification.py
# Feature description

import json
from _datetime import datetime, timedelta
from NetBrainIE import NetBrainIE, PrintMessage
from NetBrainDB import NetBrainDB, CreateGuid
from Utils.NetBrainUtils import NetBrainUtils, CurrentMethodName, CreateGuid

ConfigFile = r'.\conf\SkipKCVerification31114.conf'
#ConfigFile = r'.\conf\SkipKCVerification31175.conf'

def SkipKCVerification(configFile=''):
    #After restarting web service, you can use user credential admin/netbrain from Knowledge Cloud test server to verify
    configFile = ConfigFile if configFile == '' else configFile
    config = NetBrainUtils.GetConfig(configFile)
    if len(config) == 0:
        PrintMessage('Failed to load the configuration file: ' + configFile, 'Error')
        return False

    try:
        ret = True
        app = NetBrainDB(config)
        if app.Login():
            dbNGSystem = app.GetDatabase('NGSystem')
            systemSettings = dbNGSystem['SystemSettings']
            count = systemSettings.count_documents({})
            index = 1
            for setting in systemSettings.find({}):
                print(''.join([f'{index:03} - ', setting['key'], ': ', str(setting['value'])]))
                index += 1
            print(f'total: {count}')
            item = systemSettings.find_one({'key': 'KnowledgeCloudServerDomain'})
            if item is None:
                print('KnowledgeCloudServerDomain is not existed.')
                return True
            print(''.join([item['key'], '(old): ', item['value']]))
            # newKCServer = 'http://kc-webserve-1akq9pqpxu2kg-1721127264.us-east-1.elb.amazonaws.com'
            newKCServer = 'http://qa-knowledgecloud.netbraintech.com'
            systemSettings.update_one({'key': 'KnowledgeCloudServerDomain'},
                                      {'$set': {'value': newKCServer}})
            item = systemSettings.find_one({'key': 'KnowledgeCloudServerDomain'})
            print(''.join([item['key'], '(new): ', item['value']]))
    except Exception as e:
        PrintMessage('Exception raised: ' + str(e), 'Error')
        ret = False
    finally:
        app.Logout()
        return ret


def SkipKCVerification2(configFile=''):
    configFile = ConfigFile if configFile == '' else configFile
    config = NetBrainUtils.GetConfig(configFile)
    if len(config) == 0:
        PrintMessage('Failed to load the configuration file: ' + configFile, 'Error')
        return False

    try:
        ret = True
        app = NetBrainDB(config)
        if app.Login():
            dbNGSystem = app.GetDatabase('NGSystem')
            tableUser = dbNGSystem['User']
            tableUserProfiles = dbNGSystem['UserProfiles']
            count = tableUser.estimated_document_count()
            print('The total of User is ', str(count))
            users = list(tableUser.find({}))
            index = 1
            for user in users:
                print(''.join([f'{index:02} - ', user['name'], ': ', user['_id']]))
                index += 1
                key = 'KNOWLEDGE_CLOUD_NO_MORE_NOTIFICATION'
                noMoreNotification = {
                    #'_id': CreateGuid(),
                    'userId': user['_id'],
                    'key': key,
                    'value': True
                }
                where = {'userId': user['_id'], 'key': key,}
                app.Upsert('UserProfiles', where, noMoreNotification)
                key = 'KNOWLEDGE_CLOUD_LAST_VERIFICATION_TIME'
                timeVerification = datetime.now()
                timeVerification += timedelta(days=30)
                lastVeirficationTime = {
                    # '_id': CreateGuid(),
                    'userId': user['_id'],
                    'key': key,
                    'value': ''.join(['"', timeVerification.strftime('%Y-%m-%dT%H:%M:%S.%fZ'), '"'])
                }
                where = {'userId': user['_id'], 'key': key, }
                app.Upsert('UserProfiles', where, lastVeirficationTime)
            '''
            print(f'total: {count}')
            item = systemSettings.find_one({'key': 'KnowledgeCloudServerDomain'})
            print(''.join([item['key'], '(old): ', item['value']]))
            # newKCServer = 'http://kc-webserve-1akq9pqpxu2kg-1721127264.us-east-1.elb.amazonaws.com'
            newKCServer = 'http://qa-knowledgecloud.netbraintech.com'
            systemSettings.update_one({'key': 'KnowledgeCloudServerDomain'},
                                      {'$set': {'value': newKCServer}})
            item = systemSettings.find_one({'key': 'KnowledgeCloudServerDomain'})
            print(''.join([item['key'], '(new): ', item['value']]))
            '''
    except Exception as e:
        PrintMessage('Exception raised: ' + str(e), 'Error')
        ret = False
    finally:
        app.Logout()
        return ret


if __name__ == "__main__":
    #SkipKCVerification()
    SkipKCVerification2()

