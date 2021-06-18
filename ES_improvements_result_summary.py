import csv


def list_avg(lst1, lst2, lst3):
    lst_tmp = []
    if len(lst1) == len(lst2) and len(lst2) == len(lst3):
        for t in range(len(lst1)):
            lst_tmp.insert(t, str(round((float(lst1[t]) + float(lst2[t]) + float(lst3[t])) / 3, 3)))
    return lst_tmp


def pars_file(csvfolder_path, keylst, file_qian, file_hou):
    # outs = {'search_tips': [], 'search': [], 'SM_stype': [], 'SM_time': [], 'SM_key': [], 'SM_server': []}
    size_lst = ['30', '50', '80', '120', '160', '200']
    final_lst = []
    for keyw in keylst:
        sum_lst = [keyw]
        for size in size_lst:
            out_lst = []
            for i in range(1, 4):
                opfile_name = csvfolder_path + file_qian + size + file_hou + str(i) + '.csv'
                # print(opfile_name)
                with open(opfile_name, encoding='utf-8') as f:
                    reader = csv.reader(f)
                    csvlst = list(reader)
                    for data_row in csvlst:
                        if len(data_row) != 0:
                            if data_row[0] == keyw:
                                subout_lst = [data_row[2], data_row[7], data_row[8]]
                                print(subout_lst)
                                out_lst.append(subout_lst)
            avg_out_lst = list_avg(out_lst[0], out_lst[1], out_lst[2])
            print('avg out is: ' + str(avg_out_lst))
            sum_lst.extend(avg_out_lst[:])
        final_lst.append(sum_lst)
    return final_lst


if __name__ == '__main__':
    key_lst = ['/ServicesAPI/Search/BasicSearch/GetSearchIntellisenseTips',
               '/ServicesAPI/Search/BasicSearch/DoFullSearch', '/ServicesAPI/servicemonitor/servicetypes',
               '/ServicesAPI/ServiceMonitor/metrics/RequestsPerSecond?timeRangeHour=6',
               '/ServicesAPI/ServiceMonitor/metrics/keymetrics', '/ServicesAPI/servicemonitor/servers']
    file_folder = 'E:\\JMeter_data\\10.0a\\'
    filepart1 = 'aggregate_'
    filepart2 = 'task'
    sum_result = pars_file(file_folder, key_lst, filepart1, filepart2)
    final_csv = file_folder + 'finalsum1.csv'
    title_lst1 = ['keywd', '', '30', '', '', '50', '', '', '80', '', '', '120', '', '', '160', '', '', '200', '']
    tilte_lst2 = ['keywd', '30avg', '30min', '30max', '50avg', '50min', '50max', '80avg', '80min', '80max', '120avg', '120min', '120max', '160avg', '160min', '160max', '200avg', '200min', '200max']
    print(title_lst1)
    print(tilte_lst2)
    for tmp in sum_result:
        print(tmp)
    with open(final_csv, 'a', newline='') as data:
        live_file = csv.writer(data)
        live_file.writerow(title_lst1)
        live_file.writerow(tilte_lst2)
        for rows in sum_result:
            live_file.writerow(rows)

