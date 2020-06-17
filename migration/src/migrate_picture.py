import pandas as pd
import time
from src.settings import get_conn


# Function to get picture data from table mol.t_crew_data
def load_data():
    # Init connection
    conn = get_conn()

    # Init cursor
    cursor = conn.cursor()
    sql = "USE mol"

    # Set query statement
    sql_1 = '''
            SELECT P.news_id, P.url, N.template, P.flag
            FROM (
                SELECT d.id AS news_id, d.pic_flag AS flag, f.oss_url AS url
                FROM t_crew_data AS d 
                LEFT JOIN t_crew_data_file_rel AS r ON d.url_crc = r.data_id
                LEFT JOIN t_crew_file AS f ON r.file_url_crc = f.file_url_crc
                WHERE d.template IS NOT NULL AND f.oss_url IS NOT NULL) AS P,
                news AS N
            WHERE P.news_id = N.id AND P.url IS NOT NULL
            '''

    # Execute query statement
    cursor.execute(sql)
    cursor.execute(sql_1)

    # Get data
    res = cursor.fetchall()

    # Convert to DataFrame
    df = pd.DataFrame(list(res))
    df.columns = ['news_id', 'url', 'template', 'flag']

    df_new = df[df['flag'] == 0]

    # Close connection
    cursor.close()
    conn.close()

    return df_new


# Function to set order for picture
def set_order(df_new):
    # Set order for template = T
    df_T = df_new[df_new['template'] == 'T']

    # Group by news_id and take first 3 data
    df_T_grouped = df_T.groupby(['news_id']).head(3)

    # Set order value
    order_ls = [1, 2, 3] * (int(len(df_T_grouped) / 3))
    df_T_grouped.insert(3, 'order', order_ls)

    # Set order for template != T
    df_single = df_new[df_new['template'] != 'T']

    # Group by news_id and take first 3 data
    df_single_grouped = df_single.groupby(['news_id']).head(1)

    # Set order value
    df_single_grouped.insert(3, 'order', 1)

    # Concat
    df_ordered = pd.concat([df_single_grouped, df_T_grouped])

    return df_ordered


# Function to insert picture data to table mol.news_picture
def write_to_mysql(df_ordered):
    # Init connection
    conn = get_conn()

    # Init cursor
    cursor = conn.cursor()

    news_id = df_ordered['news_id'].tolist()
    url = df_ordered['url'].tolist()
    order = df_ordered['order'].tolist()

    for i, u, o in zip(news_id, url, order):
        sql = "INSERT INTO mol.news_picture(news_id, url, `order`) VALUES ('%d', '%s', '%d') " % (i, u, o)
        cursor.execute(sql)

    conn.commit()

    # Close connection
    cursor.close()
    conn.close()


# Function to update pic_flag in table mol.t_crew_data
def update_pic_flag():
    # Init connection
    conn = get_conn()

    # Init cursor
    cursor = conn.cursor()

    # Set query statement
    sql = '''
            UPDATE mol.t_crew_data AS d, mol.news_picture AS p
            SET d.pic_flag = 1
            WHERE d.id = p.news_id
            AND d.pic_flag = 0
            '''

    cursor.execute(sql)
    conn.commit()

    # Close connection
    cursor.close()
    conn.close()


def run():
    time_start = time.time()
    print('Start ...')

    # Step1
    print("**************************")
    print('Start to Load Data...')
    df_new = load_data()
    print('Loading Completed!')

    # Step2
    print("**************************")
    print('Start to Set Order...')
    df_ordered = set_order(df_new)
    print("Order Completed!")

    # Step3
    print("**************************")
    print('Start to migrate picture data...')
    write_to_mysql(df_ordered)

    # Step4
    print("**************************")
    print('Start to Update Picture Flag...')
    update_pic_flag()

    print("**************************")
    print('Migration Completed!')

    time_end = time.time()
    time_c = time_end - time_start
    print('Time Cost: ', time_c, 's')


if __name__ == '__main__':
    run()
