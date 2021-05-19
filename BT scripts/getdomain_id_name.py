from pymongo import MongoClient
import csv

db_user = "admin"  # mongodb用户名
db_password = "admin"  # mongodb密码
db_host = "10.10.7.220"  # mongodb IP
db_port = "27017"  # mongodb端口'
connection = MongoClient("mongodb://" + db_user + ":" + db_password + "@" + db_host + ":" + db_port +
                         "/admin?authMechanism=SCRAM-SHA-256")
write_csv = True
result_lst = []
ng_sys = connection.get_database('NGSystem')
# get_domain_list_pip_line = [{"$unwind": "$domains"}, {"$project": {'dname': '$domains.dbName', 'tname': '$name'}}]
# domain_list = ng_sys.Tenant.aggregate(get_domain_list_pip_line)
tenants = ng_sys.Tenant.find({})
for tenant in tenants:
    tenant_id = tenant.get("_id")
    tenant_name = tenant.get("name")
    domain_lst = tenant.get("domains")
    for tmp in domain_lst:
        domain_name = tmp.get('name')
        domain_id = tmp.get('guid')
        print(domain_name, domain_id)

#     if len(domain_lst) >= 20:
#         for i in range(20):
#             sub_lst = []
#             domain_id = domain_lst[i].get("guid")
#             domain_name = domain_lst[i].get("name")
#             domain_sys = connection.get_database(domain_name)
#             dg_item = domain_sys.DeviceGroup.find_one({'Name': 'auto_dg'})
#             # print(tenant_name, tenant_id, domain_id, domain_name)
#
#             if dg_item:
#                 sub_lst.append(tenant_id)
#                 sub_lst.append(domain_id)
#                 sub_lst.append(domain_name)
#                 dg_id = dg_item.get('_id')
#                 # print([dg_id])
#                 sub_lst.append(dg_id)
#                 dg_size = len(dg_item.get('StaticDevices'))
#                 print([tenant_id, domain_id, domain_name, dg_id, dg_size])
#             result_lst.append(sub_lst)
# title_list = ['Tenant_id', 'Domain_id', 'Domain_name', 'DG_id']
# domaininfo = "domain_id_name.csv"
# if write_csv:
#     with open(domaininfo, 'a', newline='') as data:
#         result_file = csv.writer(data)
#         result_file.writerow(title_list)
#         for row in result_lst:
#             result_file.writerow(row)
