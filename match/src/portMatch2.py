from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import time
from src.settings import get_conn
from multiprocessing.pool import Pool
import os
import math
import logging


# Function to get port code dictionary
def get_port_code_name():
    logging.info("=" * 60)
    logging.info("Step 1: Start to get port code dictionary...")
    print("=" * 60)
    print("Step 1: Start to get port code dictionary...")

    # Init connection
    conn = get_conn()
    try:
        # Init cursor
        with conn.cursor() as cursor:
            # Set sql statements
            # Notice: need modify
            sql = "SELECT P.port_code, P.port_name FROM ports.port_dict AS P;"

            # Execute eql statements
            cursor.execute(sql)

            # Get result
            port_code = cursor.fetchall()

            # Init container
            port_code_dict = {}
            for (code, name) in port_code:
                if code is None:
                    port_code_dict[name] = name
                else:
                    port_code_dict[code] = name
                    port_code_dict[name] = name

            logging.info("Port code dictionary loading completed~")
            print("Port code dictionary loading completed~")
    except Exception as e:
        logging.info(e)
        print(e)
    else:
        return port_code_dict
    finally:
        conn.close()

        logging.info("Database connection closed~")
        print("Database connection closed~")


# Function to get destination list
def get_destination():
    logging.info("=" * 60)
    logging.info("Step 2: Start to get (mmsi, destination) list...")
    print("=" * 60)
    print("Step 2: Start to get (mmsi, destination) list...")

    # Init connection
    conn = get_conn()

    try:
        # Init cursor
        with conn.cursor() as cursor:
            # Set sql statements
            # Notice: need modify
            sql = """SELECT TRIM(A.mmsi), A.destination, A.imo, A.eta, 
            A.match_end_port, A.match_end_type, A.score_end 
            FROM vessels.ais_info AS A 
            WHERE trim(A.destination) != '' AND (A.dest_update_time > A.match_time OR A.match_time IS NULL);
            """

            # Execute eql statements
            cursor.execute(sql)

            # Get result
            destination_list = cursor.fetchall()

            logging.info("Destination loading completed~")
            print("Destination loading completed~")
    except Exception as e:
        logging.info(e)
        print(e)
    else:
        return destination_list
    finally:
        conn.close()

        logging.info("Database connection closed~")
        print("Database connection closed~")


