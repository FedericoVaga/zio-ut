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
    config.nstress = _set_variable(config.nstress, "nstress")


def _set_variable(var, name):
    print("looking for {0}".format(name))
    if name in os.environ:
        return os.environ[name]
    else:
        return var
