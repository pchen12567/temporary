from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import time
from src.settings import get_conn
from multiprocessing.pool import Pool
import os
import math
import logging


# Function to get port code dictionary and port name list
def get_port_code_name():
    logging.info("=" * 60)
    logging.info("Step 1: Start to get port code dictionary and port name list...")
    print("=" * 60)
    print("Step 1: Start to get port code dictionary and port name list...")

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
            port_name_list = []
            for (code, name) in port_code:
                if code is None:
                    port_name_list.append(name)
                else:
                    port_code_dict[code] = name
                    port_name_list.append(name)

            logging.info("Port code dictionary and port name list loading completed~")
            print("Port code dictionary and port name list loading completed~")
    except Exception as e:
        logging.info(e)
        print(e)
    else:
        return port_code_dict, port_name_list
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
            sql = """SELECT A.mmsi, A.destination, A.imo, A.eta,
            A.match_end_port, A.match_end_type, A.score_end
            FROM vessels.ais_info AS A
            WHERE trim(A.destination) != '' AND (A.dest_update_time > A.match_time OR A.match_time IS NULL);
            """

            # sql = """SELECT A.mmsi, A.destination, A.imo, A.eta,
            # A.match_end_port, A.match_end_type, A.score_end
            # FROM vessels.ais_info AS A
            # WHERE trim(A.destination) != '' AND A.mmsi = '477141800';
            # """

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


