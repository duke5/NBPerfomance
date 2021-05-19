import requests
from pymongo import MongoClient
import urllib3
import pprint
import json

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def bulk_schedule(start_date, start_time, interval_min):
    day_lst = start_date.split('-')
    time_lst = start_time.split(':')
    s_min = int(time_lst[1])
    s_hour = int(time_lst[0])
    s_day = int(day_lst[-1])
    s_min = s_min + interval_min
    if s_min >= 60:
        s_min -= 60
        s_hour += 1
        if s_hour >= 24:
            s_hour -= 24
            s_day += 1
    day_lst[-1] = str(s_day)
    time_lst[0] = str(s_hour)
    time_lst[1] = str(s_min)
    new_start_date = '-'.join(day_lst)
    new_start_time = ':'.join(time_lst)
    return new_start_date, new_start_time


def get_tokens(h_url, nb_user, nb_password):
    login_api_url = r"/ServicesAPI/API/V1/Session"
    login_url = h_url + login_api_url
    data = {
        "username": nb_user,
        "password": nb_password,
        # "authentication_id": "1b04655c-6262-9336-5151-6180243eb8ee"
    }
    nb_token = requests.post(login_url, data=json.dumps(
        data), headers=headers, verify=False)
    if nb_token.status_code == 200:
        print(nb_token.json())
        return nb_token.json()["token"]
    else:
        return "error"


def logout(h_url, nb_token, nb_heads):
    logout_url = "/ServicesAPI/API/V1/Session"
    # time.sleep(2)
    full_url = h_url + logout_url
    body = {
        "token": nb_token
    }
    result = requests.delete(full_url, data=json.dumps(
        body), headers=nb_heads, verify=False)
    # print(result.json())
    if result.status_code == 200:
        print("LogOut success...")
    else:
        data = "errorCode" + "LogOut API test failed... "
        return data


def update_benchmark(h_url, nb_heads, ben_task_name, start_date, start_time):
    up_ben_url = "/ServicesAPI/API/V1/CMDB/Benchmark/Tasks"
    full_url = h_url + up_ben_url
    body_cont = {
        "taskName": ben_task_name,  # The name of the task.
        "startDate": start_date,
        "schedule": {
            "frequency": "once",
            "startTime": [start_time]
            },
        "isEnable": True
        }

    try:
        response = requests.put(full_url, data=json.dumps(body_cont), headers=nb_heads, verify=False)
        if response.status_code == 200:
            result = response.json()
            print(result)
        else:
            print("Benchmark Task updated Failed! - " + str(response.text))

    except Exception as e:
        print(str(e))


if __name__ == "__main__":
    user = "perf-test"
    pwd = "Perf@233"
    host_url = "http://10.10.7.153"  # 10.10./ #
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
    benmark_name = "Basic System Benchmark"
    start_d = '2020-10-28'
    start_t = '10:20:00'

    b_token = get_tokens(host_url, user, pwd)
    headers["Token"] = b_token
    # headers["TenantGuid"] = "f1114ac1-8fad-87f2-a27d-15d659200b59"
    # headers["DomainGuid"] = "b55d4b19-fbd3-4f59-9af1-8f9024ab0811"
    # update_benchmark(host_url, headers, benmark_name, start_d, start_t)
    # logout(host_url, b_token, headers)
    db_user = "admin"  # mongodb用户名
    db_password = "admin"  # mongodb密码
    db_host = "10.10.7.220"  # mongodb IP
    db_port = "27017"  # mongodb端口'
    connection = MongoClient("mongodb://" + db_user + ":" + db_password + "@" + db_host + ":" + db_port +
                             "/admin?authMechanism=SCRAM-SHA-256")

    ng_sys = connection.get_database('NGSystem')
    tenants = ng_sys.Tenant.find({})
    for tenant_sys in tenants:
        tenant_id = tenant_sys.get('_id')
        headers["TenantGuid"] = tenant_id
        domains = tenant_sys.get('domains')
        for domain_sys in domains:
            domain_name = domain_sys.get('name')
            domain_id = domain_sys.get('guid')
            headers["DomainGuid"] = domain_id
            start_d, start_t = bulk_schedule(start_d, start_t, 2)
            update_benchmark(host_url, headers, benmark_name, start_d, start_t)
    logout(host_url, b_token, headers)
