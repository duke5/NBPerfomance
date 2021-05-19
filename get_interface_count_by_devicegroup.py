from pymongo import MongoClient

generate_csv = True    #开启后在当前文件夹生成csv文件
domain_name = "1W_dm"   #domain名称
db_user = "mongodb"     #mongodb用户名
db_password = "mongodb"     #mongodb密码
db_host = "10.10.7.151"     #mongodb IP
db_port = "27019"       #mongodb端口
is_ssl = False      #是否配置SSL，默认false
dvgname = 'test50'

connection = MongoClient("mongodb://" + db_user + ":" + db_password + "@" + db_host + ":" + db_port +
                             "/admin?authMechanism=SCRAM-SHA-256")
condomain = connection.get_database(domain_name)

dvgitem = condomain.DeviceGroup.find_one({'Name': dvgname})
dvg_devices = dvgitem.get('StaticDevices')
# print(dvg_devices)
result_list = []
all_intf_count = 0

for device_id in dvg_devices:
    device_item = condomain.Device.find_one({'_id': device_id})
    device_name = device_item.get('name')
    interface_count = condomain.Interface.find({'devId': device_id}).count()
    result_list.append([device_id, device_name, interface_count])
    all_intf_count += interface_count

print('Device group ' + dvgname + ' include ' + str(all_intf_count) + ' interfaces.')
print('----------------------------------------------------')
for aa in result_list:
    print(aa)