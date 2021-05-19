from pymongo import MongoClient
import datetime
import uuid

db_user = "admin"  # mongodb用户名
db_password = "admin"  # mongodb密码
db_host = "10.10.7.220"  # mongodb IP
db_port = "27017"  # mongodb端口'
op_time = datetime.datetime(2020, 3, 26, 23, 50, 0)
connection = MongoClient("mongodb://" + db_user + ":" + db_password + "@" + db_host + ":" + db_port +
                         "/admin?authMechanism=SCRAM-SHA-256")
ng_sys = connection.get_database('NGSystem')

# tenant5_id = '35031488-62d7-2841-8105-801616a1c69e'
tenant5_id = '9602ec31-2e8f-a90b-0531-20fee589bba6'  # retrieve
tenant3_id = '6dba9b78-6485-3130-aabb-cd7aea38a835'  # cli
dmid_lst3 = ['07204d05-260f-405d-ae72-5f446b1cf7ec', '5317de05-8493-470c-9f54-ad2871fece01',
             'ce338a1d-c7f9-4ac7-90d8-f30d81b8de8b', '10c581da-c449-4483-be92-aa2e71030680',
             'c8108669-96f6-4771-a766-dbd4f18486ab', 'bc24fe22-f6ca-436d-891c-b310fe5d5c81',
             'e6c4fbb3-98bf-4284-97f3-0480697b3c0b', '379b8439-78b0-472e-84ca-32c53011c14b',
             'e182077f-8b44-42fc-9000-e0f3025fc768', '7c614dd4-33a6-4284-89bb-385ed2b9cedb',
             '41869b7f-b178-461e-8eb2-a833804b4aee']
dmid_lst5 = ['79d76c9a-ef62-44a7-ad25-38b93e3faf1c', 'ddbe39a2-768a-41e4-985c-ae29243e87e0',
             '8400d4d3-3812-4995-906a-8beeefabfed7', '2b805b27-dae0-47d5-91b4-3b182eb2fdf3',
             'eecaff75-5cfe-45f3-ba1a-66c591a2d2c0', '40bad2e5-4190-48e5-b518-ed7dca87029d',
             'd733932e-b54e-456c-9c10-35b308b6225b', '146f099d-4d66-4ba1-908e-f7cb89bf9696',
             '5c837542-4d48-4b4e-97e2-d6f3e12e5e38', '4311f9d5-32c8-4e33-af5d-b654e5ccc660',
             'ca5bc1ef-07b6-4bca-b6c4-45c099d4a0c6']
# dmid_lst5 = ['c32a7d11-ab10-4e10-a641-2bb64eb59089']
a_log_id_lst = ['cbbd04a0-3457-4a68-a219-e8510f01df92', 'c9526e64-0dc4-4120-86ac-49a7ef34c518', '9f4fa1b1-ddbf-49c8-a10a-c93012ef6190', '5b25302e-ad3e-417f-afb0-96fe81a1cf4f', '60de4e93-c3a9-4155-91b2-8d0abbdf20aa', '7ecc1c48-4309-4b48-bf3a-f7340a2bc245']

tenant_item = ng_sys.Tenant.find_one({'_id': tenant3_id})
domains = tenant_item.get('domains')
for domain_item in domains:
    domain_id = domain_item.get('guid')
    for dm in dmid_lst3:
        if dm == domain_id:
            domain_name = domain_item.get('name')
            # print('domain name is :' + domain_name)
            domain_sys = connection.get_database(domain_name)
            for alog in a_log_id_lst:
                big_items = domain_sys.DeviceBenchmarkResult.find({'alogid': alog})
                if big_items:
                    big_one = domain_sys.DeviceBenchmarkResult.find({'alogid': alog}).sort([('spendSecond', -1)]).limit(
                        1)
                    # print(big_one)
                    for one in big_one:
                        spendtime = one.get('spendSecond')
                        print(domain_name + ' Longest spend time is:' + str(spendtime))
                else:
                    print('coud not find the alog items')
