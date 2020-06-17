import yaml
import pymysql


# Function to parse yaml file
def parse_yaml():
    with open('/extract_en.yaml') as f:
        cfg = f.read()

    cfg_dic = yaml.load(cfg, Loader=yaml.FullLoader)
    return cfg_dic


# Set DEV env database connection
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


# Function to get corpus path
def get_corpus_path():
    cfg_dic = parse_yaml()

    corpus_path = cfg_dic['corpus_path']

    return corpus_path
