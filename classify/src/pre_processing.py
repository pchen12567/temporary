from src.settings import get_conn, get_root_path
import pandas as pd
import re
from nltk.stem.wordnet import WordNetLemmatizer
import time
import os


# Function to load total data
def load_data():
    # Init connection
    conn = get_conn()

    # Init cursor
    cursor = conn.cursor()

    # Set query statement
    # Just get Marine Online news for testing temporarily
    sql = "SELECT id, title, category FROM mol.news WHERE source_code = 'marineonline' and category IS NOT NULL and category != ''"

    # Execute query statement
    cursor.execute(sql)

    # Get data
    res = cursor.fetchall()

    # Close connection
    cursor.close()
    conn.close()

    return res


# Function to clean string
def clean_str(string):
    """
    Tokenization/string cleaning for all datasets except for SST.
    """
    # acronym
    string = re.sub(r"can\'t", "can not", string)
    string = re.sub(r"cannot", "can not ", string)
    string = re.sub(r"what\'s", "what is", string)
    string = re.sub(r"What\'s", "what is", string)
    string = re.sub(r"\'ve ", " have ", string)
    string = re.sub(r"n\'t", " not ", string)
    string = re.sub(r"i\'m", "i am ", string)
    string = re.sub(r"I\'m", "i am ", string)
    string = re.sub(r"\'re", " are ", string)
    string = re.sub(r"\'d", " would ", string)
    string = re.sub(r"\'ll", " will ", string)
    string = re.sub(r" e mail ", " email ", string)
    string = re.sub(r" e \- mail ", " email ", string)
    string = re.sub(r" e\-mail ", " email ", string)

    # spelling correction
    string = re.sub(r"ph\.d", "phd", string)
    string = re.sub(r"PhD", "phd", string)
    string = re.sub(r" e g ", " eg ", string)
    string = re.sub(r" fb ", " facebook ", string)
    string = re.sub(r"facebooks", " facebook ", string)
    string = re.sub(r"facebooking", " facebook ", string)
    string = re.sub(r"usa", "america", string)
    string = re.sub(r"us", "america", string)
    string = re.sub(r"u s", "america", string)
    string = re.sub(r"U\.S\.", "america", string)
    string = re.sub(r"US", "america", string)
    string = re.sub(r"American", "america", string)
    string = re.sub(r"America", "america", string)
    string = re.sub(r"Trump\'s", "trump", string)
    string = re.sub(r"China\'s", "china", string)
    string = re.sub(r"OPEC\'s", "opec", string)
    string = re.sub(r"Singapore\'s", "singapore", string)
    string = re.sub(r"Aramco\'s", "aramco", string)
    string = re.sub(r"Japan\'s", "japan", string)
    string = re.sub(r"Saudi\'s", "saudi", string)
    string = re.sub(r"Pakistan\'s", "pakistan", string)
    string = re.sub(r"Fujairah\'s", "fujairah", string)
    string = re.sub(r"HSFO\'s", "hsfo", string)
    string = re.sub(r"LSFO\'s", "lsfo", string)
    string = re.sub(r"\'s", "", string)

    # symbol replacement
    string = re.sub(r"&", " and ", string)
    string = re.sub(r"\|", " or ", string)
    string = re.sub(r"=", " equal ", string)
    string = re.sub(r"\+", " plus ", string)
    string = re.sub(r"\$", " dollar ", string)
    string = re.sub(r"[^A-Za-z0-9(),!?\'\`]", " ", string)
    string = re.sub(r",", "", string)
    string = re.sub(r"\'", "", string)
    string = re.sub(r"!", " ! ", string)
    string = re.sub(r"\(", "", string)
    string = re.sub(r"\)", "", string)
    string = re.sub(r"\?", "", string)
    string = re.sub(r"\s{2,}", " ", string)
    string = string.strip().lower()

    # Word lemmatization
    # Init lemmatizer
    stem_wordnet = WordNetLemmatizer()
    stem_token = [stem_wordnet.lemmatize(w) for w in string.split()]

    return ' '.join(i for i in stem_token)


# Function to pre-process corpus
def pre_processing(data):
    if len(data) == 0:
        print("Database is empty!")
    else:
        # Convert to Dataframe
        df = pd.DataFrame(list(data))
        df.columns = ['id', 'title', 'category']
        df['title'] = df['title'].apply(lambda x: x.strip().replace('\n', ""))
        df['category'] = df['category'].apply(lambda x: x.strip().replace('\n', ""))
        df['clean_title'] = df['title'].apply(lambda x: clean_str(x))

        # print(df[['id', 'category']])

        # Set category map
        lab_dict = {'BP': 0, 'MI': 1, 'IR': 2}
        # Set label by numbers
        df['label'] = df['category'].apply(lambda x: lab_dict[x])

        # Save corpus
        data_root_path = get_root_path()
        df_res = df.loc[:, ['id', 'clean_title', 'category', 'label']]
        df_res.to_csv(os.path.join(data_root_path, 'corpus_en.txt'), sep='\t', index=False, header=None)


def run():
    time_start = time.time()
    print('Start...')
    print("****************************")

    # Step 1
    print("Start to load total news title data")
    data = load_data()
    print("****************************")

    # Step 2
    print("Start to pre-processing total news title data")
    pre_processing(data)
    print("****************************")

    print('Completed!')
    time_end = time.time()
    time_c = time_end - time_start
    print('Time cost: ', time_c, 's')


if __name__ == '__main__':
    run()
