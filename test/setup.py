"""
@author: Federico Vaga <federico.vaga@gmail.com>
@copyright: CERN 2013
@license: GPLv2
"""
from test import config
import os

def parse_environment():
    config.trig = _set_variable(config.trig, "trig")
    config.buf = _set_variable(config.buf, "buf")
    config.nstress = int(_set_variable(config.nstress, "nstress"))
    config.nrandom = int(_set_variable(config.nrandom, "nrandom"))

    config.timer_ms_period = int(_set_variable(config.timer_ms_period, \
                                               "timer_ms_period"))
    config.acquisition_wait = int(_set_variable(config.acquisition_wait, \
                                                "acquisition_wait"))
    config.hrt_slack_nsec = int(_set_variable(config.hrt_slack_nsec, \
                                                "hrt_slack_nsec"))

def _set_variable(var, name):
    print("looking for {0}".format(name))
    if name in os.environ:
        return os.environ[name]
    else:
        return var
