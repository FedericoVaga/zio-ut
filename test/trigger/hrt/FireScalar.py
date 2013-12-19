"""
@author: Federico Vaga <federico.vaga@gmail.com>
@copyright: CERN 2013
@license: GPLv2
"""

from PyZio.ZioConfig import devices_path, triggers
from PyZio.ZioDev import ZioDev
from test import utils, config
import unittest
import time
import sys
import os

path = os.path.join(devices_path, "zzero-0000")

@unittest.skipIf(not (os.path.exists(path) and os.path.isdir(path)), "this test require zio zero")
@unittest.skipIf(not ("hrt" in triggers), "Trigger 'hrt' is required for this test")
class FireScalar(unittest.TestCase):
    """
    It tests 'hrt' programming with attributes 'exp-scalar-l' and 'exp-scalar-h'
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

        # Set and configure 'hrt' trigger
        self.cset.set_current_trigger("hrt")
        self.trigger = self.cset.trigger
        self.trigger.attribute["slack-ns"].set_value(config.hrt_slack_nsec);


        # Set and configure 'kmalloc' buffer
        self.cset.set_current_buffer("kmalloc")
        self.chan.buffer.attribute["max-buffer-len"].set_value(16)

        # Open control char device
        self.interface.open_ctrl_data(os.O_RDONLY)

        self.trigger.enable()


    def tearDown(self):
        self.trigger.disable()
        self.interface.close_ctrl_data()  # Close control cdev
        sys.stdout.write("\n")


    @unittest.skipIf(config.skip_long_test, "Skip long test")
    def test_fire_absolute(self):
        """
        It test that the HRT trigger fires at the given programmed time (nsec).
        The test use absolute time. The absolute time is calculated by this
        test and it is relative to the current time.
        """
        timers = utils.generate_random_ZioTimeStamp(10, 0, 8, 0, 999999999)
        utils.calculate_test_time_timers(timers)

        for ztstamp in timers:
            sys.stdout.write(".")
            sys.stdout.flush()
            self._test_fire_absolute(ztstamp)


    def _test_fire_absolute(self, ztstamp):
        # Program the trigger
        nsec = utils.convert_ZioTimeStamp_to_ns(ztstamp)
        nsec += int((time.time() + 2) * 1000000000)
        self.trigger.attribute["exp-scalar-l"].set_value(int(nsec) & 0xFFFFFFFF)
        hi = (int(nsec) & 0xFFFFFFFF00000000) >> 32
        self.trigger.attribute["exp-scalar-h"].set_value(hi)


        # A new block must appear in the buffer
        ready = self.interface.is_device_ready(ztstamp.seconds + 5)
        self.assertTrue(ready, "Trigger does not fire, or black was lost")

        block_tstamp = self.interface.read_ctrl().tstamp;
        block_nsec = utils.convert_ZioTimeStamp_to_ns(block_tstamp)
        delta = abs(block_nsec - nsec)

        self.assertLess(delta, config.hrt_slack_nsec,
            "programmed {0}ns, fired at {1}ns, delta {2}ns < tollerance {3}ns".format(nsec, block_nsec, delta, config.hrt_slack_nsec))



    @unittest.skipIf(config.skip_long_test, "Skip long test")
    def test_fire_time_relative(self):
        """
        It test that the HRT trigger fires at the given programmed time (nsec).
        In this test the range of value is [1000, 4294967295]
        """
        timers = utils.generate_random_ZioTimeStamp(10, 0, 4, 0, 999999999)
        utils.calculate_test_time_timers(timers)

        for ztstamp in timers:
            sys.stdout.write(".")
            sys.stdout.flush()
            self._test_fire_relative(ztstamp)


    def _test_fire_relative(self, ztstamp):
        # Program the trigger
        nsec = utils.convert_ZioTimeStamp_to_ns(ztstamp)
        self.trigger.attribute["exp-scalar-l"].set_value(int(nsec) & 0xFFFFFFFF)
        self.trigger.attribute["exp-scalar-h"].set_value(0)

        nsec = int(time.time() * 1000000000)

        # A new block must appear in the buffer
        ready = self.interface.is_device_ready(ztstamp.seconds + 5)
        self.assertTrue(ready, "Trigger does not fire, or black was lost")

        block_tstamp = self.interface.read_ctrl().tstamp;
        block_nsec = utils.convert_ZioTimeStamp_to_ns(block_tstamp)
        delta = abs(block_nsec - nsec)

        self.assertLess(delta, config.hrt_slack_nsec,
            "programmed {0}ns, fired at {1}ns, delta {2}ns < tollerance {3}ns".format(nsec, block_nsec, delta, config.hrt_slack_nsec))
