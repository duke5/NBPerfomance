# -*- coding: utf-8 -*-
"""
@File:          DomainHealthReport.py
@Description:   
@Author:        Tony Che
@Create Date:   2020-02
@Revision History:
"""

import json
import re
from NetBrainIE import NetBrainIE, PrintMessage, PrintJsonObject
from NetBrainDB import NetBrainDB
from Utils.NetBrainUtils import NetBrainUtils, CurrentMethodName, CreateGuid

ConfigFile = r'.\conf\DomainHealthReport9898.conf'


def DomainHealthReport(application=None, config_file=''):
    """ DomainHealthReport
    Parameter:
    ------------------------------------------
    application:
    config_file:
    
    Result:
    ------------------------------------------
    True
    
    Example:
    ------------------------------------------ 
        
    """
    config_file = ConfigFile if config_file == '' else config_file
    config = NetBrainUtils.GetConfig(config_file)
    if len(config) == 0:
        PrintMessage(''.join([CurrentMethodName(), 'Failed to load the configuration file: ', config_file]), 'Error')
        return False

    try:
        ret = True
        database = None
        if application is None:
            app = NetBrainIE(config['Url'], config['Username'], config['Password'])
            app.Login()
            app.ApplyTenantAndDomain(config['Tenant Name'], config['Domain Name'])
        else:
            app = application
        if app.Logined:
            report = app.DomainHealthReport()
            if len(report) <= 0:
                PrintMessage('Failed to receive Domain Health Report', 'Error')
                ret = False
                return ret
            database = NetBrainDB(config['DBInfo'])
            if not database.Login():
                PrintMessage('Failed to login Database.', 'Error')
                ret = False
                return ret
            database.GetDatabase(config['Domain Name'])
            print('Driver Associated Device')
            info = report['content']['driverInfo']
            #PrintJsonObject(info)
            CompareDriverAssociatedDevice(info, database)
            print('Basic Network Settings Completeness:')
            info = report['content']['networkSettingInfo']
            #PrintJsonObject(info)
            CompareBasicNetworkSettingsCompleteness(app, info)
            print('Discovery Status')
            info = report['content']['discoveryInfo']
            #PrintJsonObject(info)
            CompareDiscoveryStatus(app, info)
            # return True
            print('Site Definition Completeness')
            info = report['content']['siteInfo']
            #PrintJsonObject(info)
            CompareSiteDefinitionCompleteness(info)
            print('Benchmark Task Health')
            info = report['content']['benchmarkInfo']
            #PrintJsonObject(info)
            CompareBenchmarkTaskHealth(info)
            print('Path Calculation Health')
            info = report['content']['pathInfo']
            #PrintJsonObject(info)
            ComparePathCalculationHealth(info)
            print('Disk Management Settings Completeness')
            info = report['content']['dataCleanInfo']
            #PrintJsonObject(info)
            CompareDiskManagementSettingsCompleteness(info)
            print('MongoDB Disk Alert Rules: (System Settings)')
            info = report['content']['mongoDBAlertInfo']
            #PrintJsonObject(info)
            CompareMongoDBDiskAlertRules(info)
            print('Map Layout Settings Completeness')
            info = report['content']['mapLayoutInfo']
            #PrintJsonObject(info)
            CompareMapLayoutSettingsCompleteness(info)
            print('Summary')
            PrintJsonObject(report['summary'])
            CompareSummary(report['summary'])
    except Exception as e:
        print('Exception raised: ', str(e))
        ret = False
    finally:
        if application is None and app.Logined:
            app.Logout()
        if database is not None and database.Logined:
            database.Logout()
        return ret

def CompareSummary(source_info):
    return True

