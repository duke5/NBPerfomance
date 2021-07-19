# -*- coding=utf-8 -*-
from pymongo import MongoClient
import csv
import datetime
import os
import re


def dis_devices(act_id):  # 统计当前Discovery device数
    dis_msg = db.BenchmarkSummaryLog.find_one({'dataSourceId': act_id, "msg": {"$regex": "^Discovered"}})
    msg_detail = dis_msg.get('msg')
    dis_msg_parten = "Discovered (\d+) IP address\(es\), found (\d+) device"
    dis_msg_parser = re.findall(dis_msg_parten, msg_detail)
    if dis_msg_parser:
        return str(dis_msg_parser[0][0]), str(dis_msg_parser[0][1])


def topolink_log_count(act_id, topo_type):
    top_msg = db.BenchmarkSummaryLog.find_one({'dataSourceId': act_id, "msg": {"$regex": "End: build " + topo_type}})
    msg_detail = top_msg.get('msg')
    topo_msg_parten = "End: build " + topo_type + " with (\d+) links"
    topo_msg_parser = re.findall(topo_msg_parten, msg_detail)
    if topo_msg_parser:
        return str(topo_msg_parser[0])


def time_cost(act_id, start_msg, end_msg):  # 统计任务时长，从log获取
    task_start = db.BenchmarkSummaryLog.find_one({'dataSourceId': act_id, 'msg': start_msg})
    task_end = db.BenchmarkSummaryLog.find_one({'dataSourceId': act_id, 'msg': end_msg})
    if task_start and task_end:
        cost_time = task_end.get('time') - task_start.get('time')
        #   return str(cost_time).split('.')[0]
        return str(cost_time)[0: -7]
    else:
        return 'Not Found'


def full_time(act_id):  # 获取task执行时间
    dis_full = db.DeviceDataSource.find_one({'_id': act_id})
    if dis_full.get('startTime') and dis_full.get('endTime'):
        dis_full_time = dis_full.get('endTime') - dis_full.get('startTime')
        return str(dis_full_time)
    else:
        return "Not Found"


def data_size_count(act_id):  # 统计datafolder大小
    act_item = db.DeviceDataSource.find_one({'_id': act_id})
    entries_count = act_item.get('dataEntries')
    data_size_sour = act_item.get('dataSize')
    if data_size_sour / 1073741824 < 1:
        return str(round(data_size_sour / 1048576, 3)) + 'M', str(entries_count)
    else:
        return str(round(data_size_sour / 1073741824, 3)) + 'G', str(entries_count)


def demonth(a_id):
    dem = db.DeviceDataSource.find_one({'_id': a_id})
    st = dem.get('startTime')
    detm = str(st).split(' ')[0]
    deyear = detm.split('-')[0]
    demonthsour = detm.split('-')[1]
    if int(demonthsour) < 10:
        dmonth = demonthsour[-1]
    else:
        dmonth = demonthsour
    collname = 'DEMetaData_' + deyear + '_' + dmonth
    return collname


def config_coll(act_id, sep_flag):
    size = 0
    coll = db[demonth(act_id)]
    if sep_flag:
        coll_sep = sep_db[demonth(act_id)]
        config_count = coll_sep.count_documents({'dataList.taskId': act_id, 'type': 'config'})
        config_sum = coll_sep.aggregate([{'$unwind': "$dataList"}, {'$match':
                                                                        {"dataList.taskId": act_id, "type": "config"}},
                                         {'$group': {'_id': 'null', 'total': {'$sum': '$dataList.len'}}}])
    else:
        config_count = coll.count_documents({'dataList.taskId': act_id, 'type': 'config'})
        config_sum = coll.aggregate([{'$unwind': "$dataList"}, {'$match':
                                                                    {"dataList.taskId": act_id, "type": "config"}},
                                     {'$group': {'_id': 'null', 'total': {'$sum': '$dataList.len'}}}])

    for doc in config_sum:
        size = round((doc['total'] / 1048576), 3)
    return str(config_count), str(size) + 'M'


def item_count(act_id, item_name, sep_flag):  # 统计不同类型表的count，size
    size = 0
    coll = db[demonth(act_id)]
    if sep_flag:
        coll_sep = sep_db[demonth(act_id)]
        table_count = coll_sep.count_documents({'dataList.taskId': act_id, 'name': item_name})
        size_sum = coll_sep.aggregate([{'$unwind': '$dataList'}, {'$match':
                                                                      {'dataList.taskId': act_id, 'name': item_name}},
                                       {'$group': {'_id': 'null', 'total': {'$sum': '$dataList.len'}}}])
    else:
        table_count = coll.count_documents({'dataList.taskId': act_id, 'name': item_name})
        size_sum = coll.aggregate([{'$unwind': '$dataList'}, {'$match':
                                                                  {'dataList.taskId': act_id, 'name': item_name}},
                                   {'$group': {'_id': 'null', 'total': {'$sum': '$dataList.len'}}}])
    for doc in size_sum:
        size = round((doc['total'] / 1048576), 3)
    return str(table_count), str(size) + 'M'


def time_to_str(timelocal):  # Topo Table name时间处理
    liscst = str(timelocal).split(' ')
    l1 = liscst[0].split('-')
    l1.append('_')
    l2 = liscst[1].split('.')[0].split(':')
    l1.extend(l2)
    l3 = l1[:-1]
    time_trans = ''.join(l3)
    return time_trans


def topotablename_aim(tptype, tt_source):  # Topo Table name时间范围处理
    tutc = tt_source.get('time')
    th = datetime.timedelta(hours=-4)
    table_time = time_to_str(tutc + th)[:-1]
    topo_table_reg = tptype + '_' + table_time
    # topo_table_doc = db.TopologyTableManageTable.find_one({'name': {'$regex': topo_table_reg}})
    # topo_table_name = topo_table_doc.get('name')
    # print('>>>TopoTable reg is: ' + str(topo_table_reg))
    return topo_table_reg


