# -*- coding: utf-8 -*-
"""
@File:          WorkerLog.py
@Description:   
@Author:        Tony Che
@Create Date:   2021-04-17
@Revision History:
"""

import fileinput, glob, os, re
import json
import queue
import traceback
import threading
from copy import deepcopy
from datetime import timedelta
from NetBrainIE import NetBrainIE, PrintMessage
from NetBrainDB import NetBrainDB
from Utils.NetBrainUtils import NetBrainUtils, CurrentMethodName, CreateGuid

ConfigFile = r'.\conf\WorkerLog31200.conf'


def WorkerLog_RMAgent(configFile=''):
    """ WorkerLog
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
        folder_name = os.path.join(config['Log Folder'], 'RMAgent_*')
        time_start = config['Start Time'].replace('-', '/')
        time_end = config['End Time'].replace('-', '/')
        tasks_start = {}
        tasks_end = {}
        task_unknown = []
        filenames = glob.glob(folder_name)
        time_start = NetBrainUtils.StringToDateTime(time_start)
        time_end = NetBrainUtils.StringToDateTime(time_end)
        # time_end_1day = time_end + timedelta(hours=24)
        date_pattern = '\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2},\d{3}'
        #line_pattern = f'({date_pattern})\s*UTC\s*\(LocalTime\s*({date_pattern})\)\s*\[(.*?)\]\s*(\w*)\s*.*?-\s*[(Starting.*?)|(root.*)]'
        line_pattern = f'({date_pattern})\s*UTC\s*\(LocalTime\s*({date_pattern})\)\s*\[(.*?)\]\s*(\w*)\s*.*?-\s*(.*)'
        with fileinput.input(files=filenames) as f:
            for line in f:
                if fileinput.filelineno() == 1:
                    print(fileinput.filename())
                if 'RMAgentTask' not in line:
                    continue
                #print(line)
                #values = re.findall(line_pattern, line)
                values = re.search(line_pattern, line)
                if values is None:
                    task_unknown.append(line)
                    continue
                values = values.groups()
                if len(values) < 5:
                    task_unknown.append(line)
                    continue
                time_utc = NetBrainUtils.StringToDateTime(values[0], '%Y-%m-%d %H:%M:%S,%f')
                if time_utc < time_start:
                    continue
                time_local = NetBrainUtils.StringToDateTime(values[1], '%Y-%m-%d %H:%M:%S,%f')
                log_type = values[3]
                log_data = parse_log_data(values[4])
                if log_data is None:
                    PrintMessage(line, 'Error')
                    task_unknown.append(line)
                    continue
                status = log_data.get('Status', '')
                if status == 'Starting':
                    if time_utc < time_end:
                        item = {'Task': log_data['Task'], 'UTC': time_utc, 'Local': time_local, 'Original': line}
                        tasks_start.update({log_data['ID']: item})
                elif status == 'Ended':
                    tasks_end.update({log_data['ID']: log_data['Task']})
                elif status == 'Unknown':
                    task_unknown.append(line)
        task_len = len(tasks_start)
        len2 = len(tasks_end)
        PrintMessage(f'Task start: {task_len}, Task end: {len2}')
        for key in tasks_end.keys():
            tasks_start.pop(key, None)
        task_len = len(tasks_start)
        if task_len > 0:
            PrintMessage(f'There are {task_len} tasks uncompleted.', 'Error')
            for key, value in tasks_start:
                PrintMessage(f'{key}: value["UTC"] (value["Local"]) - value["Task"]', 'Error')

    except Exception as e:
        # traceback.print_exc()
        PrintMessage(traceback.format_exc(), 'Error')
        ret = False
    finally:
        # if application is None and app.Logined:
        #     app.Logout()
        return ret

def parse_log_data(data:str):
    data_info = {
        'Task': data,
        'Status': 'Unknown',
        'ID': data
    }
    if data.startswith('Starting'):
        data_pattern = 'Starting root|sub task\s*(.*?\d)\((.*)\)'
        values = re.search(data_pattern, data)
        if values != None:
            values = values.groups()
            data_info = {
                'Task': values[0],
                'Status': 'Starting',
                'ID': values[1]
            }
    else:
        data_pattern = 'root|sub task\s*(.*?)\s*ended\s*\((.*)\)'
        values = re.search(data_pattern, data)
        if values != None:
            values = values.groups()
            data_info = {
                'Task': values[0],
                'Status': 'Ended',
                'ID': values[1]
            }

    return data_info

if __name__ == "__main__":
    config = NetBrainUtils.GetConfig(ConfigFile)
    if len(config) == 0:
        PrintMessage(''.join(['Failed to load the configuration file: ', ConfigFile]), 'Error')
        exit(1)

    try:
        ret = True
        # app = NetBrainIE(config['Url'], config['Username'], config['Password'])
        # app.Login()
        # if app.Logined:
        #     app.ApplyTenantAndDomain(config['Tenant Name'], config['Domain Name'])
        ret = WorkerLog_RMAgent(config)
    except Exception as e:
        # traceback.print_exc()
        PrintMessage(traceback.format_exc(), 'Error')
    finally:
        # if app.Logined:
        #     app.Logout()
        PrintMessage('Done')

