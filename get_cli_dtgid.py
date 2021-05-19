from pymongo import MongoClient

if __name__ == '__main__':
    generate_csv = True  # 开启后在当前文件夹生成csv文件
    domain_name = "BJ_Rack"  # domain名称
    db_user = "admin"  # mongodb用户名
    db_password = "netbrain"  # mongodb密码
    db_host = "10.10.7.201"  # mongodb IP
    db_port = "27017"  # mongodb端口
    is_ssl = False  # 是否配置SSL，默认false
    #   ==========Live separate db Options=====================================

    if is_ssl:
        connection = MongoClient("mongodb://" + db_user + ":" + db_password + "@" + db_host + ":" + db_port +
                                 "/admin?authMechanism=SCRAM-SHA-256&ssl=true&ssl_cert_reqs=CERT_NONE")
    else:
        connection = MongoClient("mongodb://" + db_user + ":" + db_password + "@" + db_host + ":" + db_port +
                                 "/admin?authMechanism=SCRAM-SHA-256")
    xfsys = connection.get_database('flowengine')
    ana_task_id_lst = ["304dcccc-78ab-4a55-ab36-3dbb98b5cdc2", "8d25d949-eff5-40fb-9239-fdfe76a6344d", "20a28ba6-3b6b-4552-84c0-f327610927aa", "c4119c35-9713-47b0-85cf-91e423b87344", "d508c3c2-421d-4466-bc24-b2c47c349f88", "8c7804cf-d166-447f-b856-8b1bfe0833fb", "d3b5aa0c-39b2-45c7-83c5-6ff3f2712ef3", "345b62eb-5147-476f-ae52-d71c3a48f48e", "64ed9807-99be-48b7-b59d-5aa084c9916a", "46db7dc7-9d85-4e78-89c5-ba0ef30a2276", "ebe0d2cf-9e35-4640-9d9c-d81b74aa35df", "b783d989-3b5d-4719-8a3e-d74bf5cccb6d", "36b46166-c41a-44e1-8dc0-83c0e7b1d92d", "5c372b5e-7bf9-45ba-8d1b-15fdab0e8417", "606d1dfb-134a-4dc5-b804-333c9ac92212", "a4e885c3-1f2a-4a6b-9470-b88030580dc2", "29f50596-52da-4253-8606-dd8fdf5b25e0", "636b3578-edf9-46a0-899a-62ef6d0a5dd4", "a9e568a1-0af9-44eb-a7c0-582e8d39a98e", "1905904d-3046-4352-adaa-0f190bd84b0e", "8333001d-cf33-4a25-a8b6-14611b0b4e00", "5fd4a29a-e135-4598-9fcf-c840c7c9844a", "8280de06-1be1-4225-8991-970e8f5c8fe3", "0c186c16-7fde-4e55-aedd-b666797aefa0", "d38be25d-30a6-41fd-b9b5-e1123b5553a7", "d35be596-d642-4013-9553-dace7d43ee12", "6f1f7ca9-f0a1-4ff1-982e-4303bb4c3619", "2c0a58cc-736a-4aec-8f45-7371440ce136", "27c73199-aa9b-4a38-a045-8cf9306be379", "79da3ffd-dec4-47ef-9280-e42fd73f6ef9"]
    # outlst = []
    for anatask in ana_task_id_lst:
        ana_item = xfsys.XFTask.find_one({"_id": anatask})
        ana_dtg_id = ana_item.get('dtgId')
        if ana_dtg_id:
            # outlst.append(ana_dtg_id)
            print(ana_dtg_id)
