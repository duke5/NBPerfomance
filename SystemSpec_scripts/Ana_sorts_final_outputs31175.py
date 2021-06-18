import csv


def parse_cvs(clst):
    outs = {}
    for data_row in clst:
        if len(data_row) != 0:
            if data_row[0] == 'WebServer':
                outs['web_cmd'] = data_row
            if data_row[0] == 'WorkerServer1':
                outs['work1_cmd'] = data_row
            if data_row[0] == 'WorkerServer2':
                outs['work2_cmd'] = data_row
            if data_row[0] == 'WorkerServer3':
                outs['work3_cmd'] = data_row
            if data_row[0] == 'LinuxServer':
                outs['lin_cmd'] = data_row
            if data_row[0] == 'FSServer1':
                outs['fs1_cmd'] = data_row
            if data_row[0] == 'FSServer2':
                outs['fs2_cmd'] = data_row
            if data_row[0] == 'FSServer3':
                outs['fs3_cmd'] = data_row
            if data_row[0] == 'FSServer4':
                outs['fs4_cmd'] = data_row
            # if data_row[0] == 'FSServer5':
            #     outs['fs5_cmd'] = data_row
            # if data_row[0] == 'FSServer6':
            #     outs['fs6_cmd'] = data_row
            # if data_row[0] == 'FSServer7':
            #     outs['fs7_cmd'] = data_row
            # if data_row[0] == 'FSServer8':
            #     outs['fs8_cmd'] = data_row
            # if data_row[0] == 'FSServer9':
            #     outs['fs9_cmd'] = data_row
            if data_row[0] == 'Linuxnet':
                outs['lin_net'] = data_row
            if data_row[0] == 'Webnet':
                outs['web_net'] = data_row
            if data_row[0] == 'Workernet1':
                outs['worker1_net'] = data_row
            if data_row[0] == 'Workernet2':
                outs['worker2_net'] = data_row
            if data_row[0] == 'Workernet3':
                outs['worker3_net'] = data_row
            if data_row[0] == 'FS1net':
                outs['fs1_net'] = data_row
            if data_row[0] == 'FS2net':
                outs['fs2_net'] = data_row
            if data_row[0] == 'FS3net':
                outs['fs3_net'] = data_row
            if data_row[0] == 'FS4net':
                outs['fs4_net'] = data_row
            # if data_row[0] == 'FS5net':
            #     outs['fs5_net'] = data_row
            # if data_row[0] == 'FS6net':
            #     outs['fs6_net'] = data_row
            # if data_row[0] == 'FS7net':
            #     outs['fs7_net'] = data_row
            # if data_row[0] == 'FS8net':
            #     outs['fs8_net'] = data_row
            # if data_row[0] == 'FS9net':
            #     outs['fs9_net'] = data_row
    # if outs['web_cmd'] and outs['work1_cmd'] and outs['work2_cmd'] and outs['work3_cmd'] and outs['lin_cmd'] and outs[
    #     'fs1_cmd'] and outs['fs2_cmd'] and outs['fs3_cmd'] and outs['fs4_cmd'] and outs['fs5_cmd'] and outs[
    #     'fs6_cmd'] and outs['fs7_cmd'] and outs['fs8_cmd'] and outs['fs9_cmd'] and outs['lin_net'] and outs[
    #     'web_net'] and outs['worker1_net'] and outs['worker2_net'] and outs['worker3_net'] and outs['fs1_net'] and outs[
    #     'fs2_net'] and outs['fs3_net'] and outs['fs4_net'] and outs['fs5_net'] and outs['fs6_net'] and outs[
    #     'fs7_net'] and outs['fs8_net'] and outs['fs9_net']:
    if outs['web_cmd'] and outs['work1_cmd'] and outs['work2_cmd'] and outs['work3_cmd'] and outs['lin_cmd'] and outs[
        'fs1_cmd'] and outs['fs2_cmd'] and outs['fs3_cmd'] and outs['fs4_cmd'] and outs['lin_net'] and outs[
        'web_net'] and outs['worker1_net'] and outs['worker2_net'] and outs['worker3_net'] and outs['fs1_net'] and outs[
        'fs2_net'] and outs['fs3_net'] and outs['fs4_net']:
        lst_out = []
        lst_out.extend(outs['lin_cmd'][1:])
        lst_out.extend(outs['lin_net'][1:])
        lst_out.extend(outs['web_cmd'][1:])
        lst_out.extend(outs['web_net'][1:])
        lst_out.extend(outs['work1_cmd'][1:])
        lst_out.extend(outs['worker1_net'][1:])
        lst_out.extend(outs['work2_cmd'][1:])
        lst_out.extend(outs['worker2_net'][1:])
        lst_out.extend(outs['work3_cmd'][1:])
        lst_out.extend(outs['worker3_net'][1:])
        lst_out.extend(outs['fs1_cmd'][1:])
        lst_out.extend(outs['fs1_net'][1:])
        lst_out.extend(outs['fs2_cmd'][1:])
        lst_out.extend(outs['fs2_net'][1:])
        lst_out.extend(outs['fs3_cmd'][1:])
        lst_out.extend(outs['fs3_net'][1:])
        lst_out.extend(outs['fs4_cmd'][1:])
        lst_out.extend(outs['fs4_net'][1:])
        # lst_out.extend(outs['fs5_cmd'][1:])
        # lst_out.extend(outs['fs5_net'][1:])
        # lst_out.extend(outs['fs6_cmd'][1:])
        # lst_out.extend(outs['fs6_net'][1:])
        # lst_out.extend(outs['fs7_cmd'][1:])
        # lst_out.extend(outs['fs7_net'][1:])
        # lst_out.extend(outs['fs8_cmd'][1:])
        # lst_out.extend(outs['fs8_net'][1:])
        # lst_out.extend(outs['fs9_cmd'][1:])
        # lst_out.extend(outs['fs9_net'][1:])
        return lst_out


