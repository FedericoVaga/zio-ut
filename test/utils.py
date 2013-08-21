"""
@author: Federico Vaga <federico.vaga@gmail.com>
@copyright: CERN 2013
@license: GPLv2
"""
from PyZio.ZioCtrl import ZioTimeStamp
import random
import time

def random_list(minValue, maxValue, n):
    """
    It generates a list of 'n' random value between 'minValue' and 'maxValue'
    """

    lst = []
    for _i in range(n):
        lst.append(random.randrange(minValue, maxValue))

    return lst

def trigger_hrt_fill_buffer(trigger, n_block = 1, wait = 0.01, disable = False):
    trigger.enable()
    for _i in range(n_block):
        trigger.attribute["exp-scalar-l"].set_value(0)
        trigger.attribute["exp-scalar-h"].set_value(1)
        time.sleep(wait)
    if disable:
        trigger.disable()

def convert_ns_to_ms(time):
    """
    Convert time (sec, nsec) to ms
    """

    return time[0] * 1000 + time[1] / 1000000

def generate_random_ZioTimeStamp(n, sec_min, sec_max, ticks_min, ticks_max):
    lst = []
    for _i in range(n):
        if sec_min < sec_max:
            sec = random.randrange(sec_min, sec_max)
        else:
            sec = 0
        if ticks_min < ticks_max:
            ticks = random.randrange(ticks_min, ticks_max)
        else:
            ticks = 0
        tstamp = ZioTimeStamp(sec, ticks, 0);
        lst.append(tstamp)
    return lst

def convert_ZioTimeStamp_to_ns(ztstamp):
    return ztstamp.seconds * 1000000000 + ztstamp.ticks

def convert_ZioTimeStamp_to_s(ztstamp):
    return ztstamp.seconds + ztstamp.ticks / 1000000000.0

def convert_ns_to_ZioTimeStamp(nsec):
    sec = int(nsec / 1000000000)
    nsec_decimal = nsec - sec * 1000000000
    return ZioTimeStamp(sec, nsec_decimal, 0)

def calculate_test_time_timers(timer_list, extra_time = 0.0):
    """
    It calculate the total time to fire the list of timers. There is two
    """
    # Calculate test time
    test_time = extra_time
    for timer in timer_list:
        test_time += convert_ZioTimeStamp_to_s(timer)

    print("\nThis test can take at least {0} seconds".format(test_time))
