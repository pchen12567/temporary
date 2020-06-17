from apscheduler.schedulers.blocking import BlockingScheduler
import src.portMatch2 as match2


def task_port_match():
    match2.run()


def run():
    scheduler = BlockingScheduler()

    scheduler.add_job(task_port_match, 'interval', minutes=10)

    scheduler.start()


if __name__ == '__main__':
    run()