def topo_name_specify(act_id, topo_type):  # 拼接可能的topo table name
    if topo_type == "L3_Topo_Type":
        topo_table_source1 = db.BenchmarkSummaryLog.find_one(
            {'dataSourceId': act_id, 'msg': {'$regex': 'Begin: build IPv4 L3 topology'}})
        topo_table_source2 = db.BenchmarkSummaryLog.find_one(
            {'dataSourceId': act_id, 'msg': 'Try to build topology IPv4 L3 Topology'})
        if topo_table_source1:
            topo_table = topotablename_aim(topo_type, topo_table_source1)
            return topo_table
        elif topo_table_source2:
            topo_table = topotablename_aim(topo_type, topo_table_source2)
            return topo_table
        else:
            return None
    elif topo_type == "L2_Topo_Type":
        topo_table_source = db.BenchmarkSummaryLog.find_one(
            {'dataSourceId': act_id, 'msg': 'Try to build topology L2 Topology'})
        if topo_table_source:
            topo_table = topotablename_aim(topo_type, topo_table_source)
            return topo_table
        else:
            return []
    elif topo_type == "Ipv6_L3_Topo_Type":
        topo_table_source = db.BenchmarkSummaryLog.find_one(
            {'dataSourceId': act_id, 'msg': 'Try to build topology IPv6 L3 Topology'})
        if topo_table_source:
            topo_table = topotablename_aim(topo_type, topo_table_source)
            return topo_table
        else:
            return None
    elif topo_type == "VPN_Topo_Type":
        topo_table_source = db.BenchmarkSummaryLog.find_one(
            {'dataSourceId': act_id, 'msg': 'Try to build topology IPsec VPN Topology'})
        if topo_table_source:
            topo_table = topotablename_aim(topo_type, topo_table_source)
            return topo_table
        else:
            return None
    elif topo_type == "Logical_Topo_Type":
        topo_table_source = db.BenchmarkSummaryLog.find_one(
            {'dataSourceId': act_id, 'msg': 'Try to build topology Logical Topology'})
        if topo_table_source:
            topo_table = topotablename_aim(topo_type, topo_table_source)
            return topo_table
        else:
            return None
    else:
        return None


def get_log_info(msg, log_index):
    log_split = msg.split(' ')
    return log_split[log_index]


def topo_log_count(act_id, topo_type):
    if topo_type == "L3_Topo_Type":
        topo_end_msg = db.BenchmarkSummaryLog.find_one(
            {'dataSourceId': act_id, 'msg': {'$regex': 'End: build IPv4 L3 Topology'}})
        if topo_end_msg:
            topo_end_log = topo_end_msg.get('msg')
            topo_count = get_log_info(topo_end_log, 6)
            return topo_count
        else:
            return 'Not Ended'
    elif topo_type == "L2_Topo_Type":
        topo_end_msg = db.BenchmarkSummaryLog.find_one(
            {'dataSourceId': act_id, 'msg': {'$regex': 'End: build L2 Topology'}})
        if topo_end_msg:
            topo_end_log = topo_end_msg.get('msg')
            topo_count = get_log_info(topo_end_log, 5)
            return topo_count
        else:
            return 'Not Ended'
    elif topo_type == "Ipv6_L3_Topo_Type":
        topo_end_msg = db.BenchmarkSummaryLog.find_one(
            {'dataSourceId': act_id, 'msg': {'$regex': 'End: build IPv6 L3 Topology'}})
        if topo_end_msg:
            topo_end_log = topo_end_msg.get('msg')
            topo_count = get_log_info(topo_end_log, 6)
            return topo_count
        else:
            return 'Not Ended'
    elif topo_type == "VPN_Topo_Type":
        topo_end_msg = db.BenchmarkSummaryLog.find_one(
            {'dataSourceId': act_id, 'msg': {'$regex': 'End: build L3 VPN Tunnel'}})
        if topo_end_msg:
            topo_end_log = topo_end_msg.get('msg')
            topo_count = get_log_info(topo_end_log, 7)
            return topo_count
        else:
            return 'Not Ended'
    elif topo_type == "Logical_Topo_Type":
        topo_end_msg = db.BenchmarkSummaryLog.find_one(
            {'dataSourceId': act_id, 'msg': {'$regex': 'End: build Logical Topology'}})
        if topo_end_msg:
            topo_end_log = topo_end_msg.get('msg')
            topo_count = get_log_info(topo_end_log, 5)
            return topo_count
        else:
            return 'Not Ended'
    else:
        return 'Wrong Type'


def dis_topo_link_count(act_id, topo_type):  # 统计不同类型topo link count，size
    ttp = topo_name_specify(act_id, topo_type)
    if ttp:
        # for topo_filter_num in range(tp_min):
        topo_filter = db.TopologyTableManageTable.find_one({"name": {"$regex": ttp}})
        if topo_filter:
            topo_table_name = topo_filter.get('name')
            table_status = db.command("collstats", topo_table_name)
            # print(topo_table_name)
            topo_count = table_status.get('count')
            # topo_count = topo_log_count(act_id, topo_type)
            topo_size = round((table_status.get('size') / 1048576), 3)
            return str(topo_count), str(topo_size) + 'M'
        else:
            return "Not Found", "Not Found"
    else:
        return "No Topo", "No Topo"


