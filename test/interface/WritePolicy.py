"""
@author: Federico Vaga <federico.vaga@gmail.com>
@copyright: CERN 2013
@license: GPLv2
"""

from PyZio.ZioConfig import devices_path, triggers, buffers
from PyZio.ZioDev import ZioDev
from test import config
import unittest
import sys
import os

path = os.path.join(devices_path, "zzero-0000")

@unittest.skipIf(not (os.path.exists(path) and os.path.isdir(path)),
                 "zio zero is not loaded")
@unittest.skipIf(not (config.default_buffer in buffers),
                 "Buffer '" + config.default_buffer + "' " + \
                 "is required for this test")
@unittest.skipIf(not ("hrt" in triggers),
                 "Trigger 'hrt' is required for this test")
class WritePolicy(unittest.TestCase):
    """
    It tests that the char device interface write blocks correctly.
    """

    def setUp(self):
        self.device = ZioDev(devices_path, "zzero-0000")
        if self.device == None:
            self.skipTest("Missing device, cannot run tests")

        # Set channel set and channel to use
        self.cset = self.device.cset[0]  # Use cset input8
        self.chan = self.cset.chan[0]
        self.interface = self.chan.interface
        self.chan.attribute["alarms"].set_value(0xFF)

        # Set and configure 'hrt' trigger
        self.cset.set_current_trigger("hrt")
        self.trigger = self.cset.trigger

        # Set and flush buffer
        self.cset.set_current_buffer(config.default_buffer)
        self.chan.buffer.flush()

        # Enable trigger
        self.trigger.enable()

        sys.stdout.write("\n")


    def tearDown(self):
        self.trigger.disable()
        self.interface.close_ctrl_data()
        sys.stdout.write("\n")


    def test_write(self):
        pass


    def test_write_stress(self):
        for _i in range(config.stress_repetitions):
            self.test_write();
            self.interface.close_ctrl_data()


    def test_double_write_control(self):
        pass


    def test_double_write_data(self):
        pass
