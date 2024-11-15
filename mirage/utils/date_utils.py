import datetime
import time


def get_utc_datetime_for_filename() -> str:
    utc_now = datetime.datetime.now(datetime.timezone.utc)
    timestamp_millis = int(time.time() * 1000)
    return utc_now.strftime(f'%Y-%m-%dT%H-%M-%S_{timestamp_millis}')
