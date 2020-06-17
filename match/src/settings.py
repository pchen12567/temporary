import yaml
import psycopg2
import logging


# Function to parse yaml file
def parse_yaml():
    logging.info("-" * 40)
    logging.info("Start to load config file...")
    print("-" * 40)
    print("Start to load config file...")

    config_file_path = '../port_match.yaml'

    try:
        with open(config_file_path) as f:
            cfg = f.read()
    except IOError:
        logging.info('Can not find: ', config_file_path)
        print('Can not find: ', config_file_path)
    else:
        cfg_dic = yaml.load(cfg, Loader=yaml.FullLoader)

        logging.info("Config file {} loading completed~".format(config_file_path))
        logging.info("-" * 40)
        print("Config file {} loading completed~".format(config_file_path))
        print("-" * 40)
        return cfg_dic


# Set DEV env database connection
def get_conn():
    logging.info("-" * 40)
    logging.info("Start to connect database...")
    print("-" * 40)
    print("Start to connect database...")

    cfg_dic = parse_yaml()

    database_dic = cfg_dic['database']
    # print(database_dic)

    try:
        conn = psycopg2.connect(
            host=database_dic['host'],
            port=database_dic['port'],
            user=database_dic['user'],
            password=database_dic['password'],
            database=database_dic['database']
        )
    except Exception as e:
        logging.info(e)
        print(e)
    else:
        logging.info(
            "Database host: {}, port: {} connection completed~".format(database_dic['host'], database_dic['port']))
        logging.info("-" * 40)
        print("Database host: {}, port: {} connection completed~".format(database_dic['host'], database_dic['port']))
        print("-" * 40)
        return conn
