import schedule
import time
from datetime import datetime, timedelta
from RunSim_utils import *

def job():
    print(f"[{datetime.now()}] Running update_stock_data...")
    update_stock_data(price_monthly_data, new_monthly_data)
    print(f"[{datetime.now()}] Done.")

def maybe_run_job_day1():
    if datetime.now().day == 1:
        job()

def maybe_run_job_day2():
    if datetime.now().day == 2:
        job()

schedule.every().day.at("01:00").do(maybe_run_job_day1)
schedule.every().day.at("01:05").do(maybe_run_job_day2)

start_time = datetime.now()
end_time = start_time + timedelta(days=365)

print(f"Scheduler started at {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Scheduled to stop at {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
print("Jobs: 1st of each month @ 01:00 | 2nd of each month @ 01:05")

while True:
    if datetime.now() > end_time:
        print("One year completed. Stopping scheduler.")
        break
    schedule.run_pending()
    time.sleep(30)