# Function to match port
def port_match(port_code_dict, destination_list, subprocess):
    logging.info("Matching subprocess {} start, subprocess ID is: {} ...".format(subprocess, os.getpid()))
    print("Matching subprocess {} start, subprocess ID is: {} ...".format(subprocess, os.getpid()))

    # Init connection
    conn = get_conn()
    cursor = conn.cursor()

    for count, (mmsi, des, imo, eta, history_name, history_type, history_score) in enumerate(destination_list):
        try:
            # 处理历史记录为null的情况
            if history_name is None:
                history_name = ''
                history_type = ''
                history_score = 0
            else:
                history_name = history_name.replace("'", "''")
                history_type = history_type.replace("'", "''")

            # 初步过滤用户输入值
            des_start, des_end = filter_des(des)

            # 如果用户仅输入终点港口
            if len(des_start) == 0:

                # 如果用户输入终点港口名称长度小于等于3或者满足相关业务规则，直接将结果设置为“未知”
                if len(des_end) <= 3 or 'order' in str.lower(des_end) or 'armed' in str.lower(
                        des_end) or 'guard' in str.lower(des_end):
                    end_name = 'Unknown'
                    end_type = 'Unknown'
                    end_score = 0

                    # 如果当前终点港口和上一次终点港口不一致，则更新相应港口ais_info数据和ais_track表
                    if end_name != history_name:
                        update_history_and_end(cursor, mmsi, history_name, history_type, history_score, end_name,
                                               end_type, end_score)

                        # 历史数据插入到ais_track
                        if history_name != 'Unknown':
                            insert_ais_track(cursor, imo, mmsi, history_name, eta)

                    # 如果当前终点港口和上一次终点港口一致，则仅更新匹配时间
                    else:
                        update_match_time(cursor, mmsi)

                # 如果用户输入正常港口名称
                else:
                    # 如果可以直接从港口字典中获取对应结果，则无需进行匹配，直接进行相应更新
                    if des_end in port_code_dict.keys():
                        end_name = port_code_dict[des_end].replace("'", "''")
                        end_type = "dictionary: " + port_code_dict[des_end].replace("'", "''")
                        end_score = 100

                        # 如果当前终点港口和上一次终点港口不一致，则更新相应港口数据和ais_track表
                        if end_name != history_name:
                            update_history_and_end(cursor, mmsi, history_name, history_type, history_score, end_name,
                                                   end_type, end_score)

                            # 历史数据插入到ais_track
                            if history_name != 'Unknown':
                                insert_ais_track(cursor, imo, mmsi, history_name, eta)

                        # 如果当前终点港口和上一次终点港口一致，则仅更新匹配时间
                        else:
                            update_match_time(cursor, mmsi)

                    # 如果港口字典中不存在对应结果，则进行匹配计算
                    else:
                        # 获取匹配结果：取TOP1
                        end_result = process.extract(des_end, port_code_dict.keys(), limit=1)[0]

                        # 获取匹配TOP1的分数
                        end_score = end_result[1]

                        # 如果匹配分数不为0，则获取匹配结果
                        if end_score != 0:
                            end_name = end_result[0].replace("'", "''")
                            end_type = "editDistance: " + end_result[0].replace("'", "''")
                        # 如果匹配分数为0，则将结果设置为“未知”
                        else:
                            end_name = 'Unknown'
                            end_type = 'Unknown'

                        # 如果当前终点港口和上一次终点港口不一致，则更新相应港口数据和ais_track表，并将匹配结果写入port_dict
                        if end_name != history_name:
                            update_history_and_end(cursor, mmsi, history_name, history_type, history_score, end_name,
                                                   end_type, end_score)

                            # 历史数据插入到ais_track
                            if history_name != 'Unknown':
                                insert_ais_track(cursor, imo, mmsi, history_name, eta)

                            # 新增port_dict
                            if des_end not in port_code_dict.keys():
                                port_code_dict[des_end] = end_name

                                insert_port_dict(cursor, des_end, end_name)

                        # 如果当前终点港口和上一次终点港口一致，则仅更新匹配时间
                        else:
                            update_match_time(cursor, mmsi)

            # 如果用户输入出发港口和终点港口
            else:
                # 处理出发港口
                # 如果用户输入出发港口名称长度小于等于3或者满足相关业务规则，直接将结果设置为“未知”
                if len(des_start) <= 3 or 'order' in str.lower(des_start) or 'armed' in str.lower(
                        des_start) or 'guard' in str.lower(des_start):
                    start_name = 'Unknown'
                    start_type = 'Unknown'
                    start_score = 0
                # 如果可以直接从港口字典中获取对应结果，则无需进行匹配，直接取值
                elif des_start in port_code_dict.keys():
                    start_name = port_code_dict[des_start].replace("'", "''")
                    start_type = "dictionary: " + port_code_dict[des_start].replace("'", "''")
                    start_score = 100
                # 如果港口字典中不存在对应结果，则进行匹配计算
                else:
                    start_result = process.extract(des_start, port_code_dict.keys(), limit=1)[0]

                    # 获取匹配TOP1的分数
                    start_score = start_result[1]

                    # 如果匹配分数不为0，则获取匹配结果
                    if start_score != 0:
                        start_name = start_result[0].replace("'", "''")
                        start_type = "editDistance: " + start_result[0].replace("'", "''")
                    # 如果匹配分数为0，则将结果设置为“未知”
                    else:
                        start_name = 'Unknown'
                        start_type = 'Unknown'

                    # 新增port_dict
                    if des_start in port_code_dict.keys():
                        port_code_dict[des_start] = start_name

                        insert_port_dict(cursor, des_start, start_name)

                # 处理终点港口
                # 如果用户输入终点港口名称长度小于等于3或者满足相关业务规则，直接将结果设置为“未知”
                if len(des_end) <= 3 or 'order' in str.lower(des_end) or 'armed' in str.lower(
                        des_end) or 'guard' in str.lower(des_end):
                    end_name = 'Unknown'
                    end_type = 'Unknown'
                    end_score = 0
                # 如果可以直接从港口字典中获取对应结果，则无需进行匹配，直接取值
                elif des_end in port_code_dict.keys():
                    end_name = port_code_dict[des_end].replace("'", "''")
                    end_type = "dictionary: " + port_code_dict[des_end].replace("'", "''")
                    end_score = 100
                # 如果港口字典中不存在对应结果，则进行匹配计算
                else:
                    end_result = process.extract(des_end, port_code_dict.keys(), limit=1)[0]

                    # 获取匹配TOP1的分数
                    end_score = end_result[1]

                    # 如果匹配分数不为0，则获取匹配结果
                    if end_score != 0:
                        end_name = end_result[0].replace("'", "''")
                        end_type = "editDistance: " + end_result[0].replace("'", "''")
                    # 如果匹配分数为0，则将结果设置为“未知”
                    else:
                        end_name = 'Unknown'
                        end_type = 'Unknown'

                    # 新增port_dict
                    if des_end not in port_code_dict.keys():
                        port_code_dict[des_end] = end_name

                        insert_port_dict(cursor, des_end, end_name)

                # 更新数据库
                # 如果当前终点港口和上一次终点港口不一致，则更新相应港口数据和ais_track表
                if end_name != history_name:
                    sql_5 = """UPDATE vessels.ais_info
                    SET match_start_port = '{}', match_start_type = '{}', score_start= {},
                    match_end_port = '{}', match_end_type = '{}', score_end = {}, match_time = CURRENT_TIMESTAMP
                    WHERE mmsi = '{}';
                    """.format(start_name, start_type, start_score, end_name, end_type, end_score, mmsi)

                    if history_name != 'Unknown':
                        sql_6 = """INSERT INTO vessels.ais_track (imo, mmsi, port, eta, created_time)
                        VALUES ('%s', '%s', '%s', '%s', CURRENT_TIMESTAMP);
                        """ % (imo, mmsi, history_name, eta)

                        cursor.execute(sql_6)

                    # Execute eql statements
                    cursor.execute(sql_5)

                # 如果当前终点港口和上一次终点港口一致，则仅更新匹配时间
                else:
                    update_match_time(cursor, mmsi)

        except Exception as e:
            logging.info(e)
            print(e)
            break
        else:
            conn.commit()
            logging.info(
                "Process {} Commit item {}: mmsi '{}', destination '{}'".format(subprocess, count + 1, mmsi, des))
            print("Process {} Commit item {}: mmsi '{}', destination '{}'".format(subprocess, count + 1, mmsi, des))

    cursor.close()
    conn.close()

    logging.info("-" * 40)
    logging.info("Process {} Commit total item number: {}".format(subprocess, len(destination_list)))
    logging.info("Database connection closed~")
    logging.info("Matching subprocess {} completed, subprocess ID is: {} ~".format(subprocess, os.getpid()))
    logging.info(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))

    print("-" * 40)
    print("Process {} Commit total item number: {}".format(subprocess, len(destination_list)))
    print("Database connection closed~")
    print("Matching subprocess {} completed, subprocess ID is: {} ~".format(subprocess, os.getpid()))
    print(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))


