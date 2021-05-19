from pymongo import MongoClient
import datetime

dbusername = 'admin'
dbpassword = 'admin'
dbhost = '10.10.7.226'
dbport = 27017
domainname = '10k_new'
issl = False

bg_time = datetime.datetime(2020, 2, 21, 8, 20, 1)

sdvt_task_name = 'all_parsers'
dtg_list = []

if issl:
    connection = MongoClient("mongodb://" + str(dbusername) + ":" + str(dbpassword) + "@" + str(dbhost) + ":" + str(
        dbport) + "/admin?authMechanism=SCRAM-SHA-256&ssl=true&ssl_cert_reqs=CERT_NONE")
else:
    connection = MongoClient("mongodb://" + str(dbusername) + ":" + str(dbpassword) + "@" + str(dbhost) + ":" + str(
        dbport) + "/admin?authMechanism=SCRAM-SHA-256")

nbdomain = connection.get_database(domainname)
nbxf = connection.get_database('flowengine')

sdvt_task = nbdomain.ScheduleTask.find_one({'name': sdvt_task_name})
if sdvt_task:
    sdvt_task_status = sdvt_task.get('runStatus')
    if sdvt_task_status == 0:
        sdvt_task_jobid = sdvt_task.get('setting').get('jobId')
        print('job id is: ' + sdvt_task_jobid)
        sdvtxf_tasks = nbxf.XFTask.find(
            {'jobId': sdvt_task_jobid, 'taskType': 'ScheduleDVTAnalysisTask', 'startTime': {'$gte': bg_time}})
        for dvtana_xftask in sdvtxf_tasks:
            dtg_id = dvtana_xftask.get('dtgId')
            dtg_list.append(dtg_id)
        if dtg_list:
            print(str(dtg_list))
            print('dtg list lengh is: ' + str(len(dtg_list)))
            sdvt_task_sum = nbdomain.DEMetaData_2020_2.aggregate([{'$unwind': '$dataList'},
                                                                  {'$match': {'dataList.taskId': {'$in': dtg_list}}},
                                                                  {'$group': {'_id': 'null',
                                                                              'total': {'$sum': '$dataList.len'}}}])
            for doc in sdvt_task_sum:
                sdvt_tasksize = round((doc['total'] / 1048576), 3)
            print('SDVT task ' + sdvt_task_name + ' generate data size: ' + str(sdvt_tasksize) + 'MB')
        else:
            print('SDVT task ' + sdvt_task_name + ' generate data size: 0 MB')
    else:
        print("SDVT task " + sdvt_task_name + " is still running")
else:
    print("There's no task named " + sdvt_task_name + " !")
