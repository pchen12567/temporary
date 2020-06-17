import paddle.fluid as fluid
from src.settings import get_model_save_path, get_root_path
import os
import numpy as np


# Function to get number code of each words for prediction news
def get_dict_code(sentence, data_root_path):
    # 读取数据字典文件
    with open(os.path.join(data_root_path, 'dict_en.txt'), 'r', encoding='utf-8') as f_data:
        dict_txt = eval(f_data.readlines()[0])

    # Convert data type to dictionary
    dict_txt = dict(dict_txt)

    # 把字符串数据转换成列表数据
    keys = dict_txt.keys()

    data = []

    for s in sentence:
        if s not in keys:
            s = '<unk>'

        data.append(int(dict_txt[s]))

    return np.array(data, dtype=np.int64)


# TO DO
def get_pre_data():
    return []


def run():
    # Init prediction place
    predict_place = fluid.CPUPlace()

    # Define a prediction executor
    predict_exe = fluid.Executor(predict_place)

    # Init prediction executor
    predict_exe.run(fluid.default_startup_program())

    # Load model
    model_save_path = get_model_save_path()
    [predict_program, predict_feeded_var_names, predict_target_var] = fluid.io.load_inference_model(
        dirname=model_save_path,
        executor=predict_exe)

    # TO TO
    # news = get_pre_data()
    # Test
    news = ['Samsung Heavy Industries Targets USD 7.8 Bn Orderbook',
            'Contact Made with Kidnappers of 20 Indian Sailors',
            'Euronav Sells Suezmax Tanker for Offshore Project',
            'Norden Selected for Long-Term Indian Contract',
            'Brokers: Hyundai Mipo Dockyard Wins Tanker Quartet Order']

    pre_data = []
    data_root_path = get_root_path()

    for i in range(len(news)):
        pre_data.append(get_dict_code(news[i], data_root_path))

    base_shape = [[len(w) for w in pre_data]]

    tensor_words = fluid.create_lod_tensor(pre_data, base_shape, predict_place)

    result = predict_exe.run(program=predict_program,
                             feed={predict_feeded_var_names[0]: tensor_words},
                             fetch_list=predict_target_var)

    category_names = ['BP', 'MI', 'IR']

    for i in range(len(pre_data)):
        lab = np.argsort(result)[0][i][-1]
        print(news[i])
        print('Label:{}, Category:{}, Probability:{}'.format(lab, category_names[lab], result[0][i][lab]))
        print('**********')


if __name__ == '__main__':
    run()