def CompareDriverAssociatedDevice(source_info, db):
    count = db.Count('Interface', {})
    if count != source_info['interfaceCount']:
        PrintMessage(''.join(['Interface Count (', str(source_info['interfaceCount']), ') is not equal to the count (',
                              str(count), ') in the database.']), 'Error')
    driver_count = len(source_info['driverDetails'])
    device_count = interface_count = 0
    for driver in source_info['driverDetails']:
        device_count += driver['deviceCount']
        interface_count += driver['interfaceCount']
        #print(driver['driverName'])
        count = db.Count('Device', {'driverName':driver['driverName']})
        if count != driver['deviceCount']:
            PrintMessage(''.join(['Device Count (', device_count, ') is not equal to the count (', count,
                                  ') in the database.']), 'Error')
    if driver_count != source_info['driverCount'] or device_count != source_info['deviceCount'] or \
            interface_count != source_info['interfaceCount']:
        PrintMessage(''.join(['Driver Count: ', str(source_info['driverCount']), '(', str(count), '), Device Count: ',
                              str(source_info['deviceCount']), '(', str(device_count), '), Interface Count: ',
                              str(source_info['interfaceCount']), '(', str(interface_count), ')']), 'Error')
    else:
        PrintMessage(f'Driver Count: {driver_count}, Device Count: {device_count}, Interface Count: {interface_count}')
    return True

def ParseBasicNetworkSettingsFrontServerInfo(current_network_settings):
    front_servers = current_network_settings.get('networkServer', [])
    network_settings_info = {
        'Stand-alone Front Server (defined)': 0,
        'Stand-alone Front Server (unused)': 0,
        'Stand-alone Front Server (with over 5000 devices)': 0,
        'Front Server Group (defined)': 0,
        'Front Server Group (unused)': 0,
        'Front Server Group (with over 5000 devices)': 0
    }
    fsg_frontservers = dict()
    fs_in_fsg = list()
    for fs in front_servers:
        if fs['isFSG']:
            fsg_frontservers.update({fs['alias']: {'fs': fs['fsIds'], 'defined': 0, 'over5K': 0}})
            fs_in_fsg.extend(fs['fsIds'])
    for fs in front_servers:
        name = fs['id']
        if name not in fs_in_fsg and fs['alias'] not in fsg_frontservers.keys():
            if fs['refCount']:
                network_settings_info['Stand-alone Front Server (defined)'] += 1
            else:
                network_settings_info['Stand-alone Front Server (unused)'] += 1
            count_over5K = 1 if fs['refCount'] >= 5000 else 0
            network_settings_info['Stand-alone Front Server (with over 5000 devices)'] += count_over5K
            continue
        for key in fsg_frontservers.keys():
            if name in fsg_frontservers[key]['fs']:
                fsg_frontservers[key]['defined'] = 1
                if fs['refCount'] >= 5000:
                    fsg_frontservers[key]['over5K'] = 1
                break
    count_fsg = len(fsg_frontservers)
    count_defined = count_over5K = 0
    for fsg in fsg_frontservers.values():
        if fsg['defined']:
            count_defined += 1
        if fsg['over5K']:
            count_over5K += 1
    network_settings_info['Front Server Group (defined)'] = count_fsg
    network_settings_info['Front Server Group (unused)'] = count_fsg - count_defined
    network_settings_info['Front Server Group (with over 5000 devices)'] = count_over5K
    #PrintJsonObject(network_settings_info)
    return network_settings_info

