from apscheduler.schedulers.blocking import BlockingScheduler
import importlib

sched = BlockingScheduler()
app = importlib.import_module('app')

@sched.scheduled_job('interval', minutes=15)
def job():
    app.run()

sched.start()