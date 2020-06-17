import pymysql
import yaml


# Function to parse yaml file
def parse_yaml():
    with open('/classify_en.yaml') as f:
        cfg = f.read()

    cfg_dic = yaml.load(cfg, Loader=yaml.FullLoader)
    return cfg_dic


# Set database connection
def get_conn():
    cfg_dic = parse_yaml()

    database_dic = cfg_dic['database']

    conn = pymysql.connect(
        host=database_dic['host'],
        port=database_dic['port'],
        user=database_dic['user'],
        password=database_dic['password'],
        charset="utf8"
    )

    return conn


# Function to get data root path
def get_root_path():
    cfg_dic = parse_yaml()

    data_root_path = cfg_dic['data_root_path']

    return data_root_path


# Function to get model save path
def get_model_save_path():
    cfg_dic = parse_yaml()

    model_save_path = cfg_dic['model_save_path']

    return model_save_path