def topo_link_count(act_id, topo_type):  # 统计不同类型topo link count，size
    ttp = topo_name_specify(act_id, topo_type)
    if ttp:
        # for topo_filter_num in range(tp_min):
        topo_filter = db.TopologyTableManageTable.find_one({"name": {"$regex": ttp}})
        if topo_filter:
            topo_table_name = topo_filter.get('name')
            print(topo_type + ' Name is: ' + topo_table_name)
            table_status = db.command("collstats", topo_table_name)
            # print(topo_table_name)
            # topo_count = table_status.get('count')
            topo_count = topo_log_count(act_id, topo_type)
            topo_size = round((table_status.get('size') / 1048576), 3)
            return str(topo_count), str(topo_size) + 'M'
        else:
            if topo_type == 'L3_Topo_Type':
                topo_log_type = 'IPv4 L3 Topology'
            if topo_type == 'L2_Topo_Type':
                topo_log_type = 'L2 Topology'
            if topo_type == 'Ipv6_L3_Topo_Type':
                topo_log_type = 'IPv6 L3 Topology'
            if topo_type == 'VPN_Topo_Type':
                topo_log_type = 'L2 Overlay Topology'
            if topo_type == 'Logical_Topo_Type':
                topo_log_type = 'Logical Topology'
            if topo_type == 'L3 VPN Tunnel':
                topo_log_type = 'L3 VPN Tunnel'
            # print(topo_log_type)
            topo_count = topolink_log_count(act_id, topo_log_type)
            return topo_count, "Not Found"
    else:
        return "No Topo", "No Topo"


def mpls_cloud_time(act_id):  # 根据Benchmark name遍历所有
    mpls_flag = db.BenchmarkSummaryLog.find_one(
        {'dataSourceId': act_id, 'msg': {'$regex': 'End: recalculate Mpls Cloud Route Table.'}})
    if mpls_flag:
        return time_cost(act_id, 'Begin: recalculate Mpls Cloud Route Table.',
                         {'$regex': 'End: recalculate Mpls Cloud Route Table.'})
    else:
        return 'Not Found'


def judge_sepdb(sep_domain_name):
    tenant_item = ngsys.Tenant.find_one({'domains.name': sep_domain_name})
    sep_tenant = tenant_item.get('name')
    sep_flag = ngsys.TenantConnection.find_one({'name': sep_tenant})
    live_flag = ngsys.TenantConnection.find_one({'name': sep_tenant, 'liveDataColl': {'$exists': 1}})
    live_item = ngsys.TenantConnection.find_one({'name': sep_tenant, 'liveDataConnSetting': {'$exists': 1}})
    diften_item = ngsys.TenantConnection.find_one({'name': sep_tenant, 'tenantConnSetting': {'$exists': 1}})
    if live_item:
        sep_db_info = live_item.get('liveDataConnSetting').get('servers')[0]
    elif diften_item:
        sep_db_info = diften_item.get('tenantConnSetting').get('servers')[0]
    else:
        sep_db_info = None
    return sep_flag, live_flag, sep_db_info


def discover_data(dis_id, sep_flag):  # Discovery数据统计
    if os.path.exists(os.getcwd() + '\\OutputFiles'):
        dis_csv = os.getcwd() + '\\OutputFiles\\' + domain_name + '_Dis_live_' + dis_id + '.csv'
    else:
        os.makedirs(os.getcwd() + '\\OutputFiles')
        dis_csv = os.getcwd() + '\\OutputFiles\\' + domain_name + '_Dis_live_' + dis_id + '.csv'
    node_count = str(db.Device.count_documents({}))
    device_count = dis_devices(dis_id)
    dis_time = full_time(dis_id)[0: -7]
    dis_live = time_cost(dis_id, {'$regex': 'Begin: discover devices'}, {'$regex': 'End: discover devices'})
    data_size = data_size_count(dis_id)[0]
    entries_ct = data_size_count(dis_id)[1]
    config_count = config_coll(dis_id, sep_flag)
    IPv4L3_time = time_cost(dis_id, {'$regex': 'Begin: build IPv4 L3 topology'},
                            {'$regex': 'End: build IPv4 L3 topology'})
    IPv4L3_topo_info = dis_topo_link_count(dis_id, 'L3_Topo_Type')
    cdp_count = item_count(dis_id, 'cdpTable', sep_flag)
    route_count = item_count(dis_id, 'routeTable', sep_flag)
    # bgp_mpls_time = time_cost(dis_id, 'Begin: update BGP MPLS cloud CE list.', 'End:   update BGP MPLS cloud CE list.')
    sync_site_time = time_cost(dis_id, 'Begin: rebuild all sites.', 'End: rebuild all sites.')
    build_visual_space_logical_time = time_cost(dis_id, 'Begin: build visual space logical nodes.',
                                                'End: build visual space logical nodes.')
    build_network_tree = time_cost(dis_id, 'Begin: build network tree.', 'End: build network tree.')
    print('---Node count: ' + node_count)
    print('---Discover seed IP: ' + device_count[0])
    print('---Discover devices: ' + device_count[1])
    print('---Discover full time: ' + dis_time)
    print('---Discover live time: ' + dis_live)
    print('---Discover dataEntries: ' + entries_ct)
    print('---Full Datafolder size: ' + data_size)
    print('---Config count: ' + config_count[0] + '| Size: ' + config_count[1])
    print('---IPv4 L3 Topo time: ' + IPv4L3_time)
    print('---IPv4 L3 Topo Link count: ' + IPv4L3_topo_info[0] + ' | Size: ' + IPv4L3_topo_info[1])
    print('---CDP Table count: ' + cdp_count[0] + ' | Size: ' + cdp_count[1])
    print('---Routing Table count: ' + route_count[0] + ' | Size: ' + route_count[1])
    # print('---Update BGP MPLS cloud CE list time: ' + bgp_mpls_time)
    print('---Synchronize device to site time: ' + sync_site_time)
    print('---Build visual space logical nodes time: ' + build_visual_space_logical_time)
    print('---Build network tree time: ' + build_network_tree)
    if generate_csv:  # 生成csv
        with open(dis_csv, 'w', newline='') as data:
            live_file = csv.writer(data)
            live_file.writerow(['Task_type', 'Discovery'])
            live_file.writerow(['Discovery_id', dis_id])
            live_file.writerow(['Node Count', 'Discover seed IP', 'Discover devices', 'Discover full time',
                                'Discover live time', 'DataEntries Count', 'Full Datafolder size', 'Config count',
                                'Config size', 'IPv4 L3 Topo time', 'IPv4 L3 Topo Link count', 'IPv4 L3 Topo Link size',
                                'CDP Table count', 'CDP Table size', 'Routing Table count',
                                'Routing Table size',
                                'Synchronize device to site time', 'Build visual space logical nodes time',
                                'Build network tree time'])
            live_file.writerow([node_count, device_count[0], device_count[1], dis_time, dis_live, entries_ct, data_size,
                                config_count[0], config_count[1], IPv4L3_time, IPv4L3_topo_info[0], IPv4L3_topo_info[1],
                                cdp_count[0], cdp_count[1], route_count[0], route_count[1],
                                sync_site_time, build_visual_space_logical_time, build_network_tree])
        print('Generate Discovery CSV File done.')
        print('CSV File path:' + dis_csv)
    else:
        print('Will not Generate CSV file.')


