# -*- coding: utf-8 -*-
"""
@File:          FID.py
@Description:   
@Author:        Tony Che
@Create Date:   2020-11-11
@Revision History:
"""

import traceback
import FlashProbe
from NetBrainIE import NetBrainIE, PrintMessage
from NetBrainDB import NetBrainDB
from Utils.NetBrainUtils import NetBrainUtils, CurrentMethodName, CreateGuid

ConfigFile = r'.\conf\FID31114.conf'
#ConfigFile = r'.\conf\FID31200.conf'
#ConfigFile = r'.\conf\FID31110.conf'
#ConfigFile = r'.\conf\FID30198.conf'


def FID(application=None, configFile=''):
    """ FID
    Parameter:
    ------------------------------------------
    application:
    configFile:
    
    Result:
    ------------------------------------------
    True
    
    Example:
    ------------------------------------------ 
    >> >
    >> >
    
    """
    configFile = ConfigFile if configFile == '' else configFile
    config = NetBrainUtils.GetConfig(configFile)
    if len(config) == 0:
        PrintMessage(''.join([CurrentMethodName(), 'Failed to load the configuration file: ', configFile]), 'Error')
        return False

    try:
        ret = True
        if application is None:
            app = NetBrainIE(config['Url'], config['Username'], config['Password'])
            app.Login()
        else:
            app = application
        if app.Logined:
            app.ApplyTenantAndDomain(config['Tenant Name'], config['Domain Name'])
        # ret = AddFIDFolder(app, config)
        # ret = ImportFID(app, config)
        ret = ExecuteFID(app, config)
    except Exception as e:
        print('Exception raised: ', str(e))
        ret = False
    finally:
        if application is None and app.Logined:
            app.Logout()
        return ret

def AddFIDFolder(application=None, configFile=''):
    test_data = configFile['New Folder']
    application.fid_add_tree_folder_by_name(test_data['Folder Name'], test_data['Parent Name'])
    return True

def ImportFID(application=None, configFile=''):
    test_data = configFile['Import FID']
    fid_all = application.fid_tree()
    folders = test_data['Folder Name'].replace('\\', '/').split('/')
    folder_name = folders[-1]
    # fid = next((item for item in fid_all['results'] if item.get("name") and item["name"] == folder_name), None)
    fid = application.get_fid_folder(test_data['Folder Name'], fid_all)
    if fid is None:
        fid = application.fid_add_tree_folder_by_name(folder_name, folders[-2])
    application.fid_import_many(fid, test_data['FID Fullnames'])
    # for fullname in test_data['FID Fullnames']:
    #     name = NetBrainUtils.ParseFilename(fullname)
    #     fid = next((item for item in fid_all['results'] if item.get("name") and item["name"] == name['FilenameWithOutExtension']), None)
    #     if fid is None:
    #         application.fid_import(folder_name, fullname)
    #     else:
    #         PrintMessage(f'{fullname} is exist, skipped.', 'Warning')
    return True

def ExecuteFID(application=None, configFile=''):
    fids = configFile['Execute FIDs']
    db = NetBrainDB(configFile['DB Info'])
    db.Login()
    db.GetDatabase(configFile['Domain Name'])
    for name, value in fids.items():
        path = value.get('Path', '')
        fid = application.get_fid_by_name(name)
        if fid is None or fid == {}:
            PrintMessage(f'{name} is NOT exist, skipped.', 'Warning')
            continue
        device_ids = value.get('Device IPs', [])
        if len(device_ids) > 0:
            devices = db.GetAll('Device', {'mgmtIP':{'$in': device_ids}})
        else:
            devices = db.GetAll('Device', {})
        device_ids = [item['_id'] for item in devices]
        application.fid_execution(path, device_ids)
        status = app.wait_fid_execution_complete(fid['_id'])
        if status['current'] is None:
            last_status = 'None' if status['last'] is None else status['last']['status']
            if last_status == 4:
                PrintMessage(f'{name} run successfully.')
            else:
                PrintMessage(f'{name} run status = {last_status}.', 'Warning')
        else:
            PrintMessage(f'{name} is still running.')

    db.Logout()
    return True

def GetQualification(sub_types:list):
    qualification = ''
    for item in sub_types:
        qualification += f'$device.subTypeName == "{item}" || '
    return ' ' if len(qualification) < 4 else qualification[:-4]

