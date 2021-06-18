# -*- coding: utf-8 -*-


def list_avg(lst1, lst2, lst3):
    lst_tmp = []
    if len(lst1) == len(lst2) and len(lst2) == len(lst3):
        for t in range(len(lst1)):
            # print(t)
            # tp = round((float(lst1[t]) + float(lst2[t]) + float(lst3[t]))/3, 3)
            # print(tp)
            # lst_tmp.append(str(tp))
            lst_tmp.insert(t, str(round((float(lst1[t]) + float(lst2[t]) + float(lst3[t]))/3, 3)))
    return lst_tmp


if __name__ == '__main__':
    lst1 = [[1.23, 2.34, 3.45], [4.26, 6.24, 4.25], [5.25, 1.54, 9.75]]
    print(list_avg(lst1[0], lst1[1], lst1[2]))
    lst2 = [[1.23, 2.34, 3.45], [4.26, 6.24, 4.25], [5.25, 1.54, 9.75], []]
    lst3 = [1, 2]
    lst4 = [3, 4, 5]
    lst3.extend(lst4)
    print(lst3)
    for i in lst2:
        if len(i) != 0:
            print(i[0])

    lsts = ['abc', ['1', '2']]
