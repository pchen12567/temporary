import time
from src.settings import get_conn


# Function to set level in table mol.t_crew_file
def set_level():
    # Init connection
    conn = get_conn()

    # Init cursor
    cursor = conn.cursor()

    # Set query statement to set L1
    sql_1 = '''UPDATE mol.t_crew_file 
                SET `level` = 'L1' 
                WHERE width >= 879 AND height >= 261 AND width/height > 2 AND `level` IS NULL'''

    # Set query statement to set L3
    sql_2 = '''UPDATE mol.t_crew_file 
                SET `level` = 'L3' 
                WHERE width >= 195  AND height >= 146 AND width/height <= 2 AND `level` IS NULL'''

    # Execute query statement
    cursor.execute(sql_1)
    cursor.execute(sql_2)

    conn.commit()

    # Close connection
    cursor.close()
    conn.close()


# Function to set template in table mol.t_crew_data
def set_template():
    # Init connection
    conn = get_conn()

    # Init cursor
    cursor = conn.cursor()
    sql = "USE mol"

    # Set query statement to '1' or '2'
    sql_1 = '''
            
            UPDATE t_crew_data AS D, (
                    SELECT t.id, COUNT(*) AS num
                    FROM(
                            SELECT d.id, d.url_crc, r.file_url_crc, f.`level`
                            FROM t_crew_data AS d 
                            LEFT JOIN t_crew_data_file_rel AS r ON d.url_crc = r.data_id 
                            LEFT JOIN t_crew_file AS f ON r.file_url_crc = f.file_url_crc) AS t
                    WHERE t.`level` = 'L3'
                    GROUP BY t.id
                    HAVING num >= 1
                    ) AS T
            SET D.template = FLOOR(1 + (RAND() * 2))
            WHERE D.id=T.id AND D.tem_flag = 0;
            '''

    # Set query statement to 'T'
    sql_2 = '''
            UPDATE t_crew_data AS D, (
                SELECT t.id, t.width, t.height, COUNT(*) AS num 
                FROM(
                    SELECT d.id, d.url_crc, r.file_url_crc, f.width, f.height, f.`level`
                    FROM t_crew_data AS d 
                    LEFT JOIN t_crew_data_file_rel AS r ON d.url_crc = r.data_id 
                    LEFT JOIN t_crew_file AS f ON r.file_url_crc = f.file_url_crc) AS t
                WHERE t.`level` = 'L3'
                GROUP BY t.id
                HAVING num >= 3 AND width >= 275 AND height >= 205 AND width/height <= 2
                ) AS T
            SET D.template = 'T'
            WHERE D.id=T.id AND D.tem_flag = 0
            '''

    # Set query statement to 'S'
    sql_3 = '''
            UPDATE t_crew_data AS D, (
                SELECT t.id, COUNT(*) AS num
                FROM(
                    SELECT d.id, d.url_crc, r.file_url_crc, f.`level` 
                    FROM t_crew_data AS d 
                    LEFT JOIN t_crew_data_file_rel AS r ON d.url_crc = r.data_id
                    LEFT JOIN t_crew_file AS f ON r.file_url_crc = f.file_url_crc) AS t
                WHERE t.`level` = 'L1'
                GROUP BY t.id
                HAVING num >= 1
                ) AS T
            SET D.template = 'S'
            WHERE D.id=T.id AND D.tem_flag = 0
            '''

    # Set query statement update '1'='L' and '2'='R'
    sql_4 = '''UPDATE t_crew_data
                SET template = (
                    CASE template WHEN '1' THEN 'L'
                    WHEN '2' THEN 'R'
                    WHEN 'S' THEN 'S'
                    WHEN 'T' THEN 'T'
                    END)
                WHERE tem_flag = 0
                '''

    sql_5 = '''
                UPDATE t_crew_data 
                SET tem_flag = 1
                WHERE template IS NOT NULL and tem_flag = 0
                '''

    # Execute query statement
    cursor.execute(sql)
    cursor.execute(sql_1)
    cursor.execute(sql_2)
    cursor.execute(sql_3)
    cursor.execute(sql_4)
    cursor.execute(sql_5)

    conn.commit()

    # Close connection
    cursor.close()
    conn.close()


# Function to set content_text in table mol.t_crew_data
def set_content_text():
    # Init connection
    conn = get_conn()

    # Init cursor
    cursor = conn.cursor()

    # Set query statement
    sql = '''
           UPDATE mol.t_crew_data
           SET content_text = SUBSTRING(content FROM 1 FOR 800)
           WHERE content_text IS NULL AND template IS NOT NULL
           '''

    # Execute query statement
    cursor.execute(sql)

    conn.commit()

    # Close connection
    cursor.close()
    conn.close()


# Function to migrate data from mol.t_crew_data to mol.news
def migrate_crawl():
    # Init connection
    conn = get_conn()

    # Init cursor
    cursor = conn.cursor()

    # Set query statement
    sql = '''
        INSERT IGNORE INTO mol.news(id, template, title, content_text, source, source_url, external_post_time, source_code)
        SELECT T.*
        FROM(
            SELECT D.id, D.template, D.title, D.content_text, D.source_name, D.url, D.resource_publish_time, D.resource
            FROM mol.t_crew_data AS D LEFT JOIN mol.news_source_config AS C
            ON D.resource = C.source_code
            WHERE C.source_status = 1) AS T
        WHERE T.template IS NOT NULL
        '''

    # Execute query statement
    cursor.execute(sql)

    conn.commit()

    # Close connection
    cursor.close()
    conn.close()


def run():
    time_start = time.time()
    print("Start...")

    # Step1
    print("**************************")
    print("Start to Set Level...")
    set_level()
    print('Level Completed!')

    # Step2
    print("**************************")
    print("Start to Set Template...")
    set_template()
    print('Template Completed!')

    # Step3
    print("**************************")
    print("Start to Set Content Text...")
    set_content_text()
    print('Content Text Completed!')

    # Step4
    print("**************************")
    print("Start to Insert Data...")
    migrate_crawl()
    print("Insertion Completed!")

    time_end = time.time()
    time_c = time_end - time_start
    print('Time Cost: ', time_c, 's')


if __name__ == '__main__':
    run()