def GetRuleConditions(rule_conditions:list, prefix_space:str):
    conditions = prefix_space + 'conditions:\n'
    for item in rule_conditions:
        conditions += ''.join([prefix_space, '  - operand1: ', item['operand1'], '\n'])
        conditions += ''.join([prefix_space, '    operator: ', item['operator'], '\n'])
        conditions += ''.join([prefix_space, '    operand2: ', item['operand2'], '\n'])
    conditions += prefix_space + 'boolean_expression: A\n'
    return conditions

def GenerateFIDTemplate(app, config):
    fid_config = config.get('FlashProbe Template', None)
    if fid_config is None:
        PrintMessage(''.join([CurrentMethodName(), 'Failed to load the FlashProbe info in configuration file.']), 'Warning')
        return False
    contents = ""
    for key, item in fid_config.items():
        content = ''.join(['name: ', key, '\nversion: 1.0\nsource: ""\ndescription: "', item['Description'],
                           '"\ntags:\n  - ', item['tags'], '\n\nfeature:\n  qualification: All\n  configlet:\n',
                           '    sample: ""\n    match_rules:\n      - regexes: {}\n        patterns:\n        split_keys:\n',
                           '          group1: []\n        relation: ""\n', '        generate_one_FI_groups: []\n\n'])
        contents += content
        content = 'flash_probes:  # Definition for generating Flash Probe.\n'
        contents += content
        for fp in item['Flash Probes']:
            qualification = GetQualification(fp['Target SubType'])
            content = ''.join(['  - name: "', fp['Name'], '"\n    display_name: "', fp['Display Name'],
                               '"\n    description: "', fp['Description'], '"\n    target_type: ', fp['Target Type'],
                               '  # Device or Interface\n    qualification: |-  #\n        ', qualification, '\n'])
            contents += content
            contents += '    conflict_mode: Override  # support values: Override and Skip, the default value is Skip\n'
            contents += f'    type: {fp["Probe Type"]}  # Primary or Secondary or External\n'
            contents += f'    trigger_type: {fp["Probe SubType"]}  # AlertBased or TimerBased(User defined), AlertBased is the default value, valid for type=Primary\n'
            contents += '    alert_source: ""  # valid for type=External, such as ServiceNow...\n'
            contents += f'    frequency_multiple: {fp["Frequency Multiple"]}  # the multiple of the period of the base frequency, valid for type=Primary&&trigger_type=TimerBased\n'
            contents += '    frequency_interval: 1  # the time interval between frequency runs, the unit is hour, valid for type=Primary&&trigger_type=AlertBased\n'
            contents += '    variable_defines:  # the variables that may be used in rule or alert_message, valid for type=Primary|Secondary&&trigger_type=AlertBased\n'
            content = fp['Variable']['Parser']
            contents += f'      - parser: "{content}"\n        variables:  # the variables that want to use in rule or alert_message\n'
            for var in fp['Variable']['Variable Names']:
                content = f'          - name: {var["Name"]}  # variable full name\n'
                contents += content
                content = f'            alias: {var["Alias"]}  # alias that is actually used when referenced in Rule and alert_Message, same as "name" if alias have no value\n'
                contents += content
                content = var.get('Saved Monitor', None)
                if content is not None:
                    contents += f'            monitor:  # fill in this flag to indicate that this variable needs to be monitored\n'
                    contents += f'              display_name: {var["Name"]}  # display name which show up on the map data view.\n'
                    contents += '              unit: "' + {content['Unit']} + '"  # unit which show up on the map data view.\n'
            contents += '    rule:  # valid for type=Primary|Secondary&&trigger_type=AlertBased\n'
            content = 'true' if fp['Variable']['Rule']['Loop Table Rows'] else 'false'
            contents += f'      loop_table_rows: {content}\n'
            contents += GetRuleConditions(fp["Variable"]["Rule"]["Conditions"], '      ')
            content = fp['Variable']['Rule']['Alert Message']
            contents += f'    alert_message: "{content}"  # alert message, support variables, valid for type=Primary|Secondary&&trigger_type=AlertBased\n'
            content = 'true' if fp["Enable"] else 'false'
            contents += f'    enable: {content}  # whether to enable, true is default value\n'
    return contents