def benchmark_data(ben_id, sep_flag, ben_name):  # Benchmark数据统计
    node_count = str(db.Device.count_documents({}))
    macdevice_count = str(db.MacDevice.count_documents({}))
    intf_count = str(db.Interface.count_documents({}))
    benchmk_time = full_time(ben_id)
    benchmk_live = time_cost(ben_id, 'Begin: retrieve devices data.', {'$regex': 'End: retrieve devices data'})
    data_folder_size = data_size_count(ben_id)[0]
    config_count = config_coll(ben_id, sep_flag)
    IPv4Topo_time = time_cost(ben_id, 'Try to build topology IPv4 L3 Topology',
                              {'$regex': 'End: build IPv4 L3 Topology'})
    IPv4_topo_info = topo_link_count(ben_id, 'L3_Topo_Type')
    L2Topo_time = time_cost(ben_id, 'Try to build topology L2 Topology', {'$regex': 'End: build L2 Topology'})
    L2Topo_info = topo_link_count(ben_id, 'L2_Topo_Type')
    IPv6L3_time = time_cost(ben_id, 'Try to build topology IPv6 L3 Topology', {'$regex': 'End: build IPv6 L3 Topology'})
    IPv6L3_topo_info = topo_link_count(ben_id, 'Ipv6_L3_Topo_Type')
    ipsec_vpn_topo_time = time_cost(ben_id, 'Try to build topology L3 VPN Tunnel',
                                    {'$regex': 'End: build L3 VPN Tunnel'})
    vpn_topo_info = topo_link_count(ben_id, 'VPN_Topo_Type')
    topo_logical_time = time_cost(ben_id, 'Try to build topology Logical Topology',
                                  {'$regex': 'End: build Logical Topology'})
    topo_logical_info = topo_link_count(ben_id, 'Logical_Topo_Type')
    data_view_count = str(db.DefaultDeviceDataView.count_documents({}))
    devgp_count = str(db.DeviceGroup.count_documents({}))
    update_endpoint_time = time_cost(ben_id, 'Begin: update Global Endpoint index.',
                                     {'$regex': 'End: update Global Endpoint index.'})
    # bgp_mpls_time = time_cost(ben_id, 'Begin: update BGP MPLS cloud CE list.',
    #                           {'$regex': 'End: update BGP MPLS cloud CE list.'})
    recal_dyna_devicegp = time_cost(ben_id, 'Begin: recalculate dynamic device group.',
                                    {'$regex': 'End: recalculate dynamic device group.'})
    recal_site_time = time_cost(ben_id, 'Begin: recalculate site.', {'$regex': 'End: recalculate site.'})
    # recal_mpls_cloud = mpls_cloud_time(ben_id)
    default_dataview = time_cost(ben_id, 'Begin: build default device data view.',
                                 {'$regex': 'End: build default device data view.'})
    pre_qualify_dvt_time = time_cost(ben_id,
                                     'Begin: Pre-qualify Automation Assets against all devices and logic nodes.',
                                     'End: Pre-qualify Automation Assets against all devices and logic nodes. ')
    visual_space_time = time_cost(ben_id, 'Begin: build visual space instance.',
                                  {'$regex': 'End: build visual space instance.'})
    network_tree_time = time_cost(ben_id, 'Begin: build network tree.', {'$regex': 'End: build network tree.'})
    vp_logical_time = time_cost(ben_id, 'Begin: build visual space logical nodes.',
                                {'$regex': 'End: build visual space logical nodes.'})
    arp_table_count = item_count(ben_id, 'arpTable', sep_flag)
    cdp_table_count = item_count(ben_id, 'cdpTable', sep_flag)
    route_count = item_count(ben_id, 'routeTable', sep_flag)
    mac_count = item_count(ben_id, 'macTable', sep_flag)
    bgp_nbr_count = item_count(ben_id, 'bgpNbrTable', sep_flag)
    stp_count = item_count(ben_id, 'stpTable', sep_flag)
    vri_server_table_count = item_count(ben_id, 'Virtual Server Table', sep_flag)
    mpls_lfib_count = item_count(ben_id, 'MPLS LFIB', sep_flag)
    mpls_vrf_count = item_count(ben_id, 'MPLS VRF', sep_flag)
    mpls_vpnv4_label = item_count(ben_id, 'MPLS VPNv4 Label', sep_flag)
    nat_table_count = item_count(ben_id, 'NAT Table', sep_flag)
    nat_real_table_count = item_count(ben_id, 'NAT Table[Real-time]', sep_flag)
    ipsec_vpn_table_count = item_count(ben_id, 'IPsec VPN Table', sep_flag)
    ipsec_vpn_real_count = item_count(ben_id, 'IPsec VPN Table[Real-time]', sep_flag)

    print('---Node count: ' + node_count)
    print('---MacDevice count: ' + macdevice_count)
    print('---Interface count: ' + intf_count)
    print('---Benchmark time: ' + benchmk_time)
    print('---Retrieve live time: ' + benchmk_live)
    print('---Full Datafolder size: ' + data_folder_size)
    print('---Config count: ' + config_count[0] + '| Size: ' + config_count[1])
    print('---IPv4 Topo time: ' + IPv4Topo_time)
    print('---IPv4L3 Topo link count: ' + IPv4_topo_info[0] + ' | Size: ' + IPv4_topo_info[1])
    print('---L2 Topo time: ' + L2Topo_time)
    print('---L2 Topo link count: ' + L2Topo_info[0] + ' | Size: ' + L2Topo_info[1])
    print('---IPv6 topo time: ' + IPv6L3_time)
    print('---IPv6L3 topo count: ' + IPv6L3_topo_info[0] + ' | Size: ' + IPv6L3_topo_info[1])
    print('---IPsec VPN Topo time: ' + ipsec_vpn_topo_time)
    print('---IPsec VPN Topo count: ' + vpn_topo_info[0] + ' | Size: ' + vpn_topo_info[1])
    print('---Build topology Logical Topology time: ' + topo_logical_time)
    print('---topology Logical Topology count: ' + topo_logical_info[0] + ' | Size: ' + topo_logical_info[1])
    print('---Device Group count: ' + devgp_count)
    print('---Update Global Endpoint index time: ' + update_endpoint_time)
    # print('---Update BGP MPLS cloud CE list time: ' + bgp_mpls_time)
    print('---Recalculate dynamic device group time: ' + recal_dyna_devicegp)
    print('---Recalculate site time: ' + recal_site_time)
    # print('---Recalculate MPLS Could time: ' + recal_mpls_cloud)
    print('---Build Default Dataview Time: ' + default_dataview + ' | Count: ' + data_view_count)
    print('---Pre qualify DVT time: ' + pre_qualify_dvt_time)
    print('---Build visual space instance time: ' + visual_space_time)
    print('---Build network tree time: ' + network_tree_time)
    print('---Build VP logical nodes time: ' + vp_logical_time)
    print('---Arp Table count: ' + arp_table_count[0] + ' | Size: ' + arp_table_count[1])
    print('---CDP Table count ' + cdp_table_count[0] + ' | Size: ' + cdp_table_count[1])
    print('---Routing Table count: ' + route_count[0] + ' | Size: ' + route_count[1])
    print('---MAC Table count: ' + mac_count[0] + ' | Size: ' + mac_count[1])
    print('---BGP Nbr Table count: ' + bgp_nbr_count[0] + ' | Size: ' + bgp_nbr_count[1])
    print('---STP Table count: ' + stp_count[0] + ' | Size: ' + stp_count[1])
    print('---Virtual Server Table count: ' + vri_server_table_count[0] + ' | Size: ' + vri_server_table_count[1])
    print('---MPLS LFIB count: ' + mpls_lfib_count[0] + ' | Size: ' + mpls_lfib_count[1])
    print('---MPLS VRF count: ' + mpls_vrf_count[0] + ' | Size: ' + mpls_vrf_count[1])
    print('---MPLS VPNv4 Label count: ' + mpls_vpnv4_label[0] + ' | Size: ' + mpls_vpnv4_label[1])
    print('---NAT Table count: ' + nat_table_count[0] + ' | Size: ' + nat_table_count[1])
    print('---NAT Table[Real-time] count: ' + nat_real_table_count[0] + ' | Size: ' + nat_real_table_count[1])
    print('---IPsec VPN Table count: ' + ipsec_vpn_table_count[0] + ' | Size: ' + ipsec_vpn_table_count[1])
    print('---IPsec VPN Table[Real-time] count: ' + ipsec_vpn_real_count[0] + ' | Size: ' + ipsec_vpn_real_count[1])

    if ben_name:
        if os.path.exists(os.getcwd() + '\\OutputFiles'):
            ben_csv = os.getcwd() + '\\OutputFiles\\' + domain_name + '_Iterate_' + ben_name + '.csv'
        else:
            os.makedirs(os.getcwd() + '\\OutputFiles')
            ben_csv = os.getcwd() + '\\OutputFiles\\' + domain_name + '_Iterate_' + ben_name + '.csv'
    else:
        if os.path.exists(os.getcwd() + '\\OutputFiles'):
            ben_csv = os.getcwd() + '\\OutputFiles\\' + domain_name + '_Bench_live_' + ben_id + '.csv'
        else:
            os.makedirs(os.getcwd() + '\\OutputFiles')
            ben_csv = os.getcwd() + '\\OutputFiles\\' + domain_name + '_Bench_live_' + ben_id + '.csv'

    title_list = ['Node count', 'MacDevice count', 'Interface count', 'Benchmark time',
                  'Retrieve live time', 'Full Datafolder size', 'Config count', 'Config size',
                  'IPv4 Topo time', 'IPv4L3 Topo link count', 'IPv4L3 Topo link size', 'L2 Topo time',
                  'L2 Topo link count', 'L2 Topo link size', 'IPv6 topo time', 'IPv6L3 topo count',
                  'IPv6L3 topo size', 'IPsec VPN Topo time', 'IPsec VPN Topo count',
                  'IPsec VPN Topo size', 'topology Logical Topology time',
                  'topology Logical Topology count', 'topology Logical Topology size',
                  'Device Group count', 'Update Global Endpoint time',
                  'Recalculate dynamic device group time', 'Recalculate site time',
                  'Build Default Dataview Time', 'Default Dataview Count',
                  'Pre qualify DVT time', 'Build visual space instance time',
                  'Build network tree time', 'Build VP logical nodes time', 'Arp Table count',
                  'Arp Table size', 'CDP Table count', 'CDP Table size', 'Routing Table count',
                  'Routing Table size', 'MAC Table count', 'MAC Table size', 'BGP Nbr Table count',
                  'BGP Nbr Table size', 'STP Table count', 'STP Table size',
                  'Virtual Server Table count', 'Virtual Server Table size', 'MPLS LFIB count',
                  'MPLS LFIB size', 'MPLS VRF count', 'MPLS VRF size', 'MPLS VPNv4 Label count',
                  'MPLS VPNv4 Label size', 'NAT Table count', 'NAT Table size',
                  'NAT Table[Real-time] count', 'NAT Table[Real-time] size', 'IPsec VPN Table count',
                  'IPsec VPN Table size', 'IPsec VPN Table[Real-time] count',
                  'IPsec VPN Table[Real-time] size']
    if generate_csv:  # 生成csv
        with open(ben_csv, 'a', newline='') as data:
            live_file = csv.writer(data)
            #        live_file.writerow(['Task_type', 'Benchmark'])
            live_file.writerow(['Benchmark_id', ben_id])
            live_file.writerow(title_list)
            live_file.writerow([node_count, macdevice_count, intf_count, benchmk_time, benchmk_live, data_folder_size,
                                config_count[0], config_count[1], IPv4Topo_time, IPv4_topo_info[0], IPv4_topo_info[1],
                                L2Topo_time, L2Topo_info[0], L2Topo_info[1], IPv6L3_time, IPv6L3_topo_info[0],
                                IPv6L3_topo_info[1], ipsec_vpn_topo_time, vpn_topo_info[0], vpn_topo_info[1],
                                topo_logical_time, topo_logical_info[0], topo_logical_info[0], devgp_count,
                                update_endpoint_time, recal_dyna_devicegp, recal_site_time,
                                default_dataview, data_view_count, pre_qualify_dvt_time, visual_space_time,
                                network_tree_time, vp_logical_time, arp_table_count[0], arp_table_count[1],
                                cdp_table_count[0], cdp_table_count[1], route_count[0], route_count[1], mac_count[0],
                                mac_count[1], bgp_nbr_count[0], bgp_nbr_count[1], stp_count[0], stp_count[1],
                                vri_server_table_count[0], vri_server_table_count[1], mpls_lfib_count[0],
                                mpls_lfib_count[1], mpls_vrf_count[0], mpls_vrf_count[1], mpls_vpnv4_label[0],
                                mpls_vpnv4_label[1], nat_table_count[0], nat_table_count[1], nat_real_table_count[0],
                                nat_real_table_count[1], ipsec_vpn_table_count[0], ipsec_vpn_table_count[1],
                                ipsec_vpn_real_count[0], ipsec_vpn_real_count[1]])
        print('Generate Benchmark CSV File done.')
        print('CSV File path:' + ben_csv)
    else:
        print('Will not Generate CSV file.')


