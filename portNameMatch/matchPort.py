import pandas as pd
from fuzzywuzzy import fuzz
import time


def port_match(destination_path, port_name_path, port_code_path):
    df_port_name = pd.read_csv(port_name_path)
    port_name_ls = df_port_name['port_name'].tolist()

    df_port_code = pd.read_csv(port_code_path)
    code_list = df_port_code['port_code'].tolist()
    name_list = df_port_code['port_name'].tolist()
    code_dic = {}
    for code, name in zip(code_list, name_list):
        code_dic[code] = name

    df_destination = pd.read_csv(destination_path)
    df_target = df_destination[['imo', 'sector', 'destination']]
    destination_list = df_target['destination'].tolist()

    # Start
    data = []
    for des in destination_list:
        ratio_list = []

        if '>' in str(des):
            index = des.index('>') + 1

            if 'OFF' in str(des):
                index_off = des.index('OFF')
                des = des[index: index_off].strip()
            else:
                des = des[index:].strip()

            for name in port_name_ls:
                ratio = fuzz.token_set_ratio(des, name)
                ratio_list.append((name + ' + name&&>', ratio))
            for code in code_dic.keys():
                ratio = fuzz.token_set_ratio(des, code)
                ratio_list.append((code_dic[code] + ' + code: ' + code + '&&>', ratio))
        else:
            for name in port_name_ls:
                ratio = fuzz.token_set_ratio(des, name)
                ratio_list.append((name + ' + name', ratio))
            for code in code_dic.keys():
                ratio = fuzz.token_set_ratio(des, code)
                ratio_list.append((code_dic[code] + ' + code: ' + code, ratio))

        ratio_rank = sorted(ratio_list, key=lambda x: x[1], reverse=True)[:5]

        scores_list = []
        for (name, ratio) in ratio_rank:
            scores_list.append(name)
            scores_list.append(ratio)

        data.append(scores_list)

    col_name = ['top1', 'score1', 'top2', 'score2', 'top3', 'score3', 'top4', 'score4', 'top5', 'score5']
    df_data = pd.DataFrame(data, columns=col_name)
    df_result = pd.concat([df_target, df_data], axis=1)

    df_result.to_csv('./data/result_total.csv', encoding='utf_8', header=1, index=0)


def run():
    destination_path = './data/destination_total.csv'
    port_name_path = './data/port_name.csv'
    port_code_path = './data/port_code_total.csv'

    time_start = time.time()
    print("Start...")
    port_match(destination_path, port_name_path, port_code_path)

    time_end = time.time()
    time_c = time_end - time_start
    print('End, Time Cost: ', time_c, 's')


if __name__ == '__main__':
    run()