def port_match(port_name_list, port_code_dict, destination_list, subprocess):
    logging.info("Matching subprocess {} start, subprocess ID is: {} ...".format(subprocess, os.getpid()))
    print("Matching subprocess {} start, subprocess ID is: {} ...".format(subprocess, os.getpid()))

    # Init connection
    conn = get_conn()
    cursor = conn.cursor()

    for count, (mmsi, des, imo, eta, history_name, history_type, history_score) in enumerate(
            destination_list):
        try:
            ratio_start_list = []
            ratio_end_list = []

            if history_name is None:
                history_name = ''

            if history_type is None:
                history_type = ''

            if history_score is None:
                history_score = 0

            des_filter = ''.join(list(filter(str.isalpha, des)))
            if len(des_filter) <= 3 or 'order' in str.lower(des) or 'armed' in str.lower(des) or 'guards' in str.lower(
                    des):
                end_name = 'Unknown'
                end_type = 'Unknown'
                end_score = 0

                if end_name != history_name:
                    # Set sql statements
                    sql_1 = """UPDATE vessels.ais_info 
                    SET match_start_port = '{}', match_start_type = '{}', score_start= {},
                    match_end_port = '{}', match_end_type = '{}', score_end = {}, match_time = CURRENT_TIMESTAMP 
                    WHERE mmsi = '{}';
                    """.format(history_name.replace("'", "''"), history_type, history_score, end_name, end_type,
                               end_score, mmsi)

                    sql_2 = """INSERT INTO vessels.ais_track (imo, mmsi, port, eta, created_time)
                    VALUES ('%s', '%s', '%s', '%s', CURRENT_TIMESTAMP);
                    """ % (imo, mmsi, history_name.replace("'", "''"), eta)

                    # Execute eql statements
                    cursor.execute(sql_1)

                    cursor.execute(sql_2)
                else:
                    # Set sql statements
                    sql = """UPDATE vessels.ais_info
                    SET match_time = CURRENT_TIMESTAMP
                    WHERE mmsi = '{}';
                    """.format(mmsi)

                    # Execute eql statements
                    cursor.execute(sql)

                continue

            if '>' in str(des):
                index = des.index('>') + 1

                des_start = des[:index - 1].strip()

                des_end = des[index:].strip().strip('>')
                if 'OFF' in str(des_end):
                    index_off = des_end.index('OFF')
                    des_end = des_end[: index_off].strip()

                if len(des_start) != 0:
                    # Match start port name
                    ratio_start_name = process.extract(des_start, port_name_list, limit=1)[0]
                    ratio_start_list.append((ratio_start_name[0], 'name & arrow', ratio_start_name[1]))

                    ratio_start_code = process.extract(des_start, port_code_dict.keys(), limit=1)[0]
                    ratio_start_list.append((port_code_dict[ratio_start_code[0]],
                                             'code: ' + ratio_start_code[0] + ' & arrow',
                                             ratio_start_code[1]))

                    top_start_ratio = sorted(ratio_start_list, key=lambda x: x[2], reverse=True)[0]

                    start_score = top_start_ratio[2]
                    if start_score != 0:
                        start_name = top_start_ratio[0].replace("'", "''")
                        start_type = top_start_ratio[1]
                    else:
                        start_name = 'Unknown'
                        start_type = 'Unknown'

                    # Match end port name
                    ratio_end_name = process.extract(des_end, port_name_list, limit=1)[0]
                    ratio_end_list.append((ratio_end_name[0], 'name & arrow', ratio_end_name[1]))

                    ratio_end_code = process.extract(des_end, port_code_dict.keys(), limit=1)[0]
                    ratio_end_list.append((port_code_dict[ratio_end_code[0]],
                                           'code: ' + ratio_end_code[0] + ' & arrow',
                                           ratio_end_code[1]))

                    top_end_ratio = sorted(ratio_end_list, key=lambda x: x[2], reverse=True)[0]

                    end_score = top_end_ratio[2]
                    if end_score != 0:
                        end_name = top_end_ratio[0].replace("'", "''")
                        end_type = top_end_ratio[1]
                    else:
                        end_name = 'Unknown'
                        end_type = 'Unknown'

                    if end_name != history_name:
                        # Set sql statements
                        sql_1 = """UPDATE vessels.ais_info 
                        SET match_start_port = '{}', match_start_type = '{}', score_start= {},
                        match_end_port = '{}', match_end_type = '{}', score_end = {}, match_time = CURRENT_TIMESTAMP 
                        WHERE mmsi = '{}';
                        """.format(start_name, start_type, start_score, end_name, end_type, end_score, mmsi)

                        sql_2 = """INSERT INTO vessels.ais_track (imo, mmsi, port, eta, created_time)
                        VALUES ('%s', '%s', '%s', '%s', CURRENT_TIMESTAMP);
                        """ % (imo, mmsi, start_name, eta)

                        # Execute eql statements
                        cursor.execute(sql_1)

                        cursor.execute(sql_2)
                    else:
                        # Set sql statements
                        sql = """UPDATE vessels.ais_info
                        SET match_time = CURRENT_TIMESTAMP
                        WHERE mmsi = '{}';
                        """.format(mmsi)

                        # Execute eql statements
                        cursor.execute(sql)

                else:
                    # Match end port name
                    ratio_end_name = process.extract(des_end, port_name_list, limit=1)[0]
                    ratio_end_list.append((ratio_end_name[0], 'name & arrow', ratio_end_name[1]))

                    ratio_end_code = process.extract(des_end, port_code_dict.keys(), limit=1)[0]
                    ratio_end_list.append((port_code_dict[ratio_end_code[0]],
                                           'code: ' + ratio_end_code[0] + ' & arrow',
                                           ratio_end_code[1]))

                    top_end_ratio = sorted(ratio_end_list, key=lambda x: x[2], reverse=True)[0]

                    end_score = top_end_ratio[2]
                    if end_score != 0:
                        end_name = top_end_ratio[0].replace("'", "''")
                        end_type = top_end_ratio[1]
                    else:
                        end_name = 'Unknown'
                        end_type = 'Unknown'

                    if end_name != history_name:
                        # Set sql statements
                        sql_1 = """UPDATE vessels.ais_info 
                        SET match_start_port = '{}', match_start_type = '{}', score_start= {},
                        match_end_port = '{}', match_end_type = '{}', score_end = {}, match_time = CURRENT_TIMESTAMP 
                        WHERE mmsi = '{}';
                        """.format(history_name.replace("'", "''"), history_type, history_score, end_name, end_type,
                                   end_score, mmsi)

                        sql_2 = """INSERT INTO vessels.ais_track (imo, mmsi, port, eta, created_time)
                        VALUES ('%s', '%s', '%s', '%s', CURRENT_TIMESTAMP);
                        """ % (imo, mmsi, history_name.replace("'", "''"), eta)

                        # Execute eql statements
                        cursor.execute(sql_1)

                        cursor.execute(sql_2)
                    else:
                        # Set sql statements
                        sql = """UPDATE vessels.ais_info
                        SET match_time = CURRENT_TIMESTAMP
                        WHERE mmsi = '{}';
                        """.format(mmsi)

                        # Execute eql statements
                        cursor.execute(sql)

            else:
                # Match end port name
                ratio_end_name = process.extract(des, port_name_list, limit=1)[0]
                ratio_end_list.append((ratio_end_name[0], 'name', ratio_end_name[1]))

                ratio_end_code = process.extract(des, port_code_dict.keys(), limit=1)[0]
                ratio_end_list.append((port_code_dict[ratio_end_code[0]],
                                       'code: ' + ratio_end_code[0],
                                       ratio_end_code[1]))

                top_ratio = sorted(ratio_end_list, key=lambda x: x[2], reverse=True)[0]

                end_score = top_ratio[2]
                if end_score != 0:
                    end_name = top_ratio[0].replace("'", "''")
                    end_type = top_ratio[1]
                else:
                    end_name = 'Unknown'
                    end_type = 'Unknown'

                if end_name != history_name:
                    # Set sql statements
                    sql_1 = """UPDATE vessels.ais_info
                    SET match_start_port = '{}', match_start_type = '{}', score_start= {},
                    match_end_port = '{}', match_end_type = '{}', score_end = {}, match_time = CURRENT_TIMESTAMP
                    WHERE mmsi = '{}';
                    """.format(history_name.replace("'", "''"), history_type, history_score, end_name, end_type,
                               end_score, mmsi)

                    sql_2 = """INSERT INTO vessels.ais_track (imo, mmsi, port, eta, created_time)
                    VALUES ('%s', '%s', '%s', '%s', CURRENT_TIMESTAMP);
                    """ % (imo, mmsi, history_name.replace("'", "''"), eta)

                    # Execute eql statements
                    cursor.execute(sql_1)

                    cursor.execute(sql_2)
                else:
                    # Set sql statements
                    sql = """UPDATE vessels.ais_info
                    SET match_time = CURRENT_TIMESTAMP
                    WHERE mmsi = '{}';
                    """.format(mmsi)

                    # Execute eql statements
                    cursor.execute(sql)

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
    port_code_dict, port_name_list = get_port_code_name()
    # print(port_name_list[:5])

    # Step 2
    destination_list = get_destination()
    # print("destination_list: ", destination_list)

    # Step 3
    logging.info("=" * 60)
    logging.info("Step 3: Start to match port name...")
    logging.info("Matching main processing start...")

    print("=" * 60)
    print("Step 3: Start to match port name...")
    print("Matching main processing start...")
    # Notice: Need modify
    core_num = 1
    pool = Pool(processes=core_num)
    step = math.ceil(len(destination_list) / core_num)
    destination_groups = groups(destination_list, step)

    for num, des_list in enumerate(destination_groups):
        if len(des_list) == 0:
            continue
        else:
            pool.apply_async(port_match, args=(port_name_list, port_code_dict, des_list, num,))

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
