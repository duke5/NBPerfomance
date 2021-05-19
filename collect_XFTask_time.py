from pymongo import MongoClient
import time
import csv
t1 = time.strftime("%m%d-%H%M%S", time.localtime(time.time()))
xftime_csv = 'D:\\tmp\\dtgtime\\Schedule_APIQapp_' + t1 + '.csv'
domainname = 'Domain001'
uri = "mongodb://mongodb:mongodb@10.10.4.231:27027/admin?authMechanism=SCRAM-SHA-1"
connetion = MongoClient(uri)
db = connetion.get_database(domainname)
dbxftask = connetion.get_database('flowengine')


qapplist = db.ScheduleQappTask.find({'name': {'$regex': 'DKauto[3,4]'}})

testlist = []
for qappjobs in qapplist:
    taskname = qappjobs.get('name')
    qappjobid = qappjobs.get('setting').get('jobId')
    createtimecost = dbxftask.XFTask.aggregate([{'$match': {'jobId': qappjobid, 'taskType': "ScheduleCreateDTGTask"}},
                                              {'$project': {'jobId': 1,
                                                            'timecost': {'$subtract': ['$endTime', '$dispatchTime']}}},
                                                {'$group': {'_id': '$jobId', 'sumtime': {'$sum': '$timecost'},
                                                            'avgtime': {'$avg': '$timecost'}}}])
    anatimecost = dbxftask.XFTask.aggregate([{'$match': {'jobId': qappjobid, 'taskType': "ScheduleAnalysisDataTask"}},
                                             {'$project': {'jobId': 1,
                                                           'timecost': {'$subtract': ['$endTime', '$dispatchTime']}}},
                                             {'$group': {'_id': '$jobId', 'sumtime': {'$sum': '$timecost'},
                                                         'avgtime': {'$avg': '$timecost'}}}
                                             ])
    for doc in createtimecost:
        createavgtimesp = round(doc['avgtime']/1000, 3)

    for doc in anatimecost:
        analyavgtimesp = round(doc['avgtime']/1000, 3)
    print('qappname: ' + taskname + ', jobid: ' + qappjobid + ', createdtgavgtime: ' + str(createavgtimesp) +
          ' analysisdtgavgtime: ' + str(analyavgtimesp))
    testlist.append([taskname, qappjobid, createavgtimesp, analyavgtimesp])

with open(xftime_csv, 'w', newline='') as data:
    xftime_csv = csv.writer(data)
    xftime_csv.writerow(['qappname', 'jobid', 'createdtgavgtime', 'analysisdtgavgtime'])
    for task_line in testlist:
        xftime_csv.writerow(task_line)


