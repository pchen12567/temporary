from fuzzywuzzy import process
from settings import get_conn
import pandas as pd
import time


# Function to get port code dictionary and port name list
def get_port_code_name():
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

            print("Port code dictionary and port name list loading completed~")
    except Exception as e:
        print(e)
    else:
        return port_code_dict, port_name_list
    finally:
        conn.close()
        print("Database connection closed~")


def match(target, port_name_list, port_code_dict):
    ratio_list = []
    ratio_name = process.extract(target, port_name_list, limit=10)
    ratio_list.extend(ratio_name)

    ratio_code = process.extract(target, port_code_dict.keys(), limit=10)
    ratio_list.extend(ratio_code)
    # print(ratio_list)

    ratio_rank = sorted(ratio_list, key=lambda x: x[1], reverse=True)[:5]
    # print(ratio_rank)

    return ratio_rank


def run():
    print(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
    print("*" * 80)
    target = input("Please input file name(only xlsx): ")

    directory = "../tool/"

    target_path = directory + target + '.xlsx'

    print("*" * 80)
    print("target_path: ", target_path)

    try:
        # Step 1
        time_start = time.time()

        port_code_dict, port_name_list = get_port_code_name()

        # Step 2
        print("=" * 60)
        print("Step 2: Get target list...")

        df = pd.read_excel(target_path)
        # print(df.head())
        target_list = list(df['port'])
        # print(target_list[:5])

        print("Total target number: ", len(target_list))

        # Step 3
        print("=" * 60)
        print("Step 3: Start to match...")
        prediction_list = []

        for count, t in enumerate(target_list):
            ratio_rank = match(t, port_name_list, port_code_dict)
            prediction_list.append(ratio_rank)
            print("target: ", t, ", completed~， total: ", count + 1)

        # Step 4
        print("=" * 60)
        print("Step 4: Save result...")
        # print(prediction_list[:5])
        df['prediction'] = prediction_list

        result_path = directory + target + '_result.xlsx'

        df.to_excel(result_path, index=False, encoding='utf-8')
        print("结果保存至：", result_path)
        print("*" * 80)

        time_end = time.time()
        time_c = time_end - time_start
        minute, second = divmod(time_c, 60)

        print("End, Time Cost: {} minutes, {} seconds".format(int(minute), round(second, 2)))
        print(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
    except Exception as e:
        print(e)


if __name__ == '__main__':
    run()