def benchmark_data_easy(ben_id, sep_flag, ben_name):  # Benchmark数据统计
    node_count = str(db.Device.count_documents({}))
    macdevice_count = str(db.MacDevice.count_documents({}))
    intf_count = str(db.Interface.count_documents({}))
    benchmk_time = full_time(ben_id)
    benchmk_live = time_cost(ben_id, 'Begin: retrieve devices data.', {'$regex': 'End: retrieve devices data'})
    data_folder_size = data_size_count(ben_id)[0]
    config_count = config_coll(ben_id, sep_flag)
    IPv4Topo_time = time_cost(ben_id, 'Try to build topology IPv4 L3 Topology',
                              {'$regex': 'End: build IPv4 L3 Topology'})
    IPv4_topo_info = topo_link_count(ben_id, 'L3_Topo_Type')
    L2Topo_time = time_cost(ben_id, 'Try to build topology L2 Topology', {'$regex': 'End: build L2 Topology'})
    L2Topo_info = topo_link_count(ben_id, 'L2_Topo_Type')
    IPv6L3_time = time_cost(ben_id, 'Try to build topology IPv6 L3 Topology', {'$regex': 'End: build IPv6 L3 Topology'})
    IPv6L3_topo_info = topo_link_count(ben_id, 'Ipv6_L3_Topo_Type')
    ipsec_vpn_topo_time = time_cost(ben_id, 'Try to build topology L3 VPN Tunnel',
                                    {'$regex': 'End: build L3 VPN Tunnel'})
    vpn_topo_info = topo_link_count(ben_id, 'VPN_Topo_Type')
    topo_logical_time = time_cost(ben_id, 'Try to build topology Logical Topology',
                                  {'$regex': 'End: build Logical Topology'})
    topo_logical_info = topo_link_count(ben_id, 'Logical_Topo_Type')
    data_view_count = str(db.DefaultDeviceDataView.count_documents({}))
    devgp_count = str(db.DeviceGroup.count_documents({}))
    update_endpoint_time = time_cost(ben_id, 'Begin: update Global Endpoint index.',
                                     {'$regex': 'End: update Global Endpoint index.'})
    # bgp_mpls_time = time_cost(ben_id, 'Begin: update BGP MPLS cloud CE list.',
    #                           {'$regex': 'End: update BGP MPLS cloud CE list.'})
    recal_dyna_devicegp = time_cost(ben_id, 'Begin: recalculate dynamic device group.',
                                    {'$regex': 'End: recalculate dynamic device group.'})
    recal_site_time = time_cost(ben_id, 'Begin: recalculate site.', {'$regex': 'End: recalculate site.'})
    # recal_mpls_cloud = mpls_cloud_time(ben_id)
    default_dataview = time_cost(ben_id, 'Begin: build default device data view.',
                                 {'$regex': 'End: build default device data view.'})
    pre_qualify_dvt_time = time_cost(ben_id,
                                     'Begin: Pre-qualify Automation Assets against all devices and logic nodes.',
                                     'End: Pre-qualify Automation Assets against all devices and logic nodes. ')
    visual_space_time = time_cost(ben_id, 'Begin: build visual space instance.',
                                  {'$regex': 'End: build visual space instance.'})
    network_tree_time = time_cost(ben_id, 'Begin: build network tree.', {'$regex': 'End: build network tree.'})
    vp_logical_time = time_cost(ben_id, 'Begin: build visual space logical nodes.',
                                {'$regex': 'End: build visual space logical nodes.'})

    print('---Node count: ' + node_count)
    print('---MacDevice count: ' + macdevice_count)
    print('---Interface count: ' + intf_count)
    print('---Benchmark time: ' + benchmk_time)
    print('---Retrieve live time: ' + benchmk_live)
    print('---Full Datafolder size: ' + data_folder_size)
    print('---Config count: ' + config_count[0] + '| Size: ' + config_count[1])
    print('---IPv4 Topo time: ' + IPv4Topo_time)
    print('---IPv4L3 Topo link count: ' + IPv4_topo_info[0] + ' | Size: ' + IPv4_topo_info[1])
    print('---L2 Topo time: ' + L2Topo_time)
    print('---L2 Topo link count: ' + L2Topo_info[0] + ' | Size: ' + L2Topo_info[1])
    print('---IPv6 topo time: ' + IPv6L3_time)
    print('---IPv6L3 topo count: ' + IPv6L3_topo_info[0] + ' | Size: ' + IPv6L3_topo_info[1])
    print('---IPsec VPN Topo time: ' + ipsec_vpn_topo_time)
    print('---IPsec VPN Topo count: ' + vpn_topo_info[0] + ' | Size: ' + vpn_topo_info[1])
    print('---Build topology Logical Topology time: ' + topo_logical_time)
    print('---topology Logical Topology count: ' + topo_logical_info[0] + ' | Size: ' + topo_logical_info[1])
    print('---Device Group count: ' + devgp_count)
    print('---Update Global Endpoint index time: ' + update_endpoint_time)
    # print('---Update BGP MPLS cloud CE list time: ' + bgp_mpls_time)
    print('---Recalculate dynamic device group time: ' + recal_dyna_devicegp)
    print('---Recalculate site time: ' + recal_site_time)
    # print('---Recalculate MPLS Could time: ' + recal_mpls_cloud)
    print('---Build Default Dataview Time: ' + default_dataview + ' | Count: ' + data_view_count)
    print('---Pre qualify DVT time: ' + pre_qualify_dvt_time)
    print('---Build visual space instance time: ' + visual_space_time)
    print('---Build network tree time: ' + network_tree_time)
    print('---Build VP logical nodes time: ' + vp_logical_time)

    if ben_name:
        if os.path.exists(os.getcwd() + '\\OutputFiles'):
            ben_csv = os.getcwd() + '\\OutputFiles\\' + domain_name + '_Iterate_' + ben_name + '.csv'
        else:
            os.makedirs(os.getcwd() + '\\OutputFiles')
            ben_csv = os.getcwd() + '\\OutputFiles\\' + domain_name + '_Iterate_' + ben_name + '.csv'
    else:
        if os.path.exists(os.getcwd() + '\\OutputFiles'):
            ben_csv = os.getcwd() + '\\OutputFiles\\' + domain_name + '_Bench_live_' + ben_id + '.csv'
        else:
            os.makedirs(os.getcwd() + '\\OutputFiles')
            ben_csv = os.getcwd() + '\\OutputFiles\\' + domain_name + '_Bench_live_' + ben_id + '.csv'

    title_list = ['Node count', 'MacDevice count', 'Interface count', 'Benchmark time',
                  'Retrieve live time', 'Full Datafolder size', 'Config count', 'Config size',
                  'IPv4 Topo time', 'IPv4L3 Topo link count', 'IPv4L3 Topo link size', 'L2 Topo time',
                  'L2 Topo link count', 'L2 Topo link size', 'IPv6 topo time', 'IPv6L3 topo count',
                  'IPv6L3 topo size', 'IPsec VPN Topo time', 'IPsec VPN Topo count',
                  'IPsec VPN Topo size', 'topology Logical Topology time',
                  'topology Logical Topology count', 'topology Logical Topology size',
                  'Device Group count', 'Update Global Endpoint time',
                  'Recalculate dynamic device group time', 'Recalculate site time',
                  'Build Default Dataview Time', 'Default Dataview Count',
                  'Pre qualify DVT time', 'Build visual space instance time',
                  'Build network tree time', 'Build VP logical nodes time']
    if generate_csv:  # 生成csv
        with open(ben_csv, 'a', newline='') as data:
            live_file = csv.writer(data)
            #        live_file.writerow(['Task_type', 'Benchmark'])
            live_file.writerow(['Benchmark_id', ben_id])
            live_file.writerow(title_list)
            live_file.writerow([node_count, macdevice_count, intf_count, benchmk_time, benchmk_live, data_folder_size,
                                config_count[0], config_count[1], IPv4Topo_time, IPv4_topo_info[0], IPv4_topo_info[1],
                                L2Topo_time, L2Topo_info[0], L2Topo_info[1], IPv6L3_time, IPv6L3_topo_info[0],
                                IPv6L3_topo_info[1], ipsec_vpn_topo_time, vpn_topo_info[0], vpn_topo_info[1],
                                topo_logical_time, topo_logical_info[0], topo_logical_info[0], devgp_count,
                                update_endpoint_time, recal_dyna_devicegp, recal_site_time,
                                default_dataview, data_view_count, pre_qualify_dvt_time, visual_space_time,
                                network_tree_time, vp_logical_time])
        print('Generate Benchmark CSV File done.')
        print('CSV File path:' + ben_csv)
    else:
        print('Will not Generate CSV file.')


