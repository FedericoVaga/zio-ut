"""
@author: Federico Vaga <federico.vaga@gmail.com>
@copyright: CERN 2014
@license: GPLv2
"""

from PyZio.ZioConfig import devices_path
from PyZio.ZioDev import ZioDev
from test import config
import unittest
import sys
import os

path = os.path.join(devices_path, "zzero-0000")

@unittest.skipIf(not (os.path.exists(path) and os.path.isdir(path)),
                 "zio zero is not loaded")
class CurrentControl(unittest.TestCase):
    """
    It performs tests on the current-control sysfs attribute
    """

    def setUp(self):
        self.device = ZioDev(devices_path, "zzero-0000")
        if self.device == None:
            self.skipTest("Missing device, cannot run tests")

        # Set channel set and channel to use
        self.cset = self.device.cset[2]  # Use cset input32
        self.chan = self.cset.chan[0]
        self.interface = self.chan.interface

        # Set and configure 'hrt' trigger
        self.cset.set_current_trigger(config.trig)
        self.trigger = self.cset.trigger

        # Empty buffer
        self.trigger.disable()
        self.buffer = self.chan.buffer
        self.buffer.flush()

        # Open control char device
        self.interface.open_ctrl_data(os.O_RDONLY)

        self.trigger.enable()
        sys.stdout.write("\n")
        sys.stdout.flush()


    def tearDown(self):
        self.interface.close_ctrl_data()  # Close control cdev
        self.trigger.disable()

    def test_read_back_value(self):
        """
        It writes some values into a sysfs attribute and it verifies that it
        read back the correct value
        """
        test_attr = ("resolution-bits", "gain_factor", "offset",
                    "max-sample-rate", "vref-src", "post-samples",
                    "pre-samples", "max-buffer-len")

        for attr_name in test_attr:
            # Find the attribute within the zio device hierachy
            if attr_name in self.device.attribute:
                attr = self.device.attribute[attr_name]
            elif attr_name in self.cset.attribute:
                attr = self.cset.attribute[attr_name]
            elif attr_name in self.chan.attribute:
                attr = self.chan.attribute[attr_name]
            elif attr_name in self.trigger.attribute:
                attr = self.trigger.attribute[attr_name]
            elif attr_name in self.buffer.attribute:
                attr = self.buffer.attribute[attr_name]
            else:
                continue

            # Do no continue if the attribute is read-only
            if not attr.is_writable():
                continue

            # Do some writes
            print("    Test attribute '{0}'".format(attr_name))
            increment = 1
            for _i in range(config.nstress):
                val = int(attr.get_value())
                new_val = val + increment
                attr.set_value(new_val)
                readback = int(attr.get_value())
                self.assertEqual(new_val, readback,
                    "Write {0}, but read back {1}".format(new_val, readback))
                increment = -1 if increment == 1 else 1
