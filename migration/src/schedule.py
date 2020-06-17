import time
from apscheduler.schedulers.blocking import BlockingScheduler
import src.migrate_crawl as crawl
import src.migrate_picture as picture
import src.migrate_cms as cms


def task_cms():
    print(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
    # print("cms")
    cms.run()


def task_crawl():
    print(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
    # print("crawl")
    crawl.run()
    picture.run()


def run():
    scheduler = BlockingScheduler()

    scheduler.add_job(task_cms, 'interval', minutes=1)

    scheduler.add_job(task_crawl, 'interval', hours=2)

    scheduler.start()


if __name__ == '__main__':
    run()
