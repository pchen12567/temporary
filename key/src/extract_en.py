import pandas as pd
import re
from nltk.stem.wordnet import WordNetLemmatizer
import math
import time
from src.settings import get_conn, get_corpus_path


# Function to load total corpus
def load_corpus(corpus_path):
    corpus = []
    with open(corpus_path, 'r', encoding='utf8') as f:
        for news in f.readlines():
            corpus.append(news.strip('\n'))
    return corpus


# Function to load incremental data
def load_data():
    # Init connection
    conn = get_conn()

    # Init cursor
    cursor = conn.cursor()

    # Set query statement
    sql = "SELECT id, title, content FROM mol.t_crew_data WHERE pic_flag = 1 AND keywords_flag = 0"

    # Execute query statement
    cursor.execute(sql)

    # Get data
    res = cursor.fetchall()

    # Convert to Dataframe
    df = pd.DataFrame(list(res))
    df.columns = ['id', 'title', 'content']

    # Close connection
    cursor.close()
    conn.close()

    return df


def load_stopwords():
    # Load stop words list
    stop_words_path = './stopwords_english.txt'
    stop_list = []
    with open(stop_words_path, 'r') as f:
        for line in f:
            stop_list.append(line[0])
    return stop_list


# Function to pre-process incremental data
def pre_processing(news_list):
    # Init lemmatizer
    stem_wordnet = WordNetLemmatizer()

    # Get stop words list
    stop_words = load_stopwords()

    clean_incremental_news = []

    # Scan each news
    for news in news_list:
        # Only get English words token, replace others by space
        tokens_raw = re.sub("[^a-zA-z]", " ", news)

        # Remove duplicate space
        tokens_re = ' '.join(tokens_raw.split())

        # Cut words
        cut_tokens = tokens_re.split(' ')

        # Word lemmatization
        stem_tokens = [stem_wordnet.lemmatize(w) for w in cut_tokens]

        # Remove stop words
        tokens_without_stop = [w for w in stem_tokens if w not in stop_words]

        # Convert to lowercase letters
        tokens = [w.lower() for w in tokens_without_stop]

        clean_incremental_news.append(' '.join(tokens))

    return clean_incremental_news


# Function to calculate Term Frequency
def tf(word, document):
    words = document.split()
    return sum(1 for w in words if w == word) / len(document.split())


# Function to calculate Document Frequency
def document_frequency(word, corpus):
    return sum(1 for d in corpus if word in d)


# Function to calculate Inverse Document Frequency
def idf(word, corpus):
    return math.log10(len(corpus) / document_frequency(word, corpus))


# Function to calculate TF_IDF
def get_keywords(document, corpus):
    # Get unique words in a document
    words = set(document.split())

    # Get tf_idf list of each word in document
    # [(word, tf_idf)]
    tf_idf = [(w, tf(w, document) * idf(w, corpus)) for w in words]

    # Sort tf_idf list by tf_idf value
    tf_idf_rank = sorted(tf_idf, key=lambda x: x[1], reverse=True)

    return tf_idf_rank


def write_to_mysql(news_id, keywords):
    # Init connection
    conn = get_conn()

    # Init cursor
    cursor = conn.cursor()

    # Insert to database
    for index, tags in zip(news_id, keywords):
        for tag in tags:
            # Set query statement
            sql = """INSERT INTO mol.news_tag(news_id, tag) VALUES('%s', '%s')""" % (index, tag)

            # Execute query statement
            cursor.execute(sql)

        conn.commit()

    # Close connection
    cursor.close()
    conn.close()


def update_keywords_flag():
    # Init connection
    conn = get_conn()

    # Init cursor
    cursor = conn.cursor()

    # Set query statement
    sql = """
        UPDATE mol.t_crew_data
        SET keywords_flag = 1
        WHERE `id` in (SELECT DISTINCT news_id FROM mol.news_tag)
        AND keywords_flag = 0
        """

    cursor.execute(sql)
    conn.commit()

    # Close connection
    cursor.close()
    conn.close()


def run():
    time_start = time.time()
    print('Start to Extract KeyWords...')
    print("****************************")

    # Step 1
    print("Start to load total corpus")
    corpus_path = get_corpus_path()
    corpus = load_corpus(corpus_path)
    print("****************************")

    # Step 2
    print("Start to load incremental news data")
    incremental_df = load_data()
    incremental_news_list = incremental_df['content'].tolist()
    news_id = incremental_df['id'].tolist()
    # title = incremental_df['title'].tolist()
    print("****************************")

    # Step 3
    print("Start to pre-processing incremental news data")
    clean_incremental_news = pre_processing(incremental_news_list)
    print("****************************")

    # Step 4
    print("Start to extract top5 keywords")
    key_words_list = []
    for i in range(len(clean_incremental_news)):
        key_words_top5 = [keywords for (keywords, _) in
                          get_keywords(clean_incremental_news[i], corpus)[:5]]
        key_words_list.append(key_words_top5)
    print("****************************")

    # Step 5
    print("Start to write to database")
    write_to_mysql(news_id, key_words_list)
    update_keywords_flag()
    print("****************************")

    print('Extraction Completed')
    time_end = time.time()
    time_c = time_end - time_start
    print('Time cost: ', time_c, 's')


if __name__ == '__main__':
    run()
