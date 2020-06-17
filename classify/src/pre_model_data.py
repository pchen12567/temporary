from src.settings import get_root_path
import os
import time


# Function to generate word dictionary
def create_word_dict(data_root_path):
    # Init dictionary container
    dict_set = set()

    # Scan corpus by line
    with open(os.path.join(data_root_path, 'corpus_en.txt'), 'r', encoding='utf-8') as f:
        lines = f.readlines()

    for line in lines:
        # Get each news title
        title = line.split('\t')[1].replace('\n', "")

        # Save each word into container of title
        for t in title.split():
            dict_set.add(t)

    # Init dictionary list
    dict_list = []

    # Init id
    i = 0

    # Save each word into dictionary list with id
    for w in dict_set:
        dict_list.append([w, i])
        i += 1

    # Build word dictionary
    dict_txt = dict(dict_list)

    # Add <unk> by hand
    end_dict = {"<unk>": i}
    dict_txt.update(end_dict)

    # Save word dictionary
    with open(os.path.join(data_root_path, 'dict_en.txt'), 'w', encoding='utf-8') as f:
        f.write(str(dict_txt))

    print("Word Dictionary Completed!")


# Function to generate train and test data lists according to raw data
def create_data_list(data_root_path):
    # Create test data list
    with open(os.path.join(data_root_path, 'test_list.txt'), 'w') as f:
        pass

    # Create train data list
    with open(os.path.join(data_root_path, 'train_list.txt'), 'w') as f:
        pass

    # Load word dictionary file
    with open(os.path.join(data_root_path, 'dict_en.txt'), 'r', encoding='utf-8') as f_data:
        dict_txt = eval(f_data.readlines()[0])

    # Load corpus by line
    with open(os.path.join(data_root_path, 'corpus_en.txt'), 'r', encoding='utf-8') as f_data:
        lines = f_data.readlines()

    # Init index
    i = 0

    # Read raw data by line
    for line in lines:
        # Get current news title
        title = line.split('\t')[1].replace('\n', "")

        # Get current news label
        lab = line.split('\t')[-1].replace('\n', "")

        # Init current news number ids
        title_ids = ""

        # Pick test data each 10 news
        if i % 10 == 0:
            with open(os.path.join(data_root_path, 'test_list.txt'), 'a', encoding='utf-8') as f_test:
                for word in title.split():
                    # Get each word`s number id of current news title
                    # 获取当前标题中每个字在数据字典中对应的id
                    word_id = str(dict_txt[word])

                    # Concat words` number id by comma
                    # 拼接每一个字对应的id形成标题的完整ids，中间用逗号隔开
                    title_ids += word_id + ','

                # Delete the last comma
                title_ids = title_ids[:-1]

                # Concat current news title number ids with label by 'table'
                title_ids = title_ids + '\t' + lab + '\n'

                # Save to test list file
                f_test.write(title_ids)

        else:
            # Pick others as train data
            with open(os.path.join(data_root_path, 'train_list.txt'), 'a', encoding='utf-8') as f_train:
                for word in title.split():
                    # Get each word`s number id of current news title
                    # 获取当前标题中每个字在数据字典中对应的id
                    word_id = str(dict_txt[word])

                    # Concat words` number id by comma
                    # 拼接每一个字对应的id形成标题的完整ids，中间用逗号隔开
                    title_ids += word_id + ','

                # Delete the last comma
                title_ids = title_ids[:-1]

                # Concat current news title number ids with label by 'table'
                title_ids = title_ids + '\t' + lab + '\n'

                # Save to train list file
                f_train.write(title_ids)

        i += 1

    print('Data List Generation Completed！')


# Function to get length of word dictionary
def get_dict_len(data_root_path):
    with open(os.path.join(data_root_path, 'dict_en.txt'), 'r', encoding='utf-8') as f:
        # eval() function: switch str to dict
        line = eval(f.readlines()[0])

    return len(line.keys())


def run():
    time_start = time.time()
    print('Start...')
    print("****************************")

    # Step 1
    # Get file path
    data_root_path = get_root_path()

    # Step 2
    print("Start to create word dictionary...")
    create_word_dict(data_root_path)
    print("****************************")

    # Step 3
    print("Start to create data list...")
    create_data_list(data_root_path)
    print("****************************")

    print('Completed!')
    time_end = time.time()
    time_c = time_end - time_start
    print('Time cost: ', time_c, 's')


if __name__ == "__main__":
    run()