def ParseBasicNetworkSettingsOtherInfo(current_network_settings):
    network_settings_info = {
        'Private Key (defined)': 0,
        'Private Key (unused)': 0,
        'Jumpbox (defined)': 0,
        'Jumpbox (unused)': 0,
        'Telnet/SSH Login (defined)': 0,
        'Telnet/SSH Login (unused)': 0,
        'Privilege Key (defined)': 0,
        'Privilege Key (unused)': 0,
        'SNMP String (defined)': 0,
        'SNMP String (unused)': 0,
    }
    other_infos = current_network_settings.get('sshPrivateKey', [])
    for info in other_infos:
        network_settings_info['Private Key (defined)'] += 1
        if info['refCount'] <= 0:
            network_settings_info['Private Key (unused)'] += 1

    other_infos = current_network_settings.get('jumpbox', [])
    for info in other_infos:
        network_settings_info['Jumpbox (defined)'] += 1
        if info['refCount'] <= 0:
            network_settings_info['Jumpbox (unused)'] += 1

    other_infos = current_network_settings.get('telnetInfo', [])
    for info in other_infos:
        network_settings_info['Telnet/SSH Login (defined)'] += 1
        if info['refCount'] <= 0:
            network_settings_info['Telnet/SSH Login (unused)'] += 1

    other_infos = current_network_settings.get('enablePasswd', [])
    for info in other_infos:
        network_settings_info['Privilege Key (defined)'] += 1
        if info['refCount'] <= 0:
            network_settings_info['Privilege Key (unused)'] += 1

    other_infos = current_network_settings.get('snmpRoInfo', [])
    for info in other_infos:
        network_settings_info['SNMP String (defined)'] += 1
        if info['refCount'] <= 0:
            network_settings_info['SNMP String (unused)'] += 1

    #PrintJsonObject(network_settings_info)
    return network_settings_info

def ParseBasicNetworkSettings(current_network_settings):
    network_settings_info = {
        'Stand-alone Front Server (defined)': 0,
        'Stand-alone Front Server (unused)': 0,
        'Stand-alone Front Server (with over 5000 devices)': 0,
        'Front Server Group (defined)': 0,
        'Front Server Group (unused)': 0,
        'Front Server Group (with over 5000 devices)': 0,
        'Private Key (defined)': 0,
        'Private Key (unused)': 0,
        'Jumpbox (defined)': 0,
        'Jumpbox (unused)': 0,
        'Telnet/SSH Login (defined)': 0,
        'Telnet/SSH Login (unused)': 0,
        'Privilege Key (defined)': 0,
        'Privilege Key (unused)': 0,
        'SNMP String (defined)': 0,
        'SNMP String (unused)': 0,
        'API Server': 0,
        'CheckPoint OPSEC': 0
    }
    info = ParseBasicNetworkSettingsFrontServerInfo(current_network_settings)
    network_settings_info.update(info)
    info = ParseBasicNetworkSettingsOtherInfo(current_network_settings)
    network_settings_info.update(info)

    return network_settings_info

def CompareBasicNetworkSettingsCompleteness(app, source_info):
    #app.CheckDeviceCount()
    current_network_settings = app.GetDiscoverNetworkSetting()
    dest_info = ParseBasicNetworkSettings(current_network_settings)
    info = app.GetExternalAPIServer()
    dest_info['API Server'] = len(info)
    info = app.GetCheckPointOPSEC()
    dest_info['CheckPoint OPSEC'] = len(info)
    PrintJsonObject(dest_info)
    return True