def list_avg(lst1, lst2, lst3):
    lst_tmp = []
    if len(lst1) == len(lst2) and len(lst2) == len(lst3):
        for t in range(len(lst1)):
            lst_tmp.insert(t, str(round((float(lst1[t]) + float(lst2[t]) + float(lst3[t])) / 3, 3)))
    return lst_tmp


if __name__ == '__main__':
    filepath = 'E:\\JMeter_data\\SystemSpec0513\\outputs\\20k\\'  # 这里配置output文件存放目录
    # filepath = 'C:\\Systemspec_folder\\TestOutputs\\'  # 这里配置output文件存放目录
    filename_end1 = 'user_outputs'  # 这里配置文件名（不包含后缀）
    filename_end2 = '_sortout.csv'
    outfile = filepath + 'final_sum.csv'
    user_lst = ['5', '10', '20', '30', '40', '50']
    # devscop_lst = ['1k', '3k', '5k', '8k', '10k']
    devscop_lst = ['20k']
    op_lst = []
    for tm1 in devscop_lst:
        for tm2 in user_lst:
            sub_lsts = []
            for tm3 in range(1, 4):
                opfile = filepath + tm1 + '_' + tm2 + filename_end1 + str(tm3) + filename_end2
                # print('file name is ' + opfile)
                with open(opfile, encoding='utf-8') as f:
                    reader = csv.reader(f)
                    csvlst = list(reader)
                    sub2_lst = parse_cvs(csvlst)
                    # print(sub2_lst)
                    sub_lsts.append(sub2_lst)
            # print(sub_lsts)
            subavg_lst = list_avg(sub_lsts[0], sub_lsts[1], sub_lsts[2])
            subavg_lst.insert(0, tm2)
            subavg_lst.insert(0, tm1)
            # print(subavg_lst)
            op_lst.append(subavg_lst)

    for tm in op_lst:
        print(tm)

    with open(outfile, 'a', newline='') as data:
        live_file = csv.writer(data)
        # live_file.writerow(
        #     ['Device Scope', 'Users', 'CPU of linux server', 'Memory of Linux server', 'Disk IO read of Linux server',
        #      'Disk IO write of Linux server', 'Network receive of Linux server', 'Network send of Linux server',
        #      'CPU of Web server', 'Memory of Web server', 'Disk IO read of Web server', 'Disk IO Web of Windows server',
        #      'Network receive of Web server', 'Network send of Web server',
        #      'CPU of Worker1', 'Memory of Worker1', 'Disk IO read of Worker1', 'Disk IO Worker of Windows1',
        #      'Network receive of Worker1', 'Network send of Worker1',
        #      'CPU of Worker2', 'Memory of Worker2', 'Disk IO read of Worker2', 'Disk IO Worker of Windows2',
        #      'Network receive of Worker2', 'Network send of Worker2',
        #      'CPU of Worker3', 'Memory of Worker3', 'Disk IO read of Worker3', 'Disk IO Worker of Windows3',
        #      'Network receive of Worker3', 'Network send of Worker3',
        #      'CPU of FS1', 'Memory of FS1', 'Disk IO read of FS1', 'Disk IO write of FS1', 'Network receive of FS1',
        #      'Network send of FS1',
        #      'CPU of FS2', 'Memory of FS2', 'Disk IO read of FS2', 'Disk IO write of FS2', 'Network receive of FS2',
        #      'Network send of FS2',
        #      'CPU of FS3', 'Memory of FS3', 'Disk IO read of FS3', 'Disk IO write of FS3', 'Network receive of FS3',
        #      'Network send of FS3',
        #      'CPU of FS4', 'Memory of FS4', 'Disk IO read of FS4', 'Disk IO write of FS4', 'Network receive of FS4',
        #      'Network send of FS4',
        #      'CPU of FS5', 'Memory of FS5', 'Disk IO read of FS5', 'Disk IO write of FS5', 'Network receive of FS5',
        #      'Network send of FS5',
        #      'CPU of FS6', 'Memory of FS6', 'Disk IO read of FS6', 'Disk IO write of FS6', 'Network receive of FS6',
        #      'Network send of FS6',
        #      'CPU of FS2', 'Memory of FS7', 'Disk IO read of FS7', 'Disk IO write of FS7', 'Network receive of FS7',
        #      'Network send of FS7',
        #      'CPU of FS2', 'Memory of FS8', 'Disk IO read of FS8', 'Disk IO write of FS8', 'Network receive of FS8',
        #      'Network send of FS8',
        #      'CPU of FS2', 'Memory of FS9', 'Disk IO read of FS9', 'Disk IO write of FS9', 'Network receive of FS9',
        #      'Network send of FS9'
        #      ])
        live_file.writerow(
            ['Device Scope', 'Users', 'CPU of linux server', 'Memory of Linux server', 'Disk IO read of Linux server',
             'Disk IO write of Linux server', 'Network receive of Linux server', 'Network send of Linux server',
             'CPU of Web server', 'Memory of Web server', 'Disk IO read of Web server', 'Disk IO Web of Windows server',
             'Network receive of Web server', 'Network send of Web server',
             'CPU of Worker1', 'Memory of Worker1', 'Disk IO read of Worker1', 'Disk IO Worker of Windows1',
             'Network receive of Worker1', 'Network send of Worker1',
             'CPU of Worker2', 'Memory of Worker2', 'Disk IO read of Worker2', 'Disk IO Worker of Windows2',
             'Network receive of Worker2', 'Network send of Worker2',
             'CPU of Worker3', 'Memory of Worker3', 'Disk IO read of Worker3', 'Disk IO Worker of Windows3',
             'Network receive of Worker3', 'Network send of Worker3',
             'CPU of FS1', 'Memory of FS1', 'Disk IO read of FS1', 'Disk IO write of FS1', 'Network receive of FS1',
             'Network send of FS1',
             'CPU of FS2', 'Memory of FS2', 'Disk IO read of FS2', 'Disk IO write of FS2', 'Network receive of FS2',
             'Network send of FS2',
             'CPU of FS3', 'Memory of FS3', 'Disk IO read of FS3', 'Disk IO write of FS3', 'Network receive of FS3',
             'Network send of FS3',
             'CPU of FS4', 'Memory of FS4', 'Disk IO read of FS4', 'Disk IO write of FS4', 'Network receive of FS4',
             'Network send of FS4'
             ])
        for tm in op_lst:
            live_file.writerow(tm)
