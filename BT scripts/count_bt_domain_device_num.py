from pymongo import MongoClient
import csv

db_user = "admin"  # mongodb用户名
db_password = "admin"  # mongodb密码
db_host = "10.10.7.220"  # mongodb IP
db_port = "27017"  # mongodb端口'
connection = MongoClient("mongodb://" + db_user + ":" + db_password + "@" + db_host + ":" + db_port +
                         "/admin?authMechanism=SCRAM-SHA-256")
# write_csv = True
# result_lst = []
ng_sys = connection.get_database('NGSystem')
# get_domain_list_pip_line = [{"$unwind": "$domains"}, {"$project": {'dname': '$domains.dbName', 'tname': '$name'}}]
# domain_list = ng_sys.Tenant.aggregate(get_domain_list_pip_line)
tenants = ng_sys.Tenant.find({})
for tenant in tenants:
    # tenant_id = tenant.get("_id")
    # tenant_name = tenant.get("name")
    domain_lst = tenant.get("domains")
    for tmp in domain_lst:
        domain_name = tmp.get('name')
        # domain_id = tmp.get('guid')
        # print(domain_name, domain_id)
        domain_sys = connection.get_database(domain_name)
        device_count = domain_sys.Device.estimated_document_count()
        # if device_count < 20:
        print(domain_name + ' device count is: ' + str(device_count))



