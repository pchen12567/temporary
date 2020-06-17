import multiprocessing
from multiprocessing.pool import Pool
import random
from time import sleep
import os


def groups(ls, step):
    for i in range(0, len(ls), step):
        yield ls[i: i + step]


def dayin(index, numbers):
    print("son {} start...son ID: {}".format(index, os.getpid()))
    print(numbers)
    print("---------")
    sleep(random.choice([5, 10, 15, 20, 25, 30]))
    print("son {} end...".format(index))


def run():
    ls = [i for i in range(203)]
    step = 20
    ls_groups = groups(ls, step)

    print("father start............")
    print("CPU number: {}".format(multiprocessing.cpu_count()))

    p = Pool(8)

    for i, g in enumerate(ls_groups):
        p.apply_async(dayin, args=(i, g,))

    p.close()
    p.join()

    print("Father end!!!")


if __name__ == '__main__':
    run()
