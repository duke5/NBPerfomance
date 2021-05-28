# Create by Tony Che at 2020-02

# VerifyMongoDBIndex.py
# Feature description

import json
from NetBrainDB import NetBrainDB
from Utils.NetBrainUtils import NetBrainUtils, CurrentMethodName, CreateGuid

ConfigFile = r'.\conf\VerifyMongoDBIndex31200.conf'


def VerifyMongoDBIndex(application=None, configFile=''):
    savedIndexes = LoadCollectionIndexes(configFile, ['Database Name', 'Collection Indexes'])
    currentIndexes = SaveCollectionIndexes()
    if savedIndexes != currentIndexes:
        print('\n different.')
    else:
        print('\nsame.')
    return True

def SaveCollectionIndexes(application=None, configFile=''):
    configFile = ConfigFile if configFile == '' else configFile
    config = NetBrainUtils.GetConfig(configFile)
    if len(config) == 0:
        NetBrainUtils.PrintMessage(''.join([CurrentMethodName(), 'Failed to load the configuration file: ',
                                            configFile]), 'Error')
        return False

    try:
        ret = True
        collectionIndexes = list()
        if application is None:
            app = NetBrainDB(config)
            app.Login()
        else:
            app = application
        if app.Logined:
            dbNames = app.GetDatabaseNames()
            for dbName in dbNames:
                collections = app.GetCollectionNames(dbName)
                print(''.join(['-----------------\t', dbName, '\t-----------------']))
                collectionIndex = dict()
                for collection in collections:
                    print(collection)
                    indexInfo = app.GetIndex(dbName, collection).keys()
                    indexes = sorted([key for key in indexInfo])
                    print(''.join(['indexes count: ', str(len(indexes))]))
                    #for index in indexes:
                    #    print('\t', index)
                    collectionIndex.update({collection: indexes})
                collectionIndexes.append({'Database Name': dbName, 'Collection Indexes': collectionIndex})
            filename = config['Output Filename']
            if len(filename):
                #NetBrainUtils.DictionaryToCSVFile(collectionIndexes, filename, ['Database Name', 'Collection Indexes'])
                NetBrainUtils.JsonToFile(collectionIndexes, filename)
    except Exception as e:
        print('Exception raised: ', str(e))
        ret = False
    finally:
        if application is None and app.Logined:
            app.Logout()
        return collectionIndexes


def LoadCollectionIndexes(configFile, header):
    configFile = ConfigFile if configFile == '' else configFile
    config = NetBrainUtils.GetConfig(configFile)
    if len(config) == 0:
        NetBrainUtils.PrintMessage(''.join([CurrentMethodName(), 'Failed to load the configuration file: ',
                                            configFile]), 'Error')
        return False
    #return NetBrainUtils.CSVFileToDictionary(config['Input Filename'], header)
    return NetBrainUtils.FileToJson(config['Input Filename'])

if __name__ == "__main__":
    VerifyMongoDBIndex()

