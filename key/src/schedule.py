import time
from apscheduler.schedulers.blocking import BlockingScheduler
import src.generate_total_corpus_en as gen
import src.extract_en as ext


def task():
    print(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
    gen.run()
    ext.run()


def run():
    scheduler = BlockingScheduler()

    scheduler.add_job(task, 'interval', hours=2)

    scheduler.start()


if __name__ == '__main__':
    run()
