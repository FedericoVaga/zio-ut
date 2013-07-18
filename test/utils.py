"""
@author: Federico Vaga <federico.vaga@gmail.com>
@copyright: CERN 2013
@license: GPLv2
"""
import random


def random_list(minValue, maxValue, n):
    """
    It generates a list of 'n' random value between 'minValue' and 'maxValue'
    """

    lst = []
    for _i in range(n):
        lst.append(random.randrange(minValue, maxValue))

    return lst

def trigger_hrt_fill_buffer(trigger, n_block = 1, disable = False):
    trigger.enable()
    for _i in range(n_block):
        trigger.attribute["exp-sec"].set_value(0)
    if disable:
        trigger.disable()
