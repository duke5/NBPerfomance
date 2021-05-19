import requests
import json
from pymongo import MongoClient


# tenant_id = "fa00d18a-bf1a-b4c2-6782-01729afcd9e3"
# domain_id = "d473cf9c-56a5-477e-94f0-05db35406437"
# domain_id = "5aadeab3-26f3-4958-ad55-3fbc66595e24"
# tenant_id = "514b1bef-e55f-f7f7-808f-aba5398023a0"


def get_tokens(host_url, headers, user, password):
    login_api_url = r"/ServicesAPI/API/V1/Session"
    login_url = host_url + login_api_url
    data = {
        "username": user,
        "password": password,
        # "authentication_id": 'c600c90d-e29c-26d5-8f15-4fee3dce41a0'
    }
    token = requests.post(login_url, data=json.dumps(
        data), headers=headers, verify=False)
    if token.status_code == 200:
        print(token.json())
        return token.json()["token"]
    else:
        return "error"


dis_body = {
    "taskName": "API_Dis",
    "newTaskName": "",
    "description": "",
    "startDate": "2020/05/04",
    "endDate": "2020/05/05",
    "schedule": {
        "frequency": "once",
        "interval": "",
        "startTime": ["15:16:10"],
        "weekday": [],
        "dayOfMonth": "",
        "months": []
    },
    "isEnable": True
}

ip_body = {     # for test
    "seeds": [
        {"mgmtIP": "192.168.1.101"},
        {"mgmtIP": "192.168.1.102"}
    ]

}


def add_discovery_task(host_url, body, dis_header):
    add_dis_url = host_url + "/ServicesAPI/API/V1/CMDB/Discovery/Tasks"
    try:
        # Do the HTTP request
        response = requests.post(add_dis_url, headers=dis_header, data=json.dumps(body), verify=False)
        # Check for HTTP codes other than 200
        if response.status_code == 200:
            # Decode the JSON response into a dictionary and use the data
            js = response.json()
            return js
        else:
            return "Add discovery task failed! - " + str(response.text)
    except Exception as e:
        return str(e)


def add_dis_ips(host_url, body, dis_header, task_id):
    dis_ip_url = host_url + "/ServicesAPI/API//V1/CMDB/Discovery/Tasks/" + str(task_id) + "/Seeds"
    try:
        # Do the HTTP request
        response = requests.post(dis_ip_url, headers=dis_header, data=json.dumps(body), verify=False)
        # Check for HTTP codes other than 200
        if response.status_code == 200:
            # Decode the JSON response into a dictionary and use the data
            js = response.json()
            return js
        else:
            return "Add discovery task failed! - " + str(response.text)
    except Exception as e:
        return str(e)


def run_discover_task(task_id, headers):
    run_discover_url = nb_url + "/ServicesAPI/API//V1/CMDB/Discovery/Tasks/" + str(task_id) + "/Run"
    try:
        response = requests.post(run_discover_url, headers=headers, verify=False)
        if response.status_code == 200:
            res = response.json()
            print(res)
        else:
            print("Discover Task running Failed! - " + str(response.text))

    except Exception as e:
        print(str(e))


if __name__ == '__main__':
    db_user = "admin"  # mongodb用户名
    db_password = "admin"  # mongodb密码
    db_host = "10.10.7.220"  # mongodb IP
    db_port = "27017"  # mongodb端口'
    connection = MongoClient("mongodb://" + db_user + ":" + db_password + "@" + db_host + ":" + db_port +
                             "/admin?authMechanism=SCRAM-SHA-256")

    nb_url = "http://10.10.7.153"
    nb_headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
    nb_user = "perf-test"
    nb_passwd = "Netb@233"

    discover_task_name = 'API_Dis'

    tenant_sys = connection.get_database('NGSystem')
    tenant_item = tenant_sys.Tenant.find({})
    for tenant in tenant_item:
        nb_token = get_tokens(nb_url, nb_headers, nb_user, nb_passwd)
        nb_headers["Token"] = nb_token
        tenant_name = tenant.get('name')
        tenant_id = tenant.get('_id')
        nb_headers["TenantGuid"] = tenant_id
        domain_items = tenant.get('domains')
        for domain in domain_items:
            domain_name = domain.get('name')
            domain_id = domain.get('guid')
            if tenant_id and domain_id:
                # domain_sys = connection.get_database(domain_name)
                # dis_task_item = domain_sys.BenchmarkDefinition.find_one({'name': discover_task_name})
                # dis_task_id = dis_task_item.get('_id')
                nb_headers["DomainGuid"] = domain_id
                print('### Start Add api discovery task in domain ' + domain_name)
                print(add_discovery_task(nb_url, dis_body, nb_headers))
        print('Complete add ' + str(len(domain_items)) + ' discover tasks in tenant ' + tenant_name + '!')

