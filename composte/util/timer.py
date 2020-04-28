"""Run a function on a timer."""
import time
from threading import Thread


def every(delay_in_seconds, timer_resolution, fun, continue_predicate):
    """
    Invoke a function on an iterval.

    There is a delay of delay_in_seconds between the end of one
    invocation and the start of the next. Invokes continue_predicate every
    timetimer_resolution seconds, allowing polling-lke behavior
    """

    def go():
        t1 = time.clock_gettime(time.CLOCK_REALTIME)

        while continue_predicate():
            t2 = time.clock_gettime(time.CLOCK_REALTIME)

            if (t2 - t1) < delay_in_seconds:
                sleep_time = min(delay_in_seconds - (t2 - t1), timer_resolution)
                time.sleep(sleep_time)
            else:
                t1 = time.clock_gettime(time.CLOCK_REALTIME)
                fun()

    thread = Thread(target=go)
    thread.start()
    return thread
