# Create by Tony Che at 2020-01

# NetBrainDB.py
# Feature description

import json
import csv
import uuid
import inspect
import psycopg2
from datetime import datetime
from pymongo import MongoClient
from Utils.NetBrainUtils import NetBrainUtils, CurrentMethodName, CreateGuid
from NetBrainIE import NetBrainIE, PrintMessage

class NetBrainDB():
    def __init__(self, dbInfo):
        self.Server = dbInfo.get('MongoDB Server', '')
        self.Port = str(dbInfo.get('Port', 27017))
        self.SSLEnable = dbInfo.get('SSL Enable', False)
        self.Username = dbInfo.get('Username', '')
        self.Password = dbInfo.get('Password', '')
        self.ConnectedClient = None
        self.Database = None
        self.Logined = False

    def Login(self, username:str='', password:str=''):
        if len(username):
            self.Username = username
        if len(password):
            self.Password = password
        if self.Server == '':
            PrintMessage('DB server is NOT set.', 'Error')
            return False
        if self.Port == '':
            PrintMessage('DB port is NOT set.', 'Error')
            return False
        if self.Username == '':
            PrintMessage('DB user is NOT set', 'Error')
            return False
        if self.SSLEnable:
            connect = ''.join(['mongodb://', self.Username, ':', self.Password, '@', self.Server, ':', str(self.Port),
                               '/admin?authMechanism=SCRAM-SHA-256&ssl=true&ssl_cert_reqs=CERT_NONE'])
        else:
            connect = ''.join(['mongodb://', self.Username, ':', self.Password, '@', self.Server, ':', str(self.Port),
                               '/admin?authMechanism=SCRAM-SHA-256'])
        try:
            self.ConnectedClient = MongoClient(connect)
            self.Logined = True
        except Exception as e:
            PrintMessage(''.join([CurrentMethodName(), 'failed: ', str(e)]), 'Error')
            return False
        return True

    def Logout(self):
        self.ConnectedClient.close()
        self.Logined = False

    def GetDatabase(self, databaseName:str):
        try:
            self.Database = self.ConnectedClient.get_database(databaseName.replace(' ', '_'))
        except Exception as e:
            PrintMessage(''.join([CurrentMethodName(), 'failed: ', str(e)]), 'Error')
            return None
        return self.Database

    def LocalTimeToUTCTime(self, localTime:datetime):
        offsetTimeZone = datetime.utcnow() - datetime.now()
        utcTime = localTime + offsetTimeZone
        return utcTime

    def Count(self, tableName:str, conditions={}):
        count = self.Database[tableName].find(conditions).count()
        return count

    def GetDatabaseNames(self):
        return sorted(self.ConnectedClient.database_names())

    def GetCollectionNames(self, dbName:str):
        return sorted(self.ConnectedClient[dbName].list_collection_names())

    def CreateCollection(self, name:str):
        self.Database.create_collection(name)

    def GetStats(self, dbName:str=None):
        if dbName is not None:
            self.GetDatabase(dbName)
        return self.Database.command("dbstats")

    def GetIndex(self, dbName:str, collectionName:str):
        return self.ConnectedClient[dbName][collectionName].index_information()

    def GetDistinct(self, tableName:str, distinct, query):
        item = self.Database[tableName].find(query).distinct(distinct)
        return item

    def Group(self, tableName:str, key, condition, initial, reduce):
        item = self.Database[tableName].group(key=key, condition=condition, initial=initial, reduce=reduce)
        return list(item)

    def AggregrateAll(self, tableName:str, conditions={}):
        item = self.Database[tableName].aggregate(conditions)['result']
        return list(item)

    def GetAll(self, tableName:str, conditions={}, sort='_id', sortOrder=-1, limit=100000):
        # For multiple fields: .sort([("field1", pymongo.ASCENDING), ("field2", pymongo.DESCENDING)])
        table = self.Database[tableName]
        #x = table.find({'name':'ustta000231'})
        #y = list(x)
        if sort is None:
            item = self.Database[tableName].find(conditions).limit(limit)
        else:
            if isinstance(sort, list):
                item = self.Database[tableName].find(conditions).sort(sort).limit(limit)
            else:
                item = self.Database[tableName].find(conditions).sort(sort, sortOrder).limit(limit)
        return list(item)

    def GetOne(self, tableName:str, conditions={}):
        item = self.Database[tableName].find_one(conditions)
        return item

    def InsertOne(self, tableName:str, value):
        item = self.Database[tableName].insert(value)
        return item

    def InsertMany(self, tableName:str, value):
        if len(value) <= 0:
            return []
        item = self.Database[tableName].insert_many(value)
        return item.inserted_ids

    def Update(self, tableName:str, where:dict, value):
        item = self.Database[tableName].update(where,{"$set":value}, upsert=False)
        return item

    def UpdateMulti(self, tableName:str, where:dict, value):
        item = self.Database[tableName].update(where,{"$set":value}, upsert=False, multi=True)
        return list(item)

    def Upsert(self, tableName:str, where:dict, value):
        item = self.Database[tableName].update(where,{"$set":value}, upsert=True)
        return list(item)

    def UpsertMany_deletet_insert(self, tableName:str, where:dict, values:list):
        item = self.Database[tableName].delete_many(where)
        item = self.InsertMany(tableName, values)

        return item

    def UpsertMany(self, tableName:str, where_cols:list, values:list):
        #not finished yet
        for value in values:
            where = {}
            for col in where_cols:
                where[col] = value[col]
            item = self.GetAll(tableName, where)
            if item:
                del value['_id']
                item = self.Database[tableName].replace_one(where, value, upsert=True)
            else:
                item = self.Database[tableName].insert_one(value)
        return item

    def GetDeviceIDs(self, tableName:str, deviceIPs:list):
        deviceIDs = []
        devices = self.Database[tableName].find({'manageIP': {'$in': deviceIPs}})
        for device in devices:
            deviceIDs.append(device['_id'])
        return deviceIDs

class PostgresDB():
    def __init__(self, dbInfo):
        self.Server = dbInfo.get('Server', '')
        self.Port = str(dbInfo.get('Port', 5432))
        self.Username = dbInfo.get('Username', '')
        self.Password = dbInfo.get('Password', '')
        self.Database = dbInfo.get('Database', 'postgres')
        self.ConnectedClient = None
        self.Cursor = None
        self.Logined = False

    def Login(self, database:str='postgres', username:str='', password:str=''):
        if len(username):
            self.Username = username
        if len(password):
            self.Password = password
        if self.Server == '':
            PrintMessage('DB server is NOT set.', 'Error')
            return False
        if self.Port == '':
            PrintMessage('DB port is NOT set.', 'Error')
            return False
        if self.Username == '' or self.Password == '':
            PrintMessage('DB user/password is NOT set', 'Error')
            return False
        try:
            self.ConnectedClient = psycopg2.connect(host=self.Server, port=self.Port, database=database,
                                                    user=self.Username, password=self.Password)
            self.Logined = True
            self.Cursor = self.ConnectedClient.cursor()
        except Exception as e:
            PrintMessage(''.join([CurrentMethodName(), ' failed: ', str(e)]), 'Error')
            return False
        return True

    def Logout(self):
        if self.Logined:
            self.Cursor.close()
            self.ConnectedClient.close()
            self.Logined = False

    def Execute(self, sql:str):
        self.Cursor.execute(sql)
        return True

    def GetOne(self, sql:str):
        self.Execute(sql)
        ret = self.Cursor.fetchone()
        return ret

    def GetAll(self, sql:str):
        self.Execute(sql)
        ret = self.Cursor.fetchall()
        return ret



