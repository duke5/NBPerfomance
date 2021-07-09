# -*- coding: utf-8 -*-
from pymongo import MongoClient


if __name__ == '__main__':
    generate_csv = False  # 开启后在当前文件夹生成csv文件
    domain_name = "NA45K"  # domain名称
    tenant_name = "Initial_Tenant"
    # benchmark_name = ""  # 如果配置Benchmark name将直接根据name遍历所有该name的Benchmark，task id配置将无效
    # task_id = "19a6c5e8-d3dc-4ba4-9f16-2c75398c7900"  # task id 自动识别类型
    db_user = "admin"  # mongodb用户名
    db_password = "Netbrain123"  # mongodb密码
    db_host = "192.168.31.197"  # mongodb IP
    db_port = "27017"  # mongodb端口
    is_ssl = False  # 是否配置SSL，默认false

    if is_ssl:
        connection = MongoClient("mongodb://" + db_user + ":" + db_password + "@" + db_host + ":" + db_port +
                                 "/admin?authMechanism=SCRAM-SHA-256&ssl=true&ssl_cert_reqs=CERT_NONE")
    else:
        connection = MongoClient("mongodb://" + db_user + ":" + db_password + "@" + db_host + ":" + db_port +
                                 "/admin?authMechanism=SCRAM-SHA-256")
    tensys = connection.get_database(tenant_name)

    rbtf_lst = []
    rbttreefolders = tensys.RunbookTree.find({"nodeType": 0, "name": {"$regex": "ptest"}})
    for tmp1 in rbttreefolders:
        rbtft1 = tmp1.get("_id")
        if rbtft1:
            rbtf_lst.append(rbtft1)
    print()