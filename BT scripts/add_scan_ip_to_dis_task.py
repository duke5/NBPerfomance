from pymongo import MongoClient
import uuid
import datetime

op_time = datetime.datetime(2020, 5, 4, 11, 11, 11)

insert_content = {
    "_id": "a0499eda-10a8-e909-41b6-ab46bec8acb4",
    "mgmtIP": "172.24.101.12",
    "proxyServer": None,
    "cliType": None,
    "cliPort": None,
    "username": None,
    "password": None,
    "privilegeUsername": None,
    "privilegePassword": None,
    "snmpCommunityString": None,
    "operateInfo": {
        "opUserId": "1072c220-11ed-4495-b76e-d1c5ac742b1e",
        "opUser": "perf-test",
        "opTime": op_time
    },
    "designatedCredentials": False,
    "discoverTask": "53d51b9c-aaf2-442e-9988-2453af894b69",
    "hostname": None,
    "sourceType": 0
}

if __name__ == '__main__':
    db_user = "admin"  # mongodb用户名
    db_password = "admin"  # mongodb密码
    db_host = "10.10.7.220"  # mongodb IP
    db_port = "27017"  # mongodb端口'
    connection = MongoClient("mongodb://" + db_user + ":" + db_password + "@" + db_host + ":" + db_port +
                             "/admin?authMechanism=SCRAM-SHA-256")

    discover_task_name = 'API_Dis'

    tenant_sys = connection.get_database('NGSystem')
    tenant_item = tenant_sys.Tenant.find({})
    for tenant in tenant_item:
        tenant_name = tenant.get('name')
        domain_items = tenant.get('domains')
        for domain in domain_items:
            ip_count = 0
            domain_name = domain.get('name')
            print('Begin process domain ' + domain_name)
            domain_sys = connection.get_database(domain_name)
            dis_item = domain_sys.BenchmarkDefinition.find_one({'name': discover_task_name})
            dis_id = dis_item.get('_id')
            print('dis id is ' + dis_id)
            insert_content['discoverTask'] = dis_id
            ip_item = domain_sys.BenchmarkDefinition.find_one({'name': 'auto_dis'})
            ip_lists = ip_item.get('discoverOption').get('hostips')
            for ip_item in ip_lists:
                insert_content['_id'] = str(uuid.uuid1())
                insert_content['mgmtIP'] = ip_item
                domain_sys.ThirdPartyDiscovery.insert_one(insert_content)
                ip_count += 1
            print('Finished insert ' + str(ip_count) + ' ips in domain ' + domain_name + '!')

        print('Complete add ' + str(len(domain_items)) + ' discover tasks in tenant ' + tenant_name + '!')