def GetDevicesWithFlashAlert(config):
    db = NetBrainDB(config['DB Info'])
    db.Login()
    db.GetDatabase(config['Domain Name'])
    devices = db.GetAll('Device', {'subType': {'$in': [2, 2001]}}, 'name', 1)
    db.Logout()
    device_count = int(len(devices) * 1.11 * config['Device Group With Flash Alert']['Alert Percentage'] + 0.5)
    return devices[:device_count]

def DefineDeviceGroupWithAlert(app: NetBrainIE, config, devices=None):
    group_info = config.get('Device Group With Flash Alert', None)
    if group_info is None:
        PrintMessage('Please define Device Group With Flash Alert.', 'Error')
        return False
    group_all = app._getAllDeviceGroupInfo()
    device_group_name = group_info['Name']
    if group_info['Type'] != 'Public':
        PrintMessage(f'Just support "Public" folder.', 'Warning')
    group = next((item for item in group_all if item['Name'] == device_group_name and item['Type'] == 0), None)
    if group is not None:
        PrintMessage(f'{group} is exist.', 'Warning')
    else:
        if devices is None:
            devices = GetDevicesWithFlashAlert(config)
        group_info['DeviceID'] = [item['mgmtIP'] for item in devices]
        app.SaveDeviceGroup(group_info)
        group_all = app._getAllDeviceGroupInfo()
        group = next((item for item in group_all if item['Name'] == group_info['Name'] and item['Type'] == 0), None)
        if group is None:
            PrintMessage(f'Failed to create the device group "{group}".', 'Error')
            return False
    return True

def ModifyProbeAndApply(app, config, devices:list, probe_name='show_access_lists01'):
    device = devices[0]
    flash_probes = app.flashprobes_search(device['_id'])
    source_probe = next((item for item in flash_probes['flashProbes'] if item.get('name', None) == probe_name), None)
    if source_probe is None:
        PrintMessage(f'Failed to find {probe_name} on {device["name"]}.', 'Error')
        return False
    probe_id = source_probe.pop('id')
    source_probe['createSrc'] = {'type': 'Manually', 'name': 'Manually'}
    source_probe['rule']['conditions'][0]['operator'] = 2
    app.flashprobes_save(probe_id, source_probe)
    apply_devices = []
    device_ids = []
    for item in devices[1:]:
        value = {'devId': item['_id'], 'devName': item['name'], 'devTypeId': item['subType']}
        apply_devices.append(value)
        device_ids.append(item['_id'])
    db = NetBrainDB(config['DB Info'])
    db.Login()
    db.GetDatabase(config['Domain Name'])
    flash_probes = db.GetAll('AMFPInstance', {'npv': {'$in': device_ids}, 'n': probe_name}, 'nn', 1)
    db.Logout()
    apply_flashprobe_ids = []
    for item in flash_probes:
        apply_flashprobe_ids.append(item['_id'])
    app.flashprobes_apply(probe_id, apply_devices, apply_flashprobe_ids)
    return True


if __name__ == "__main__":
    config = NetBrainUtils.GetConfig(ConfigFile)
    if len(config) == 0:
        PrintMessage(''.join([CurrentMethodName(), 'Failed to load the configuration file: ', ConfigFile]), 'Error')
        exit(-1)

    try:
        ret = True
        FlashProbe.InitFlashProbeEnv(config)
        app = NetBrainIE(config['Url'], config['Username'], config['Password'])
        app.Login()
        if app.Logined:
            app.ApplyTenantAndDomain(config['Tenant Name'], config['Domain Name'])
            devices = GetDevicesWithFlashAlert(config)
            ret = DefineDeviceGroupWithAlert(app, config, devices)
            # ret = AddFIDFolder(app, config)
            ret = ImportFID(app, config)
            # ret = GenerateFIDTemplate(app, config)
            # with open('fid.yaml', 'w') as fp:
            #     fp.write(ret)
            ret = ExecuteFID(app, config)
            ret = ModifyProbeAndApply(app, config, devices)
    except Exception as e:
        msg = traceback.format_exc()
        PrintMessage("Exception: " + msg, 'Error')
    finally:
        if app.Logined:
            app.Logout()