def ParseDiscoveryStatusSourceInfo(source_info):
    discovered_devices = dict()
    licensed_node_usage = dict()
    fine_tune = dict()
    for info in source_info:
        name = info['name']
        detail = info['countDetail']
        if name == 'Discovered Devices':
            devices = filter(None, detail.split(','))
            for device in devices:
                # 'Legacy Device: 44171'
                item = device.split(':')
                discovered_devices.update({item[0]: int(item[1])})
            discovered_devices.update({'Attention': info['needAttention']})
        elif name == 'Licensed Node Usage':
            # licensed_node_usage.update({'Licensed Node Usage': detail, 'Attention': info['needAttention']})
            # '44171 out of 100000 Licensed Nodes (Usage: 44.17%)'
            item = re.search('(\d*)\s*out of\s*(\d*)\s*.*?:\s*(\d*\.\d*)%\)', detail, re.I)
            if len(item.groups()) == 3:
                licensed_node_usage.update({'Licensed Node Usage': detail, 'Legacy Count': int(item[1]),
                                            'Domain Nodes': int(item[2]), 'Used Device Ratio': float(item[3]),
                                            'Attention': info['needAttention']})
            else:
                PrintMessage(''.join([CurrentMethodName(), ': Failed to parse Licensed Node Usage\n', detail]), 'Error')
        elif name == 'Discovered by SNMP':
            fine_tune.update({'Discovered by SNMP': int(info['countDetail']), 'Attention': info['needAttention']})
        elif name == 'Licensed Node Usage':
            fine_tune.update({'Licensed Node Usage': int(info['countDetail']), 'Attention': info['needAttention']})
        elif name == 'Unknown IP':
            fine_tune.update({'Unknown IP': int(info['countDetail']), 'Attention': info['needAttention']})
        elif name == 'Missed Devices':
            fine_tune.update({'Missed Devices': int(info['countDetail']), 'Attention': info['needAttention']})
        elif name == 'Unclassified Network Devices':
            fine_tune.update({'Unclassified Network Devices': int(info['countDetail']),
                              'Attention': info['needAttention']})
        elif name == 'Unknown SNMP SysObjectID':
            fine_tune.update({'Unknown SNMP SysObjectID': int(info['countDetail']), 'Attention': info['needAttention']})
        elif name == 'Subnet with Conflicted IPs':
            fine_tune.update({'Unknown SNMP SysObjectID': int(info['countDetail']), 'Attention': info['needAttention']})
        elif name == 'Zone':
            fine_tune.update({'Zone': int(info['countDetail']), 'Attention': info['needAttention']})
        elif name == 'Hostname Change':
            fine_tune.update({'Hostname Change': int(info['countDetail']), 'Attention': info['needAttention']})
    return {'Discovered Devices': discovered_devices, 'Licensed Node Usage': licensed_node_usage, 'Fine Tune': fine_tune}

def ParseDiscoveryStatusDestInfo(dest_info):
    discovered_devices = dict()
    licensed_node_usage = dict()
    fine_tune = dict()
    info = dest_info['Domain Summary']['nodeSizeSummary']
    name = info.get('legacyCnt', None)
    if name is not None:
        discovered_devices.update({'Legacy Device': name})
        licensed_node_usage.update({'Legacy Count': name, 'Domain Nodes': info['domainNodes'],
                                   'Used Device Ratio': info['usedDeviceRatio']})
    for info in dest_info['Device Count List']:
        name = info['device']
        if name == 'DiscoveredBySNMP':
            fine_tune.update({'Discovered by SNMP': info['count']})
        elif name == 'UnknownIP':
            fine_tune.update({'Unknown IP': info['count']})
        elif name == 'MissedDevices':
            fine_tune.update({'Missed Devices': info['count']})
        elif name == 'UnclassifiedNetworkDevs':
            fine_tune.update({'Unclassified Network Devices': info['count']})
        elif name == 'UnknownSNMPSysOID':
            fine_tune.update({'Unknown SNMP SysObjectID': info['count']})
        elif name == 'HostnameChange':
            fine_tune.update({'Hostname Change': info['count']})
    fine_tune.update({'Subnet with Conflicted IPs': dest_info['Subnets']['conflictedSubnetsCount']})
    fine_tune.update({'Zone': len(dest_info['Zones'])})
    return {'Discovered Devices': discovered_devices, 'Licensed Node Usage': licensed_node_usage, 'Fine Tune': fine_tune}

def CompareDiscoveryStatus(app, source_info):
    src_info = ParseDiscoveryStatusSourceInfo(source_info)
    dest_info = app.GetDiscoveryStatusInDomainHealthReport()
    dest_info = ParseDiscoveryStatusDestInfo(dest_info)
    #fine_tune_summary_info = app._fineTuneSummaryInfo()

    return True

def CompareSiteDefinitionCompleteness(source_info):
    return True

def CompareBenchmarkTaskHealth(source_info):
    return True

def ComparePathCalculationHealth(source_info):
    return True

def CompareDiskManagementSettingsCompleteness(source_info):
    return True

def CompareMongoDBDiskAlertRules(source_info):
    return True

def CompareMapLayoutSettingsCompleteness(source_info):
    return True


if __name__ == "__main__":
    DomainHealthReport()