def update_history_and_end(cursor, mmsi, history_name, history_type, history_score, end_name, end_type, end_score):
    # Set sql statements
    # 将上一次终点港口更新到当前出发港口，将匹配结果更新到当前终点港口
    sql_1 = """UPDATE vessels.ais_info
    SET match_start_port = '{}', match_start_type = '{}', score_start= {},
    match_end_port = '{}', match_end_type = '{}', score_end = {}, match_time = CURRENT_TIMESTAMP
    WHERE mmsi = '{}';
    """.format(history_name, history_type, history_score, end_name, end_type, end_score, mmsi)

    # Execute eql statements
    cursor.execute(sql_1)


def insert_ais_track(cursor, imo, mmsi, history_name, eta):
    # 将上一次匹配结果插入到ais_track表
    sql_2 = """INSERT INTO vessels.ais_track (imo, mmsi, port, eta, created_time)
    VALUES ('%s', '%s', '%s', '%s', CURRENT_TIMESTAMP);
    """ % (imo, mmsi, history_name, eta)

    # Execute eql statements
    cursor.execute(sql_2)


def update_match_time(cursor, mmsi):
    # Set sql statements
    # 仅更新匹配时间
    sql_3 = """UPDATE vessels.ais_info
    SET match_time = CURRENT_TIMESTAMP
    WHERE mmsi = '{}';
    """.format(mmsi)

    # Execute eql statements
    cursor.execute(sql_3)


