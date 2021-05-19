import csv


def output_data(oword, kew, clst):
    outs = {'item': oword}
    for orglst in clst:
        if len(orglst) >= 7:
            lcpu = kew + 'cpu'
            # print(lcpu)
            lmem = kew + 'mem'
            ldiskread = kew + '_read'
            ldiskwrite = kew + '_write'
            if lcpu in orglst[2]:
                outs['lincpu'] = orglst[4]
            if lmem in orglst[2]:
                outs['linmem'] = orglst[4]
            if ldiskread in orglst[2]:
                outs['lindr'] = orglst[4]
            if ldiskwrite in orglst[2]:
                outs['lindw'] = orglst[4]
    return [outs['item'], outs['lincpu'], outs['linmem'], outs['lindr'], outs['lindw']]


def win_output(oword, mach, kew, clst):
    outs = {'item': oword}
    for orglst in clst:
        if len(orglst) >= 7:
            wcpu = kew + '\\% Pro'
            wmem = kew + '\\Working Set:1'
            wdiskread = kew + '\\IO Read'
            wdiskwrite = kew + '\\IO Write'
            if mach in orglst[2] and wcpu in orglst[2]:
                outs['wcpu'] = float(orglst[4]) / 16
            elif mach in orglst[2] and wmem in orglst[2]:
                outs['wmem'] = float(orglst[4]) / 1048576
            elif mach in orglst[2] and wdiskread in orglst[2]:
                outs['wdr'] = float(orglst[4]) / 1024
            elif mach in orglst[2] and wdiskwrite in orglst[2]:
                outs['wdw'] = float(orglst[4]) / 1024
    return [outs['item'], outs['wcpu'], outs['wmem'], outs['wdr'], outs['wdw']]


def net_data(oword, mach, mtype, clst):
    outs = {'item': oword, 'machine': mach}
    for orglst in clst:
        if len(orglst) >= 7:
            if mtype == 'win':
                if mach in orglst[2] and 'Bytes Received/sec' in orglst[2]:
                    outs['received'] = float(orglst[4]) / 1024
                elif mach in orglst[2] and 'Bytes Sent/sec' in orglst[2]:
                    outs['sends'] = float(orglst[4]) / 1024
                # elif mach in orglst[2] and 'Current Bandwidth' in orglst[2]:
                #     outs['bandwidth'] = float(orglst[4]) / 1024
            if mtype == 'linux':
                if mach in orglst[2] and 'ReceiveBytes' in orglst[2]:
                    outs['received'] = float(orglst[4]) / 1024
                elif mach in orglst[2] and 'TransmitBytes' in orglst[2]:
                    outs['sends'] = float(orglst[4]) / 1024
    return [outs['item'], outs['received'], outs['sends']]


def server_outputs(oword, mach, mtype, clst):
    outs = {'item': oword, 'machine': mach}
    if mtype == 'win':
        for orglst in clst:
            if len(orglst) >= 7:
                if mach in orglst[2] and 'Total\\% Processor' in orglst[2]:
                    outs['tcpu'] = orglst[4]
                elif mach in orglst[2] and 'Available MBytes' in orglst[2]:
                    outs['tmem'] = float(orglst[4]) / 1024
                elif mach in orglst[2] and 'PhysicalDisk\\0 C|\\Disk Read Bytes' in orglst[2]:
                    outs['diskr'] = float(orglst[4]) / 1024
                elif mach in orglst[2] and 'PhysicalDisk\\0 C|\\Disk Write Bytes' in orglst[2]:
                    outs['diskw'] = float(orglst[4]) / 1024
        if 'fs' in mach:
            return [outs['item'], outs['tcpu'], 8.00 - outs['tmem'], outs['diskr'], outs['diskw']]
        else:
            return [outs['item'], outs['tcpu'], 32.00 - outs['tmem'], outs['diskr'], outs['diskw']]
    if mtype == 'linux':
        for orglst in clst:
            if len(orglst) >= 7:
                if mach in orglst[2] and 'Total\\System' in orglst[2]:
                    outs['tcpu'] = orglst[4]
                elif mach in orglst[2] and 'MemTotal' in orglst[2]:
                    outs['tmemtotal'] = float(orglst[4]) / 1048576
                elif mach in orglst[2] and 'MemAvailable' in orglst[2]:
                    outs['tmemava'] = float(orglst[4]) / 1048576
                elif 'dm2_read' in orglst[2]:
                    outs['diskr'] = float(orglst[4])
                elif 'dm2_write' in orglst[2]:
                    outs['diskw'] = float(orglst[4])
        return [outs['item'], outs['tcpu'], outs['tmemtotal'] - outs['tmemava'], outs['diskr'], outs['diskw']]


