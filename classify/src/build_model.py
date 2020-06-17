import os
from multiprocessing import cpu_count
import numpy as np
import paddle
import paddle.fluid as fluid
from src.pre_model_data import get_dict_len
from src.settings import get_root_path, get_model_save_path
import time


def data_mapper(sample):
    data, label = sample
    data = [int(data) for data in data.split(',')]
    return data, int(label)


# Function to create train data reader
def train_extractor(data_root_path):
    def reader():
        # Read train data by line
        with open(os.path.join(data_root_path, 'train_list.txt'), 'r') as f:
            lines = f.readlines()

            # Shuffle data
            np.random.shuffle(lines)

            # Get each news title numerical ids and category label
            for line in lines:
                data, label = line.split('\t')
                yield data, label

    return paddle.reader.xmap_readers(data_mapper, reader, cpu_count(), 1024)


# Function to create test data reader
def test_extractor(data_root_path):
    def reader():
        # Read test data by line
        with open(os.path.join(data_root_path, 'test_list.txt'), 'r') as f:
            lines = f.readlines()

            # Get each news title numerical ids and category label
            for line in lines:
                data, label = line.split('\t')
                yield data, label

    return paddle.reader.xmap_readers(data_mapper, reader, cpu_count(), 1024)


# Function to create CNN
def CNN_net(data, dict_dim, class_dim=10, emb_dim=128, hid_dim=128, hid_dim2=98):
    emb = fluid.layers.embedding(input=data, size=[dict_dim, emb_dim])

    conv_3 = fluid.nets.sequence_conv_pool(
        input=emb,
        num_filters=hid_dim,
        filter_size=3,
        act='tanh',
        pool_type='sqrt')

    conv_4 = fluid.nets.sequence_conv_pool(
        input=emb,
        num_filters=hid_dim2,
        filter_size=4,
        act='tanh',
        pool_type='sqrt')

    output = fluid.layers.fc(
        input=[conv_3, conv_4],
        size=class_dim,
        act='softmax')

    return output


def save_model(model_save_path, words, model, exe):
    if not os.path.exists(model_save_path):
        os.makedirs(model_save_path)

    fluid.io.save_inference_model(dirname=model_save_path,
                                  feeded_var_names=[words.name],
                                  target_vars=[model],
                                  executor=exe)
    print("Model Saved!")


def run():
    time_start = time.time()
    print('Start...')
    print("****************************")

    # 定义输入数据， lod_level不为0指定输入数据为序列数据#
    words = fluid.layers.data(name='words', shape=[1], dtype='int64', lod_level=1)
    label = fluid.layers.data(name='label', shape=[1], dtype='int64')

    # Get file path
    data_root_path = get_root_path()
    # Get length of word dictionary
    dict_dim = get_dict_len(data_root_path)

    # Get classifier
    model = CNN_net(words, dict_dim)

    # 获取损失函数和准确率函数
    cost = fluid.layers.cross_entropy(input=model, label=label)
    avg_cost = fluid.layers.mean(cost)
    acc = fluid.layers.accuracy(input=model, label=label)

    # 定义优化方法
    optimizer = fluid.optimizer.AdagradOptimizer(learning_rate=0.001)
    opt = optimizer.minimize(avg_cost)

    # 获取预测程序
    test_program = fluid.default_main_program().clone(for_test=True)

    # 创建一个执行器，CPU训练速度比较慢
    place = fluid.CPUPlace()  # CPU
    # place = fluid.CUDAPlace(0)  # GPU
    exe = fluid.Executor(place)

    # 进行参数初始化
    exe.run(fluid.default_startup_program())

    # 获取训练数据读取器和测试数据读取器
    train_reader = paddle.batch(reader=train_extractor(data_root_path), batch_size=128)
    test_reader = paddle.batch(reader=test_extractor(data_root_path), batch_size=128)

    # 定义数据映射器
    feeder = fluid.DataFeeder(place=place, feed_list=[words, label])

    # 设置训练轮数
    EPOCH_NUM = 10

    for epoch_id in range(EPOCH_NUM):

        # 进行训练
        for batch_id, data in enumerate(train_reader()):
            # 对于 train_reader 中的每次batch，执行exe.run()运行执行器训练
            # 喂入每个batch的训练数据，fetch损失值、准确率
            train_cost, train_acc = exe.run(
                program=fluid.default_main_program(),
                feed=feeder.feed(data),
                fetch_list=[avg_cost, acc])

            # 每100个batch打印一次训练结果，一个batch包含128条数据
            if batch_id % 50 == 0:
                print('Epoch: {}, Batch: {}, Cost: {:.4f}, Acc: {:.4f}'.format(epoch_id, batch_id, float(train_cost),
                                                                               float(train_acc)))

        # 进行测试
        test_costs = []
        test_accs = []

        for batch_id, data in enumerate(test_reader()):
            # 对于 test_reader 中的每次batch，执行exe.run()运行执行器训练
            # 喂入每个batch的训练数据，fetch损失值、准确率
            test_cost, test_acc = exe.run(
                program=test_program,
                feed=feeder.feed(data),
                fetch_list=[avg_cost, acc])

            test_costs.append(test_cost[0])
            test_accs.append(test_acc[0])

        # 计算每轮所有batch的误差平均值、误差准确率，然后输出
        test_cost = (sum(test_costs) / len(test_costs))
        test_acc = (sum(test_accs) / len(test_accs))
        print('Test: {}, Cost: {:.4f}, Acc: {:.4f}'.format(epoch_id, float(test_cost), float(test_acc)))
        print("*************************************")

    # Save model file
    model_save_path = get_model_save_path()
    save_model(model_save_path, words, model, exe)

    print('Completed!')
    time_end = time.time()
    time_c = time_end - time_start
    print('Time cost: ', time_c, 's')


if __name__ == '__main__':
    run()
