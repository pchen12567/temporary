from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import sys
from settings import get_conn


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


def method_one(target, port_name_list, port_code_dict):
    ratio_list = []
    ratio_name = process.extract(target, port_name_list, limit=10)
    ratio_list.extend(ratio_name)

    ratio_code = process.extract(target, port_code_dict.keys(), limit=10)
    ratio_list.extend(ratio_code)
    print(ratio_list)

    ratio_rank = sorted(ratio_list, key=lambda x: x[1], reverse=True)[:5]
    print(ratio_rank)


def method_two(target, source):
    ratio_list = []
    ratio_name = process.extract(target, source, limit=10)
    ratio_list.extend(ratio_name)

    ratio_rank = sorted(ratio_list, key=lambda x: x[1], reverse=True)[:5]
    print(ratio_rank)


def method_three(target, port_name_list, port_code_dict):
    ratio_list = []
    for name in port_name_list:
        ratio = fuzz.token_set_ratio(target, name)
        ratio_list.append((name + ' + name', ratio))
    for code in port_code_dict.keys():
        ratio = fuzz.token_set_ratio(target, code)
        ratio_list.append((port_code_dict[code] + ' + code: ' + code, ratio))

    ratio_rank = sorted(ratio_list, key=lambda x: x[1], reverse=True)[:10]
    print(ratio_rank)


def run():
    print("开始测试...")
    port_code_dict, port_name_list = get_port_code_name()

    print("=" * 60)
    # print(len(sys.argv))

    if len(sys.argv) == 3:
        target = sys.argv[1]
        print("Target: ", target)
        flag = sys.argv[2]
        print("Flag: ", flag)
        print("-" * 40)

        if flag == '1':
            method_one(target, port_name_list, port_code_dict)
        elif flag == '3':
            method_three(target, port_name_list, port_code_dict)
        else:
            print("Error")

    if len(sys.argv) == 4:
        target = sys.argv[1]
        print("Target: ", target)
        flag = sys.argv[2]
        print("Flag: ", flag)
        source = sys.argv[3].split(",")
        print("Source: ", source)
        print("-" * 40)

        if flag == '2':
            method_two(target, source)
        elif flag == '4':
            pass
        else:
            print("Error")

    print("=" * 60)
    print("测试完成~")


if __name__ == '__main__':
    run()