if __name__ == '__main__':

    filepath = 'C:\\Systemspec_folder\\45k_28.248_backends\\'  # 这里配置output文件存放目录
    filename = '45k_backend_outputs3'  # 这里配置文件名（不包含后缀）
    opfile = filepath + filename + '.csv'  # 补充后缀

    sortfilename = filename + '_sortout'  # 统计后的文件在原名称后加 _sortout
    sortopfile = filepath + sortfilename + '.csv'

    with open(opfile, encoding='utf-8') as f:
        reader = csv.reader(f)
        csvlst = list(reader)
        dbserverinfo = server_outputs('LinuxServer', '170linux', 'linux', csvlst)
        webserverinfo = server_outputs('WebServer', '248web', 'win', csvlst)
        workerserverinfo1 = server_outputs('WorkerServer1', '249worker1', 'win', csvlst)
        workerserverinfo2 = server_outputs('WorkerServer2', '115worker2', 'win', csvlst)
        workerserverinfo3 = server_outputs('WorkerServer3', '183worker3', 'win', csvlst)
        fsserverinfo1 = server_outputs('FSServer1', '38fs1', 'win', csvlst)
        fsserverinfo2 = server_outputs('FSServer2', '68fs2', 'win', csvlst)
        fsserverinfo3 = server_outputs('FSServer3', '83fs3', 'win', csvlst)
        fsserverinfo4 = server_outputs('FSServer4', '84fs4', 'win', csvlst)
        fsserverinfo5 = server_outputs('FSServer5', '88fs5', 'win', csvlst)
        fsserverinfo6 = server_outputs('FSServer6', '96fs6', 'win', csvlst)
        fsserverinfo7 = server_outputs('FSServer7', '98fs7', 'win', csvlst)
        fsserverinfo8 = server_outputs('FSServer8', '112fs8', 'win', csvlst)
        fsserverinfo9 = server_outputs('FSServer9', '85fs9', 'win', csvlst)
        linuxservernetinfo = net_data('Linuxnet', '170linux', 'linux', csvlst)
        webservernetinfo = net_data('Webnet', '248web', 'win', csvlst)
        workerservernetinfo1 = net_data('Workernet1', '249worker1', 'win', csvlst)
        workerservernetinfo2 = net_data('Workernet2', '115worker2', 'win', csvlst)
        workerservernetinfo3 = net_data('Workernet3', '183worker3', 'win', csvlst)
        fsservernetinfo1 = net_data('FS1net', '38fs1', 'win', csvlst)
        fsservernetinfo2 = net_data('FS2net', '68fs2', 'win', csvlst)
        fsservernetinfo3 = net_data('FS3net', '83fs3', 'win', csvlst)
        fsservernetinfo4 = net_data('FS4net', '84fs4', 'win', csvlst)
        fsservernetinfo5 = net_data('FS5net', '88fs5', 'win', csvlst)
        fsservernetinfo6 = net_data('FS6net', '96fs6', 'win', csvlst)
        fsservernetinfo7 = net_data('FS7net', '98fs7', 'win', csvlst)
        fsservernetinfo8 = net_data('FS8net', '112fs8', 'win', csvlst)
        fsservernetinfo9 = net_data('FS9net', '85fs9', 'win', csvlst)

        dbinfo = output_data('Mongodb', 'db', csvlst)
        esinfo = output_data('ES', 'es', csvlst)
        mqinfo = output_data('RabbitMQ', 'mq', csvlst)
        redisinfo = output_data('Redis', 'redis', csvlst)

        iis1info = win_output('IIS1', '248web', 'w3wp', csvlst)
        # iis2info = win_output('IIS2', 'w3wp#1', csvlst)
        teinfo = win_output('TE', '248web', 'TaskEngineServices', csvlst)
        fscinfo = win_output('FSC', '248web', 'FSController', csvlst)

        wo1rminfo = win_output('RMAgent', '249worker1', 'RMAgent', csvlst)
        wo1ws1info = win_output('WorkShell1', '249worker1', 'WorkerShell', csvlst)
        wo1ws2info = win_output('WorkShell2', '249worker1', 'WorkerShell#1', csvlst)
        wo1ws3info = win_output('WorkShell3', '249worker1', 'WorkerShell#2', csvlst)
        wo1ws4info = win_output('WorkShell4', '249worker1', 'WorkerShell#3', csvlst)
        wo1ws5info = win_output('WorkShell5', '249worker1', 'WorkerShell#4', csvlst)
        wo1ws6info = win_output('WorkShell6', '249worker1', 'WorkerShell#5', csvlst)
        wo1ws7info = win_output('WorkShell7', '249worker1', 'WorkerShell#6', csvlst)
        wo1ws8info = win_output('WorkShell8', '249worker1', 'WorkerShell#7', csvlst)
        wo1ec1info = win_output('EVCSharp1', '249worker1', 'EVShellCSharp', csvlst)
        wo1ec2info = win_output('EVCSharp2', '249worker1', 'EVShellCSharp#1', csvlst)
        wo1ec3info = win_output('EVCSharp3', '249worker1', 'EVShellCSharp#2', csvlst)
        wo1ec4info = win_output('EVCSharp4', '249worker1', 'EVShellCSharp#3', csvlst)
        wo2rminfo = win_output('RMAgent', '115worker2', 'RMAgent', csvlst)
        wo2ws1info = win_output('WorkShell1', '115worker2', 'WorkerShell', csvlst)
        wo2ws2info = win_output('WorkShell2', '115worker2', 'WorkerShell#1', csvlst)
        wo2ws3info = win_output('WorkShell3', '115worker2', 'WorkerShell#2', csvlst)
        wo2ws4info = win_output('WorkShell4', '115worker2', 'WorkerShell#3', csvlst)
        wo2ws5info = win_output('WorkShell5', '115worker2', 'WorkerShell#4', csvlst)
        wo2ws6info = win_output('WorkShell6', '115worker2', 'WorkerShell#5', csvlst)
        wo2ws7info = win_output('WorkShell7', '115worker2', 'WorkerShell#6', csvlst)
        wo2ws8info = win_output('WorkShell8', '115worker2', 'WorkerShell#7', csvlst)
        wo2ec1info = win_output('EVCSharp1', '115worker2', 'EVShellCSharp', csvlst)
        wo2ec2info = win_output('EVCSharp2', '115worker2', 'EVShellCSharp#1', csvlst)
        wo2ec3info = win_output('EVCSharp3', '115worker2', 'EVShellCSharp#2', csvlst)
        wo2ec4info = win_output('EVCSharp4', '115worker2', 'EVShellCSharp#3', csvlst)
        wo3rminfo = win_output('RMAgent', '183worker3', 'RMAgent', csvlst)
        wo3ws1info = win_output('WorkShell1', '183worker3', 'WorkerShell', csvlst)
        wo3ws2info = win_output('WorkShell2', '183worker3', 'WorkerShell#1', csvlst)
        wo3ws3info = win_output('WorkShell3', '183worker3', 'WorkerShell#2', csvlst)
        wo3ws4info = win_output('WorkShell4', '183worker3', 'WorkerShell#3', csvlst)
        wo3ws5info = win_output('WorkShell5', '183worker3', 'WorkerShell#4', csvlst)
        wo3ws6info = win_output('WorkShell6', '183worker3', 'WorkerShell#5', csvlst)
        wo3ws7info = win_output('WorkShell7', '183worker3', 'WorkerShell#6', csvlst)
        wo3ws8info = win_output('WorkShell8', '183worker3', 'WorkerShell#7', csvlst)
        wo3ec1info = win_output('EVCSharp1', '183worker3', 'EVShellCSharp', csvlst)
        wo3ec2info = win_output('EVCSharp2', '183worker3', 'EVShellCSharp#1', csvlst)
        wo3ec3info = win_output('EVCSharp3', '183worker3', 'EVShellCSharp#2', csvlst)
        wo3ec4info = win_output('EVCSharp4', '183worker3', 'EVShellCSharp#3', csvlst)

        fs1fsinfo = win_output('FS141', '38fs1', 'Process\\FrontServer', csvlst)
        fs1fspinfo = win_output('FSParser141', '38fs1', 'Process\\FSParser', csvlst)
        fs1fsapiinfo = win_output('FS141', '38fs1', 'Process\\FSApiServer', csvlst)
        fs1postgreinfo = win_output('FSParser141', '38fs1', 'Process\\postgres', csvlst)
        fs2fsinfo = win_output('FS142', '68fs2', 'Process\\FrontServer', csvlst)
        fs2fspinfo = win_output('FSParser142', '68fs2', 'Process\\FSParser', csvlst)
        fs2fsapiinfo = win_output('FS142', '68fs2', 'Process\\FSApiServer', csvlst)
        fs2postgreinfo = win_output('FSParser142', '68fs2', 'Process\\postgres', csvlst)
        fs3fsinfo = win_output('FS143', '83fs3', 'Process\\FrontServer', csvlst)
        fs3fspinfo = win_output('FSParser143', '83fs3', 'Process\\FSParser', csvlst)
        fs3fsapiinfo = win_output('FS143', '83fs3', 'Process\\FSApiServer', csvlst)
        fs3postgreinfo = win_output('FSParser143', '83fs3', 'Process\\postgres', csvlst)
        fs4fsinfo = win_output('FS144', '84fs4', 'Process\\FrontServer', csvlst)
        fs4fspinfo = win_output('FSParser144', '84fs4', 'Process\\FSParser', csvlst)
        fs4fsapiinfo = win_output('FS144', '84fs4', 'Process\\FSApiServer', csvlst)
        fs4postgreinfo = win_output('FSParser144', '84fs4', 'Process\\postgres', csvlst)
        fs5fsinfo = win_output('FS145', '88fs5', 'Process\\FrontServer', csvlst)
        fs5fspinfo = win_output('FSParser145', '88fs5', 'Process\\FSParser', csvlst)
        fs5fsapiinfo = win_output('FS145', '88fs5', 'Process\\FSApiServer', csvlst)
        fs5postgreinfo = win_output('FSParser145', '88fs5', 'Process\\postgres', csvlst)
        fs6fsinfo = win_output('FS146', '96fs6', 'Process\\FrontServer', csvlst)
        fs6fspinfo = win_output('FSParser146', '96fs6', 'Process\\FSParser', csvlst)
        fs6fsapiinfo = win_output('FS146', '96fs6', 'Process\\FSApiServer', csvlst)
        fs6postgreinfo = win_output('FSParser146', '96fs6', 'Process\\postgres', csvlst)
        fs7fsinfo = win_output('FS147', '98fs7', 'Process\\FrontServer', csvlst)
        fs7fspinfo = win_output('FSParser147', '98fs7', 'Process\\FSParser', csvlst)
        fs7fsapiinfo = win_output('FS147', '98fs7', 'Process\\FSApiServer', csvlst)
        fs7postgreinfo = win_output('FSParser147', '98fs7', 'Process\\postgres', csvlst)
        fs8fsinfo = win_output('FS148', '112fs8', 'Process\\FrontServer', csvlst)
        fs8fspinfo = win_output('FSParser148', '112fs8', 'Process\\FSParser', csvlst)
        fs8fsapiinfo = win_output('FS1418', '112fs8', 'Process\\FSApiServer', csvlst)
        fs8postgreinfo = win_output('FSParser148', '112fs8', 'Process\\postgres', csvlst)
        fs9fsinfo = win_output('FS149', '85fs9', 'Process\\FrontServer', csvlst)
        fs9fspinfo = win_output('FSParser149', '85fs9', 'Process\\FSParser', csvlst)
        fs9fsapiinfo = win_output('FS1419', '85fs9', 'Process\\FSApiServer', csvlst)
        fs9postgreinfo = win_output('FSParser149', '85fs9', 'Process\\postgres', csvlst)

    server_lsts = [dbserverinfo, webserverinfo, workerserverinfo1, workerserverinfo2, workerserverinfo3, fsserverinfo1,
                   fsserverinfo2, fsserverinfo3, fsserverinfo4, fsserverinfo5, fsserverinfo6, fsserverinfo7,
                   fsserverinfo8, fsserverinfo9]
    server_net_lsts = [linuxservernetinfo, workerservernetinfo1, workerservernetinfo2, workerservernetinfo3,
                       fsservernetinfo1, fsservernetinfo2, fsservernetinfo3, fsservernetinfo4, fsservernetinfo5,
                       fsservernetinfo6, fsservernetinfo7, fsservernetinfo8, fsservernetinfo9]
    service_lsts = [dbinfo, esinfo, mqinfo, redisinfo, iis1info, teinfo, fscinfo, wo1rminfo, wo1ws1info, wo1ws2info,
                    wo1ws3info, wo1ws4info, wo1ws5info, wo1ws6info, wo1ws7info, wo1ws8info, wo1ec1info, wo1ec2info,
                    wo1ec3info, wo1ec4info, wo2rminfo, wo2ws1info, wo2ws2info, wo2ws3info, wo2ws4info, wo2ws5info,
                    wo2ws6info, wo2ws7info, wo2ws8info, wo2ec1info, wo2ec2info, wo2ec3info, wo2ec4info, wo3rminfo,
                    wo3ws1info, wo3ws2info, wo3ws3info, wo3ws4info, wo3ws5info, wo3ws6info, wo3ws7info, wo3ws8info,
                    wo3ec1info, wo3ec2info, wo3ec3info, wo3ec4info, fs1fsinfo, fs1fspinfo, fs1fsapiinfo, fs1postgreinfo,
                    fs2fsinfo, fs2fspinfo, fs2fsapiinfo, fs2postgreinfo, fs3fsinfo, fs3fspinfo, fs3fsapiinfo,
                    fs3postgreinfo, fs4fsinfo, fs4fspinfo, fs4fsapiinfo, fs4postgreinfo, fs5fsinfo, fs5fspinfo,
                    fs5fsapiinfo, fs5postgreinfo, fs6fsinfo, fs6fspinfo, fs6fsapiinfo, fs6postgreinfo, fs7fsinfo,
                    fs7fspinfo, fs7fsapiinfo, fs7postgreinfo, fs8fsinfo, fs8fspinfo, fs8fsapiinfo, fs8postgreinfo,
                    fs9fsinfo, fs9fspinfo, fs9fsapiinfo, fs9postgreinfo]

    with open(sortopfile, 'a', newline='') as data:
        live_file = csv.writer(data)
        live_file.writerow(['Server', 'CPU(%)', 'MEM(GB)', 'Disk IO Read(KB/S)', 'Disk IO Write(KB/S)'])
        for records in server_lsts:
            print(records)
            live_file.writerow(records)
        live_file.writerow((['ServerNet', 'Received (KB/s)', 'Send (KB/s)']))
        for records in server_net_lsts:
            print(records)
            live_file.writerow(records)
        live_file.writerow([])
        live_file.writerow(['Service', 'CPU(%)', 'MEM(GB)', 'Disk IO Read(KB/S)', 'Disk IO Write(KB/S)'])
        for records in service_lsts:
            print(records)
            live_file.writerow(records)
