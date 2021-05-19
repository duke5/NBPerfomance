# -*- coding=utf-8 -*-
from pymongo import MongoClient
import csv


generate_csv = True    #开启后在当前文件夹生成csv文件
domain_name = "4W_mic"   #domain名称
db_user = "mongodb"     #mongodb用户名
db_password = "mongodb"     #mongodb密码
db_host = "10.10.7.220"     #mongodb IP
db_port = "27019"       #mongodb端口
is_ssl = False      #是否配置SSL，默认false
devlist = ["174.38.194.132", "11.63.41.195", "11.115.21.64", "11.115.4.70", "11.112.2.104", "11.115.25.105", "11.126.142.81", "11.88.120.154", "174.38.236.49", "11.115.4.13", "11.63.127.154", "174.38.236.55", "145.254.220.190", "174.38.209.217", "174.38.236.52", "11.63.41.132", "11.65.199.34", "11.88.120.141", "174.38.236.50", "174.38.200.240", "11.63.127.193", "11.126.142.20", "11.115.2.9", "11.115.2.4", "11.76.162.232", "11.115.4.78", "11.115.8.133", "11.126.142.21", "11.152.152.89", "11.65.165.132", "11.115.4.73", "11.115.2.175", "11.76.162.234", "11.63.127.194", "11.63.127.140", "174.38.208.105", "11.115.4.74", "11.115.2.142", "11.112.4.23", "174.38.236.51", "145.254.79.2", "11.115.2.10", "11.115.40.1", "11.76.162.231", "11.115.4.79", "174.38.200.231", "11.66.216.102", "11.115.4.72", "174.38.194.135", "174.38.236.18", "11.115.18.18", "11.137.12.5", "174.38.236.21", "11.126.142.89", "11.63.127.210", "11.115.4.71", "174.38.236.54", "174.38.209.194", "11.115.4.75", "11.76.162.230", "11.65.165.133", "11.103.26.4", "11.115.2.8", "11.65.165.135", "11.137.15.163", "11.65.199.30", "11.115.8.65", "11.65.165.131", "11.115.2.6", "11.88.120.134", "11.66.216.242", "11.115.4.76", "174.38.192.46", "11.65.129.132", "11.65.165.136", "145.254.146.51", "11.63.41.133", "174.38.209.186", "11.115.21.65", "11.115.2.109", "11.115.4.68", "174.38.236.110", "174.38.236.114", "11.76.175.130", "11.115.2.76", "11.63.41.193", "11.65.129.133", "11.115.4.69", "11.137.15.145", "174.38.209.110", "11.115.25.104", "174.38.209.109", "174.38.208.210", "11.76.175.46", "174.38.236.53", "174.38.200.230", "11.115.2.43", "11.152.152.4", "11.115.2.5", "11.115.2.7"]
count_list = []

if is_ssl:
    connection = MongoClient("mongodb://" + db_user + ":" + db_password + "@" + db_host + ":" + db_port +
                             "/admin?authMechanism=SCRAM-SHA-1&ssl=true&ssl_cert_reqs=CERT_NONE")
else:
    connection = MongoClient("mongodb://" + db_user + ":" + db_password + "@" + db_host + ":" + db_port +
                             "/admin?authMechanism=SCRAM-SHA-1")
condomain = connection.get_database(domain_name)


for device_ip in devlist:
    devitem = condomain.Device.find_one({'mgmtIP': device_ip})
    if devitem:
        devid = devitem.get('_id')
        devname = devitem.get('name')
        interface_count = condomain.Interface.count({'devId': devid})
    count_list.append([device_ip, devname, interface_count])
    print(device_ip, devname, interface_count)

if generate_csv:
    with open("GDRInterfaceCount220.csv", 'a', newline='') as data:
        live_file = csv.writer(data)
        live_file.writerow(['Device IP', 'Device Name', 'Device Interface Count'])
        for list_item in count_list:
            live_file.writerow(list_item)

