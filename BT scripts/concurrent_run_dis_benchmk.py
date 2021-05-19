from pymongo import MongoClient
import time
import requests
import json
import logging


def get_tokens(user, password):
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
        logger.debug(token.json())
        return token.json()["token"]
    else:
        return "error"


def run_benchmk_task(task_name):
    run_benchmk_url = host_url + "/ServicesAPI/API/V1/CMDB/Benchmark/Tasks/" + task_name + "/Run"
    try:
        response = requests.post(run_benchmk_url, headers=headers, verify=False)
        if response.status_code == 200:
            res = response.json()
            logger.info(res)
        else:
            logger.error("Benchmark Task running Failed! - " + str(response.text))

    except Exception as e:
        logger.error(str(e))


def run_discover_task(task_id):
    run_discover_url = host_url + "/ServicesAPI/API//V1/CMDB/Discovery/Tasks/" + str(task_id) + "/Run"
    try:
        response = requests.post(run_discover_url, headers=headers, verify=False)
        if response.status_code == 200:
            res = response.json()
            logger.info(res)
        else:
            logger.error("Discover Task running Failed! - " + str(response.text))

    except Exception as e:
        logger.error(str(e))


def get_task_counts():
    fe_sys = connection.get_database('flowengine')
    results = fe_sys.XFTask.aggregate([{"$match": {"taskStatus": {"$lt": 4}}}, {"$group": {"_id": "$taskflowId"}}])
    current_tasks = len(list(results))
    return current_tasks


def define_benchmk_loop(task_name):
    task_count = get_task_counts()
    logger.info('current task num is: ' + str(task_count))
    if task_count >= 16:
        logger.info('current task num fit filter, sleep 5 sec')
        time.sleep(5)
        define_benchmk_loop(task_name)
    else:
        logger.info(run_benchmk_task(task_name))
        logger.info('>>>>> start benchmark task and sleep 10 sec')
        time.sleep(10)


def define_discover_loop(task_name):
    task_count = get_task_counts()
    logger.info('current task num is: ' + str(task_count))
    if task_count >= 16:
        logger.info('current task num fit filter, sleep 5 sec')
        time.sleep(5)
        define_discover_loop(task_name)
    else:
        logger.info(run_discover_task(task_name))
        logger.info('>>>>> start discover task and sleep 10 sec')
        time.sleep(10)


if __name__ == '__main__':
    run_time = time.strftime("%Y-%m-%d_%H-%M", time.localtime())
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    log_fomatter = logging.Formatter("%(asctime)s -- %(levelname)s -- %(message)s")
    handler = logging.FileHandler("Run_dis_benchmk_" + str(run_time) + ".log")
    handler.setLevel(logging.INFO)
    handler.setFormatter(log_fomatter)
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(log_fomatter)
    logger.addHandler(handler)
    logger.addHandler(console)

    db_user = "admin"  # mongodb用户名
    db_password = "admin"  # mongodb密码
    db_host = "10.10.7.220"  # mongodb IP
    db_port = "27017"  # mongodb端口'
    connection = MongoClient("mongodb://" + db_user + ":" + db_password + "@" + db_host + ":" + db_port +
                             "/admin?authMechanism=SCRAM-SHA-256")

    host_url = 'http://10.10.7.153'
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
    user_name = 'perf-test'
    user_passwd = 'Netb@233'
    benchmk_task_name = 'Basic System Benchmark'
    discover_task_name = 'API_Dis'

    tenant_sys = connection.get_database('NGSystem')
    tenant_item = tenant_sys.Tenant.find({})
    for tenant in tenant_item:
        nb_token = get_tokens(user_name, user_passwd)
        headers["Token"] = nb_token
        tenant_name = tenant.get('name')
        tenant_id = tenant.get('_id')
        headers["TenantGuid"] = tenant_id
        domain_items = tenant.get('domains')
        for domain in domain_items:
            domain_name = domain.get('name')
            domain_id = domain.get('guid')
            if tenant_id and domain_id:
                domain_sys = connection.get_database(domain_name)
                dis_task_item = domain_sys.BenchmarkDefinition.find_one({'name': discover_task_name})
                dis_task_id = dis_task_item.get('_id')
                headers["DomainGuid"] = domain_id
                logger.info('### Start schedule discover in domain ' + domain_name)
                define_discover_loop(dis_task_id)
                logger.info('### Start Basic System benchmark in domain ' + domain_name)
                define_benchmk_loop(benchmk_task_name)
        logger.info('Complete ' + str(len(domain_items)) + ' domains in tenant ' + tenant_name + '!')