def insert_port_dict(cursor, key, value):
    sql_4 = """INSERT INTO ports.port_dict (port_code, port_name, source, flag, update_time)
    VALUES ('%s', '%s', '%s', '%s', CURRENT_TIMESTAMP)
    ON CONFLICT ON CONSTRAINT unique_port_code DO NOTHING;
    """ % (key, value, 1, 0)

    # Execute eql statements
    cursor.execute(sql_4)


def filter_des(des):
    des = str(des)
    des = des.replace("OFF", '')

    if '>' in des:
        index = des.index('>') + 1

        des_start = des[:index - 1]
        des_start = ''.join(list(filter(str.isalpha, des_start)))

        des_end = des[index:].strip('>')
        des_end = ''.join(list(filter(str.isalpha, des_end)))
    else:
        des_start = ''
        des_end = ''.join(list(filter(str.isalpha, des)))

    return des_start, des_end


# Function to split destination list
def groups(ls, step):
    if step == 0:
        logging.info("Target is empty")
        print("Target is empty")
        return []
    for i in range(0, len(ls), step):
        yield ls[i: i + step]


def run():
    logging.basicConfig(level=logging.INFO, filename='./port_match.log', filemode='w')

    logging.info("开始港口名称模糊匹配...")
    logging.info(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
    logging.info("*" * 100)

    print("开始港口名称模糊匹配...")
    print(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
    print("*" * 100)

    time_start = time.time()

    # Step 1
    port_code_dict = get_port_code_name()

    # Step 2
    destination_list = get_destination()
    # print("destination_list: ", len(destination_list))

    # Step 3
    logging.info("=" * 60)
    logging.info("Step 3: Start to match port name...")
    logging.info("Matching main processing start...")

    print("=" * 60)
    print("Step 3: Start to match port name...")
    print("Matching main processing start...")
    # Notice: Need modify
    core_num = 2
    pool = Pool(processes=core_num)
    step = math.ceil(len(destination_list) / core_num)
    destination_groups = groups(destination_list, step)

    for num, des_list in enumerate(destination_groups):
        if len(des_list) == 0:
            continue
        else:
            pool.apply_async(port_match, args=(port_code_dict, des_list, num,))

    pool.close()
    pool.join()

    logging.info("Matching main processing completed~")
    logging.info("=" * 60)

    print("Matching main processing completed~")
    print("=" * 60)

    time_end = time.time()
    time_c = time_end - time_start
    minute, second = divmod(time_c, 60)

    logging.info("Matching port name completed~")
    logging.info("Total completed: {}".format(len(destination_list)))
    logging.info("End, Time Cost: {} minutes, {} seconds".format(int(minute), round(second, 2)))
    logging.info("*" * 100)
    logging.info("完成港口模糊匹配~")
    logging.info(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))

    print("Matching port name completed~")
    print("Total completed: {}".format(len(destination_list)))
    print("End, Time Cost: {} minutes, {} seconds".format(int(minute), round(second, 2)))
    print("*" * 100)
    print("完成港口模糊匹配~")
    print(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))


if __name__ == '__main__':
    run()
