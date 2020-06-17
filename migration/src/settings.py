import yaml
import pymysql


# Function to parse yaml file
def parse_yaml():
    with open('/data_migration.yaml') as f:
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


# Function to get cms data url head
def get_url():
    cfg_dic = parse_yaml()
    url_head = cfg_dic['cms_url']

    return url_head
