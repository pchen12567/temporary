import pandas as pd
import re
from nltk.stem.wordnet import WordNetLemmatizer
import time
from src.settings import get_conn, get_corpus_path
import os


# Function to load total data
def load_data():
    # Init connection
    conn = get_conn()

    # Init cursor
    cursor = conn.cursor()

    # Set query statement
    sql = "SELECT id, title, content FROM mol.t_crew_data WHERE pic_flag = 1"

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


# Function to pre-process corpus
def pre_processing(news_list):
    # Init lemmatizer
    stem_wordnet = WordNetLemmatizer()

    # Get stop words list
    stop_words = load_stopwords()

    corpus = []

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

        corpus.append(' '.join(tokens))

    return corpus


# Function to save total clean news
def save_corpus(corpus):
    corpus_path = get_corpus_path()
    if not os.path.isfile(corpus_path):
        fd = open(corpus_path, mode="w", encoding="utf-8")
        fd.close()

    with open(corpus_path, 'w', encoding='utf-8') as f:
        for news in corpus:
            f.write(news + '\n')


def run():
    time_start = time.time()
    print('Start...')
    print("****************************")

    # Step 1
    print("Start to load total news data")
    df = load_data()
    news_list = df['content'].tolist()
    # news_id = df['id'].tolist()
    # title = df['title'].tolist()
    print("****************************")

    # Step 2
    print("Start to pre-processing total news data")
    corpus = pre_processing(news_list)
    print("****************************")

    # Step 3
    print("Start to save corpus")
    save_corpus(corpus)
    print("****************************")

    print('Completed!')
    time_end = time.time()
    time_c = time_end - time_start
    print('Time cost: ', time_c, 's')


if __name__ == '__main__':
    run()
