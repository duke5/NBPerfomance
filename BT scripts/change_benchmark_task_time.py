from pymongo import MongoClient


def schedule_add_day(day):
    lst = day.split('-')
    lst[-1] = str(int(lst[-1]) + 1)
    new_day = '-'.join(lst)
    return new_day


def trans_time(c_time):
    tlst = c_time.split(':')
    tm_count = int(tlst[0]) * 3600 + int(tlst[1]) * 60
    return tm_count


def trans_sec(c_sec):
    c_hour, c_tm_sec = divmod(c_sec, 3600)
    c_min, c_sec = divmod(c_tm_sec, 60)
    return str(c_hour) + ':' + str(c_min)


tenant_name = "BT_Tenant6"
db_user = "admin"  # mongodb用户名
db_password = "admin"  # mongodb密码
db_host = "10.10.7.220"  # mongodb IP
db_port = "27017"  # mongodb端口'
connection = MongoClient("mongodb://" + db_user + ":" + db_password + "@" + db_host + ":" + db_port +
                         "/admin?authMechanism=SCRAM-SHA-256")

start_time = '11:25'
start_sec = trans_time(start_time)

ng_sys = connection.get_database('NGSystem')
# tenants = ng_sys.Tenant.find_one({'name': tenant_name})
# domain_lst = tenants.get('domains')
#
# for domain in domain_lst:
#     domain_name = domain.get('name')
#     # print(domain_name)
#     if domain_name:
#         domain_sys = connection.get_database(domain_name)
#         domain_sys.BenchmarkDefinition.update_one({'name': 'auto_dis'},
#                                                   {'$set': {"schedule.frequency.runOnce.startTime": start_sec}})
#         dis_job = domain_sys.BenchmarkDefinition.find_one({'name': 'auto_dis'})
#         dis_job_id = dis_job.get('jobId')
#         ng_sys.JobDef.update_one({'job.domainDbName': domain_name, 'job.jobId': dis_job_id},
#                                  {'$set': {"job.scheduleTime.frequency.runOnce.startTime": start_sec}})
#         if start_sec >= 86400:
#             start_sec -= 86400
#             ben_def_start_day = dis_job.get("schedule").get('startDate')
#             task_start_day = schedule_add_day(ben_def_start_day)
#             domain_sys.BenchmarkDefinition.update_one({'name': 'auto_dis'},
#                                                       {'$set': {"schedule.startDate": task_start_day}})
#             ng_sys.JobDef.update_one({'job.domainDbName': domain_name, 'job.jobId': dis_job_id},
#                                      {'$set': {"schedule.startDate": task_start_day}})
#         else:
#             task_start_day = dis_job.get("schedule").get('startDate')
#         print('set ' + domain_name + ' discover task start-time: ' + str(task_start_day) + ' ' + str(start_sec))
#         start_sec += 60


for i in range(139, 161):
    domain_name = 'Bdm5_' + str(i)
    domain_sys = connection.get_database(domain_name)
    domain_sys.BenchmarkDefinition.update_one({'name': 'auto_dis'},
                                              {'$set': {"schedule.frequency.runOnce.startTime": start_sec}})
    dis_job = domain_sys.BenchmarkDefinition.find_one({'name': 'auto_dis'})
    dis_job_id = dis_job.get('jobId')
    ng_sys.JobDef.update_one({'job.domainDbName': domain_name, 'job.jobId': dis_job_id},
                             {'$set': {"job.scheduleTime.frequency.runOnce.startTime": start_sec}})

    ben_def_start_day = dis_job.get("schedule").get('startDate')
    task_start_day = '2020-10-27'
    domain_sys.BenchmarkDefinition.update_one({'name': 'auto_dis'},
                                              {'$set': {"schedule.startDate": task_start_day}})
    ng_sys.JobDef.update_one({'job.domainDbName': domain_name, 'job.jobId': dis_job_id},
                             {'$set': {"job.scheduleTime.startDate": task_start_day}})
    print('set ' + domain_name + ' discover task start-time: ' + str(task_start_day) + ' ' + trans_sec(start_sec))
    start_sec += 60
