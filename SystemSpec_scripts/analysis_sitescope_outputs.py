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


def win_output(oword, kew, clst):
    outs = {'item': oword}
    for orglst in clst:
        if len(orglst) >= 7:
            wcpu = kew + '\\% Pro'
            wmem = kew + '\\Working Set:1'
            wdiskread = kew + '\\IO Read'
            wdiskwrite = kew + '\\IO Write'
            if wcpu in orglst[2]:
                outs['wcpu'] = float(orglst[4]) / 16
            elif wmem in orglst[2]:
                outs['wmem'] = float(orglst[4]) / 1048576
            elif wdiskread in orglst[2]:
                outs['wdr'] = float(orglst[4]) / 1024
            elif wdiskwrite in orglst[2]:
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
        if 'FS' in mach:
            return [outs['item'], outs['tcpu'], 16.00 - outs['tmem'], outs['diskr'], outs['diskw']]
        else:
            return [outs['item'], outs['tcpu'], 64.00 - outs['tmem'], outs['diskr'], outs['diskw']]
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

    filepath = 'C:\\Systemspec_folder\\10k_backends\\'  # 这里配置output文件存放目录
    filename = '8k_backend_outputs3'  # 这里配置文件名（不包含后缀）
    opfile = filepath + filename + '.csv'  # 补充后缀

    sortfilename = filename + '_sortout'  # 统计后的文件在原名称后加 _sortout
    sortopfile = filepath + sortfilename + '.csv'

    with open(opfile, encoding='utf-8') as f:
        reader = csv.reader(f)
        csvlst = list(reader)
        dbinfo = output_data('Mongodb', 'db', csvlst)
        esinfo = output_data('ES', 'es', csvlst)
        mqinfo = output_data('RabbitMQ', 'mq', csvlst)
        redisinfo = output_data('Redis', 'redis', csvlst)
        dbserverinfo = server_outputs('LinuxServer', 'DB29123', 'linux', csvlst)
        iis1info = win_output('IIS1', 'w3wp', csvlst)
        # iis2info = win_output('IIS2', 'w3wp#1', csvlst)
        teinfo = win_output('TE', 'TaskEngineServices', csvlst)
        fscinfo = win_output('FSC', 'FSController', csvlst)
        fs1info = win_output('FS29176', 'FS29176/Process\\FrontServer', csvlst)
        fsp1info = win_output('FSParser29176', 'FS29176/Process\\FSParser', csvlst)
        fs2info = win_output('FS29177', 'FS29177/Process\\FrontServer', csvlst)
        fsp2info = win_output('FSParser29177', 'FS29177/Process\\FSParser', csvlst)
        rminfo = win_output('RMAgent', 'RMAgent', csvlst)
        ws1info = win_output('WorkShell1', 'WorkerShell', csvlst)
        ws2info = win_output('WorkShell2', 'WorkerShell#1', csvlst)
        ws3info = win_output('WorkShell3', 'WorkerShell#2', csvlst)
        ws4info = win_output('WorkShell4', 'WorkerShell#3', csvlst)
        ws5info = win_output('WorkShell5', 'WorkerShell#4', csvlst)
        ws6info = win_output('WorkShell6', 'WorkerShell#5', csvlst)
        ws7info = win_output('WorkShell7', 'WorkerShell#6', csvlst)
        ws8info = win_output('WorkShell8', 'WorkerShell#7', csvlst)
        ec1info = win_output('EVCSharp1', 'EVShellCSharp', csvlst)
        ec2info = win_output('EVCSharp2', 'EVShellCSharp#1', csvlst)
        ec3info = win_output('EVCSharp3', 'EVShellCSharp#2', csvlst)
        ec4info = win_output('EVCSharp4', 'EVShellCSharp#3', csvlst)
        webserverinfo = server_outputs('WinServer', 'web28232', 'win', csvlst)
        fsserverinfo = server_outputs('FSServer', 'FS29176', 'win', csvlst)
        fsserverinfo2 = server_outputs('FSServer2', 'FS29177', 'win', csvlst)
        webservernetinfo = net_data('Winnet', 'web28232', 'win', csvlst)
        dbservernetinfo = net_data('Linuxnet', 'DB29123', 'linux', csvlst)
        fsservernetinfo = net_data('FSnet', 'FS29176', 'win', csvlst)
        fsservernetinfo2 = net_data('FS2net', 'FS29177', 'win', csvlst)

    linuxoutlists = [dbinfo, esinfo, mqinfo, redisinfo, dbserverinfo]
    # winoutlists = [iis1info, teinfo, fscinfo, fs1info, fsp1info,
    #                rminfo, ws1info, ws2info, ws3info, ws4info, ws5info, ws6info, ws7info, ws8info,
    #                ec1info, ec2info, ec3info, ec4info]
    winoutlists = [iis1info, teinfo, fscinfo, fs1info, fsp1info, fs2info, fsp2info,
                   rminfo, ws1info, ws2info, ws3info, ws4info, ws5info, ws6info, ws7info, ws8info,
                   ec1info, ec2info, ec3info, ec4info]
    netoutlists = [webservernetinfo, fsservernetinfo, fsservernetinfo2, dbservernetinfo]
    # netoutlists = [webservernetinfo, fsservernetinfo, dbservernetinfo]

    with open(sortopfile, 'a', newline='') as data:
        live_file = csv.writer(data)
        live_file.writerow(['Services', 'CPU(%)', 'MEM(GB)', 'Disk IO Read(KB/S)', 'Disk IO Write(KB/S)'])
        for records in linuxoutlists:
            print(records)
            live_file.writerow(records)
        live_file.writerow(['WinProcess', 'CPU(%)', 'MEM(MB)', 'Disk IO Read(KB/S)', 'Disk IO Write(KB/S)'])
        for records in winoutlists:
            print(records)
            live_file.writerow(records)
        live_file.writerow(['Server', 'CPU(%)', 'MEM(GB)', 'Disk IO Read(KB/S)', 'Disk IO Write(KB/S)'])
        live_file.writerow(webserverinfo)
        live_file.writerow(fsserverinfo)
        live_file.writerow(fsserverinfo2)
        live_file.writerow((['ServerNet', 'Received (KB/s)', 'Send (KB/s)']))
        for records in netoutlists:
            print(records)
            live_file.writerow(records)
