# -*- coding: utf-8 -*-
"""
@File:          FlashProbe.py
@Description:   
@Author:        Tony Che
@Create Date:   2020-11-16
@Revision History:

design document:
https://confluence.netbraintech.com/confluence/display/SDNA/1.+Adaptive+Monitor+front-end+High+Level+Design
"""

from datetime import datetime, timedelta
#import json
#import logging
import os
import queue
import traceback
import threading
from copy import deepcopy
from time import strftime, gmtime, sleep
from NBPackage.nbcrypto import NBCrypto
from NetBrainIE import NetBrainIE
from NetBrainDB import NetBrainDB, PostgresDB
from Utils.NetBrainUtils import NetBrainUtils, CurrentMethodName, CreateGuid

ConfigFile = r'.\conf\FlashProbe31114.conf'
#ConfigFile = r'.\conf\FlashProbe99188.conf'
#ConfigFile = r'.\conf\FlashProbe3197.conf'
#ConfigFile = r'.\conf\FlashProbe31110.conf'
log_filename = r'flashprobe.log'
logger = None

inputQueue = queue.Queue()   # PrimaryFlashProbe
inputQueue2 = queue.Queue()  # SecondaryFlashProbe
inputQueue3 = queue.Queue()  # Enable FlashProbes
inputQueue4 = queue.Queue()  # VerifyBuildInProbes


