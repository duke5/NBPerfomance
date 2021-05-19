from pymongo import MongoClient
import datetime

db_user = "admin"  # mongodb用户名
db_password = "admin"  # mongodb密码
db_host = "10.10.7.220"  # mongodb IP
db_port = "27017"  # mongodb端口'
op_time = datetime.datetime(2020, 10, 23, 18, 50, 0)
connection = MongoClient("mongodb://" + db_user + ":" + db_password + "@" + db_host + ":" + db_port +
                         "/admin?authMechanism=SCRAM-SHA-256")
ng_sys = connection.get_database('NGSystem')
tenant_sys = ng_sys.Tenant.find({})
for tenants in tenant_sys:
    domain_lst = tenants.get('domains')
    for domains in domain_lst:
        domain_name = domains.get('name')
        domain_sys = connection.get_database(domain_name)
        # domain_sys.EnablePasswd.delete_many({})
        # domain_sys.SnmpRoInfo.delete_many({})
        # domain_sys.TelnetInfo.delete_many({})
        pass_flag = domain_sys.EnablePasswd.find_one({'_id': 'nb'})
        snmp_flag = domain_sys.SnmpRoInfo.find_one({'_id': 'nb'})
        telnet_flag = domain_sys.TelnetInfo.find_one({'_id': 'nb'})
        if not pass_flag:
            domain_sys.EnablePasswd.insert_one({
                "_id": "nb",
                "enableUserName": "eyJjZCI6Ill2cHFoWUpobEtXVFgwV244Nis1NlE9PSIsImNuIjoiYWVzLTI1Ni1jYmMiLCJpdiI6Ik5hNlhabWFvQUdZQlFvUGVtWWFIL1E9PSIsImtuIjoiTkJfRU5DWVBUX0RFQ1JZUFRfMCIsImt2IjoxLCJ2IjoxfQo=",
                "refCount": 0,
                "alias": "nb",
                "enablePassword": "eyJjZCI6Im1zcGl0VzIzRi82bVRXSGthR3k2S1E9PSIsImNuIjoiYWVzLTI1Ni1jYmMiLCJpdiI6ImdWZEUrNnoxdllqUWswQzZqSnU5WXc9PSIsImtuIjoiTkJfRU5DWVBUX0RFQ1JZUFRfMCIsImt2IjoxLCJ2IjoxfQo=",
                "order": 0,
                "operateInfo": {
                    "opUser": "admin",
                    "opUserId": None,
                    "opTime": op_time
                }
            })
        if not snmp_flag:
            domain_sys.SnmpRoInfo.insert_many([{
                "_id": "nb",
                "snmpPort": 0,
                "roString": "eyJjZCI6ImtMcTlOV1pEdzRMeGtGODRBU2thWWc9PSIsImNuIjoiYWVzLTI1Ni1jYmMiLCJpdiI6IlJKNTk1RmV5OEd2bGs0RGREUDVaSEE9PSIsImtuIjoiTkJfRU5DWVBUX0RFQ1JZUFRfMCIsImt2IjoxLCJ2IjoxfQo=",
                "alias": "nb",
                "snmpVersion": 1,
                "v3": None,
                "refCount": 0,
                "order": 0,
                "operateInfo": {
                    "opUser": "admin",
                    "opUserId": None,
                    "opTime": op_time
                }
            }, {
                "_id": "netbrain",
                "snmpPort": 0,
                "roString": "eyJjZCI6IitkRWR0ZlBrT1M5a1NmNEtiTHlZU2c9PSIsImNuIjoiYWVzLTI1Ni1jYmMiLCJpdiI6IkY5SUVDbk5wV1JlYkZJTXdacHBKYmc9PSIsImtuIjoiTkJfRU5DWVBUX0RFQ1JZUFRfMCIsImt2IjoxLCJ2IjoxfQo=",
                "alias": "netbrain",
                "snmpVersion": 1,
                "v3": None,
                "refCount": 0,
                "order": 1,
                "operateInfo": {
                    "opUser": "admin",
                    "opUserId": None,
                    "opTime": op_time
                }
            }])
        if not telnet_flag:
            domain_sys.TelnetInfo.insert_one({
                "_id": "nb",
                "userName": "eyJjZCI6Ik83Qms5d2o3d1N1OStlcTdJRDQ5eXc9PSIsImNuIjoiYWVzLTI1Ni1jYmMiLCJpdiI6IjBaYkFyNll4Z3dTZHVmdnZKMnEzYUE9PSIsImtuIjoiTkJfRU5DWVBUX0RFQ1JZUFRfMCIsImt2IjoxLCJ2IjoxfQo=",
                "alias": "nb",
                "cliMode": 0,
                "sshKeyID": "",
                "password": "eyJjZCI6IlliOEFmQzJlU2JMcSsrUSs3SGs5amc9PSIsImNuIjoiYWVzLTI1Ni1jYmMiLCJpdiI6ImNiQjZyZWNNNWxWZlVuaGJMdDhYMGc9PSIsImtuIjoiTkJfRU5DWVBUX0RFQ1JZUFRfMCIsImt2IjoxLCJ2IjoxfQo=",
                "refCount": 0,
                "order": 0,
                "operateInfo": {
                    "opUser": "admin",
                    "opUserId": None,
                    "opTime": op_time
                }
            })
