# -*- coding=utf-8 -*-
from pymongo import MongoClient
import csv

generate_csv = True    #开启后在当前文件夹生成csv文件
domain_name = "5Wmic"   #domain名称
db_user = "mongodb"     #mongodb用户名
db_password = "mongodb"     #mongodb密码
db_host = "10.10.7.220"     #mongodb IP
db_port = "27019"       #mongodb端口
is_ssl = False      #是否配置SSL，默认false

# built_in_qapplist = ["Highlight Specified VLAN        ", "Device Information              ", "Highlight Routing Protocol      ", "BGP                             ", "QoS                             ", "OSPF                            ", "Spanning Tree                   ", "Multicast                       ", "Interface Speed and MTU Overview", "MPLS                            ", "VRF                             ", "Access List                     ", "Network Table Overview          ", "EIGRP                           ", "Basic Health Check [SNMP]       "]
# built_in_qapplist = ["Highlight Specified VLAN        ", "BGP                             ", "QoS                             ", "OSPF                            ", "Spanning Tree                   ", "Multicast                       ", "MPLS                            ", "VRF                             ", "Access List                     ", "Network Table Overview          ", "EIGRP                           "]
# built_in_qapplist = ["Highlight Specified VLAN", "BGP", "QoS", "OSPF", "Spanning Tree", "Multicast", "MPLS", "VRF", "Access List", "Network Table Overview", "EIGRP"]


if is_ssl:
    connection = MongoClient("mongodb://" + db_user + ":" + db_password + "@" + db_host + ":" + db_port +
                             "/admin?authMechanism=SCRAM-SHA-1&ssl=true&ssl_cert_reqs=CERT_NONE")
else:
    connection = MongoClient("mongodb://" + db_user + ":" + db_password + "@" + db_host + ":" + db_port +
                             "/admin?authMechanism=SCRAM-SHA-1")
condomain = connection.get_database(domain_name)
conflowengine = connection.get_database("flowengine")

built_in_qapplist = []
result_list = []

active_qapps = condomain.ScheduleQappTask.find({'active': True})
for actitems in active_qapps:
    actqapp_name = actitems.get('name')
    built_in_qapplist.append(actqapp_name)

print("---------------------------------------------------------------------------------")
# print("| Scheduler Qapp name                |   Create DTG Time  |  Analysis DTG Time |")
# print("| \033[1;34mScheduler Qapp name\033[0m                |   \033[1;34mCreate DTG \033[0m      |  \033[1;34mAnalysis DTG Time\033[0m |")
print("{:^1}\t{:^38}\t{:^1}\t{:^28}\t{:^1}\t{:^28}\t{:^1}".format('|', '\033[1;34mScheduler Qapp name\033[0m', '|', '\033[1;34mCreate DTG \033[0m', '|', '\033[1;34mAnalysis DTG Time\033[0m', '|'))
print("|-------------------------------|-----------------------|-----------------------|")

for qapp_name in built_in_qapplist:
    trimed_name = qapp_name.strip()
    sqapp_task = condomain.ScheduleQappTask.find_one({"name": trimed_name})
    sqapp_jobid = sqapp_task.get('setting').get('jobId')
    xftask_createitem = conflowengine.XFTask.find({'jobId': sqapp_jobid, 'taskType': 'ScheduleCreateDTGTask'}).sort([('submitTime',-1)]).skip(0).limit(1)
    xftask_analysisitem = conflowengine.XFTask.find({'jobId': sqapp_jobid,
                                                         'taskType': {'$regex': 'ScheduleAnalysisDataTask'}}).sort([('submitTime',-1)]).skip(0).limit(1)
    for anatk in xftask_createitem:
        analisys_task_type = xftask_analysisitem.get('taskType')
    # create_start_time = xftask_createitem.get('startTime')
    # create_dispatch_time = xftask_createitem.get('dispatchTime')
    create_end_exist = xftask_createitem.get('endTime')
    if create_end_exist:
        create_dtg_time = xftask_createitem.get('endTime') - xftask_createitem.get('startTime')
        # create_end_time = xftask_createitem.get('endTime')
    # analysis_start_time = xftask_analysisitem.get('startTime')
    # analysis_dispatch_time = xftask_analysisitem.get('dispatchTime')
    analysis_end_exist = xftask_analysisitem.get('endTime')
    if analysis_end_exist:
        ayalysis_dtg_time = xftask_analysisitem.get('endTime') - xftask_analysisitem.get('startTime')
        # analysis_end_time = xftask_analysisitem.get('endTime')
    if create_end_exist and analysis_end_exist:
        result_list.append([qapp_name, create_dtg_time, ayalysis_dtg_time, analisys_task_type])
        # print('| ' + qapp_name + '   |   ' + str(create_dtg_time) + '   |   ' + str(ayalysis_dtg_time) + '   |')
        print("{:^1}\t{:^24}\t{:^1}\t{:^16}\t{:^1}\t{:^16}\t{:^1}".format('|', qapp_name, '|', str(create_dtg_time), '|', str(ayalysis_dtg_time), '|'))
    elif create_end_exist and not analysis_end_exist:
        result_list.append([qapp_name, create_dtg_time, 'Not Finished', analisys_task_type])
        # print('| ' + qapp_name + '   |   ' + str(create_dtg_time) + '   |   ' + 'Not Finished     |')
        print("{:^1}\t{:^24}\t{:^1}\t{:^16}\t{:^1}\t{:^16}\t{:^1}".format('|', qapp_name, '|', str(create_dtg_time), '|', 'Not Finished', '|'))
print("---------------------------------------------------------------------------------")

if generate_csv:
    with open("QappDTGTime.csv", 'a', newline='') as data:
        live_file = csv.writer(data)
        live_file.writerow(['Scheduler Qapp name', 'Create DTG Time', 'Analysis DTG Time'])
        for list_item in result_list:
            live_file.writerow(list_item)




