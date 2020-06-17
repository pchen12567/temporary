import time
from src.settings import get_conn, get_url


# Function to generate table cms.cms_tmp
def pre_processing():
    url_head = get_url()

    # Init connection
    conn = get_conn()

    # Init cursor
    cursor = conn.cursor()
    sql = "USE cms"

    # Set query statement to get id, tag, title, resource_publish_time
    sql_1 = """INSERT IGNORE INTO cms_tmp(id, tag, title, resource_publish_time)
            SELECT id, `code`, `subject`, update_date FROM article AS a
            WHERE a.is_active = 1 
            AND a.`code` in ('articles', 'market', 'people')
            """

    # Set query statement to set source_name
    sql_2 = """UPDATE cms_tmp
            SET source_name = 'Marine Online'
            WHERE source_name IS NULL
            """

    # Set query statement to set template and tem_flag
    sql_3 = """UPDATE cms_tmp
            SET template = 'L', tem_flag = 1
            WHERE template IS NULL
            """

    # Set query statement to set url
    sql_4 = """UPDATE cms_tmp SET url = CONCAT('%s', cms_tmp.id) WHERE url IS NULL""" % url_head

    # Set query statement to set pic_url
    sql_5 = """UPDATE cms_tmp AS t1,
            (select * from (
            select id,json_extract_c(data,"$.featurePic") as pic
            from cms.article a
            where a.is_active=1) AS t
            where t.pic is not null and t.pic <>'') AS t2
            SET t1.pic_url = t2.pic
            WHERE t1.id = t2.id
            """

    # Set unique identification for cms migration data
    sql_6 = """UPDATE cms_tmp
            SET created_by = 'cms_migrator'
            WHERE created_by IS NULL
            """

    # Set category from table category_match
    sql_7 = """UPDATE cms.cms_tmp AS T, cms.category_match AS M
            SET T.category = M.category
            WHERE T.id = M.newsId
            AND T.category IS NULL
            """

    # Set content from table article
    sql_8 = """UPDATE cms.cms_tmp AS C,
            (SELECT id, json_extract_c(data, "$.content") AS content
            FROM cms.article AS A
            WHERE A.is_active = 1) AS T
            SET C.content = T.content
            WHERE C.id = T.id
            """

    # Execute query statement
    cursor.execute(sql)
    cursor.execute(sql_1)
    cursor.execute(sql_2)
    cursor.execute(sql_3)
    cursor.execute(sql_4)
    cursor.execute(sql_5)
    cursor.execute(sql_6)
    cursor.execute(sql_7)
    cursor.execute(sql_8)

    conn.commit()

    # Close connection
    cursor.close()
    conn.close()


# Function to migrate data from cms.cms_tmp to mol.news
def migrate_news():
    # Init connection
    conn = get_conn()

    # Init cursor
    cursor = conn.cursor()

    # Set query statement
    sql_1 = '''
        INSERT IGNORE INTO mol.news(id, template, title, content, source, source_url, external_post_time, create_by) 
        SELECT id, template, title, content, source_name, url, resource_publish_time, created_by FROM cms.cms_tmp AS C
        WHERE C.pic_url IS NOT NULL
        '''

    # Set cource_code
    sql_2 = '''
        UPDATE mol.news
        SET source_code = 'marineonline'
        WHERE source = 'Marine Online'
        AND source_code IS NULL
        '''

    # Set is_original from 0 to 1
    sql_3 = """UPDATE mol.news AS N, cms.cms_tmp AS C
            SET N.is_original = 1
            WHERE N.id = C.id
            AND N.source_code = 'marineonline'
            AND N.create_by = 'cms_migrator'
            AND N.is_original = 0
            """

    # Execute query statement
    cursor.execute(sql_1)
    cursor.execute(sql_2)
    cursor.execute(sql_3)

    conn.commit()

    # Close connection
    cursor.close()
    conn.close()


def migrate_picture():
    # Init connection
    conn = get_conn()

    # Init cursor
    cursor = conn.cursor()

    # Set query statement
    sql_1 = '''
            INSERT IGNORE INTO mol.news_picture(news_id, url)
            SELECT id, pic_url FROM cms.cms_tmp AS T
            WHERE T.pic_flag = 0 AND T.pic_url IS NOT NULL
            AND T.id NOT IN (SELECT news_id FROM mol.news_picture)
            '''

    sql_2 = """
            UPDATE cms.cms_tmp
            SET pic_flag = 1
            WHERE pic_url IS NOT NULL
            """

    sql_3 = """
                UPDATE mol.news_picture AS t1, mol.news AS t2
                SET t1.`order` = 1
                WHERE t1.news_id = t2.id AND t2.source = 'Marine Online' AND t1.`order` = 0
                """

    # Execute query statement
    cursor.execute(sql_1)
    cursor.execute(sql_2)
    cursor.execute(sql_3)

    conn.commit()

    # Close connection
    cursor.close()
    conn.close()


def migrate_tag():
    # Init connection
    conn = get_conn()

    # Init cursor
    cursor = conn.cursor()

    # Set query statement
    sql_1 = """
        INSERT IGNORE INTO mol.news_tag(news_id, tag)
        SELECT id, tag FROM cms.cms_tmp AS T
        WHERE T.pic_url IS NOT NULL AND T.tag_flag = 0
        """
    sql_2 = """
        UPDATE cms.cms_tmp
        SET tag_flag = 1
        WHERE pic_url IS NOT NULL
        """
    # Execute query statement
    cursor.execute(sql_1)
    cursor.execute(sql_2)

    conn.commit()

    # Close connection
    cursor.close()
    conn.close()


def run():
    time_start = time.time()
    print("Start...")

    # Step1
    print("**************************")
    print("Start to Generate table cms_tmp...")
    pre_processing()
    print("Generation cms_tmp Completed!")

    print("**************************")
    print("Start to Move cms to news...")
    migrate_news()
    print("CMS news Migration Completed!")

    print("**************************")
    print("Start to Move cms to news_picture...")
    migrate_picture()
    print("CMS picture Migration Completed!")

    print("**************************")
    print("Start to Move cms to news_tag...")
    migrate_tag()
    print("CMS tag Migration Completed!")

    print("**************************")
    print("CMS Data Migration Completed!")

    time_end = time.time()
    time_c = time_end - time_start
    print('Time Cost: ', time_c, 's')


if __name__ == "__main__":
    run()
