import datetime
import re

from pymongo import MongoClient

if __name__ == '__main__':
    generate_csv = False  # 开启后在当前文件夹生成csv文件
    domain_name = "NA45k_dm"  # domain名称
    # benchmark_name = ""  # 如果配置Benchmark name将直接根据name遍历所有该name的Benchmark，task id配置将无效
    # task_id = "19a6c5e8-d3dc-4ba4-9f16-2c75398c7900"  # task id 自动识别类型
    db_user = "admin"  # mongodb用户名
    db_password = "netbrain"  # mongodb密码
    db_host = "192.168.31.197"  # mongodb IP
    db_port = "27017"  # mongodb端口
    is_ssl = False  # 是否配置SSL，默认false

    starttime = datetime.datetime(2021, 6, 9, 6, 42, 0)
    endtime = datetime.datetime(2021, 6, 9, 7, 44, 0)

    task_type_lst5 = ['ExeCliCmdMiniTask']
    task_type_lst10 = ['RunCompareTask', 'RetrieveLiveDataMiniTask', 'ExeCliCmdMiniTask', 'RunMultiNIAnalysisTask',
                       'RunNICreateDTGTask']
    task_type_lst20 = ['RunCompareTask', 'RunPingMiniTask', 'RunTraceRouteMiniTask', 'RetrieveLiveDataMiniTask',
                       'ExeCliCmdMiniTask', 'QappHistoricalDataAnalysisTask', 'RunNICreateDTGTask',
                       'RunMultiNIAnalysisTask']

    if is_ssl:
        connection = MongoClient("mongodb://" + db_user + ":" + db_password + "@" + db_host + ":" + db_port +
                                 "/admin?authMechanism=SCRAM-SHA-256&ssl=true&ssl_cert_reqs=CERT_NONE")
    else:
        connection = MongoClient("mongodb://" + db_user + ":" + db_password + "@" + db_host + ":" + db_port +
                                 "/admin?authMechanism=SCRAM-SHA-256")
    tesys = connection.get_database('flowengine')
    domsys = connection.get_database(domain_name)

    path_tasks = domsys.P2pPath.find({'startTime': {'$gt': starttime, '$lt': endtime}})
    pt_lst = list(path_tasks)
    pt_sum = 0.00
    success_count = 0
    for pt in pt_lst:
        pt_log = pt.get('log')
        partn = re.compile(r'A to B Path was done with status "(.*)" in (.*)s', re.M)
        m = partn.search(pt_log)
        p_status = m.group(1)
        if p_status == 'Success':
            p_time = float(m.group(2))
            pt_sum += p_time
            success_count += 1
    if success_count != 0:
        pt_avg_time = round(pt_sum / success_count, 3)
    else:
        pt_avg_time = 0.000
    print('Path avg execution time is: ' + str(pt_avg_time))

    for task_t in task_type_lst20:
        work_tasks = tesys.XFTask.find({'taskType': task_t, 'startTime': {'$gt': starttime, '$lt': endtime}})
        task_lst = list(work_tasks)
        count_time = datetime.timedelta(seconds=0)
        for cli_t in task_lst:
            t_start = cli_t.get('startTime')
            t_end = cli_t.get('endTime')
            if t_start and t_end:
                task_time = t_end - t_start
                # print(task_t + ' time is: ' + str(task_time))
                count_time += task_time
        if len(task_lst) != 0:
            avg_task_time = count_time / len(task_lst)
        else:
            avg_task_time = 0

        print(task_t + ' avg execution time is: ' + str(avg_task_time))