def itera_benchmark(benchmk_name, sep_flag, bt_flag):
    benchmk_list = db.DeviceDataSource.find({"srcType": "benchmark task", "name": benchmk_name})
    for benchmk_id in benchmk_list:
        benid = benchmk_id.get('_id')
        print("Benchmark id is: " + benid)
        if bt_flag:
            benchmark_data(benid, sep_flag, benchmark_name)
        else:
            benchmark_data_easy(benid, sep_flag, benchmark_name)


if __name__ == '__main__':
    generate_csv = False  # 开启后在当前文件夹生成csv文件
    need_table_data = False   #是否需要统计ARP, CDP等Table数据
    domain_name = "NA45k_dm"  # domain名称
    benchmark_name = ""  # 如果配置Benchmark name将直接根据name遍历所有该name的Benchmark，task id配置将无效
    task_id = "4f7b5400-79e0-420d-88cb-be5673245b89"  # task id 自动识别类型
    db_user = "admin"  # mongodb用户名
    db_password = "netbrain"  # mongodb密码
    db_host = "10.10.5.248"  # mongodb IP
    db_port = "27017"  # mongodb端口
    is_ssl = False  # 是否配置SSL，默认false
    topo_min = 4  # 定义topo start time - topo table name的时间范围
    #   ==========Live separate db Options=====================================
    sep_db_user = "admin"  # 分库db user
    sep_db_password = "admin"  # 分库db password
    sep_ssl = False  # 分库是否配置ssl

    if is_ssl:
        connection = MongoClient("mongodb://" + db_user + ":" + db_password + "@" + db_host + ":" + db_port +
                                 "/admin?authMechanism=SCRAM-SHA-256&ssl=true&ssl_cert_reqs=CERT_NONE")
    else:
        connection = MongoClient("mongodb://" + db_user + ":" + db_password + "@" + db_host + ":" + db_port +
                                 "/admin?authMechanism=SCRAM-SHA-256")
    ngsys = connection.get_database('NGSystem')

    is_sep = judge_sepdb(domain_name)

    if is_sep[0]:
        if sep_ssl:
            sep_connection = MongoClient("mongodb://" + sep_db_user + ":" + sep_db_password + "@" + is_sep[-1]
                                         + "/admin?authMechanism=SCRAM-SHA-1&ssl=true&ssl_cert_reqs=CERT_NONE")
        else:
            sep_connection = MongoClient("mongodb://" + sep_db_user + ":" + sep_db_password + "@" + is_sep[-1]
                                         + "/admin?authMechanism=SCRAM-SHA-1")
        sep_db = sep_connection.get_database(domain_name)
        if is_sep[1]:
            db = connection.get_database(domain_name)
        else:
            db = sep_connection.get_database(domain_name)
    else:
        db = connection.get_database(domain_name)

    if benchmark_name:
        benchmk_est = db.DeviceDataSource.find_one({"srcType": "benchmark task", "name": benchmark_name})
        if benchmk_est:
            print('==>> Will retrieve all benchmark live data iterate by benchmark name <<==')
            itera_benchmark(benchmark_name, is_sep[0], need_table_data)
        else:
            print("There's no benchmark named: " + benchmark_name + '!!')
    else:
        judge_type = db.DeviceDataSource.find_one({'_id': task_id})
        if judge_type:
            sts = judge_type.get('status')
            if 'Succeeded' in sts:
                if judge_type.get('srcType') == "ondemand discover task" or judge_type.get('srcType') == \
                        "schedule discover task":
                    print(">>>This is discovery task<<<")
                    print("Domain is: " + domain_name)
                    print("Discovery ID is: " + task_id)
                    print("Discovery status is: " + str(judge_type.get('status')))
                    discover_data(task_id, is_sep[0])
                elif judge_type.get('srcType') == "benchmark task":
                    get_ben_name = str(judge_type.get('name'))
                    print(">>>This is Benchmark task<<<")
                    print("Domain is: " + domain_name)
                    print("Benchmark ID is: " + task_id)
                    print("Benchmark author is: " + str(judge_type.get('author')))
                    print("Benchmark name is: " + get_ben_name)
                    if need_table_data:
                        benchmark_data(task_id, is_sep[0], benchmark_name)
                    else:
                        benchmark_data_easy(task_id, is_sep[0], benchmark_name)
                else:
                    print(">>>Can not judge the task id type, will stop get data.<<<")
            else:
                print('Task status was not Succeeded, pass')
        else:
            print(">>>Can not find the ID you pointed.")
    # if is_sep[0]:
    #     sep_connection.close()
    #     connection.close()
    # else:
        connection.close()
