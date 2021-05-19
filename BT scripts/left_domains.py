from pymongo import MongoClient

db_user = "admin"  # mongodb用户名
db_password = "admin"  # mongodb密码
db_host = "10.10.7.220"  # mongodb IP
db_port = "27017"  # mongodb端口'
connection = MongoClient("mongodb://" + db_user + ":" + db_password + "@" + db_host + ":" + db_port +
                         "/admin?authMechanism=SCRAM-SHA-256")
left_cout = 0
ng_sys = connection.get_database('NGSystem')
tenants = ng_sys.Tenant.find({})
for tenant_sys in tenants:
    domains = tenant_sys.get('domains')
    for domain_sys in domains:
        domain_name = domain_sys.get('name')
        domain_item = connection.get_database(domain_name)
        dg_item = domain_item.DeviceGroup.find_one({'Name': 'auto_dg'})
        if dg_item:
            # domain_item.DeviceGroup.remove({'Name': 'auto_dg'})
            # print('Delete device group in ' + domain_name)
            # left_cout += 1
            staticdevice = dg_item.get('StaticDevices')
            device_count = len(staticdevice)
            print('Dg in ' + domain_name + ' has ' + str(device_count) + ' devices')
            if device_count < 20:
                left_cout += 1
print(str(left_cout))
