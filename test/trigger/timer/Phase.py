"""
@author: Federico Vaga <federico.vaga@gmail.com>
@copyright: CERN 2013
@license: GPLv2
"""

from PyZio.ZioConfig import devices_path, triggers
from PyZio.ZioDev import ZioDev
from test import config

import unittest
import sys
import os

path = os.path.join(devices_path, "zzero-0000")

@unittest.skipIf(not (os.path.exists(path) and os.path.isdir(path)), "this test require zio zero")
@unittest.skipIf(not ("timer" in triggers), "Trigger 'timer' is required for this test")
class Phase(unittest.TestCase):
    """
    This TestCase tests the 'ms-phase' attribute of the trigger 'timer'
    """

    def setUp(self):
        self.device = ZioDev(devices_path, "zzero-0000")
        if self.device == None:
            self.skipTest("Missing device, cannot run tests")

        for cset in self.device.cset:  # Disable all trigger
            cset.trigger.disable()

        # Set channel set and channel to use
        self.cset = self.device.cset[0]  # Use cset input8
        self.chan = self.cset.chan[0]
        self.interface = self.chan.interface

        self.cset.set_current_trigger("timer")  # Set trigger 'timer'
        self.trigger = self.cset.trigger

        self.trigger.disable()  # Disable the trigger
        self.chan.buffer.flush()

        # Open char devices
        self.chan.interface.open_ctrl_data(os.O_RDONLY)
        sys.stdout.write("\n")


    def tearDown(self):
        self.chan.interface.close_ctrl_data()  # Close control cdev
        self.trigger.disable()
        self.chan.buffer.flush()
        sys.stdout.write("\n")


    def test_phase(self):
        """
        Test that trigger fires with a given phase
        """
        sync = False
        self.trigger.attribute["ms-period"].set_value(1000)

        self.chan.buffer.flush()  # Flush buffer
        self.trigger.enable()  # Enable the trigger

        ready = self.interface.is_device_ready(1)
        self.assertTrue(ready, "Expected block in the buffer")
        tstamp = self.interface.read_ctrl().tstamp
        msec = 1000 - int(tstamp.ticks / 1000000)
        self.trigger.attribute["ms-phase"].set_value(msec)

        # find synchonization point
        sys.stdout.write("Syncing ")
        sys.stdout.flush()
        for i in range(10):
            sys.stdout.write(str(i))
            if not self.interface.is_device_ready(1):
                break
            tstamp = self.interface.read_ctrl().tstamp
            if int(tstamp.ticks / 1000000) < config.time_tollerance_msec:
                sync = True
                break

        if not sync:
            self.fail("Synchonization failed")

        sys.stdout.write(" done!\n")
        sys.stdout.flush()

        for _i in range(config.nstress):
            sys.stdout.write(".")
            sys.stdout.flush()
            ready = self.interface.is_device_ready(1.2)
            self.assertTrue(ready, "Trigger does not fire, or black was lost")
            tstamp = self.interface.read_ctrl().tstamp
            self.assertLess(int(tstamp.ticks / 1000000), config.time_tollerance_msec, "Alignment to seconds failed {0}".format(tstamp.ticks))
        self.trigger.disable()
