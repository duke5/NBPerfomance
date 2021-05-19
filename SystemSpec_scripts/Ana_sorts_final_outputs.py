import csv


def parse_cvs(dev_c, user_c, clst):
    outs = {}
    for data_row in clst:
        if data_row[0] == 'WinServer':
            outs['win_cmd'] = data_row
        if data_row[0] == 'LinuxServer':
            outs['lin_cmd'] = data_row
        if data_row[0] == 'FSServer':
            outs['fs_cmd'] = data_row
        if data_row[0] == 'Winnet':
            outs['win_net'] = data_row
        if data_row[0] == 'Linuxnet':
            outs['lin_net'] = data_row
        if data_row[0] == 'FSnet':
            outs['fs_net'] = data_row
        if data_row[0] == 'FSServer2':
            outs['fs2_cmd'] = data_row
        if data_row[0] == 'FS2net':
            outs['fs2_net'] = data_row
    if outs['win_cmd'] and outs['lin_cmd'] and outs['fs_cmd'] and outs['win_net'] and outs['lin_net'] and outs[
        'fs_net']:
        lst_out = [dev_c, user_c]
        lst_out.extend(outs['lin_cmd'][1:])
        lst_out.extend(outs['lin_net'][1:])
        lst_out.extend(outs['win_cmd'][1:])
        lst_out.extend(outs['win_net'][1:])
        lst_out.extend(outs['fs_cmd'][1:])
        lst_out.extend(outs['fs_net'][1:])
        if outs.get('fs2_cmd') and outs.get('fs2_net'):
            lst_out.extend(outs['fs2_cmd'][1:])
            lst_out.extend(outs['fs2_net'][1:])
        return lst_out


if __name__ == '__main__':
    filepath = 'C:\\Systemspec_folder\\TestOutputs\\'  # 这里配置output文件存放目录
    filename_end = 'user_outputs_sortout.csv'  # 这里配置文件名（不包含后缀）
    outfile = filepath + 'final_sum.csv'
    user_lst = ['5', '10', '20', '30', '40', '50']
    devscop_lst = ['1k', '3k', '5k', '8k', '10k']
    op_lst = []
    for tm1 in devscop_lst:
        for tm2 in user_lst:
            opfile = filepath + tm1 + '_outputs\\' + tm1 + '_' + tm2 + filename_end
            with open(opfile, encoding='utf-8') as f:
                reader = csv.reader(f)
                csvlst = list(reader)
                sub_lst = parse_cvs(tm1, tm2, csvlst)
                # print(sub_lst)
                op_lst.append(sub_lst)

    for tm in op_lst:
        print(tm)

    with open(outfile, 'a', newline='') as data:
        live_file = csv.writer(data)
        live_file.writerow(
            ['Device Scope', 'Users', 'CPU of linux server', 'Memory of Linux server', 'Disk IO read of Linux server',
             'Disk IO write of Linux server', 'Network receive of Linux server',
             'Network send of Linux server', 'CPU of Windows server', 'Memory of Windows server',
             'Disk IO read of Windows server', 'Disk IO write of Windows server',
             'Network receive of Windows server', 'Network send of Windows server', 'CPU of FS1',
             'Memory of FS1', 'Disk IO read of FS1', 'Disk IO write of FS1', 'Network receive of FS1',
             'Network send of FS1', 'CPU of FS2', 'Memory of FS2', 'Disk IO read of FS2',
             'Disk IO write of FS2', 'Network receive of FS2', 'Network send of FS2'
             ])
        for tm in op_lst:
            live_file.writerow(tm)