def FlashProbe(application=None, configFile=''):
    """ FlashProbe
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
        if InitNBCrypto(config['DB Info']):
            PrintMessage('NBCrypto.init_module failed', 'Error')
            exit(-1)

        device_name = None
        if application is None:
            app = NetBrainIE(config['Url'], config['Username'], config['Password'])
            app.Login()
        else:
            app = application
        if app.Logined:
            app.ApplyTenantAndDomain(config['Tenant Name'], config['Domain Name'])
        if ret:
            if config.get('Multi Thread Info', {}).get('ThreadCount', 0) == 0:
                config['Multi Thread Info'] = {'ThreadCount': 1}
            #     ret = WriteFlashProbeToDB(app, config)
            #     if ret:
            #         ret = WriteSecondaryFlashProbeToDB(app, config)
            # else:
            primary_probe_start = datetime.now()
            ret = WriteFlashProbeToDB_multithread(app, config)
            primary_probe_end = datetime.now()
            if ret:
                ret = WriteSecondaryFlashProbeToDB_multithread(app, config)
            secondary_probe_end = datetime.now()
            if ret:
                NotifyCreateResourceFullPackage(config)
        PrintMessage(''.join(['Primary Probe start: ', str(primary_probe_start), '; Primary Probe end: ', str(primary_probe_end)]))
        PrintMessage(''.join(['Secondary Probe start: ', str(primary_probe_end), '; Secondary Probe end: ', str(secondary_probe_end)]))
        #device_name = 'ustta000000'
        #ret = DeleteFlashProbe(app, config)
    except Exception as e:
        # traceback.print_exc()
        # print('Exception raised: ', str(e))
        msg = traceback.format_exc()
        PrintMessage("Exception: " + msg, 'Error')
        ret = False
    finally:
        if application is None and app.Logined:
            app.Logout()
        return ret

def InitFlashProbeEnv(config):
    app = NetBrainIE(config['Url'], config['Username'], config['Password'])
    app.Login()
    if not app.Logined:
        return False
    app.ApplyTenantAndDomain(config['Tenant Name'], config['Domain Name'])
    parser_lib = app.parserlib_category()
    shared_parsers = next((item for item in parser_lib['nodes'] if item.get('name') and item['name'] == 'Shared Files in Tenant'), None)
    if shared_parsers is None:
        PrintMessage('Failed to find the folder "Shared Parsers in Tenant".', 'Error')
        return False
    interface_parsers = {}  # next((item for item in shared_parsers['nodes'] if item.get('name') and item['name'] == 'new_parsers 79 CLI command'), None)
    if interface_parsers is None:
        ret = ImportParsers(app, config['Import Parsers']['Interface Parsers'])
        # PrintMessage('Failed to find interface parsers, please import them.', 'Error')
        # return False
    snmp_parsers = next((item for item in shared_parsers['nodes'] if item.get('name') and item['name'] == 'snmp parser'), None)
    if snmp_parsers is None:
        ret = ImportParsers(app, config['Import Parsers']['Snmp Parsers'])
    parser_lib = app.parserlib_category()
    shared_parsers = next((item for item in parser_lib['nodes'] if item.get('name') and item['name'] == 'Shared Files in Tenant'), None)
    snmp_parsers = next((item for item in shared_parsers['nodes'] if item.get('name') and item['name'] == 'snmp parser'), {})
    if len(snmp_parsers) == 0 or len(snmp_parsers.get('parsers', [])) < 4:
        ret = ImportParsers(app, config['Import Parsers']['Snmp Parsers'])
        if not ret:
            PrintMessage('Failed to find snmp parsers, please import them.', 'Error')
            return False
    ret = RemoveParsersQualify(app, config['Remove Parsers Qualify'], parser_lib)
    default_frequency = config.get('Device Polling Default Frequency', None)
    if default_frequency is not None:
        current_default_frequency = app.DefaultPollingFrequency_Get()
        if current_default_frequency['setting'] != default_frequency:
            app.DefaultPollingFrequency(default_frequency)
    return ret

def ImportParsers(application=None, configFile=''):
    if configFile['Folder Fullname'] is None:
        application.parser_import(configFile['Parser Fullname'], configFile['Parent Name'])
    else:
        files = os.listdir(configFile['Folder Fullname'])
        parser_files = []
        for file in files:
            if not file.endswith('.xpar'):
                continue
            parser_files.append(file)
        index = len(parser_files)
        import_token = application._fileUploadRestrictionToken(f'{index}')
        parser_lib = None
        index = 1
        for file in parser_files:
            print(f'----------------------{index}: {file}----------------------------')
            index += 1
            fullname = os.path.join(configFile['Folder Fullname'], file)
            application.parser_import(fullname, configFile['Parent Name'], parser_lib, import_token)
            if parser_lib is None:
                parser_lib = application.parserlib_category()
    return True

def GenerateFlashProbePayload(device, parser, interface, variable, compound_info=None):
    variable_name = variable['name']
    variable_type = variable['type']
    flashprobe_name = ''.join(['FP_', parser['name'], '_intf_', variable_name])
    parser_variable = next((item for item in parser['variables'] if item.get("name") and item["name"] == '$'+variable_name), None)
    if variable_type == 'int':
        # 0: Violates GB Rule, 1: Equals to, 2: Does not Equal to, 3: is none, 4: is not none, 5：Greater than,
        # 6: Less than, 7: Greater than or Equals to, 8: Less than or Equals to, 9: Range
        rule_operator = 2
        rule_expect_result = '-10000'
    elif variable_type == 'string':
        # 0: Violates GB Rule, 1: Equals to, 2: Does not Equal to, 3: is none, 4: is not none,
        # 5: contains, 6: Does not contain
        rule_operator = 2
        rule_expect_result = 'abcdef'
    payload = {
        'nodePathSchema': 'Legacy',
        'nodePathValue': device['_id'],  # '9b8ab543-b637-495b-bfc2-426eb4d53c7d',
        'nodeName': device['name'],  #'ustta000001',
        'name': flashprobe_name,
        'displayName': flashprobe_name,
        'desc': '',
        'type': 1,
        'category': 1,
        'alertSrc': 'Netbrain',
        'createSrc': {
            'type': 'Manually',
            'name': 'Manually'
        },
        'variables': [
            {
                'fullName': parser_variable['fullName'],  # 'intfs_table.$status',
                'alias': variable_name,  # 'status',
                'scope': 2,
                'type': 1,
                'dataType': variable_type,  # 'string',
                'parserPath': parser['path'],  # 'Shared Files in Tenant/new_parsers 79 CLI command/InterfaceAM_2 [Cisco IOS]',
                'parserType': 1,
                'varType': 1
            }
        ],
        'rule': {
            'isVerifyTable': False,
            'conditions': [
                {
                    'operand1': variable_name,  # 'status',
                    'operator': rule_operator,  # 2,
                    'operand2': {'ruleParam': rule_expect_result}
                }
            ],
            'expression': 'A'
        },
        'alertLevel': 2,
        'alertMsg': {
            'originalExpression': flashprobe_name + '_alert'
        },
        'triggeredBy': [],
        'enabled': False,  # True,
        'intfName': interface['name'],  # 'GigabitEthernet0/0/0/10',
        'intfPathSchema': 'intfs._id',
        'intfPathValue': interface['_id'],  # '15d2a25d-8578-4f84-9c68-84266bb8d24c',
        'usedParsers': [
            {
                'parserPath': parser['path']  # 'Shared Files in Tenant/new_parsers 79 CLI command/InterfaceAM_2 [Cisco IOS]'
            }
        ]
    }
    if variable['isCompound']:
        item = {
            'fullName': CreateGuid(),
            'alias': f'{variable_name}_Compound_{variable_type}',  # 'status',
            'scope': 2,
            'type': 2,
            'dataType': 'double' if variable['type'] == 'int' else 'string',
            'expression': f'${variable_name} + 1' if variable['type'] == 'int' else f'${variable_name} + "abcdef"'
        }
        payload['variables'].append(item)
        payload['name'] += '_Compound'
        payload['displayName'] += '_Compound'
    return payload

def AddFlashProbe(application, configFile):
    db = NetBrainDB(configFile['DB Info'])
    db.Login()
    db.GetDatabase(configFile['Tenant Name'])
    parsers = db.GetAll('Parsers', {'path':{'$regex': '.*InterfaceAM_.*'}, 'accessType': 4}, 'path', 1)
    db.GetDatabase(configFile['Domain Name'])
    devices = db.GetAll('Device', {'subType': 2001})
    variables = configFile['Flash Probe Info']['Variables']
    for device in devices:
        interfaces = db.GetAll('Interface', {'devId': device['_id'], 'name': {'$regex': 'GigabitEthernet0/0/0/.*'}}, 'name', 1)
        interface_names = [item['name'] for item in interfaces]
        for parser in parsers:
            interface_name = parser['command'].replace('show interface ', '')
            index = interface_names.index(interface_name)
            print(f'{index}: {interface_name}')
            if index < 0:
                continue
            for variable in variables:
                payload = GenerateFlashProbePayload(device ,parser, interfaces[index], variable)
                application.flashprobe_add(payload)
    db.Logout()

    return True

def DeleteFlashProbe(application, configFile, device_name=None):
    if device_name is not None:
        devices = {'deviceList': [{'name': device_name}]}
    else:
        devices = application.getDevicesByTypesByPaging()
    for device in devices['deviceList']:
        flashprobes = application.flashprobe_search_by_name(device['name'])
        flashprobe_ids = [item['id'] for item in flashprobes['flashProbes']]
        application.flashprobe_delete(flashprobe_ids)
    return True

def WorkerThread_Primary(app, payload):
    ret = True
    try:
        #ret = app.flashprobe_add(payload)
        db = payload['DB']
        device = payload['Device']
        flash_probes = []
        task_definitions = []
        monitor_variables = []
        application_info = payload['Application Info']
        no_alert = payload['No Alert']
        # device parsers
        application_info['npv'] = device['_id']  # nodePathValue
        for item in payload['Device Parsers']:
            flash_probe_info = PrepareFlashProbe_Device(item, device)
            flash_probe = GenerateFlashProbe_Device(device, flash_probe_info, application_info, no_alert, 1, monitor_variables)
            flash_probes.append(flash_probe)
            parser_name = flash_probe['ups'][0]['ppt']
            task_definition_item_action = None
            for task_definition_item in task_definitions:
                task_definition_item_action = next((x for x in task_definition_item['taskDefinition']['actions'] if x.get("parser") and x["parser"] == parser_name), None)
            if task_definition_item_action is not None:
                task_definition_item['srcIdentifiers'].append(flash_probe['_id'])
                continue
            actions = []
            for automation_task in item['automation tasks']:
                action = {
                    'commandtype': automation_task['command type'],
                    'command': automation_task['command'],
                    'parser': automation_task['parser'],
                    'uploadoriginalfile': 0,
                    'devices': [device['name']],
                    'nodes': [],
                    'parameter': None,
                    'retrieveparameter': None,
                    'AdditionalData': None,
                }
                actions.append(action)
            task_definition = GenerateAutomationTaskDefinition(application_info, [flash_probe['_id']], actions, 3)
            task_definitions.append(task_definition)
        length = len(flash_probes)
        result = db.InsertMany('AMFPInstance', flash_probes)
        if len(result) != length:
            PrintMessage('Write to collection AMFPInstance failed!!!!!', 'Error')
        else:
            PrintMessage(f'{device["name"]}: Device Primary Flash Probes: {length}.')
            length = len(monitor_variables)
            result = db.InsertMany('AMMonitorVariable', monitor_variables)
            if len(result) != length:
                PrintMessage('Write to collection AMMonitorVariable failed!!!!!', 'Error')
            else:
                PrintMessage(f'{device["name"]}: AM Monitor Variable: {length}.')
            length = len(task_definitions)
            result = db.InsertMany('AutomationTaskDefinition', task_definitions)
            if len(result) != length:
                PrintMessage('Write to collection AutomationTaskDefinition failed!!!!!', 'Error')
            else:
                PrintMessage(f'{device["name"]}: Automation Task Definition: {length}.')
        #time.sleep(30)
    except Exception as e:
        traceback.print_exc()
        # PrintMessage('Exception raised: ' + str(e), 'Error')
        ret = False
    finally:
        return ret

def WorkerThread_Secondary(app, payload):
    ret = True
    try:
        db = payload['DB']
        device = payload['Device']
        application_info = payload['Application Info']
        flash_probes = []
        task_definitions = []
        trigger_relations = []
        monitor_variables = []
        no_alert = False
        # device parsers
        primary_probes = db.GetAll('AMFPInstance', {'npv': device['_id'], 't': 1,
                                                    'operateInfo.opUser': app.Username}, 'n', 1)
        application_info['npv'] = device['_id']  # nodePathValue
        for item in payload['Device Parsers']:
            flash_probe_info = PrepareFlashProbe_Device(item, device)
            second_probe = GenerateFlashProbe_Device(device, flash_probe_info, application_info, no_alert, 2, monitor_variables)
            for primary_probe in primary_probes:
                flash_probe = deepcopy(second_probe)  # second_probe.copy()
                #flash_probe['tb'] = second_probe['tb'][:]
                id = CreateGuid().replace('-', '')
                name = '_'.join([flash_probe['n'], primary_probe['n']])
                if primary_probe['n'] == 'ustta000000_dec_snmp03':
                    a = 1
                flash_probe['_id'] = id
                flash_probe['n'] = flash_probe['dn'] = flash_probe['ds'] = name
                flash_probe['am']['oe'] = flash_probe['am']['e'] = name + '_alert'
                flash_probe['tb'].append(primary_probe['_id'])
                flash_probes.append(flash_probe)
                parser_name = flash_probe['ups'][0]['ppt']
                actions = []
                for automation_task in item['automation tasks']:
                    action = {
                        'commandtype': automation_task['command type'],
                        'command': automation_task['command'],
                        'parser': automation_task['parser'],
                        'uploadoriginalfile': 0,
                        'devices': [device['name']],
                        'nodes': [],
                        'parameter': None,
                        'retrieveparameter': None,
                        'AdditionalData': None,
                    }
                    actions.append(action)
                task_definition = GenerateAutomationTaskDefinition(application_info, [flash_probe['_id']], actions, 7)
                task_definitions.append(task_definition)
                trigger_relation = {
                    '_id': CreateGuid().replace('-', ''),
                    't': 1,
                    'src': primary_probe['_id'],
                    'npv': device['_id'],
                    'dest': id,
                    'dt': task_definition['_id'],
                    'tr':{
                        'rt': 1,
                        'rc': None,
                        's': {'ise': False, 'tss': None}
                    },
                    'ise': True,
                    'operateInfo':{
                        'opUserId': application_info['userid'],
                        'opUser': application_info['username'],
                        'opTime': datetime.utcnow()
                    }
                }
                trigger_relations.append(trigger_relation)
        # write to DB
        length = len(flash_probes)
        result = db.InsertMany('AMFPInstance', flash_probes)
        if len(result) != length:
            PrintMessage('Write to collection AMFPInstance failed!!!!!', 'Error')
        else:
            PrintMessage(f'{device["name"]}: Device Secondary Flash Probes: {length}.')
            length = len(monitor_variables)
            result = db.InsertMany('AMMonitorVariable', monitor_variables)
            if len(result) != length:
                PrintMessage('Write to collection AMMonitorVariable failed!!!!!', 'Error')
            else:
                PrintMessage(f'{device["name"]}: AM Monitor Variable: {length}.')
            length = len(task_definitions)
            result = db.InsertMany('AutomationTaskDefinition', task_definitions)
            if len(result) != length:
                PrintMessage('Write to collection AutomationTaskDefinition failed!!!!!', 'Error')
            else:
                PrintMessage(f'{device["name"]}: Automation Task Definition: {length}.')
            length = len(trigger_relations)
            result = db.InsertMany('AMTriggerRelationship', trigger_relations)
            if len(result) != length:
                PrintMessage('Write to collection AMTriggerRelationship failed!!!!!', 'Error')
            else:
                PrintMessage(f'{device["name"]}: AM Trigger Relationship: {length}.')
    except Exception as e:
        traceback.print_exc()
        # PrintMessage('Exception raised: ' + str(e), 'Error')
        ret = False
    finally:
        return ret

def WorkerThread_Verify(db, payload):
    ret = True
    try:
        for day in payload['Days']:
            VerifyFlashProbeResultByDay(db, payload['Collection Name'], payload['Flash Probe'], day,
                                        payload['Min Interval'], payload['Max Interval'])
        #time.sleep(30)
    except Exception as e:
        traceback.print_exc()
        # PrintMessage('Exception raised: ' + str(e), 'Error')
        ret = False
    finally:
        return ret

def StartWorkerThread(app, type):
    # 1: primary probe, 2: secondary probe, 3: verify probe
    while True:
        try:
            if type == 1:
                size = inputQueue.qsize()
                if size <= 0:
                    sleep(1)
                    continue
                PrintMessage(f'{size} tasks in primary probe queue.')
                param = inputQueue.get()
                WorkerThread_Primary(app, param)
                inputQueue.task_done()
            elif type == 2:
                size = inputQueue2.qsize()
                if size <= 0:
                    sleep(1)
                    continue
                PrintMessage(f'{size} tasks in secondary probe queue.')
                param = inputQueue2.get()
                WorkerThread_Secondary(app, param)
                inputQueue2.task_done()
            elif type == 3:
                size = inputQueue3.qsize()
                if size <= 0:
                    sleep(1)
                    continue
                PrintMessage(f'{size} tasks in verify probe queue.')
                param = inputQueue3.get()
                WorkerThread_Verify(app, param)
                inputQueue3.task_done()
        except Exception:
            exception_stack = traceback.format_exc()
            PrintMessage('Exception raised: ' + exception_stack, 'Error')
        finally:
            pass

    return True

def AddFlashProbe_multithread(application=None, configFile=''):
    db = NetBrainDB(configFile['DB Info'])
    db.Login()
    db.GetDatabase(configFile['Tenant Name'])
    parsers = db.GetAll('Parsers', {'path': {'$regex': '.*InterfaceAM_.*'}, 'accessType': 4}, 'path', 1)
    db.GetDatabase(configFile['Domain Name'])
    devices = db.GetAll('Device', {'subType': 2001})
    variables = configFile['Flash Probe Info']['Variables']
    for device in devices:
        print(device['name'])
        interfaces = db.GetAll('Interface', {'devId': device['_id'], 'name': {'$regex': 'GigabitEthernet0/0/0/.*'}},
                               'name', 1)
        interface_names = [item['name'] for item in interfaces]
        for parser in parsers:
            interface_name = parser['command'].replace('show interface ', '')
            index = interface_names.index(interface_name)
            print(f'{index}: {interface_name}')
            if index < 0:
                continue
            for variable in variables:
                payload = GenerateFlashProbePayload(device, parser, interfaces[index], variable)
                inputQueue.put(payload)
    db.Logout()
    multi_thread_info = configFile['Multi Thread Info']
    maxThread = multi_thread_info['ThreadCount'] + 1
    apps = []
    for i in range(1, maxThread):
        username = ''.join([multi_thread_info['Username'], f'{i:02}'])
        app = NetBrainIE(configFile['Url'], username, multi_thread_info['Password'])
        if not app.Login():
            PrintMessage('Failed to login with the name: ' + username, 'Error')
            app = None
            continue
        app.ApplyTenantAndDomain(configFile['Tenant Name'], configFile['Domain Name'])
        apps.append(app)
        t = threading.Thread(target=StartWorkerThread, args=(app,))
        t.daemon = True
        t.start()

    inputQueue.join()  # Block until all tasks are done

    for app in apps:
        if app.Logined:
            app.Logout()
    return True

def GetDeviceFilter():
    return {'subType': {'$in': [2, 2001]}}

def GetDeviceAlertCount(config, device_count):
    alert_percentage = config.get('Device-Alerted Percentage', None)
    if alert_percentage is None:
        device_alerted_total = config['Device-Alerted Total']
    else:
        device_alerted_total = device_count*len(config['Flash Probe Info Device Parser DB Template'])*alert_percentage
        device_alerted_total = int(device_alerted_total/100 + 0.5)
    return device_alerted_total

def WriteFlashProbeToDB(application: NetBrainIE, config):
    db = NetBrainDB(config['DB Info'])
    db.Login()
    #db.GetDatabase(config['Tenant Name'])
    #parsers = db.GetAll('Parsers', {'path':{'$regex': '.*InterfaceAM_.*'}, 'accessType': 4}, 'path', 1)
    db.GetDatabase(config['Domain Name'])
    devices = db.GetAll('Device', GetDeviceFilter(), 'name', 1)  # mgmtIP
    # devices = db.GetAll('Device', {})
    length = len(devices)
    PrintMessage(f'Total devices: {length}')
    application_info = {
        'tenantid': application.TenantID,
        'tenantname': application.TenantName.replace(' ', '_'),
        'domainid': application.DomainID,
        'domainname': application.DomainName,
        'userid': application.UserID,
        'username': application.Username
    }
    # user = {'id': application.UserID, 'name': application.Username}
    device_alerted_total = GetDeviceAlertCount(config, length)
    interface_parser_total = config['Interface-Parser Total'] + 1
    count = total = total_task = 0
    for device in devices:
        # if '392' not in device['name']:
        #     continue
        count += 1
        flash_probes = []
        task_definitions = []
        monitor_variables = []
        no_alert = True if count > device_alerted_total else False
        # device parsers
        application_info['npv'] = device['_id']  # nodePathValue
        for item in config['Flash Probe Info Device Parser DB Template']:
            # if 'show_access_lists06' not in item['name']:
            #     continue
            flash_probe_info = PrepareFlashProbe_Device(item, device)
            flash_probe = GenerateFlashProbe_Device(device, flash_probe_info, application_info, no_alert, 1, monitor_variables)
            flash_probes.append(flash_probe)
            parser_name = flash_probe['ups'][0]['ppt']
            #monitor_variable = {}
            #monitor_variables.append(monitor_variable)
            task_definition_item_action = None
            for task_definition_item in task_definitions:
                task_definition_item_action = next((x for x in task_definition_item['taskDefinition']['actions'] if x.get("parser") and x["parser"] == parser_name), None)
            if task_definition_item_action is not None:
                task_definition_item['srcIdentifiers'].append(flash_probe['_id'])
                continue
            actions = []
            for automation_task in item['automation tasks']:
                action = {
                    'commandtype': automation_task['command type'],
                    'command': automation_task['command'],
                    'parser': automation_task['parser'],
                    'uploadoriginalfile': 0,
                    'devices': [device['name']],
                    'nodes': [],
                    'parameter': None,
                    'retrieveparameter': None,
                    'AdditionalData': None,
                }
                actions.append(action)
            task_definition = GenerateAutomationTaskDefinition(application_info, [flash_probe['_id']], actions, 3)
            task_definitions.append(task_definition)
        # write to DB
        length = len(flash_probes)
        result = db.InsertMany('AMFPInstance', flash_probes)
        if len(result) != length:
            PrintMessage('Write to collection AMFPInstance failed!!!!!', 'Error')
        else:
            total += length
            PrintMessage(f'{count}: {device["name"]}. Device Primary Flash Probes: {length}, total: {total}')
            length = len(monitor_variables)
            result = db.InsertMany('AMMonitorVariable', monitor_variables)
            if len(result) != length:
                PrintMessage('Write to collection AMMonitorVariable failed!!!!!', 'Error')
            else:
                PrintMessage(f'{count}: {device["name"]}. AM Monitor Variable: {length}.')
            length = len(task_definitions)
            result = db.InsertMany('AutomationTaskDefinition', task_definitions)
            if len(result) != length:
                PrintMessage('Write to collection AutomationTaskDefinition failed!!!!!', 'Error')
            else:
                total_task += length
                PrintMessage(f'{count}: {device["name"]}. Automation Task Definition: {length}, total: {total_task}')
        flash_probes.clear()
        task_definitions.clear()
        if len(config.get('Flash Probe Info Interface Parser DB Template', [])) <= 0:
            continue
        # 79 interface parsers
        device_interfaces = db.GetAll('Interface', {'devId': device['_id']})
        for index in range(1, interface_parser_total):
            device_flash_probe_ids = []
            for item in config['Flash Probe Info Interface Parser DB Template']:
                flash_probe_info = PrepareFlashProbe_Interfaces(item, str(index))
                interface = flash_probe_info['interface']
                device_interface = next((item for item in device_interfaces if item["name"] == interface), None)
                if device_interface is None:
                    continue
                # no_alert = True if index % 2 == 0 else False
                flash_probe = GenerateFlashProbe_Interfaces(device, device_interface, flash_probe_info, application_info, no_alert)
                #result = db.InsertOne('AMFPInstance', flash_probe)
                flash_probes.append(flash_probe)
                device_flash_probe_ids.append(flash_probe['_id'])
            #print(f'interface: {index}')
            action = {
                'commandtype': 15,
                'command': f'show interface {interface}',
                'parser': flash_probe_info['variables'][0]['interface variables'][0]['parser path'],
                'uploadoriginalfile': 0,
                'devices': [device['name']],
                'nodes': [],
                'parameter': None,
                'retrieveparameter': None,
                'AdditionalData': None,
            }
            if len(device_flash_probe_ids) > 0:
                task_definition = GenerateAutomationTaskDefinition(application_info, device_flash_probe_ids, [action])
                task_definitions.append(task_definition)
        length = len(flash_probes)
        if length <= 0:
            PrintMessage(f'{count}: {device["name"]}. Interface Flash Probes: {length}, total: {total}', 'Warning')
            continue
        #result = db.UpsertMany('AMFPInstance', {'nodePathValue': device['_id'], 'name':{'$regex':'InterfaceAM_'}}, flash_probes)
        where = {'nodePathValue': device['_id'], 'intfPathValue': interface, 'name':{'$regex':'InterfaceAM_'}}
        if db.Count('AMFPInstance', where) > 0:
            result = db.UpsertMany('AMFPInstance', ['nodePathValue', 'intfPathValue', 'name'], flash_probes)
        else:
            result = db.InsertMany('AMFPInstance', flash_probes)
        if len(result) != length:
            PrintMessage('Write to collection AMFPInstance failed!!!!!', 'Error')
            continue
        total += length
        PrintMessage(f'{count}: {device["name"]}. Interface Flash Probes: {length}, total: {total}',
                     'Warning' if length < (interface_parser_total-1)*56 else 'Info')
        length = len(task_definitions)
        if length <= 0:
            PrintMessage(f'{count}: {device["name"]}. Automation Task Definition: {length}, total: {total_task}', 'Warning')
            continue
        # where = {'taskDefinition.domainname': application_info['domainname'], 'taskDefinition.actions.parser': {'$regex': 'InterfaceAM_'},
        #          'taskDefinition.actions.actions.devices': [device['name']]}
        # if db.Count('AutomationTaskDefinition', where) > 0:
        #     result = db.UpsertMany('AutomationTaskDefinition', ['taskDefinition.domainname', 'taskDefinition.actions.parser', 'taskDefinition.actions.actions.devices'], task_definitions)
        # else:
        #     result = db.InsertMany('AutomationTaskDefinition', task_definitions)
        result = db.InsertMany('AutomationTaskDefinition', task_definitions)
        if len(result) != length:
            PrintMessage('Write to collection AutomationTaskDefinition failed!!!!!', 'Error')
        else:
            total_task += length
            PrintMessage(f'{count}: {device["name"]}. Automation Task Definition: {length}, total: {total_task}',
                         'Warning' if length < interface_parser_total-1 else 'Info')
    db.Logout()
    return (total, total_task)

def PrepareFlashProbe_Interfaces(flash_probe_template: dict, index: str):
    flash_probe_info = {
        'name': flash_probe_template['name'].replace('{index}', index),
        'display name': flash_probe_template['display name'].replace('{index}', index),
        'description': flash_probe_template['description'].replace('{index}', index),
        'interface': flash_probe_template['interface'].replace('{index}', index),
        'variables': [],
        'define alert rules': flash_probe_template['define alert rules'].copy(),
        'frequency': flash_probe_template['frequency'].copy()
    }
    for variable in flash_probe_template['variables']:
        item = {
            'interface variables': [],
            'compounds variables': variable['compounds variables'].copy(),
        }
        for interface_variable in variable['interface variables']:
            value = interface_variable.copy()
            value['parser path'] = interface_variable['parser path'].replace('{index}', index)
            item['interface variables'].append(value)
        flash_probe_info['variables'].append(item)
    flash_probe_info['define alert rules']['define alert message'] = flash_probe_template['define alert rules']['define alert message'].replace('{index}', index)
    return flash_probe_info

def GenerateFlashProbe_Interfaces(device, interface, flash_probe_info, application_info, no_alert):
    operator = {
        'int': ['Violates GB Rule', 'Equals to', 'Does not Equal to', 'Is none', 'Is not none', 'Contains', 'Does not contain',
                'Greater than', 'Less than', 'Greater than or Equals to', 'Less than or Equals to', 'Range'],
        'string': ['Violates GB Rule', 'Equals to', 'Does not Equal to', 'Is none', 'Is not none', 'Contains', 'Does not contain']
    }
    for variable in flash_probe_info['variables']:
        interface_variables = variable['interface variables']
        compounds = variable['compounds variables']
        variables = []
        used_parsers = []
        for interface_variable in interface_variables:
            for parser_variable in interface_variable['parser variables']:
                full_name = parser_variable['full name']
                alias = full_name.replace('$', '').split('.')
                parser = interface_variable['parser path']
                if parser not in used_parsers:
                    used_parsers.append({'ppt': parser,  # parserPath
                                         # 'pt': 1,
                                         'mvs': []})  #monitorVars
                item = {
                    'ppt': parser,  # parserPath
                    'pt': 1,  # parserType: interface parser
                    'fn': full_name,  # fullName
                    'a': alias[-1],  # alias
                    's': 2,  # scope
                    't': 1,  # type
                    'dt': parser_variable['type'],  # dataType
                    'vt': 1  # varType
                }
                variables.append(item)
        for compound_variable in compounds:
            item = {
                'pt': 0,
                'fn': CreateGuid(),  # fullName
                'a': compound_variable['full name'],  # alias
                's': 2, # scope
                't': 2,  # type
                'dt': compound_variable['type'],  # dataType
                'vt': 0,
                'e': compound_variable['expression']  # expression
            }
            variables.append(item)
        define_alert_rules = flash_probe_info['define alert rules']
        rules = {
            'isvt': define_alert_rules['verify table'],  # isVerifyTable
            'c': [],  # conditions
            'e': define_alert_rules['boolean expression']  # expression
        }
        for condition in define_alert_rules['rules']:
            if no_alert:
                if condition['operator'].startswith('Does not Equal'):
                    condition['operator'] = 'Is none'
                    condition['value'] = None
            item = {
                'o1': condition['variable'],  # operand1
                'o': operator[condition['type']].index(condition['operator']),  # operator
                'o2': {} if condition['value'] is None else {'ruleParam': condition['value']}  # operand2
            }
            rules['c'].append(item)  # conditions
        create_time = datetime.utcnow()

        flash_probe_old = {
            '_id': CreateGuid(),
            'nodePathSchema': 'Legacy',
            'nodePathValue': device['_id'],
            'intfPathSchema': 'intfs._id',
            'intfPathValue': interface['_id'],
            'name': flash_probe_info['name'],
            'alertSrc': 'NetBrain',
            'nodeName': device['name'],
            'intfName': interface['name'],
            'displayName': flash_probe_info['display name'],
            'desc': flash_probe_info['description'],
            'type': 1,  #
            'category': 1,  #
            'createSrc':{
                'type': 'Manually',
                'name': 'Manually'
            },
            'variables': variables,
            'usedParsers': used_parsers,
            'rule': rules,
            'alertLevel': 2,
            'alertMsg': {
                'originalExpression': define_alert_rules['define alert message'],
                'expression': define_alert_rules['define alert message'],
                'variables': []
            },
            'triggeredBy': [],
            'frequency': {
                'type': flash_probe_info['frequency']['type'],
                'baseMultiple': flash_probe_info['frequency']['baseMultiple'],
                'timer': None,
                'modifyUserId': application_info['userid'],
                'modifyUserName': application_info['username'],
                'modifyTime': create_time
            },
            'errorTrigger': {
                'enableEmailNotify': False,
                'emails': None,
                'ticketEVTId': None,
                'ticketEVTName': None,
                'enableTicketEVT': False
            },
            'enabled': True,
            'isDeleted': False,
            'createInfo':{
                'userId': application_info['userid'],
                'userName': application_info['username'],
                'dateTime': create_time
            },
            'operateInfo': {
                'opUserId': application_info['userid'],
                'opUser': application_info['username'],
                'opTime': create_time
            }
        }

        flash_probe = {
            '_id': CreateGuid(),
            'nps': 'Legacy',  # nodePathSchema
            'npv': device['_id'],  # nodePathValue
            'ips': 'intfs._id',  # intfPathSchema
            'ipv': interface['_id'],  # intfPathValue
            'n': flash_probe_info['name'],  # name
            'as': 'NetBrain',  # alertSrc
            'nn': device['name'],  # nodeName
            'in': interface['name'],  # intfName
            'dn': flash_probe_info['display name'],  # displayName
            'ds': flash_probe_info['description'],  # desc
            't': 1,  # type
            'c': 1,  #category
            'cs': {  # createSrc
                't': 'Manually',  # type
                'n': 'Manually'  # name
            },
            'vs': variables,  # variables
            'ups': used_parsers,  # usedParsers
            'rl': rules,  # rule
            'al': 2,  # alertLevel
            'am': {  # alertMsg
                'oe': define_alert_rules['define alert message'],  # originalExpression
                'e': define_alert_rules['define alert message'],  # expression
                'vs': []  # variables
            },
            'tb': [],  # triggeredBy
            'f': {  # frequency
                't': flash_probe_info['frequency']['type'],  # type
                'bm': flash_probe_info['frequency']['baseMultiple'],  # baseMultiple
                'tr': None,  # timer
                'mid': application_info['userid'],  # modifyUserId
                'md': application_info['username'],  # modifyUserName
                'mt': create_time  # modifyTime
            },
            'et': {  # errorTrigger
                'ee': False,  # enableEmailNotify
                'es': None,  # emails
                'tid': None,  # ticketEVTId
                'tn': None,  # ticketEVTName
                'et': False  # enableTicketEVT
            },
            'ise': True,  # enabled
            'isd': False,  # isDeleted
            'ci': {  # createInfo
                'userId': application_info['userid'],
                'userName': application_info['username'],
                'dateTime': create_time
            },
            'operateInfo': {
                'opUserId': application_info['userid'],
                'opUser': application_info['username'],
                'opTime': create_time
            }
        }
    return flash_probe

def get_primary_id(flash_probe):
    primary_key = flash_probe["nps"] + \
                  flash_probe["npv"] + \
                  flash_probe["n"].lower() + \
                  flash_probe["as"].lower()
    return NBCrypto.spooky_hash(primary_key)

def generate_probe_name(device, probe_name):
    #name = '_'.join([device['name'], probe_name])
    name = NetBrainUtils.ReplaceSpecialCharacters(probe_name)
    return name

def PrepareFlashProbe_Device(flash_probe_template: dict, device):
    # name = '_'.join([device['name'], flash_probe_template['name']])
    # name = NetBrainUtils.ReplaceSpecialCharacters(name)
    name = generate_probe_name(device, flash_probe_template['name'])
    flash_probe_info = {
        'name': name,
        'display name': name,
        'description': name,
        'variables': [],
        'define alert rules': flash_probe_template['define alert rules'].copy(),
        'frequency': flash_probe_template['frequency'].copy()
    }
    for variable in flash_probe_template['variables']:
        item = {
            'device variables': [],
            'compounds variables': variable['compounds variables'].copy(),
        }
        for device_variable in variable['device variables']:
            value = device_variable.copy()
            value['parser path'] = device_variable['parser path']
            item['device variables'].append(value)
        flash_probe_info['variables'].append(item)
    #flash_probe_info['define alert rules']['define alert message'] = flash_probe_template['define alert rules']['define alert message'].replace('{index}', index)
    return flash_probe_info

def GenerateFlashProbe_Device(device, flash_probe_info, application_info, no_alert, flash_probe_type=1, am_monitor_variables=[]):
    # flash_probe_type： primary probe=1, secondary probe=2
    operator = {
        'int': ['Violates GB Rule', 'Equals to', 'Does not Equal to', 'Is none', 'Is not none', 'Contains', 'Does not contain',
                'Greater than', 'Less than', 'Greater than or Equals to', 'Less than or Equals to', 'Range'],
        'string': ['Violates GB Rule', 'Equals to', 'Does not Equal to', 'Is none', 'Is not none', 'Contains', 'Does not contain']
    }
    parser_types = ['', 'CLI Command', 'Configuration', 'SNMPGet', 'SNMPWalk', 'SNMPTable', 'API', ]
    define_alert_rules = flash_probe_info['define alert rules']
    create_time = datetime.utcnow()
    for variable in flash_probe_info['variables']:
        #flash_probe_id = CreateGuid().replace('-', '')
        probe_info = {
            'nps': 'Legacy',  # nodePathSchema
            'npv': device['_id'],  # nodePathValue
            'n': flash_probe_info['name'],  # name
            'as': 'NetBrain'  # alertSrc
        }
        flash_probe_id = get_primary_id(probe_info)
        device_variables = variable['device variables']
        compounds = variable['compounds variables']
        variables = []
        used_parsers = []
        for device_variable in device_variables:
            parser_type = device_variable.get('parser type', 'CLI Command')
            if parser_type in parser_types:
                parser_type = parser_types.index(parser_type)
            else:
                parser_type = 1
            for parser_variable in device_variable['parser variables']:
                full_name = parser_variable['full name']
                cap_name = full_name.split('.')[-1]
                alias = cap_name.replace('$', '')
                parser = device_variable['parser path']
                #data_type = 1
                #var_type = 1
                var_type = parser_variable['var type']
                monitor_variables = []
                if define_alert_rules['verify table']:
                    alert_variable = define_alert_rules['rules'][0]
                    save_monitor_variable = alert_variable['save monitor variable']
                    if save_monitor_variable:
                        item = alert_variable['variable'].split('.')[-1]
                        fn = '.$'.join([full_name, item])
                        monitor_variable = {
                            'fn': fn,  # fullName
                            'cn': alert_variable['variable'],  # CapName
                            'ism': True,
                            'dn': item,
                            'u': None,
                            'dt': alert_variable['type'],  # dataType
                            'vt': 1
                        }
                        monitor_variables.append(monitor_variable)
                        monitor_variable = {
                            'fn': full_name,  # fullName
                            'cn': cap_name,  # CapName
                            'ism': False,
                            'dn': cap_name,
                            'u': None,
                            'dt': parser_variable['data type'],  # dataType
                            'vt': var_type  # varType
                        }
                        am_monitor_variable = {
                            '_id': CreateGuid(),
                            'nodePathSchema': 'Legacy',
                            'nodePathValue': device['_id'],
                            'nodeName': device['name'],
                            'parserPath': parser,
                            'variable': cap_name.replace('$', ''),
                            'dataType': parser_variable['data type'],
                            'varType': parser_variable['var type'],
                            'columns': [item],
                            'fpIds': [flash_probe_id],
                            'operateInfo': {
                                'opUser': application_info['username'],
                                'opTime': create_time
                            }
                        }
                        for am_monitor_variable_item in am_monitor_variables:
                            if am_monitor_variable_item['parserPath'] == am_monitor_variable['parserPath']:
                                if am_monitor_variable_item['variable'] == am_monitor_variable['variable']:
                                    if item in am_monitor_variable_item['columns']:
                                        am_monitor_variable_item['fpIds'].append(flash_probe_id)
                                    else:
                                        am_monitor_variable_item['columns'].append(item)
                                        am_monitor_variable_item['fpIds'].append(flash_probe_id)
                                    am_monitor_variable = None
                                    break
                else:
                    save_monitor_variable = parser_variable['save monitor variable']
                    if save_monitor_variable:
                        monitor_variable = {
                            'fn': full_name,  # fullName
                            'cn': cap_name if cap_name.startswith('$') else '$' + cap_name,  # CapName
                            'ism': True,
                            'dn': cap_name,
                            'u': None,
                            'dt': parser_variable['data type'],  # dataType
                            'vt': var_type  # varType
                        }
                        am_monitor_variable = {
                            '_id': CreateGuid(),
                            'nodePathSchema': 'Legacy',
                            'nodePathValue': device['_id'],
                            'nodeName': device['name'],
                            'parserPath': parser,
                            'variable': cap_name.replace('$', ''),
                            'dataType': parser_variable['data type'],
                            'varType': parser_variable['var type'],
                            'fpIds': [flash_probe_id],
                            'operateInfo': {
                                'opUser': application_info['username'],
                                'opTime': create_time
                            }
                        }
                        for am_monitor_variable_item in am_monitor_variables:
                            if am_monitor_variable_item['parserPath'] == am_monitor_variable['parserPath']:
                                if am_monitor_variable_item['variable'] == am_monitor_variable['variable']:
                                    am_monitor_variable_item['fpIds'].append(flash_probe_id)
                                    am_monitor_variable = None
                                    break
                if save_monitor_variable:
                    monitor_variables.append(monitor_variable)
                    if am_monitor_variable is not None:
                        am_monitor_variables.append(am_monitor_variable)
                if parser not in used_parsers:
                    used_parsers.append({'ppt': parser,  # parserPath
                                         #'pt': parser_type,
                                         'mvs': monitor_variables})  #monitorVars
                item = {
                    'ppt': parser,  # parserPath
                    'pt': parser_type,  # parserType: interface parser
                    'fn': full_name,  # fullName
                    'cn': cap_name,  # CapName
                    'a': alias,  # alias
                    's': 1,  # scope
                    't': 1,  # type
                    'dt': parser_variable['data type'],  # dataType
                    'vt': var_type  # varType
                }
                variables.append(item)
        for compound_variable in compounds:
            item = {
                'pt': 0,
                'fn': CreateGuid(),  # fullName
                'a': compound_variable['full name'],  # alias
                's': 1, # scope
                't': 2,  # type
                'dt': compound_variable['type'],  # dataType
                'vt': 0,
                'e': compound_variable['expression']  # expression
            }
            variables.append(item)
        rules = {
            'isvt': define_alert_rules['verify table'],  # isVerifyTable
            'c': [],  # conditions
            'e': define_alert_rules['boolean expression']  # expression
        }
        for condition in define_alert_rules['rules']:
            if no_alert:
                if condition['operator'].startswith('Does not Equal'):
                    condition['operator'] = 'Equals to'
                    condition['value'] = 'Equals to yyyyyy'
            item = {
                'o1': condition['variable'],  # operand1
                'o': operator[condition['type']].index(condition['operator']),  # operator
                'o2': {} if condition['value'] is None else {'ruleParam': condition['value']}  # operand2
            }
            rules['c'].append(item)  # conditions
        name = '_'.join([device['name'], define_alert_rules['define alert message']])
        name = NetBrainUtils.ReplaceSpecialCharacters(name)
        flash_probe = {
            '_id': flash_probe_id,
            'nps': 'Legacy',  # nodePathSchema
            'npv': device['_id'],  # nodePathValue
            'ips': None,  # intfPathSchema
            'ipv': None,  # intfPathValue
            'n': flash_probe_info['name'],  # name
            'as': 'NetBrain',  # alertSrc
            'nn': device['name'],  # nodeName
            'intfs': None,  # intfName
            'dn': flash_probe_info['display name'],  # displayName
            'ds': flash_probe_info['description'],  # desc
            't': flash_probe_type,  # type
            'c': 1,  #category
            'cs': {  # createSrc
                't': 'Manually',  # type
                'n': 'Manually'  # name
            },
            'vs': variables,  # variables
            'ups': used_parsers,  # usedParsers
            'rl': rules,  # rule
            'al': 1,  # alertLevel
            'am': {  # alertMsg
                'oe': name,  # originalExpression
                'e': name,  # expression
                'vs': []  # variables
            },
            'tb': [],  # triggeredBy
            'f': {  # frequency
                't': flash_probe_info['frequency']['type'],  # type
                'bm': flash_probe_info['frequency']['baseMultiple'],  # baseMultiple
                'tr': None,  # timer
                'mid': application_info['userid'],  # modifyUserId
                'mn': application_info['username'],  # modifyUserName
                'mt': create_time  # modifyTime
            },
            'et': {  # errorTrigger
                'ee': False,  # enableEmailNotify
                'es': None,  # emails
                'tid': None,  # ticketEVTId
                'tn': None,  # ticketEVTName
                'et': False  # enableTicketEVT
            },
            'ise': True,  # enabled
            'isd': False,  # isDeleted
            'ci': {  # createInfo
                'userId': application_info['userid'],
                'userName': application_info['username'],
                'dateTime': create_time
            },
            'operateInfo': {
                'opUserId': application_info['userid'],
                'opUser': application_info['username'],
                'opTime': create_time
            }
        }
    return flash_probe

def WriteAutomationTaskDefinitionToDB(application: NetBrainIE, config):
    application_info = {
        'tenantid': application.TenantID,
        'tenantname': application.TenantName,
        'domainid': application.DomainID,
        'domainname': application.DomainName,
        'userid': application.UserID,
        'username': application.Username
    }
    db = NetBrainDB(config['DB Info'])
    db.Login()
    db.GetDatabase(config['Domain Name'])
    task_definition = GenerateAutomationTaskDefinition(application_info)
    #automation_task_def =
    return True

def GenerateAutomationTaskDefinition(application_info, flash_probe_ids: list, actions, task_category=3,
                                     schedule={'type':1,'basemultiple':1}):
    # enum EnumAmTaskCategory
    # {
    #     enum_AM_CLI = 1,
    #     enum_AM_NI,
    #     enum_AM_PrimaryAlertProbe ,
    #     enum_AM_BuiltInTimerProbe ,
    #     enum_AM_UserDefinedTimerProbe ,
    #     enum_AM_ConfigChangeProbe ,
    #     enum_AM_SecondaryProbe
    # };
    # Task Type:
    # -1: enumTkType_Unknow = -1,
    # 0: enumTkType_Dtg,                //schedule Qapp, SDVT
    # 1: enumTkType_DLA,                //direct live access
    # 2: enumTkType_Emulate,            //Emulate task.
    # 3: enumTkType_AMPrimayProbe,      //adaptive monitor task
    # 4: enumTkType_AMSecondaryProbe,   //secondary probe
    # 5 :enumTkType_AMTimerProbe,       //time probe
    # 6: enumTkType_AMTriggered_NI,     //Triggered NI/CLI.
    # 7: enumTkType_AMTriggered_CLI,    // Triggered NI/CLI.
    # 8: enumTkType_AMTimer_NI,         // Schedule NI/CLI.
    # 9: enumTkType_AMTimer_CLI,        // Schedule NI/CLI.
    # 10: enumTkType_AMConfigProbe,     // config flash probe.
    #
    task_id = CreateGuid()
    task_definition = {
        '_id': task_id,
        'type': 4 if task_category == 7 else 3,
        'domainid': application_info['domainid'],
        'domainname': application_info['domainname'],
        'tenantid': application_info['tenantid'],
        'tenantname': application_info['tenantname'],
        'version': 200,
        'nolive': False,
        'issavetode': 0,
        'issupportcounting': False,
        'isondemand': False,
        'iscalculategoldenbaseline': True,
        'issavemonitorvariable': True,
        'usecachedata': True,
        'priority': 1 if task_category == 7 else 2,
        'schedule': {
            'type': schedule['type'],
            'begintime': None,
            'endtime': None,
            'duration': 0,
            'frequency': 0,
            'retrievecount': 0,
            'basefrequencymultiple': schedule['basemultiple'],
        },
        'actions': actions,
        'userdata': None,
        'AdditionalData': None
    }
    automation_task_definition = {
        '_id': task_id,
        'category': task_category,
        'srcIdentifiers': flash_probe_ids,
        'npv': application_info['npv'],
        'enabled': True,
        'taskDefinition': task_definition,
        'operateInfo':{
            'opUserId': application_info['userid'],
            'opUser': application_info['username'],
            'opTime': datetime.utcnow()
        }
    }
    return automation_task_definition

def RemoveParsersQualify(app, parsers, parser_category=None):
    for parser in parsers:
        app.RemoveParsersQualify(parser, parser_category)
    return True

def VerifyFlashProbeResult(configFile=''):
    configFile = ConfigFile if configFile == '' else configFile
    config = NetBrainUtils.GetConfig(configFile)
    if len(config) == 0:
        PrintMessage(''.join([CurrentMethodName(), 'Failed to load the configuration file: ', configFile]), 'Error')
        return False
    if config.get('Multi Thread Info', {}).get('ThreadCount', 1) > 1:
         return VerifyFlashProbeResult_multithread(config)

    db = NetBrainDB(config['DB Info'])
    db.Login()
    db.GetDatabase(config['Domain Name'])
    # flash_probe_history = db.GetDistinct('FlashProbeHistory_2020_11', 'probeId', {})
    # flash_probe_history_ids = [history['probeId'] for history in flash_probe_history]
    flash_probes = db.Database['AMFPInstance'].find({}, no_cursor_timeout=True)
    total = index = first_run_times = 0
    PrintMessage('Start to verify flash probes.')
    verify_config = config['Verify FlashProbe']
    min_inteval = verify_config['Run Schedule'] * 60 * 0.9
    max_inteval = verify_config['Run Schedule'] * 60 * 1.2
    for flash_probe in flash_probes:
        if ' Unreachable' in flash_probe['n'] or 'Configuration Change' in flash_probe['n'] or ' Frequency' in flash_probe['n']:
            continue
        for day in verify_config['Day']:
            VerifyFlashProbeResultByDay(db, verify_config['Collection'], flash_probe, day, min_inteval, max_inteval)
        continue
        count = 0
        flash_probe_history = db.GetAll(verify_config['Collection'], {'probeId': flash_probe['_id'], 'day': verify_config['Day']}, None)
        # for history in flash_probe_history:
        #     count += len(history['ai'])
        count = len(flash_probe_history)
        #count = db.Count('FlashProbeHistory_2020_12', {'probeId': flash_probe['_id']})
        if count <= 0:
            if flash_probe['t'] == 1:
                PrintMessage(''.join([flash_probe['nn'], ' - ', flash_probe['n'], ': never run. probe id is: ',
                                      flash_probe['_id']]), 'Error')
        else:
            hts = flash_probe_history[0]['ht']
            current = -1
            run_times = len(hts)
            if first_run_times <= 0:
                first_run_times = run_times
            diff = abs(run_times - first_run_times)
            if diff > 2:
                PrintMessage(''.join([flash_probe['nn'], ' - ', flash_probe['n'], ', probe id is: ', flash_probe['_id'],
                                      '. run ', str(run_times), ' times. (first run times is ', str(first_run_times),
                                      '.)']), 'Error')
            # else:
            #     PrintMessage(''.join([flash_probe['nn'], ' - ', flash_probe['n'], ', probe id is: ', flash_probe['_id'],
            #                           '. run ', str(run_times), ' times.']))
            for ht in hts:
                if current == -1:
                    current = ht
                    continue
                diff = ht - current
                if diff <= min_inteval or diff >= max_inteval:
                    PrintMessage(''.join([flash_probe['n'], ' (probe id=', flash_probe['_id'], ')', ':\trun time is ',
                                          str(ht), ' seconds (',
                                          strftime('%H:%M:%S', gmtime(ht)), '), previous run time is ', str(current),
                                          ' seconds (', strftime('%H:%M:%S', gmtime(current)), '), the interval is ',
                                          str(diff), ' seconds (', strftime('%H:%M:%S', gmtime(diff)), '). ']), 'Error')
                current = ht
        index += 1
        if index >= 5000:
            total += index
            index = 0
            PrintMessage(f'Verified {total} flash probes.')
    return True

def VerifyFlashProbeResultByDay(db, collection_name, flash_probe, day, min_inteval, max_inteval):
    index = count = first_run_times = total = 0
    #PrintMessage(f'day={day}')
    flash_probe_history = db.GetAll(collection_name, {'probeId': flash_probe['_id'], 'day': day}, None)
    # for history in flash_probe_history:
    #     count += len(history['ai'])
    count = len(flash_probe_history)
    # count = db.Count('FlashProbeHistory_2020_12', {'probeId': flash_probe['_id']})
    if count <= 0:
        if flash_probe['t'] == 1:
            PrintMessage(''.join([flash_probe['nn'], ' - ', flash_probe['n'], ': never run on the day ', str(day),
                                  '. probe id is: ', flash_probe['_id']]), 'Error')
    else:
        hts = flash_probe_history[0]['ht']
        current = -1
        run_times = len(hts)
        if first_run_times <= 0:
            first_run_times = run_times
        diff = abs(run_times - first_run_times)
        if diff > 2:
            PrintMessage(''.join([flash_probe['nn'], ' - ', flash_probe['n'], ', probe id is: ', flash_probe['_id'],
                                  '. run ', str(run_times), ' times. (Number of run of the first probe is ',
                                  str(first_run_times), '.) day=', str(day)]), 'Error')
        # else:
        #     PrintMessage(''.join([flash_probe['nn'], ' - ', flash_probe['n'], ', probe id is: ', flash_probe['_id'],
        #                           '. run ', str(run_times), ' times.']))
        for ht in hts:
            if current == -1:
                current = ht
                continue
            diff = ht - current
            if diff <= min_inteval or diff >= max_inteval:
                PrintMessage(''.join(['day=', str(day), '. ', flash_probe['n'], ' (probe id=', flash_probe['_id'], ')',
                                      ':\trun time is ', str(ht), ' seconds (',
                                      strftime('%H:%M:%S', gmtime(ht)), '), previous run time is ', str(current),
                                      ' seconds (', strftime('%H:%M:%S', gmtime(current)), '), the interval is ',
                                      str(diff), ' seconds (', strftime('%H:%M:%S', gmtime(diff)), '). ']), 'Error')
            current = ht
    index += 1
    if index >= 5000:
        total += index
        index = 0
        PrintMessage(f'Verified {total} flash probes.')
    return True

def WriteSecondaryFlashProbeToDB(application: NetBrainIE, config, primary_probe_count=0, primary_task_count=0):
    db = NetBrainDB(config['DB Info'])
    db.Login()
    db.GetDatabase(config['Domain Name'])
    collections = db.GetCollectionNames(config['Domain Name'])
    if 'AMTriggerRelationship' not in collections:
        db.CreateCollection('AMTriggerRelationship')

    devices = db.GetAll('Device', {'subType': {'$in': [2, 2001]}}, 'name', 1)  # mgmtIP
    length = len(devices)
    PrintMessage(f'Total devices: {length}')
    application_info = {
        'tenantid': application.TenantID,
        'tenantname': application.TenantName.replace(' ', '_'),
        'domainid': application.DomainID,
        'domainname': application.DomainName,
        'userid': application.UserID,
        'username': application.Username
    }
    # device_alerted_total = config['Device-Alerted Total']
    alert_percentage = config.get('Device-Alerted Percentage', None)
    if alert_percentage is None:
        device_alerted_total = config['Device-Alerted Total']
    else:
        device_alerted_total = length * len(config['Flash Probe Info Device Parser DB Template']) * alert_percentage
        device_alerted_total = int(device_alerted_total/100 + 0.5)
    total = primary_probe_count
    total_task = primary_task_count
    count = total_relation = 0
    for device in devices:
        count += 1
        flash_probes = []
        task_definitions = []
        trigger_relations = []
        monitor_variables = []
        no_alert = False
        # device parsers
        primary_probes = db.GetAll('AMFPInstance', {'npv': device['_id'], 't': 1,
                                                    'operateInfo.opUser': application.Username}, 'ci.dateTime', 1)
        application_info['npv'] = device['_id']  # nodePathValue
        for item in config['Secondary Flash Probe Info Device Parser DB Template']:
            flash_probe_info = PrepareFlashProbe_Device(item, device)
            second_probe = GenerateFlashProbe_Device(device, flash_probe_info, application_info, no_alert, 2, monitor_variables)
            for primary_probe in primary_probes:
                flash_probe = deepcopy(second_probe)  # second_probe.copy()
                #flash_probe['tb'] = second_probe['tb'][:]
                id = CreateGuid().replace('-', '')
                name = '_'.join([flash_probe['n'], primary_probe['n']])
                # if primary_probe['n'] == 'ustta000000_dec_snmp03':
                #     a = 1
                flash_probe['_id'] = id
                flash_probe['n'] = flash_probe['dn'] = flash_probe['ds'] = name
                flash_probe['am']['oe'] = flash_probe['am']['e'] = name + '_alert'
                flash_probe['tb'].append(primary_probe['_id'])
                flash_probes.append(flash_probe)
                parser_name = flash_probe['ups'][0]['ppt']
                actions = []
                for automation_task in item['automation tasks']:
                    action = {
                        'commandtype': automation_task['command type'],
                        'command': automation_task['command'],
                        'parser': automation_task['parser'],
                        'uploadoriginalfile': 0,
                        'devices': [device['name']],
                        'nodes': [],
                        'parameter': None,
                        'retrieveparameter': None,
                        'AdditionalData': None,
                    }
                    actions.append(action)
                task_definition = GenerateAutomationTaskDefinition(application_info, [flash_probe['_id']], actions, 7)
                task_definitions.append(task_definition)
                trigger_relation = {
                    '_id': CreateGuid().replace('-', ''),
                    't': 1,
                    'src': primary_probe['_id'],
                    'npv': device['_id'],
                    'dest': id,
                    'dt': task_definition['_id'],
                    'tr':{
                        'rt': 1,
                        'rc': None,
                        's': {'ise': False, 'tss': None}
                    },
                    'ise': True,
                    'operateInfo':{
                        'opUserId': application_info['userid'],
                        'opUser': application_info['username'],
                        'opTime': datetime.utcnow()
                    }
                }
                trigger_relations.append(trigger_relation)
        # write to DB
        length = len(flash_probes)
        result = db.InsertMany('AMFPInstance', flash_probes)
        if len(result) != length:
            PrintMessage('Write to collection AMFPInstance failed!!!!!', 'Error')
        else:
            total += length
            PrintMessage(f'{count}: {device["name"]}. Device Secondary Flash Probes: {length}, total: {total}')
            length = len(monitor_variables)
            result = db.InsertMany('AMMonitorVariable', monitor_variables)
            if len(result) != length:
                PrintMessage('Write to collection AMMonitorVariable failed!!!!!', 'Error')
            else:
                PrintMessage(f'{count}: {device["name"]}. AM Monitor Variable: {length}.')
            length = len(task_definitions)
            result = db.InsertMany('AutomationTaskDefinition', task_definitions)
            if len(result) != length:
                PrintMessage('Write to collection AutomationTaskDefinition failed!!!!!', 'Error')
            else:
                total_task += length
                PrintMessage(f'{count}: {device["name"]}. Automation Task Definition: {length}, total: {total_task}')
            length = len(trigger_relations)
            result = db.InsertMany('AMTriggerRelationship', trigger_relations)
            if len(result) != length:
                PrintMessage('Write to collection AMTriggerRelationship failed!!!!!', 'Error')
            else:
                total_relation += length
                PrintMessage(f'{count}: {device["name"]}. AM Trigger Relationship: {length}, total: {total_relation}')
        flash_probes.clear()
        task_definitions.clear()
        trigger_relations.clear()
    return True

def PrintMessage(message, level='Info'):
    NetBrainUtils.PrintMessage(message, level, logger)
    return True

def WriteFlashProbeToDB_multithread(application: NetBrainIE, config):
    multi_thread_info = config['Multi Thread Info']
    maxThread = multi_thread_info['ThreadCount'] + 1

    db = NetBrainDB(config['DB Info'])
    db.Login()
    db.GetDatabase(config['Domain Name'])
    # devices = db.GetAll('Device', {'subType': {'$in': [2, 2001]}}, 'name', 1)  # mgmtIP
    # length = len(devices)
    # PrintMessage(f'Total devices: {length}')
    application_info = {
        'tenantid': application.TenantID,
        'tenantname': application.TenantName.replace(' ', '_'),
        'domainid': application.DomainID,
        'domainname': application.DomainName,
        'userid': application.UserID,
        'username': application.Username
    }
    length = db.Count('Device', {'subType': {'$in': [2, 2001]}})
    PrintMessage(f'Total devices: {length}')
    alert_percentage = config.get('Device-Alerted Percentage', None)
    if alert_percentage is None:
        device_alerted_total = config['Device-Alerted Total']
    else:
        device_alerted_total = length * len(config['Flash Probe Info Device Parser DB Template']) * alert_percentage
        device_alerted_total = int(device_alerted_total / 100 + 0.5)
    multi_fs = config.get('Multi FS', None)
    if multi_fs is None:
        count = 0
        devices = db.Database['Device'].find({'subType': {'$in': [2, 2001]}}).sort('name', 1)
        for device in devices:
            count += 1
            param = {
                'DB': db,
                'Device': device,
                'No Alert': True if count > device_alerted_total else False,
                'Application Info': application_info,
                'Device Parsers': config['Flash Probe Info Device Parser DB Template']
            }
            inputQueue.put(param)
    else:
        multi_fs_count = len(multi_fs)
        device_alerted_count_per_fs = int((device_alerted_total + multi_fs_count - 1) / multi_fs_count)
        for single_fs in multi_fs:
            device_group = db.GetOne('DeviceGroup', {'Name': single_fs['Device Group Name']})
            ids = device_group['StaticDevices']
            ids.extend(device_group['DynamicDevices'])
            devices = db.Database['Device'].find({'subType': {'$in': [2, 2001]}, '_id':{'$in': ids}}).sort('name', 1)
            #count = db.Count('Device', {'subType': {'$in': [2, 2001]}, '_id':{'$in': ids}})
            count = 0
            for device in devices:
                count += 1
                param = {
                    'DB': db,
                    'Device': device,
                    'No Alert': True if count > device_alerted_count_per_fs else False,
                    'Application Info': application_info,
                    'Device Parsers': config['Flash Probe Info Device Parser DB Template']
                }
                inputQueue.put(param)

    for i in range(1, maxThread):
        t = threading.Thread(target=StartWorkerThread, args=(application, 1))
        t.daemon = True
        t.start()

    inputQueue.join()  # Block until all tasks are done

    db.Logout()

    return True

def WriteSecondaryFlashProbeToDB_multithread(application: NetBrainIE, config):
    multi_thread_info = config['Multi Thread Info']
    maxThread = multi_thread_info['ThreadCount'] + 1

    db = NetBrainDB(config['DB Info'])
    db.Login()
    db.GetDatabase(config['Domain Name'])
    collections = db.GetCollectionNames(config['Domain Name'])
    if 'AMTriggerRelationship' not in collections:
        db.CreateCollection('AMTriggerRelationship')
    # devices = db.GetAll('Device', {'subType': {'$in': [2, 2001]}}, 'name', 1)  # mgmtIP
    # length = len(devices)
    # PrintMessage(f'Total devices: {length}')
    application_info = {
        'tenantid': application.TenantID,
        'tenantname': application.TenantName.replace(' ', '_'),
        'domainid': application.DomainID,
        'domainname': application.DomainName,
        'userid': application.UserID,
        'username': application.Username
    }
    length = db.Count('Device', {'subType': {'$in': [2, 2001]}})
    PrintMessage(f'Total devices: {length}')
    devices = db.Database['Device'].find({'subType': {'$in': [2, 2001]}}).sort('name', 1)
    count = 0
    for device in devices:
        count += 1
        param = {
            'DB': db,
            'Device': device,
            'Application Info': application_info,
            'Device Parsers': config['Secondary Flash Probe Info Device Parser DB Template']
        }
        inputQueue2.put(param)

    for i in range(1, maxThread):
        t = threading.Thread(target=StartWorkerThread, args=(application, 2))
        t.daemon = True
        t.start()

    inputQueue2.join()  # Block until all tasks are done

    db.Logout()

    return True

def VerifyFlashProbeResult_multithread(configFile=''):
    configFile = ConfigFile if configFile == '' else configFile
    config = NetBrainUtils.GetConfig(configFile)
    if len(config) == 0:
        PrintMessage(''.join([CurrentMethodName(), 'Failed to load the configuration file: ', configFile]), 'Error')
        return False
    multi_thread_info = config['Multi Thread Info']
    maxThread = multi_thread_info['ThreadCount'] + 1
    db = NetBrainDB(config['DB Info'])
    db.Login()
    db.GetDatabase(config['Domain Name'])
    PrintMessage('Start to verify flash probes.')
    verify_config = config['Verify FlashProbe']
    param = {
        'Collection Name': verify_config['Collection'],
        'Min Interval': verify_config['Run Schedule'] * 60 * 0.9,
        'Max Interval': verify_config['Run Schedule'] * 60 * 1.2,
        'Days': verify_config['Day']
    }
    input_thread = threading.Thread(target=GenerateInputDataThread, args=(db, param))
    input_thread.daemon = True
    input_thread.start()
    sleep(10)

    for i in range(1, maxThread):
        t = threading.Thread(target=StartWorkerThread, args=(db, 3))
        t.daemon = True
        t.start()
    #size = inputQueue.qsize()
    input_thread.join()
    inputQueue.join()

    return True

def GenerateInputDataThread(db, param:dict):
    flash_probes = db.Database['AMFPInstance'].find({}, no_cursor_timeout=True)
    #count = flash_probes.count()
    for flash_probe in flash_probes:
        if ' Unreachable' in flash_probe['n'] or 'Configuration Change' in flash_probe['n'] or ' Frequency' in flash_probe['n']:
            continue
        data = param.copy()
        data['Flash Probe'] = flash_probe
        inputQueue.put(data)
    return True

def VerifyBuildInProbes(db=None, configFile=''):
    if db is None:
        configFile = ConfigFile if configFile == '' else configFile
        config = NetBrainUtils.GetConfig(configFile)
        if len(config) == 0:
            PrintMessage(''.join([CurrentMethodName(), 'Failed to load the configuration file: ', configFile]), 'Error')
            return False
        db = NetBrainDB(config['DB Info'])
        db.Login()
        db.GetDatabase(config['Domain Name'])
    devices = db.Database['Device'].find({}, no_cursor_timeout=True).sort('name', 1)
    maxThread = config.get('Multi Thread Info', {}).get('ThreadCount', 1)
    if maxThread > 1:  # multi-thread
        for device in devices:
            inputQueue4.put(device)
        for i in range(1, maxThread):
            t = threading.Thread(target=StartVerifyBuildInProbesWorkerThread, args=(db, ))
            t.daemon = True
            t.start()
        inputQueue4.join()
        db.Logout()
        return True
    # single-thread
    index = 1
    for device in devices:
        DoVerifyBuildInProbes(db, device, index)
        index += 1
    db.Logout()
    # if total > 0:
    #     PrintMessage(f'Total lacked probes: {total}', 'Warning')
    return True

def DoVerifyBuildInProbes(db, device, index=0):
    device_name = device['name']
    probes = db.GetAll('AMFPInstance', {'npv': device['_id'], 'c': {'$in': [2, 4, 5, 6]}}, 'n', 1)
    # index = 0
    # total = 0
    length = len(probes)
    if length < 6:
        # index += 1
        # total += 6 - length
        probe_names = [item['n'] for item in probes]
        if 'High Frequency' not in probe_names or 'Medium Frequency' not in probe_names or 'Low Frequency' not in probe_names:
            PrintMessage(f'{index}: No Frequency probes for {device_name}. ({length}) {probe_names}.', 'Error')
        elif 'Configuration Change' not in probe_names:
            snmp_devices = db.GetAll('DiscoveredDevice', {'accessType': 2}, 'name', 1)
            snmp_device = next((item for item in snmp_devices if item.get("name") and item["name"] == device['name']), None)
            if snmp_device is not None:
                if 'CLI Unreachable' not in probe_names:
                    if snmp_device['reason'] != "Don't Support CLI":
                        PrintMessage(f'{index}: No Configuration and CLI probes for {device_name}.\t({length}) {probe_names}.', 'Error')
                    else:
                        PrintMessage(f'{index}: No Configuration and CLI probes for {device_name}.\t({length}) {probe_names}.', 'Warning')
                else:
                    PrintMessage(f'{index}: No Configuration probe for {device_name}.\t({length}) {probe_names}.', 'Warning')
            else:
                PrintMessage(f'{index}: No Configuration probe for {device_name}.\t({length}) {probe_names}.', 'Error')
        else:
            PrintMessage(f'{index}: No SNMP probe for {device_name}.\t({length}) {probe_names}', 'Error')
        # for probe in probes:
        #     PrintMessage(''.join(['\t', probe['_id'], ': ', probe['dn']]))
    return True

def StartVerifyBuildInProbesWorkerThread(db):
    global inputQueue4
    while True:
        #size = inputQueue4.qsize()
        param = inputQueue4.get()
        # msg = ''.join([str(size), ' tasks in queue.'])
        DoVerifyBuildInProbes(db, param)
        # PrintMessage(msg)
        inputQueue4.task_done()
    return True

def EnableProbes(application=None, configFile=''):
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
        db = NetBrainDB(config['DB Info'])
        db.Login()
        db.GetDatabase(config['Domain Name'])
        devices = db.Database['Device'].find({}, no_cursor_timeout=True).sort('name', 1)
        maxThread = config.get('Multi Thread Info', {}).get('ThreadCount', 1)
        if maxThread > 1:  # multi-thread
            for device in devices:
                inputQueue3.put([device, config['Enable FlashProbes']])
            for i in range(1, maxThread):
                t = threading.Thread(target=StartEnableProbesWorkerThread, args=(app, ))
                t.daemon = True
                t.start()
            inputQueue3.join()
        else:  # single-thread
            for device in devices:
                DoEnableProbes(app, device, config['Enable FlashProbes'])
    except Exception as e:
        traceback.print_exc()
        # print('Exception raised: ', str(e))
        # traceback.print_stack()
        ret = False
    finally:
        db.Logout()
        if application is None and app.Logined:
            app.Logout()
        return ret

def DoEnableProbes(app:NetBrainIE, device:dict, enable_probes:dict):
    device_id = device['_id']
    # device_name = device['name']
    probes = app.flashprobes_search(device_id)
    probes_info = {'type': 1, 'ids': []}
    for probe_name in enable_probes['Probe Names']:
        probe = next((item for item in probes['flashProbes'] if item.get("name") and item["name"] == probe_name), None)
        if probe is None:
            continue
        probes_info['type'] = probe['type']
        probes_info['ids'].append(probe['id'])
    ret = app.flashprobes_enable(probes_info, enable_probes['Enabled'])
    return True if ret > 0 else False

def StartEnableProbesWorkerThread(app:NetBrainIE):
    global inputQueue3
    while True:
        size = inputQueue3.qsize()
        param = inputQueue3.get()
        msg = ''.join([str(size), ' tasks in queue. ', str(param[1]), ' probe '])
        ret = DoEnableProbes(app, param[0], param[1])
        if ret:
            PrintMessage(msg + 'successful.')
        else:
            PrintMessage(msg + 'failed.', 'Error')
        inputQueue3.task_done()
    return True

def CreateFlashProbesForMultiDomains(application=None, configFile=''):
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
            domain_name = config['Domain Name']
            app.ApplyTenantAndDomain(config['Tenant Name'], domain_name)
            domainFrom = config.get('DomainName From', None)
            if domainFrom is None:
                domainCount = config.get('DomainCount', 1) + 1
                domainFrom = 1
                domainTo = domainCount
            else:
                domainTo = config.get('DomainName To', None)
                if domainTo is None:
                    domainTo = domainFrom + 1
                domainTo += 1
                domainCount = domainTo - domainFrom + 1
                for index in range(domainFrom, domainTo):
                    config['Domain Name'] = ''.join([domain_name, f'{index:02}'])
                    PrintMessage('=======================>Create Flash Probes for the domain ' + config['Domain Name'])
                    FlashProbe(app, config)
                    # app.ApplyTenantAndDomain(config['Tenant Name'], config['Domain Name'])
                    # default_frequency = config.get('Device Polling Default Frequency', None)
                    # if default_frequency is not None:
                    #     app.DefaultPollingFrequency(default_frequency)
                    # app.PollingEnabledStatus(False)
    except Exception as e:
        traceback.print_exc()
        # print('Exception raised: ', str(e))
        ret = False
    finally:
        if application is None and app.Logined:
            app.Logout()
        return ret

def DeleteFlashProbesFromMultiDomains(db, domain_name:str, create_user:str, configFile=''):
    if db is None:
        configFile = ConfigFile if configFile == '' else configFile
        config = NetBrainUtils.GetConfig(configFile)
        if len(config) == 0:
            PrintMessage(''.join([CurrentMethodName(), 'Failed to load the configuration file: ', configFile]), 'Error')
            return False
        db = NetBrainDB(config['DB Info'])
        db.Login()
    db.GetDatabase(domain_name)
    # fp = list(db.Database['AMFPInstance'].find({'operateInfo.opUser': config['Username']}))
    ret = db.Database['AMFPInstance'].delete_many({'operateInfo.opUser': create_user})
    db.Database['AutomationTaskDefinition'].delete_many({'operateInfo.opUser': create_user})
    db.Database['AMTriggerRelationship'].delete_many({'operateInfo.opUser': create_user})
    db.Database['AMMonitorVariable'].delete_many({'operateInfo.opUser': create_user})
    return True

def DeleteFlashProbesFromMultiDomains(application=None, configFile=''):
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
            domain_name = config['Domain Name']
            app.ApplyTenantAndDomain(config['Tenant Name'], domain_name)
            domainFrom = config.get('DomainName From', None)
            if domainFrom is None:
                domainCount = config.get('DomainCount', 1) + 1
                domainFrom = 1
                domainTo = domainCount
            else:
                domainTo = config.get('DomainName To', None)
                if domainTo is None:
                    domainTo = domainFrom + 1
                domainTo += 1
                domainCount = domainTo - domainFrom + 1
            db = NetBrainDB(config['DB Info'])
            db.Login()
            for index in range(domainFrom, domainTo):
                current_domain_name = ''.join([domain_name, f'{index:02}'])
                PrintMessage('=======================>Delete Flash Probes for the domain ' + current_domain_name)
                DeleteFlashProbesFromMultiDomains(db, current_domain_name, config['Username'])
            db.Logout()
    except Exception as e:
        # traceback.print_exc()
        exception_stack = traceback.format_exc()
        PrintMessage('Exception raised: ' + exception_stack, 'Error')
        ret = False
    finally:
        if application is None and app.Logined:
            app.Logout()
        return ret

def NotifyCreateResourceFullPackage(config):
    fsc_server = config.get('FSC Server', None)
    if fsc_server is None:
        return True
    fsc_config_file = fsc_server.get('Config File', r'C:\Program Files\NetBrain\Front Server Controller\conf\frontctlr.ini')
    fsc_config_fullpath = ''.join(['\\\\', fsc_server['IP'], '\\', fsc_config_file.replace(':', '$')])
    with open(fsc_config_fullpath, 'a+') as f:
        f.seek(0)
        content = f.read()
        ret = content.rfind('build=')
        if ret != -1:
            content = content[0:ret]
        content += 'build=1\n'
        f.seek(0)
        f.write(content)
    return True

def VerifyMonitorVariable(db=None, configFile=''):
    configFile = ConfigFile if configFile == '' else configFile
    config = NetBrainUtils.GetConfig(configFile)
    if len(config) == 0:
        PrintMessage(''.join([CurrentMethodName(), 'Failed to load the configuration file: ', configFile]), 'Error')
        return False
    postgresdb_info = config.get('PostgresDB Info', None)
    if postgresdb_info is None:
        PrintMessage(''.join([CurrentMethodName(), 'Please set run PostgresDB Info in config file.']), 'Error')
        return False
    run_schedule = config.get('Monitor Variable', {}).get('Run Schedule (Minutes)', None)
    if run_schedule is None:
        PrintMessage(''.join([CurrentMethodName(), 'Please set run schedule in config file.']), 'Error')
        return False
    today:datetime = NetBrainUtils.GetLocalTime()
    days = config.get('Monitor Variable', {}).get('Days', [today.strftime(r'%Y-%m-%d')])
    need_logout = False
    if len(config) == 0:
        PrintMessage(''.join([CurrentMethodName(), 'Failed to load the configuration file: ', configFile]), 'Error')
        return False
    if db is None:
        db = NetBrainDB(config['DB Info'])
        db.Login()
        need_logout = True
    db.GetDatabase('NGSystem')
    tenants = db.GetAll('Tenant', {'name': config['Tenant Name']})
    if len(tenants) <= 0:
        tenant = None
    else:
        tenant = next((item for item in tenants if item.get('name') and item['name'] == config['Tenant Name']), None)
    if tenant is None:
        PrintMessage(''.join([CurrentMethodName(), 'Failed to find the tenant "', config['Tenant Name'], '" in Mongo DB.']), 'Error')
        if need_logout:
            db.Logout()
        return False
    domains = tenant['domains']
    if len(domains) <= 0:
        domain = None
    else:
        domain = next((item for item in domains if item.get('name') and item['name'] == config['Domain Name']), None)
    if domain is None:
        PrintMessage(''.join([CurrentMethodName(), 'Failed to find the domain "', config['Domain Name'],
                              '" in the Tenant "', config['Tenant Name'], '" in Mongo DB.']), 'Error')
        if need_logout:
            db.Logout()
        return False
    db.GetDatabase(config['Domain Name'])
    count = db.Count('Device', {'subType': {'$in': [2, 2001]}})
    if count > 0:
        domain_id = domain['guid'].replace('-', '_')
        if domain_id[0] >= '0' and domain_id[0] <= '9':
            postgres_database = 'db_' + domain_id
        else:
            postgres_database = domain_id
        try:
            postgres_db = PostgresDB(postgresdb_info)
            postgres_db.Login(postgres_database)
            if not postgres_db.Logined:
                return False
            devices = db.Database['Device'].find({'subType': {'$in': [2, 2001]}}, no_cursor_timeout=True).sort('name', 1)
            index = 1
            for device in devices:  # [devices[0]]:
                PrintMessage(f'{index}: Verify {device["name"]}.')
                index += 1
                for day in days:
                    day_from = datetime.strptime(day.replace('/', '-'), '%Y-%m-%d')
                    day_to = NetBrainUtils.DateAddDays(day_from, 1)
                    VerifyMonitorVariableByDevice(postgres_db, device['_id'], day_from, day_to, run_schedule)
        except Exception as e:
            msg = traceback.format_exc()
            PrintMessage("Exception: " + msg, 'Error')
        finally:
            if postgres_db.Logined:
                postgres_db.Logout()
    if need_logout:
        db.Logout()
    return True

def VerifyMonitorVariableByDevice(db:PostgresDB, device_id:str, day_from, day_to, run_schedule:int=15):
    min_inteval = run_schedule * 60 * 0.9
    max_inteval = run_schedule * 60 * 1.2
    variables = db.GetAll(f'select * from public.ammonitorvariable where nodepathvalue=\'{device_id}\' ;')
    for variable in variables:
        # column: _id:0, nodepatchschema:1, nodepathvalue:2, nodename:3, parserpath:4, parserparam:5,
        # variable: 6, columns: 7, meta_id: 8
        if variable[7] is None:
            variable_single = variable[6]
            VerifyMonitorVariableSingle(db, variable, min_inteval, max_inteval, day_from, day_to)
        else:
            variable_table = variable[7]
            VerifyMonitorVariableTable(db, variable, min_inteval, max_inteval, day_from, day_to)

    return True

def VerifyMonitorVariableSingle(db:PostgresDB, variable:dict, min_inteval:int, max_inteval:int, day_from, day_to):
    # column: _id:0, nodepatchschema:1, nodepathvalue:2, nodename:3, parserpath:4, parserparam:5,
    # variable: 6, columns: 7, meta_id: 8
    condition = f'meta_id={variable[8]} and ts > \'{day_from}\' and ts < \'{day_to}\''
    sql = f"select original_len, encode(content, 'escape'), ts from monitor_variable_single where {condition} order by ts"
    items = db.GetAll(sql)
    previous_ts = None
    device_name = variable[3]
    parser = variable[4]
    variable_names = variable[6]
    error_messages = []
    if len(items) <= 0:
        PrintMessage(f'There is no data between {day_from} and {day_to} "{variable_names}" at the parser "{parser}" on the device "{device_name}".', 'Warning')
        return True
    for item in items:
        if item[0] < 1:
            error_messages.append('\tThere is no value.')
        if previous_ts is None:
            previous_ts = item[2]
            continue
        current_ts = item[2]
        ts = current_ts - previous_ts
        diff = ts.total_seconds()
        if diff <= min_inteval or diff >= max_inteval:
            message = f'\tThe interval is wrong: previous run time is {previous_ts}, current run time is {current_ts}, the interval is {diff} second.'
            error_messages.append(message)
        previous_ts = current_ts
        #data = item[1]
    if len(error_messages) > 0:
        message = f'"{variable_names}" at the parser "{parser}" on the device "{device_name}": \n' + '\n'.join(error_messages)
        PrintMessage(f'{message}\n', 'Error')
    return True

def VerifyMonitorVariableTable(db:PostgresDB, variable:dict, min_inteval:int, max_inteval:int, day_from, day_to):
    # column: _id:0, nodepatchschema:1, nodepathvalue:2, nodename:3, parserpath:4, parserparam:5,
    # variable: 6, columns: 7, meta_id: 8
    condition = f'meta_id={variable[8]} and ts > \'{day_from}\' and ts < \'{day_to}\''
    sql = f"select original_len, encode(content, 'escape'), ts from monitor_variable_table where {condition} order by ts"
    items = db.GetAll(sql)
    previous_ts = None
    device_name = variable[3]
    parser = variable[4]
    variable_names = ', '.join(variable[7])
    error_messages = []
    #message = f'"{variable_names}" at the parser "{parser}" on the device "{device_name}": '
    #print(message)
    for item in items:
        if item[0] < 23:
            error_messages.append('\tThere is no value.')
            #PrintMessage(f'{message} There is no value.', 'Error')
        if previous_ts is None:
            previous_ts = item[2]
            continue
        current_ts = item[2]
        ts = current_ts - previous_ts
        diff = ts.total_seconds()
        if diff <= min_inteval or diff >= max_inteval:
            message = f'\tThe interval is wrong: previous run time is {previous_ts}, current run time is {current_ts}, the interval is {diff} second.'
            error_messages.append(message)
        previous_ts = current_ts
        #data = item[1]
    else:
        PrintMessage(f'There is no data between {day_from} and {day_to} for "{variable_names}" at the parser "{parser}" on the device "{device_name}".', 'Warning')
    if len(error_messages) > 0:
        message = f'"{variable_names}" at the parser "{parser}" on the device "{device_name}": \n' + '\n'.join(error_messages)
        PrintMessage(f'{message}\n', 'Error')
    return True

def GetOperatorIndex(operator:str):
    operators = ['Violates GB Rule', 'Equals to', 'Does not Equal to', 'Is none', 'Is not none', 'Contains', 'Does not contain',
                'Greater than', 'Less than', 'Greater than or Equals to', 'Less than or Equals to', 'Range']
    index = operators.index(operator)
    return index

def ModifyFlashProbeVariableName(database:NetBrainDB=None, configFile='', devices=None):
    configFile = ConfigFile if configFile == '' else configFile
    config = NetBrainUtils.GetConfig(configFile)
    if len(config) == 0:
        PrintMessage(''.join([CurrentMethodName(), 'Failed to load the configuration file: ', configFile]), 'Error')
        return False
    variable_names = config.get('Modify FlashProbe Variable Names', None)
    if variable_names is None:
        return True
    if database is None:
        db = NetBrainDB(config['DB Info'])
        db.Login()
        db.GetDatabase(config['Domain Name'])
    else:
        db = database
    if devices is None:
        devices = db.Database['Device'].find({'subType': {'$in': [2, 2001]}}).sort('name', 1)
    utc_time = NetBrainUtils.GetUtcTime()
    count = 1
    for device in devices:
        for item in variable_names:
            alert_rule = item['define alert rules']['rules'][0]
            condition = {'npv': device['_id'], 'n': item['name']}
            fp = db.GetOne('AMFPInstance', condition)
            variable = item['variables'][0]['device variables'][0]['parser variables'][0]
            vs = next((item for item in fp['vs'] if item.get('fn') and item['fn'] == variable['old name']), None)
            if vs is None:
                continue
            vs['fn'] = variable['full name']
            vs['cn'] = variable['cap name']
            vs['a'] = variable['alias name']
            vs['dt'] = variable['data type']
            vs['vt'] = variable['var type']
            fp['rl']['c'][0]['o1'] = alert_rule['new variable']
            fp['rl']['c'][0]['o'] = GetOperatorIndex(alert_rule['operator'])
            fp['rl']['c'][0]['o2'] = {'ruleParam' : alert_rule['value']}
            fp['operateInfo']['opTime'] = utc_time
            # save to db
            ret = db.Update('AMFPInstance', condition, fp)
            save_mv = variable.get('save monitor variable', None)
            if save_mv is None:
                save_mv = alert_rule.get('save monitor variable', False)
            if save_mv:
                id = fp['_id']
                device_variable = item['variables'][0]['device variables'][0]
                condition = {'nodePathValue': device['_id'], 'parserPath': device_variable['parser path'],
                                 'variable': alert_rule['old variable']}
                mv = db.GetOne('AMMonitorVariable', condition)
                if id in mv['fpIds']:
                    mv['fpIds'].remove(id)
                    mv['operateInfo']['opTime'] = utc_time
                    # save to db
                    ret = db.Update('AMMonitorVariable', condition, mv)
                condition = {'nodePathValue': device['_id'], 'parserPath': device_variable['parser path'],
                                 'variable': alert_rule['new variable']}
                mv = None  # db.GetOne('AMMonitorVariable', condition)
                if mv is None:
                    #insert new one
                    mv = {
                        '_id': CreateGuid(),
                        'nodePathSchema': 'Legacy',
                        'nodePathValue': device['_id'],
                        'nodeName': device['name'],
                        'parserPath': device_variable['parser path'],
                        'variable': alert_rule['new variable'],
                        'dataType': alert_rule['type'],
                        'varType': 1,
                        'fpIds': [fp['_id']],
                        'operateInfo':{'opUser': 'NetBrain', 'opTime': utc_time}
                    }
                    ret = db.InsertOne('AMMonitorVariable', mv)
                else:
                    if id not in mv['fpIds']:
                        mv['fpIds'].append(id)
                        mv['operateInfo']['opTime'] = utc_time
                        # save to db
                        ret = db.Update('AMMonitorVariable', condition, mv)
        if count >= 1000:
            PrintMessage(f'Verified {count} devices.')
            count = 1
        count += 1
    if database is None:
        db.Logout()
    return True

def InitNBCrypto(db_info):
    # "mongodb://admin:Netbrain1!@192.168.31.95:27017/admin?authMechanism=SCRAM-SHA-256&ssl=true&sslAllowInvalidCertificates=true&ssl_cert_reqs=CERT_NONE"
    connect_string = ''.join(['mongodb://', db_info['Username'], ':', db_info['Password'], '@',
                              db_info['MongoDB Server'], 'admin?authMechanism=SCRAM-SHA-256'])
    if db_info['SSL Enable']:
        connect_string += '&ssl=true&sslAllowInvalidCertificates=true&ssl_cert_reqs=CERT_NONE'
    #print(connect_string)
    NBCrypto.clean_module()
    if not NBCrypto.init_module(connect_string):
        return False
    return True

def VerifyFlashAlertResult(config):
    db_info = config.get('DB Info', None)
    if db_info is None:
        PrintMessage(''.join([CurrentMethodName(), 'Please set MongoDB Info in config file.']), 'Error')
        return False
    flash_alert_info = config.get('Flash Alert', None)
    if flash_alert_info is None:
        PrintMessage(''.join([CurrentMethodName(), 'Please set Flash Alert Info in config file.']), 'Error')
        return False
    # run_schedule = flash_alert_info.get('Run Schedule (Minutes)', None)
    # if run_schedule is None:
    #     PrintMessage(''.join([CurrentMethodName(), 'Please set Run Schedule in config file.']), 'Error')
    #     return False
    start_time = flash_alert_info.get('Start Time', None)
    if start_time is None:
        PrintMessage(''.join([CurrentMethodName(), 'Please set Start Time in config file.']), 'Error')
        return False
    db:NetBrainDB = NetBrainDB(db_info)
    db.Login()
    db.GetDatabase(config['Domain Name'])
    VerifyFlashAlertCount(db, flash_alert_info, start_time)
    VerifyFlashAlertProbeResultEqualOne(db, flash_alert_info, start_time)
    VerifyFlashAlertProbeResultEqualThree(db, flash_alert_info, start_time)  # timer-based probes
    filter = GetDeviceFilter()
    device_count = db.Count('Device', filter)
    total_alert = GetDeviceAlertCount(config, device_count)
    VerifyFlashAlertTriggerNI(db, flash_alert_info, start_time, total_alert)
    db.Logout()

    return True

def VerifyFlashAlertCount(db:NetBrainDB, flash_alert_info, start_time:str):
    interval = flash_alert_info.get('Interval', 1)
    start_time = NetBrainUtils.StringToDateTime(start_time.replace('-', '/'))
    end_time = NetBrainUtils.DatetimeAddHours(start_time, 1)
    stop_time = NetBrainUtils.DatetimeAddHours(start_time, 24)  # 1 day
    time_now = NetBrainUtils.GetUtcTime()
    if stop_time > time_now:
        stop_time = time_now
    db_flashalert_name = f'FlashAlert_{start_time.year}_{start_time.month:02}'
    device_count = db.Count('Device', GetDeviceFilter())
    device_alert_count = flash_alert_info.get('Device Alert', None)
    if device_alert_count is None:
        device_alert_count = GetDeviceAlertCount(config, device_count)
    #device_alert_count*3：1 primary probe + 2 secondary probes, total 3 alerts per device
    count_per_interval = int(device_alert_count*3*interval*(60/flash_alert_info['Run Schedule (Minutes)']))
    PrintMessage(f'{db_flashalert_name}, the Count1 per {interval} hour: {count_per_interval}. ' +
                 'Count1: probeResult=1, Count2: probeResult=2, Count3: probeResult=3.')
    while start_time < stop_time:
        result1_count = db.Count(db_flashalert_name, {'probeResult': 1, 'time': {'$gte': start_time, '$lt': end_time}})
        result2_count = db.Count(db_flashalert_name, {'probeResult': 2, 'time': {'$gte': start_time, '$lt': end_time}})
        result3_count = db.Count(db_flashalert_name, {'probeResult': 3, 'time': {'$gte': start_time, '$lt': end_time}})
        diff_symbol = '(-***-)' if result1_count != count_per_interval else ''
        if result1_count > count_per_interval * 1.1 or result1_count < count_per_interval * 0.9:
            PrintMessage(f'{start_time} - {end_time}: Count1={result1_count}{diff_symbol}, Count2={result2_count}, Count3={result3_count}', 'Error')
        else:
            PrintMessage(f'{start_time} - {end_time}: Count1={result1_count}{diff_symbol}, Count2={result2_count}, Count3={result3_count}')
        start_time = end_time
        end_time = NetBrainUtils.DatetimeAddHours(start_time, interval)
    return True

def VerifyFlashAlertProbeResultEqualOne_avgtimecost(db:NetBrainDB, flash_alert_info, start_time:str):
    interval = flash_alert_info.get('Interval', 1)
    run_schedule = flash_alert_info.get('Run Schedule (Minutes)', 30) * 60
    run_schedule_min = run_schedule * 0.9
    run_schedule_max = run_schedule * 1.1
    start_time = NetBrainUtils.StringToDateTime(start_time.replace('-', '/'))
    end_time = NetBrainUtils.DatetimeAddHours(start_time, interval)
    stop_time = NetBrainUtils.DatetimeAddHours(start_time, 24)  # 1 day
    time_now = NetBrainUtils.GetUtcTime()
    if stop_time > time_now:
        stop_time = time_now
    db_flashalert_name = f'FlashAlert_{start_time.year}_{start_time.month:02}'
    PrintMessage(f'{db_flashalert_name}, probeResult=1.')
    # first_alert_group = db.Database[db_flashalert_name].find(
    #     {'probeResult': 1, 'time': {'$gte': start_time, '$lt': end_time}}, no_cursor_timeout=True).sort('time', 1)
    first_alert_group = previous_alert_group = None
    first_alert_group_probe_ids = []
    current_alert_group_probe_ids = []
    PrintMessage(f'{start_time} - {end_time}:')
    first_alert_group = db.GetAll(db_flashalert_name,
                                  {'probeResult': 1, 'time': {'$gte': start_time, '$lt': end_time}},'time', 1)
    count = 0
    for alert in first_alert_group:
        probe_id = alert["flashProbeId"]
        first_alert_group_probe_ids.append(probe_id)
        probe = db.GetOne('AMFPInstance', {'_id': probe_id})
        time_cost = alert['avgtimecost']
        count += 1
        if time_cost < run_schedule_min or time_cost > run_schedule_max:
            msg = f'\t{count}. {alert["time"]}: spend={time_cost}, FlashAlert ID={alert["_id"]},' +\
                  f' FlashProbe ID={probe_id}, FlashProbe={probe["n"]}, Device={probe["nn"]}'
            PrintMessage(msg, 'Error')
    previous_alert_group = first_alert_group
    previous_alert_group_probe_ids = first_alert_group_probe_ids
    while start_time < stop_time:
        start_time = end_time
        end_time = NetBrainUtils.DatetimeAddHours(start_time, interval)
        PrintMessage(f'------------------------{start_time} - {end_time}:---------------------------')
        current_alert_group = db.GetAll(db_flashalert_name,
                                        {'probeResult': 1, 'time': {'$gte': start_time, '$lt': end_time}}, 'time', 1)
        count = 0
        for alert in current_alert_group:
            probe_id = alert["flashProbeId"]
            current_alert_group_probe_ids.append(probe_id)
            time_cost = alert['avgtimecost']
            count += 1
            if time_cost < run_schedule_min or time_cost > run_schedule_max:
                probe = db.GetOne('AMFPInstance', {'_id': probe_id})
                msg = f'\t{count}. {alert["time"]}: spend={time_cost}, FlashAlert ID={alert["_id"]}, ' + \
                      f'FlashProbe ID={probe_id}, FlashProbe={probe["n"]}, Device={probe["nn"]}'
                PrintMessage(msg, 'Error')
        # diff_alerts = list(set(previous_alert_group_probe_ids) - set(current_alert_group_probe_ids))
        # if len(diff_alerts) <= 0:
        #     continue
        count = 0
        for probe_id in current_alert_group_probe_ids:
            count += 1
            if probe_id not in previous_alert_group_probe_ids:
                probe = db.GetOne('AMFPInstance', {'_id': probe_id})
                index = current_alert_group_probe_ids.index(probe_id)
                alert = current_alert_group[index]
                msg = f'\t{count}. Not in Previous: {alert["time"]}: FlashAlert ID={alert["_id"]}, ' + \
                      f'FlashProbe ID={probe_id}, FlashProbe={probe["n"]}, Device={probe["nn"]}'
                PrintMessage(msg, 'Error')
        count = 0
        for probe_id in previous_alert_group_probe_ids:
            count += 1
            if probe_id not in current_alert_group_probe_ids:
                probe = db.GetOne('AMFPInstance', {'_id': probe_id})
                index = previous_alert_group_probe_ids.index(probe_id)
                alert = previous_alert_group[index]
                msg = f'\t{count}. Not in Current: {alert["time"]}: FlashAlert ID={alert["_id"]}, ' + \
                      f'FlashProbe ID={probe_id}, FlashProbe={probe["n"]}, Device={probe["nn"]}'
                PrintMessage(msg, 'Error')
        previous_alert_group = current_alert_group
        previous_alert_group_probe_ids = current_alert_group_probe_ids

    return True

def VerifyFlashAlertProbeResultEqualOne(db:NetBrainDB, flash_alert_info, start_time:str):
    interval = flash_alert_info.get('Interval', 1)
    run_schedule = flash_alert_info.get('Run Schedule (Minutes)', 30) * 60
    run_schedule_min = timedelta(seconds=(run_schedule * 0.9))
    run_schedule_max = timedelta(seconds=(run_schedule * 1.1))
    first_time = start_time = NetBrainUtils.StringToDateTime(start_time.replace('-', '/'))
    end_time = NetBrainUtils.DatetimeAddHours(start_time, interval)
    stop_time = NetBrainUtils.DatetimeAddHours(start_time, 24)  # 1 day
    time_now = NetBrainUtils.GetUtcTime()
    if stop_time > time_now:
        stop_time = time_now
    db_flashalert_name = f'FlashAlert_{start_time.year}_{start_time.month:02}'
    PrintMessage(f'\n----------------------{db_flashalert_name}, probeResult = 1.  (Current run/Previous run)------------------')
    count = 0
    is_first_group = True
    while start_time < stop_time:
        # PrintMessage(f'{start_time} - {end_time}:')
        time_range = {'$gte': start_time, '$lt': end_time}
        sort = [('flashProbeId', 1), ('time', 1)]
        alert_group_current = db.GetAll(db_flashalert_name, {'probeResult': 1, 'time': time_range}, sort)
        alert_group_probe_ids_current = [item['flashProbeId'] for item in alert_group_current]
        #flash_probe_ids = list(set(alert_group_probe_ids_current))
        alert_info_current = {}
        flash_probe_id_previous = None
        index = 0
        for alert in alert_group_current:
            index += 1
            probe_id = alert['flashProbeId']
            if flash_probe_id_previous is None:
                flash_probe_id_previous = probe_id
                alert_time_privious = alert['time']
                alert_info_current.update({probe_id: 1})
                continue
            if probe_id == flash_probe_id_previous:
                alert_time_current = alert['time']
                time_cost = alert_time_current - alert_time_privious
                if time_cost <= run_schedule_min or time_cost >= run_schedule_max:
                    probe = db.GetOne('AMFPInstance', {'_id': probe_id})
                    msg = f'\t{count}. {alert["time"]}: spend={time_cost}, FlashAlert ID={alert["_id"]}, ' + \
                          f'FlashProbe ID={probe_id}, FlashProbe={probe["n"]}, Device={probe["nn"]}'
                    PrintMessage(msg, 'Error')
                    count += 1
                alert_time_privious = alert_time_current
                alert_info_current[probe_id] += 1
            else:
                flash_probe_id_previous = probe_id
                alert_time_privious = alert['time']
                alert_info_current.update({probe_id: 1})
        PrintMessage(f'{start_time} - {end_time}: {index}')
        start_time = end_time
        end_time = NetBrainUtils.DatetimeAddHours(start_time, interval)
        if time_now - start_time < timedelta(hours=1):
            break
        if is_first_group:
            is_first_group = False
        else:
            for probe_id, count in alert_info_current.items():
                count_previous = alert_info_previous.get(probe_id, None)
                if count_previous == count:
                    continue
                probe = db.GetOne('AMFPInstance', {'_id': probe_id})
                n = probe['n']
                nn = probe['nn']
                if count_previous is None:
                    msg = f'NOT in Previous: FlashProbe={n}, Device={nn}, FlashProbe ID={probe_id}'
                    PrintMessage(msg, 'Error')
                elif count_previous != count:
                    msg = f'Run {count}/{count_previous} times: FlashProbe={n}, Device={nn}, FlashProbe ID={probe_id}'
                    PrintMessage(msg, 'Error')
        alert_group_probe_ids_previous = alert_group_probe_ids_current
        alert_group_previous = alert_group_current
        alert_info_previous = alert_info_current
    return True

def VerifyFlashAlertProbeResultEqualThree(db:NetBrainDB, flash_alert_info, start_time:str):
    start_time = NetBrainUtils.StringToDateTime(start_time.replace('-', '/'))
    end_time:datetime = NetBrainUtils.DatetimeAddHours(start_time, 24)  # 1 day
    time_now = NetBrainUtils.GetUtcTime()
    if end_time > time_now:
        end_time = time_now
        time_range = (end_time - start_time).seconds//3600  # hours
        alert_count = time_range//4
    else:
        alert_count = 6
    db_flashalert_name = f'FlashAlert_{start_time.year}_{start_time.month:02}'
    time_range = {'$gte': start_time, '$lt': end_time}
    sort = [('flashProbeId', 1), ('time', 1)]
    frequency_probes = list(db.Database['AMFPInstance'].find({'n': 'High Frequency'}, no_cursor_timeout=True).sort('nn', 1))
    frequency_probe_ids = []
    alert_info_current = {}
    for item in frequency_probes:
        probe_id = item['_id']
        frequency_probe_ids.append(probe_id)
        alert_info_current.update({probe_id: 0})
    # db.FlashAlert_2021_03.aggregate([
    #     {$match:{probeResult:3,time:{$gte:ISODate("2021-03-26T22:00:00Z"),$lt:ISODate("2021-03-27T22:00:00Z")}}},
    #     {$group:{_id:"$flashProbeId",count:{$sum:1}}},
    #     {$sort:{flashProbeId:1}}
    # ])
    alert_group_current = db.GetAll(db_flashalert_name,
                                    {'flashProbeId': {'$in': frequency_probe_ids}, 'time': time_range}, sort)
    # High Frequency run once per 4 hours
    for alert in alert_group_current:
        probe_id = alert['flashProbeId']
        alert_info_current[probe_id] += 1
    PrintMessage(f'\n----------------------{db_flashalert_name}, timer-based probes (probeResult=3). From {start_time} to {end_time}------------------')
    for id, count in alert_info_current.items():
        probe = next((item for item in frequency_probes if item['_id'] == id), None)
        if count == 0:
            if time_now - start_time >= timedelta(hours=4):
                PrintMessage(f'The probe is never run. probe id={id}, name={probe["n"]}, device={probe["nn"]}', 'Error')
        elif count < alert_count:
            PrintMessage(f'The probe is run {count}/{alert_count} times. probe id={id}, name={probe["n"]}, device={probe["nn"]}', 'Error')
    # Medium Frequency run once per day
    frequency_probes = list(db.Database['AMFPInstance'].find({'n': 'Medium Frequency'}, no_cursor_timeout=True).sort('nn', 1))
    frequency_probe_ids = []
    alert_info_current = {}
    for item in frequency_probes:
        probe_id = item['_id']
        frequency_probe_ids.append(probe_id)
        alert_info_current.update({probe_id: 0})
    alert_group_current = db.GetAll(db_flashalert_name,
                                    {'flashProbeId': {'$in': frequency_probe_ids}, 'time': time_range}, sort)
    for alert in alert_group_current:
        probe_id = alert['flashProbeId']
        alert_info_current[probe_id] += 1
    # Medium Frequency run once per day
    for id, count in alert_info_current.items():
        probe = next((item for item in frequency_probes if item['_id'] == id), None)
        if count == 0 and time_now - start_time >= timedelta(hours=24):
            PrintMessage(f'The probe is never run. probe id={id}, name={probe["n"]}, device={probe["nn"]}', 'Error')

    return True

def VerifyFlashAlertTriggerNI(db:NetBrainDB, flash_alert_info, start_time:str, total_alert):
    interval = flash_alert_info.get('Interval', 1)
    start_time = NetBrainUtils.StringToDateTime(start_time.replace('-', '/'))
    end_time = NetBrainUtils.DatetimeAddHours(start_time, interval)
    stop_time = NetBrainUtils.DatetimeAddHours(start_time, 24)  # 1 day
    time_now = NetBrainUtils.GetUtcTime()
    if stop_time > time_now:
        stop_time = time_now
    db_flashalert_name = f'FlashAlert_{start_time.year}_{start_time.month:02}'
    PrintMessage(f'\n----------------------{db_flashalert_name}: FlashAlertTriggerNIResult, probeResult = 1.------------------')
    trigger_ni_probe_ids = GetAllMediumFrequencyProbes(db)
    trigger_ni_probe_ids.extend(GetAllPrimaryProbesWithAlert(db, total_alert))
    while start_time <= stop_time:
        # print(''.join[trigger_ni_probe_ids], end=', ')
        time_range = {'$gte': start_time, '$lt': end_time}
        filter = {'flashProbeId': {'$in': trigger_ni_probe_ids}, 'time': time_range}
        sort = [('_id', 1), ('time', 1)]
        alert_group_current = db.GetAll(db_flashalert_name, filter, sort)
        alert_ids = [item['_id'] for item in alert_group_current]
        filter = {'flashAlertId': {'$in': alert_ids}, 'flashAlertCreateTime': time_range}
        sort = [('flashAlertId', 1), ('time', 1)]
        ni_result_group_current = db.GetAll('FlashAlertTriggerNIResult', filter, sort)
        ni_result_ids = [item['flashAlertId'] for item in ni_result_group_current]
        #alert_id_diff = list(set(alert_ids) - set(ni_result_ids))
        alert_id_diff = set(alert_ids).symmetric_difference(set(ni_result_ids))
        msg = len(alert_id_diff)
        # if msg > 0:
        #     PrintMessage(f'{start_time} - {end_time}: differnece={msg}')
        # else:
        PrintMessage(f'{start_time} - {end_time}')
        for alert_id in alert_id_diff:
            if alert_id in alert_ids:  # not in ni_result_ids
                index = alert_ids.index(alert_id)
                alert = alert_group_current[index]
                if alert['probeResult'] not in [1, 3] or len(alert['drillDownInfo']) <= 0:
                    continue
                probe_id = alert_group_current[index]['flashProbeId']
                msg = 'It is not in FlashAlertTriggerNIResult: '
            else:
                alert = db.GetOne(db_flashalert_name, {'_id': alert_id})
                probe_id = alert['flashProbeId']
                msg = 'It is not in {db_flashalert_name}: '
            probe = db.GetOne('AMFPInstance', {'_id': probe_id})
            msg += f'Flash Alert ID={alert_id}({alert["time"]}), Flash Probe ID={probe_id}, Flash Probe={probe["n"]}, Device={probe["nn"]}'
            PrintMessage(msg, 'Error')
        start_time = end_time
        end_time = NetBrainUtils.DatetimeAddHours(start_time, interval)
        if time_now - start_time < timedelta(hours=1):
            break
    return True

def GetAllMediumFrequencyProbes(db:NetBrainDB):
    filter = GetDeviceFilter()
    devices = db.Database['Device'].find(filter, {'_id': 1}).sort('n', 1)
    device_ids = []
    for item in devices:
        device_ids.append(item['_id'])
    filter = {'npv': {'$in': device_ids}, 'n': 'Medium Frequency'}
    medium_frequency_probes = db.Database['AMFPInstance'].find(filter, {'_id': 1}).sort('n', 1)
    probe_ids = []
    for probe in medium_frequency_probes:
        probe_ids.append(probe['_id'])
    return probe_ids

def GetAllPrimaryProbesWithAlert(db:NetBrainDB, total_alert:int):
    filter = GetDeviceFilter()
    devices = db.Database['Device'].find(filter, {'_id': 1}).sort('n', 1).limit(total_alert)
    device_ids = []
    for item in devices:
        device_ids.append(item['_id'])
    filter = {'npv': {'$in': device_ids}, 'n': 'show_access_lists01'}
    devices = db.Database['AMFPInstance'].find(filter, {'_id': 1}).sort('n', 1).limit(total_alert)
    probe_ids = []
    for item in devices:
        probe_ids.append(item['_id'])
    return list(probe_ids)

def GetAppAndDb(config):
    db_info = config.get('DB Info', None)
    if db_info is None:
        PrintMessage(''.join([CurrentMethodName(), 'Please set MongoDB Info in config file.']), 'Error')
        return None, None
    app:NetBrainIE = NetBrainIE(config['Url'], config['Username'], config['Password'])
    app.Login()
    if not app.Logined:
        PrintMessage(''.join([CurrentMethodName(), 'Failed to log into IE system.']), 'Error')
        return None, None
    app.ApplyTenantAndDomain(config['Tenant Name'], config['Domain Name'])
    db:NetBrainDB = NetBrainDB(db_info)
    db.Login()
    if not db.Logined:
        app.Logout()
        PrintMessage(''.join([CurrentMethodName(), 'Failed to log into MongoDB.']), 'Error')
        return None, None
    db.GetDatabase(config['Domain Name'])
    return app, db

def TriggerAnotherDeviceSecondaryProbe(config):
    app, db = GetAppAndDb(config)
    if app is None or db is None:
        return False
    devices = db.GetAll('Device', GetDeviceFilter(), 'name', 1)  # mgmtIP
    device_count = len(devices)
    total_alert = GetDeviceAlertCount(config, device_count)
    devices_group1 = devices[0: total_alert]
    devices_group2 = devices[total_alert: total_alert + total_alert]
    devices_id1 = [item['_id'] for item in devices_group1]
    devices_id2 = [item['_id'] for item in devices_group2]
    filter = {'npv':{'$in': devices_id1}, 't': 1, 'n': 'show_access_lists01'}
    probes_primary = db.GetAll('AMFPInstance', filter, 'nn', 1) #primary probes
    filter = {'npv':{'$in': devices_id2}, 't': 2, 'n': 'show_isis_neighbors_detail_show_access_lists01'}
    probes_secondary = db.GetAll('AMFPInstance', filter, 'nn', 1) #secondary probes
    for i in range(total_alert):
        probe_primary = probes_primary[i]
        probe_secondary = probes_secondary[i]
        name = probe_secondary['n'] + '_another_device'
        item = next((item for item in probes_secondary if item.get('n', None) == name), None)
        if item is not None:
            PrintMessage(''.join([CurrentMethodName(), f'The secondary probe "{name}" is existed, skipped.']), 'Warning')
            continue
        #parser_path = probe_secondary[]
        payload = {
            'nodePathSchema': 'Legacy',
            'nodePathValue': probe_secondary['npv'],
            'nodeName': probe_secondary['nn'],
            'name': name,
            'displayName': name,
            'desc': probe_secondary['ds'],
            'type': 2,
            'category': 1,
            'alertSrc': 'NetBrain',
            'createSrc': {
                'type': 'Manually',
                'name': 'Manually'
            },
            'variables': [
                {
                    'alias': 'isis_nbrs',
                    'fullName': 'isis.isis_nbrs',
                    'capName': 'isis_nbrs',
                    'scope': 1,
                    'type': 1,
                    'dataType': 'paragraph',
                    'parserPath': 'Built-in Files/Network Vendors/Cisco/Cisco IOS/show isis neighbors detail [Cisco IOS]',
                    'parserType': 1,
                    'varType': 3
                }
            ],
            'rule': {
                'isVerifyTable': True,
                'conditions': [
                    {
                        'operand1': 'isis_nbrs.system_id',
                        'operator': 2,
                        'operand2': {
                            'ruleParam': 'xxxxxxxx'
                        }
                    }
                ],
                'expression': 'A'
            },
            'alertLevel': 1,
            'alertMsg': {
                'originalExpression': name + '_alert'
            },
            'triggeredBy': [
                probe_primary['_id']
            ],
            'usedParsers': [
                {
                    'parserPath': 'Built-in Files/Network Vendors/Cisco/Cisco IOS/show isis neighbors detail [Cisco IOS]'
                }
            ],
            'enabled': True
        }
        app.flashprobe_add(payload)
    db.Logout()
    app.Logout()
    return True

def AlertedPrimaryProbesTriggerOneSecondaryProbe(config, total_alert=0):
    app, db = GetAppAndDb(config)
    if app is None or db is None:
        return False
    devices = db.GetAll('Device', GetDeviceFilter(), 'name', 1)  # mgmtIP
    device_count = len(devices)
    if total_alert is None or total_alert <= 0:
        total_alert = GetDeviceAlertCount(config, device_count)
    devices_group1 = devices[0: total_alert]
    device2 = devices[total_alert]
    devices_id1 = [item['_id'] for item in devices_group1]
    filter = {'npv':{'$in': devices_id1}, 't': 1, 'n': 'show_access_lists01'}
    probes_primary = db.GetAll('AMFPInstance', filter, 'nn', 1) #primary probes
    filter = {'npv': device2['_id'], 't': 2, 'n': 'show_isis_neighbors_detail_show_access_lists01'}
    probe_secondary = db.GetOne('AMFPInstance', filter) #secondary probes
    probe_secondary_info = app.flashprobe_get(probe_secondary['_id'])
    for probe in probes_primary:
        id = probe['_id']
        if id not in probe_secondary_info['triggeredBy']:
            probe_secondary_info['triggeredBy'].append(id)

    probe = app.flashprobes_save(probe_secondary['_id'], probe_secondary_info)
    return True


if __name__ == "__main__":
    try:
        config = NetBrainUtils.GetConfig(ConfigFile)
        if len(config) == 0:
            PrintMessage(''.join([CurrentMethodName(), 'Failed to load the configuration file: ', ConfigFile]), 'Error')
            exit(-1)

        logger = open(log_filename, 'a+')
        #InitFlashProbeEnv(config)
        #FlashProbe()
        #VerifyFlashProbeResult()
        #VerifyBuildInProbes()
        #ModifyFlashProbeVariableName()
        #EnableProbes()
        #CreateFlashProbesForMultiDomains()
        #DeleteFlashProbesFromMultiDomains()
        #VerifyMonitorVariable()
        #VerifyFlashAlertResult(config)
        #TriggerAnotherDeviceSecondaryProbe(config)
        AlertedPrimaryProbesTriggerOneSecondaryProbe(config)
    except Exception as e:
        #traceback.print_exc()
        msg = traceback.format_exc()
        PrintMessage("Exception: " + msg, 'Error')
    finally:
        if logger is not None:
            logger.close()
