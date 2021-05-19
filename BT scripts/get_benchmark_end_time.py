from pymongo import MongoClient
import csv

db_user = "admin"  # mongodb用户名
db_password = "admin"  # mongodb密码
db_host = "10.10.7.220"  # mongodb IP
db_port = "27017"  # mongodb端口'
connection = MongoClient("mongodb://" + db_user + ":" + db_password + "@" + db_host + ":" + db_port +
                         "/admin?authMechanism=SCRAM-SHA-256")
# count = 0
ng_sys = connection.get_database('NGSystem')
tenant_items = ng_sys.Tenant.find({'name': 'BT_Tenant1'})
for tenant in tenant_items:
    domain_items = tenant.get('domains')
    for domain in domain_items:
        domain_name = domain.get('name')
        domain_sys = connection.get_database(domain_name)
        benmk = domain_sys.DeviceDataSource.find({'name': 'Basic System Benchmark'}).sort('endTime', -1).limit(1)
        if benmk:
            for dm in benmk:
                print('End time in domain ' + domain_name + ' is: ' + str(dm.get('endTime')))
            # count += 1
# print('Total count is: ' + str(count))

# for tenant in tenant_items:
#     tenant_id = tenant.get('_id')
#     domain_items = tenant.get('domains')
#     for domain in domain_items:
#         sub_lst = []
#         domain_id = domain.get('guid')
#         domain_name = domain.get('name')
#         domain_sys = connection.get_database(domain_name)
#         ben_item = domain_sys.BenchmarkDefinition.find_one({'name': 'Basic System Benchmark'})
#         ben_job_id = ben_item.get('jobId')
#         print(tenant_id, domain_id, ben_job_id)
