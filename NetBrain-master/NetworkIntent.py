# -*- coding: utf-8 -*-
"""
@File:          NetworkIntent.py
@Description:   
@Author:        Tony Che
@Create Date:   2020-12-22
@Revision History:
"""

import json
import queue
import threading
import traceback
from datetime import datetime
from time import sleep
from NetBrainIE import NetBrainIE
from NetBrainDB import NetBrainDB
from Utils.NetBrainUtils import NetBrainUtils, CurrentMethodName, CreateGuid

ConfigFile = r'.\conf\NetworkIntent3197.conf'
#ConfigFile = r'.\conf\NetworkIntent31200.conf'
ConfigFile = r'.\conf\NetworkIntent31110.conf'

inputQueue = queue.Queue()
inputQueue2 = queue.Queue()
inputQueue_NI = queue.Queue()
inputQueue_Automation = queue.Queue()
log_filename = r'NetworkIntent.log'
logger = None


def NetworkIntent(application=None, configFile=''):
    """ NetworkIntent
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
            ret = create_network_intent(app, config)
    except Exception as e:
        traceback.print_exc()
        # print('Exception raised: ', str(e))
        ret = False
    finally:
        if application is None and app.Logined:
            app.Logout()
        return ret

def create_network_intent(app:NetBrainIE, config):
    folders = app.NICategories_get()
    folder_name = config['Network Intent']['Folder Name']
    item = next((item for item in folders if item.get("name") and item["name"] == folder_name), None)
    if item is None:
        folders = app.NICategories(folder_name)
        folder_id = folders['id']
    else:
        folder_id = item['id']
    maxThread = config.get('Multi Thread Info', {}).get('ThreadCount', 1)
    if maxThread > 1:  # multi-thread
        db = NetBrainDB(config['DB Info'])
        db.Login()
        db.GetDatabase(config['Domain Name'])
        input_thread = threading.Thread(target=GenerateInputDataThread, args=(db, folder_id))
        input_thread.daemon = True
        input_thread.start()
        sleep(5)

        for i in range(1, maxThread):
            t = threading.Thread(target=StartWorkerThread, args=(app, ))
            t.daemon = True
            t.start()
        input_thread.join()
        db.Logout()
        inputQueue.join()
        return True
    # single-thread
    db = NetBrainDB(config['DB Info'])
    db.Login()
    db.GetDatabase(config['Domain Name'])
    devices = db.GetAll('Device', {'subType': {'$in': [2, 2001]}}, 'name', 1)
    length = len(devices)
    PrintMessage(f'Total devices: {length}')
    count = total = total_task = 0
    for device in devices:
        # if '4500' not in device['name']:
        #     continue
        count += 1
        nis = app.GetNIS()
        ni_name = generate_ni_name(device["name"], config['Network Intent']['NI Name'])
        #ni_name = generate_ni_parsers(app, config, device)
        ni = next((item for item in nis if item.get("name") and item["name"] == ni_name), None)
        if ni is not None:
            PrintMessage(f'{count}: {device["name"]}. Device NI: {ni_name} is existed, skipped.', 'Warning')
            continue
        PrintMessage(f'{count}: {device["name"]}. Device NI: {ni_name}')
        ni = generate_network_intent(app, config, device)
        ret = app.SaveNetworkIntent(folder_id, ni)
        if ret:
            path = ret['path']
            app.AddInstalledAutomation(device, ret, config['Network Intent']['FlashProbe Info'])

    db.Logout()

    return True

def GenerateInputDataThread(db, folder_id):
    devices = db.Database['Device'].find({'subType': {'$in': [2, 2001]}}).sort('name', 1)
    length = db.Database['Device'].count_documents({'subType': {'$in': [2, 2001]}})
    PrintMessage(f'Total devices: {length}')
    for device in devices:
        param = {
            'Folder ID': folder_id,
            'Device': device
        }
        inputQueue.put(param)

    return True

def StartWorkerThread(app):
    global inputQueue
    while True:
        size = inputQueue.qsize()
        if size <= 0:
            sleep(1)
            continue
        param = inputQueue.get()
        device = param['Device']
        folder_id = param['Folder ID']
        try:
            nis = app.GetNIS()
            ni_name = generate_ni_name(device["name"], config['Network Intent']['NI Name'])
            ni = next((item for item in nis if item.get("name") and item["name"] == ni_name), None)
            if ni is None:
                PrintMessage(f'{size} tasks in queue. Device NI: {ni_name}')
                ni = generate_network_intent(app, config, device)
                ret = app.SaveNetworkIntent(folder_id, ni)
                if ret:
                    path = ret['path']
                    ret = app.AddInstalledAutomation(device, ret, config['Network Intent']['FlashProbe Info'])
            else:
                PrintMessage(f'{size} tasks in queue. Device NI: {ni_name} is existed, skipped.', 'Warning')
        except Exception as e:
            exception_stack = traceback.format_exc()
            PrintMessage('Exception raised: ' + exception_stack, 'Error')
        finally:
            #sleep(0.2)
            inputQueue.task_done()
    return True

def generate_parser_rules(app, ni_parser, device, variable_name=None, is_table_variable=False):
    result = app.RetrieveCmd(device['_id'], ni_parser['Command'], ni_parser['Command Type'])
    if result is None:
        result_lines = []
        result = {'fileId': None}
    else:
        result_lines = result['command'].split('\r\n')
    lines = []
    length = len(result_lines)
    if length > 20:
        length = 20
    for i in range(0, length):
        item = {
            'row': i,
            'text': result_lines[i]
        }
        lines.append(item)
    value = result_lines[:length]
    data = '\n'.join(value)
    table_variables = None
    if is_table_variable:
        skip_line = ni_parser['Skip Lines']
        is_skip_line = '1' if skip_line > 0 else '0'
        skip_line = str(skip_line) if skip_line > 0 else '0'
        parse_rule = {
            'name': 'Table1',
            'type': '3',
            'headers': '',
            'endLine': '^$',
            'isSkipLine': is_skip_line,
            'skipLine': skip_line,
            'headerToVariables': '',  # 'Neighbor:$string:neighbor;V:$int:v;AS:$int:as;MsgRcvd:$int:msgrcvd;MsgSent:$int:msgsent;TblVer:$int:tblver;InQ:$int:inq;OutQ:$int:outq;Up/Down:$string:up_down;State/PfxRcd:$int:state_pfxrcd',
            'leftAlign': '1',
            'alignType': '0',
            'alignRange': '',
            'keyVariables': '',
            'isUsePrevars': '0',
            'usePrevars': '',
            'alignRightVars': '',
            'variableTypes': {'variableType': []},
            'xxid': CreateGuid(),
            'niStart': {
                'text': '',
                'type': 0,
                'pattern': '',
                'xxid': '',
                'skip': 0,
                'hide': 1,
                'iRow': -1
            },
            'niEnd': {
                'text': '',
                'type': 0,
                'pattern': '',
                'xxid': '',
                'skip': 0,
                'hide': 1,
                'iRow': -1
            },
            'operations': [],
            'tColumns': [],
            'groupName': 'Table1'
        }
        variable_header = header_to_variables = ''
        variable_types = []
        variable_columns = []
        table_variables = [{
            'name': 'Table1',
            'fullName': 'Table1',
            'capName': 'Table1',
            'desc': '',
            'varType': 3,
            'dataType': 'table',
            'sampleIndex': 1,
            'extraInfo': {'hashColumns': []}
        }]
        cap_names = []
        index = 1000
        for variable_type in ni_parser['Variables Type']:
            variable_name = None
            header = variable_type['Header']
            name = variable_type['Name']
            type = variable_type['Type']
            cap_name = name.replace('$', '')
            cap_names.append(cap_name)
            variable_header += ''.join([header, ';'])
            header_to_variables += ''.join([header, ':$', type, ':', cap_name, ';'])
            variable_types.append(':'.join([name, type]))
            variable_column = {
                'id': index,
                'name': cap_name,
                'type': type,
                'text': header,
                'bindName': name,
                'dispName': name if type == 'string' else f'${type}:{cap_name}',
                'err': ''
            }
            variable_columns.append(variable_column)
            index += 1
            table_variable = {
                'name': name,
                'fullName': f'Table1.{name}',
                'capName': f'Table1.{name}',
                'desc': '',
                'varType': 1,
                'dataType': type,
                'realType': type,
                'sampleIndex': 1,
                'extraInfo': {'hashColumns': [], 'hashSort': False}
            }
            table_variables.append(table_variable)
        parse_rule['headers'] = variable_header[:-1]
        parse_rule['headerToVariables'] = header_to_variables[:-1]
        parse_rule['variableTypes']['variableType'] = variable_types
        parse_rule['tColumns'] = variable_columns
        item = {'parseRule': [parse_rule]}
    else:
        item = {
            'parseRule': [
                {
                    'name': 'Text1',
                    'type': '15',
                    'lines': lines,
                    'xxid': CreateGuid(),
                    'niStart': {
                        'text': '',
                        'type': 0,
                        'pattern': '',
                        'xxid': '',
                        'skip': 0,
                        'hide': 1,
                        'iRow': -1
                    },
                    'niEnd': {
                        'text': '',
                        'type': 0,
                        'pattern': '',
                        'xxid': '',
                        'skip': 0,
                        'hide': 1,
                        'iRow': -1
                    },
                    'operations': [],
                    'groupName': 'Text1',
                }
            ]
        }
    if variable_name is not None:
        name = variable_name.replace('$', '')
        keyword = f'{name} ${name}$'
        item['parseRule'].append({
            'type': 0,
            'keyWords': { 'keyWord': [keyword]},
            'tKeywords': [
                {
                    'type': 1,
                    'hide': 0,
                    'prefix': '',
                    'sBefore': '',
                    'sType': 'string',
                    'sVar': '',
                    'sAfter': '',
                    'sPattern': keyword,
                    'cBefore': '#000',
                    'cVar': '#00f',
                    'cAfter': '#000',
                    'subPatterns': [],
                    'errs': []
                }
            ],
            'statements': [],
            'variableTypes': { 'variableType': [f'{variable_name}:string']},
            'xxid': CreateGuid(),
            'niStart': {
                'text': '',
                'type': 0,
                'pattern': '',
                'xxid': '',
                'skip': 0,
                'hide': 1,
                'iRow': -1
            },
            'niEnd': {
                'text': '',
                'type': 0,
                'pattern': '',
                'xxid': '',
                'skip': 0,
                'hide': 1,
                'iRow': -1
            },
            'operations': [],
            'groupName': 'Variables1',
            'name': 'Variables1',
        })
    parser_rules = {
        'parser rules':  json.dumps(item),
        'command result': data,
        'resource id': result['fileId'],
        'table variables': [] if table_variables is None else table_variables
    }
    return parser_rules

def generate_ni_parsers(app, config, device):
    ni_parser_config = config['Network Intent']['NI Parser']
    config_parser_rules = generate_parser_rules(app, ni_parser_config['Config'], device)
    cli_parser_rules = generate_parser_rules(app, ni_parser_config['CLI'], device, ni_parser_config['CLI']['Variable'])
    parser_config = {
        'id': CreateGuid(),
        'name': CreateGuid().replace('-', ''),
        'author': '',
        'accessType': 16,
        'command': ni_parser_config['Config']['Command'],
        'devTypes': [device['subType']],
        'version': '7.1',
        'type': 2,
        "subtype": "visual",
        'qualify': {
            'Conditions': [
                {
                    'Schema': 'name',
                    'Operator': 4,
                    'Expression': device['name']
                }
            ],
            'Expression': 'A'
        },
        'samples': [
            {
                'index': 1,
                'name': 'Sample1',
                'devName': '',
                'content': '',
                'parserRules': config_parser_rules['parser rules'],
                'operations': [],
                'keyWords': '{"keyWords":[]}',
                'identify': '{"ConfigKey":{"MustConditions":{"Item":[]},"OptionalConditions":{"Item":[]}}}',
                'interfaceKeys': [],
                'tableKeys': []
            }
        ],
        'sequences': [1],
        'variables': [
            {
                'name': 'Text1',
                'fullName': 'Text1',
                'capName': 'Text1',
                'desc': '',
                'varType': 1,
                'dataType': 'string',
                'realType': 'string',
                'sampleIndex': 0,
                'extraInfo': {
                    'hashColumns': [],
                    'hashSort': False
                }
            }
        ]
    }
    parser_cli = {
        'id': CreateGuid(),
        'name': CreateGuid().replace('-', ''),
        'author': '',
        'accessType': 16,
        'command': ni_parser_config['CLI']['Command'],
        'devTypes': [device['subType']],
        'version': '7.1',
        'type': 1,
        "subtype": "visual",
        'qualify': {
            'Conditions': [
                {
                    'Schema': 'name',
                    'Operator': 4,
                    'Expression': device['name']
                }
            ],
            'Expression': 'A'
        },
        'samples': [
            {
                'index': 1,
                'name': 'Sample1',
                'devName': '',
                'content': '',
                'parserRules': cli_parser_rules['parser rules'],
                'operations': [],
                'keyWords': '{"keyWords":[]}',
                'identify': '{"ConfigKey":{"MustConditions":{"Item":[]},"OptionalConditions":{"Item":[]}}}',
                'interfaceKeys': [],
                'tableKeys': []
            }
        ],
        'sequences': [1],
        'variables': [
            {
                'name': 'Text1',
                'fullName': 'Text1',
                'capName': 'Text1',
                'desc': '',
                'varType': 1,
                'dataType': 'string',
                'realType': 'string',
                'sampleIndex': 0,
                'extraInfo': {
                    'hashColumns': [],
                    'hashSort': False
                }
            },
            {
                'name': ni_parser_config['CLI']['Variable'],
                'fullName': ni_parser_config['CLI']['Variable'],
                'capName': ni_parser_config['CLI']['Variable'],
                'desc': '',
                'varType': 1,
                'dataType': 'string',
                'realType': 'string',
                'sampleIndex': 0,
                'extraInfo': {
                    'hashColumns': [],
                    'hashSort': False
                }
            }
        ]
    }
    cli_table_parser_config = ni_parser_config.get('CLI Table', None)
    if cli_table_parser_config is not None:
        cli_table_parser_rules = generate_parser_rules(app, cli_table_parser_config, device, None, True)
        parser_cli_table = {
            'id': CreateGuid(),
            'name': CreateGuid().replace('-', ''),
            'author': '',
            'accessType': 16,
            'command': cli_table_parser_config['Command'],
            'devTypes': [device['subType']],
            'version': '7.1',
            'type': 1,
            "subtype": "visual",
            'qualify': {
                'Conditions': [
                    {
                        'Schema': 'name',
                        'Operator': 4,
                        'Expression': device['name']
                    }
                ],
                'Expression': 'A'
            },
            'samples': [
                {
                    'index': 1,
                    'name': 'Sample1',
                    'devName': '',
                    'content': '',
                    'parserRules': cli_table_parser_rules['parser rules'],
                    'operations': [],
                    'keyWords': '{"keyWords":[]}',
                    'identify': '{"ConfigKey":{"MustConditions":{"Item":[]},"OptionalConditions":{"Item":[]}}}',
                    'interfaceKeys': [],
                    'tableKeys': []
                }
            ],
            'sequences': [1],
            'variables': cli_table_parser_rules['table variables']
        }
    else:
        cli_table_parser_rules = {'command result': None, 'resource id': None}
    ni_parsers = {
        'ni parsers': [parser_config, parser_cli, parser_cli_table],
        'ni parsers data': [config_parser_rules['command result'], cli_parser_rules['command result'], cli_table_parser_rules['command result']],
        'resource id':[config_parser_rules['resource id'], cli_parser_rules['resource id'], cli_table_parser_rules['resource id']]
    }

    return ni_parsers

def generate_ni_name(device_name, ni_name):
    name = '_'.join([device_name, 'ni', ni_name])
    name = NetBrainUtils.ReplaceSpecialCharacters(name)  # name.replace(' ', '_')
    return name

def generate_network_intent(app, config, device):
    id = CreateGuid()
    automations_id = CreateGuid()
    automations_id2 = CreateGuid()
    # name = '_'.join([device['name'], 'ni', config['Network Intent']['NI Name']])
    # name = NetBrainUtils.ReplaceSpecialCharacters(name)  # name.replace(' ', '_')
    name = generate_ni_name(device['name'], config['Network Intent']['NI Name'])
    cli_var_name = config['Network Intent']['NI Parser']['CLI']['Variable']
    ni_parsers = generate_ni_parsers(app, config, device)
    org_txt_id = ni_parsers['resource id'][0]
    org_txt_id2 = ni_parsers['resource id'][1]
    network_intent = {
        "parsers": ni_parsers['ni parsers'],
        "networkIntent": {
            'type': 1,
            'name': name,
            'description': name,
            'tags': [],
            'disabled': False,
            'lockPwd': '',
            'locked': False,
            'id': id,
            'path': '/'.join([config['Network Intent']['Folder Name'], name]),
            'flag': 0,
            'inputVariables': [
                {
                    'dev': {
                        'varName': '$device1',
                        'defaultDevName': device['name'],
                        'defaultDevId': device['_id']
                    },
                    'cmds': []
                }
            ],
            'deviceSections': [
                {
                    'devId': device['_id'],
                    'devName': device['name'],
                    'description': '',
                    'devType': device['subType'],
                    'actions': [],
                    'devTemplate': '$device1',
                    'commandSections':[
                        {
                            'id': 'Config1',
                            'name': 'Configuration',
                            'type': 2,
                            'orgTxtId': org_txt_id,
                            'baselineId': org_txt_id,
                            'baselineTxt': '',
                            'parserSampleId': org_txt_id,
                            'autoData1': ni_parsers['ni parsers data'][0],
                            'verifyBaseline': False,
                            'parserId': ni_parsers['ni parsers'][0]['id'],
                            'notes': [],
                            'compoundVars': [],
                            'mergeTables': [],
                            'extendData': '{"marks":[]}',
                            'automations': [
                                {
                                    'id': automations_id,
                                    'varName': 'Text1',
                                    'varIndex': 0,
                                    'title': '',
                                    'name': '_'.join([device['name'], 'ni_config_Diagnosis']),
                                    'desc': '',
                                    'tableVarOption': {
                                        'verify': False,
                                        'verifyType': 1,
                                        'tableName': '',
                                        'devId': '',
                                        'cmdId': '',
                                    },
                                    'enabledBaseline': True,
                                    'conditions': [
                                        {
                                            'key': 'A',
                                            'varSource': 1,
                                            'dataType': 'string',
                                            'varName': 'Text1',
                                            'operator': 3,
                                            'devId': device['_id'],
                                            'cmdId': 'Config1',
                                            'rightDevId': '',
                                            'rightCmdId': '',
                                            'expression': 'XXXXXXXX',
                                            'expType': 2,
                                            'rVarSource': 1,
                                            '$baselineValue': '',
                                            'isBaselineValue': False,
                                            'varValSource': 1,
                                            'rVarValSource': 1,
                                            '$$hashKey': 'object:3242'
                                        }
                                    ],
                                    'expression': 'A',
                                    'alertCondition': 1,
                                    'alerts': [
                                        {
                                            'alertCondition': 1,
                                            'alertMsg': '_'.join([device['name'], 'ni_config_alert_msg']),
                                            'alertColor': '#f4cccc',
                                            'niStatusCode': True,
                                            'niStatusCodeType': 2,
                                            'niStatusCodeMsg': '_'.join([device['name'], 'ni_config_alert']),
                                            'devStatusCode': True,
                                            'devStatusCodeType': 2,
                                            'isOpen': False,
                                            'devStatusCodeMsg': ''
                                        }
                                    ],
                                    'alertVars': [],
                                    'alertMsg': '',
                                    'niStatusCode': False,
                                    'niStatusCodeMsg': '',
                                    'devStatusCode': False,
                                    'devStatusCodeMsg': '',
                                    '_id': automations_id,
                                    'dispName': 'Text1',
                                    'current': False
                                }
                            ]
                        },
                        {
                            'id': 'Cli1',
                            'name': ni_parsers['ni parsers'][1]['command'],
                            'type': 1,
                            'orgTxtId': org_txt_id2,
                            'baselineId': org_txt_id2,
                            'baselineTxt': '',
                            'parserSampleId': org_txt_id2,
                            'autoData1': ni_parsers['ni parsers data'][1],
                            'verifyBaseline': False,
                            'parserId': ni_parsers['ni parsers'][1]['id'],
                            'notes': [],
                            'compoundVars': [],
                            'mergeTables': [],
                            'extendData': '{"marks":[]}',
                            'automations': [
                                {
                                    'id': automations_id2,
                                    'varName': cli_var_name,
                                    'varIndex': 0,
                                    'title': '',
                                    'name': '_'.join([device['name'], 'ni_cli_Diagnosis']),
                                    'desc': '',
                                    'tableVarOption': {
                                        'verify': False,
                                        'verifyType': 1,
                                        'tableName': '',
                                        'devId': '',
                                        'cmdId': '',
                                    },
                                    'enabledBaseline': True,
                                    'conditions': [
                                        {
                                            'key': 'A',
                                            'varSource': 1,
                                            'dataType': 'string',
                                            'varName': cli_var_name.replace('$', ''),
                                            'operator': 3,
                                            'devId': device['_id'],
                                            'cmdId': 'Cli1',
                                            'rightDevId': '',
                                            'rightCmdId': '',
                                            'expression': 'XXXXXXXX',
                                            'expType': 2,
                                            'rVarSource': 1,
                                            '$baselineValue': '',
                                            'isBaselineValue': False,
                                            'varValSource': 1,
                                            'rVarValSource': 1,
                                            '$$hashKey': 'object:3870'
                                        }
                                    ],
                                    'expression': 'A',
                                    'alertCondition': 1,
                                    'alerts': [
                                        {
                                            'alertCondition': 1,
                                            'alertMsg': '_'.join([device['name'], 'ni_cli_alert_msg']),
                                            'alertColor': '#f4cccc',
                                            'niStatusCode': True,
                                            'niStatusCodeType': 2,
                                            'niStatusCodeMsg': '_'.join([device['name'], 'ni_cli_alert']),
                                            'devStatusCode': True,
                                            'devStatusCodeType': 2,
                                            'isOpen': False,
                                            'devStatusCodeMsg': ''
                                        }
                                    ],
                                    'alertVars': [],
                                    'alertMsg': '',
                                    'niStatusCode': False,
                                    'niStatusCodeMsg': '',
                                    'devStatusCode': False,
                                    'devStatusCodeMsg': '',
                                    '_id': automations_id2,
                                    'dispName': cli_var_name,
                                    'current': False
                                }
                            ]
                        }
                    ]
                }
            ]
        }
    }
    if len(ni_parsers['ni parsers']) == 3:
        automations_id3 = CreateGuid()
        org_txt_id3 = ni_parsers['resource id'][2]
        variable_name = config['Network Intent']['NI Parser']['CLI Table']['Variable']
        command_section_table_variable = {
            'id': 'Cli2',
            'name': ni_parsers['ni parsers'][2]['command'],
            'type': 1,
            'orgTxtId': org_txt_id3,
            'baselineId': org_txt_id3,
            'baselineTxt': '',
            'parserSampleId': org_txt_id3,
            'autoData1': ni_parsers['ni parsers data'][2],
            'verifyBaseline': False,
            'parserId': ni_parsers['ni parsers'][2]['id'],
            'notes': [],
            'compoundVars': [],
            'mergeTables': [],
            'extendData': '{"marks":[]}',
            'automations': [
                {
                    'id': automations_id3,
                    'varName': '',
                    'varIndex': 0,
                    'title': '',
                    'name': '_'.join([device['name'], 'ni_cli_table_var_Diagnosis']),
                    'desc': '',
                    'tableVarOption': {
                        'verify': True,
                        'verifyType': 1,
                        'tableName': 'Table1',
                        'devId': device['_id'],
                        'cmdId': 'Cli2',
                    },
                    'enabledBaseline': True,
                    'conditions': [
                        {
                            'key': 'A',
                            'varSource': 1,
                            'dataType': 'string',
                            'varName': '.'.join(['Table1', variable_name]),
                            'operator': 3,
                            'devId': device['_id'],
                            'cmdId': 'Cli2',
                            'rightDevId': '',
                            'rightCmdId': '',
                            'expression': 'XXXXXXXX',
                            'expType': 2,
                            'rVarSource': 1,
                            '$baselineValue': '',
                            'isBaselineValue': False,
                            'varValSource': 1,
                            'rVarValSource': 1,
                            '$$hashKey': 'object:3870'
                        }
                    ],
                    'expression': 'A',
                    'alertCondition': 1,
                    'alerts': [
                        {
                            'alertCondition': 1,
                            'alertMsg': '_'.join([device['name'], 'ni_cli_table_var_alert_msg']),
                            'alertColor': '#fec9cf',
                            'niStatusCode': True,
                            'niStatusCodeType': 2,
                            'niStatusCodeMsg': '_'.join([device['name'], 'ni_cli_table_var_alert']),
                            'devStatusCode': True,
                            'devStatusCodeType': 2,
                            'isOpen': False,
                            'devStatusCodeMsg': ''
                        }
                    ],
                    'alertVars': [],
                    'alertMsg': '',
                    'niStatusCode': False,
                    'niStatusCodeMsg': '',
                    'devStatusCode': False,
                    'devStatusCodeMsg': '',
                    '_id': automations_id3,
                    'dispName': ''.join(['Select Variable: ', variable_name]),
                    'current': False
                }
            ]
        }
        network_intent['networkIntent']['deviceSections'][0]['commandSections'].append(command_section_table_variable)

    return network_intent

def schedule_cli_command(application=None, configFile=''):
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
            ret = create_schedule_cli_command(app, config)
    except Exception as e:
        traceback.print_exc()
        # print('Exception raised: ', str(e))
        ret = False
    finally:
        if application is None and app.Logined:
            app.Logout()
        return ret

def create_schedule_cli_command(app:NetBrainIE, config):
    db = NetBrainDB(config['DB Info'])
    db.Login()
    db.GetDatabase(config['Domain Name'])
    devices = db.GetAll('DiscoveredDevice', {'accessType': 2}, 'name', 1)
    db.Logout()
    snmp_device_ids = [item['_id'] for item in devices]
    devices = app.getDevicesByTypes(config['Schedule CLI Commands']['type'])
    for device in devices:
        if device['ID'] in snmp_device_ids:
            devices.remove(device)
    total = len(devices)
    if total <= 0:
        PrintMessage('no device found.', 'Error')
        return False
    PrintMessage(f'Total devices: {total}')
    index = count = 0
    count_per_batch = config.get('Schedule CLI Commands', {}).get('Number of Every Batch', 300)
    maxThread = config.get('Multi Thread Info', {}).get('ThreadCount', 1)
    if maxThread > 1:  # multi-thread
        while index < total:
            devices_batch = devices[index: index + count_per_batch]  # create Schedule CLI per 1000 devices
            inputQueue2.put([devices_batch, config['Schedule CLI Commands']['cli commands']])
            index += count_per_batch
        for i in range(1, maxThread):
            t = threading.Thread(target=StartWorkerThread2, args=(app, ))
            t.daemon = True
            t.start()
        inputQueue2.join()
        return True
    # single-thread
    while index < total:
        devices_batch = devices[index: index + count_per_batch]  # create Schedule CLI per 1000 devices
        #devices_batch = devices[0: 1]
        count += len(devices_batch)
        ret = app.ScheduleCliCommand_Upinsert(devices_batch, config['Schedule CLI Commands']['cli commands'])
        if ret:
            PrintMessage('create Schedule CLI Commands successful - ' + str(count))
        else:
            #PrintMessage(f'{count}: {device["name"]} create Schedule CLI Commands failed.', 'Error')
            PrintMessage('create Schedule CLI Commands failed - ' + str(count), 'Error')
        index += count_per_batch

    #db.Logout()

    return True

def StartWorkerThread2(app):
    global inputQueue2
    while True:
        size = inputQueue2.qsize()
        if size <= 0:
            sleep(1)
            continue
        param = inputQueue2.get()
        count = len(param[0])
        msg = ''.join([str(size), ' tasks in queue. Create ', str(count), ' Schedule CLI Commands '])
        try:
            ret = app.ScheduleCliCommand_Upinsert(param[0], param[1])
            if ret:
                PrintMessage(msg + 'successful.')
            else:
                PrintMessage(msg + 'failed.', 'Error')
        except Exception as e:
            exception_stack = traceback.format_exc()
            PrintMessage('Exception raised: ' + exception_stack, 'Error')
        finally:
            inputQueue2.task_done()
    return True

def AddInstalledAutomationForNI(app, config):
    db = NetBrainDB(config['DB Info'])
    db.Login()
    db.GetDatabase(config['Domain Name'])
    devices = db.GetAll('Device', {'subType': {'$in': [2, 2001]}}, 'name', 1)
    length = len(devices)
    PrintMessage(f'Total devices: {length}')
    count = total = total_task = 0
    for device in devices:
        ni_name = generate_ni_name(device['name'], config['Network Intent']['NI Name'])
        nis = app.GetNIS()
        ni = next((item for item in nis if item.get('name') and item['name'] == ni_name), None)
        if ni is None:
            PrintMessage(f'{ni_name} is not existed, skipped', 'Warning')
            continue
        app.AddInstalledAutomation(device, ni, config['Network Intent']['FlashProbe Info'])
    db.Logout()
    return True

def delete_all_network_intent(app, config):
    nis = app.NICategories_get()
    ni_folder_name = config['Network Intent']['Folder Name']
    ni_folder = next((item for item in nis if item.get('name') and item['name'] == ni_folder_name), None)
    if ni_folder is not None:
        app.deleteNodes([ni_folder['id']])
        delete_all_installed_automation(app, config)
    return True

def delete_network_intents(app, ni_names):
    nis = app.DoFullSearch_NI([])
    maxThread = config.get('Multi Thread Info', {}).get('ThreadCount', 1)
    if maxThread > 1:  # multi-thread
        for ni in nis['result']:
            if ni['name'] in ni_names:
                inputQueue_NI.put(ni)
        for i in range(1, maxThread):
            t = threading.Thread(target=StartDeleteNIWorkerThread, args=(app, ))
            t.daemon = True
            t.start()
        inputQueue_NI.join()
        return True
    # single-thread
    for ni in nis['result']:
        if ni['name'] in ni_names:
            app.nis_delete(ni['id'])
            #delete_all_installed_automation(app, config)
    return True

def StartDeleteNIWorkerThread(app):
    global inputQueue_NI
    while True:
        size = inputQueue_NI.qsize()
        if size <= 0:
            sleep(1)
            continue
        param = inputQueue_NI.get()
        msg = ''.join([str(size), ' tasks in queue. Delete NI '])
        ret = app.nis_delete(param['id'])
        # if ret:
        #     PrintMessage(msg + 'successful.')
        # else:
        #     PrintMessage(msg + 'failed.', 'Error')
        inputQueue_NI.task_done()
    return True

def delete_all_installed_automation(app, config):
    installed_automations = app.InstalledAutomationGetList()
    installed_automation_ids = [installed_automation['id'] for installed_automation in installed_automations['records']]
    return app.DeleteInstalledAutomation(installed_automation_ids)

def delete_installed_automations(app, automation_names):
    installed_automations = app.InstalledAutomationGetList()
    maxThread = config.get('Multi Thread Info', {}).get('ThreadCount', 1)
    if maxThread > 1:  # multi-thread
        for installed_automation in installed_automations['records']:
            if installed_automation['name'] in automation_names:
                inputQueue_Automation.put(installed_automation)
        for i in range(1, maxThread):
            t = threading.Thread(target=StartDeleteAutomationWorkerThread, args=(app, ))
            t.daemon = True
            t.start()
        inputQueue_Automation.join()
        return True
    # single-thread
    for installed_automation in installed_automations['records']:
        if installed_automation['name'] in automation_names:
            app.DeleteInstalledAutomation(installed_automation['id'])
    return True

def StartDeleteAutomationWorkerThread(app):
    global inputQueue_Automation
    while True:
        size = inputQueue_Automation.qsize()
        if size <= 0:
            sleep(1)
            continue
        param = inputQueue_Automation.get()
        msg = ''.join([str(size), ' tasks in queue. Delete Installed Automation '])
        ret = app.DeleteInstalledAutomation(param['id'])
        # if ret:
        #     PrintMessage(msg + 'successful.')
        # else:
        #     PrintMessage(msg + 'failed.', 'Error')
        inputQueue_Automation.task_done()
    return True

def PrintMessage(message, level='Info'):
    NetBrainUtils.PrintMessage(message, level, logger)
    return True

if __name__ == "__main__":
    config = NetBrainUtils.GetConfig(ConfigFile)
    if len(config) == 0:
        PrintMessage(''.join([CurrentMethodName(), 'Failed to load the configuration file: ', ConfigFile]), 'Error')
        exit(1)

    try:
        logger = open(log_filename, 'a+')
        application = NetBrainIE(config['Url'], config['Username'], config['Password'])
        application.Login()
        ret = True
        if application.Logined:
            application.ApplyTenantAndDomain(config['Tenant Name'], config['Domain Name'])
            # ni_start = datetime.now()
            # ret = NetworkIntent(application, config)
            # ni_end = datetime.now()
            ret = create_schedule_cli_command(application, config)
            # scli_end = datetime.now()
            # #ret = delete_all_network_intent(application, config)
            # PrintMessage(''.join(['Network Intent start: ', str(ni_start), '; Network Intent end: ', str(ni_end)]))
            # PrintMessage(''.join(['Schedule CLI start: ', str(ni_end), '; Schedule CLI end: ', str(scli_end)]))
            # AddInstalledAutomationForNI(application, config)

    except Exception as e:
        # traceback.print_exc()
        exception_stack = traceback.format_exc()
        PrintMessage('Exception raised: ' + exception_stack, 'Error')
        ret = False

    finally:
        logger.close()
        if application.Logined:
            application.Logout()

