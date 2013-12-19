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
class FireSecond(unittest.TestCase):
    """
    It tests 'hrt' programming with attributes 'exp-nsec' and 'exp-sec'
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

        self.trigger.disable()
        self.chan.buffer.flush()
        self.trigger.enable()

    def tearDown(self):
        self.trigger.disable()
        self.interface.close_ctrl_data()  # Close control cdev
        sys.stdout.write("\n")


    @unittest.skipIf(config.skip_long_test, "Skip long test")
    def test_fire_absolute(self):
        """
        It test that the HRT trigger fires at the given programmed
        time (sec.nsec).
        """
        timers = utils.generate_random_ZioTimeStamp(10, 0, 16, 0, 999999999)
        utils.calculate_test_time_timers(timers)

        for ztstamp in timers:
            sys.stdout.write(".")
            sys.stdout.flush()
            self._test_fire_absolute(ztstamp)


    def _test_fire_absolute(self, ztstamp):
        sec = int(time.time()) + ztstamp.seconds + 1
        self.trigger.attribute["exp-nsec"].set_value(ztstamp.ticks)
        self.trigger.attribute["exp-sec"].set_value(sec)

        # A new block must appear in the buffer
        ready = self.interface.is_device_ready(sec + 1)
        self.assertTrue(ready, "Trigger does not fire, or black was lost")

        block_tstamp = self.interface.read_ctrl().tstamp;
        delta = abs(block_tstamp.ticks - ztstamp.ticks)

        self.assertEqual(sec, block_tstamp.seconds,
            "Programmed second {0}, but it fired at {1}".format(sec, block_tstamp.seconds))
        self.assertLess(delta, config.hrt_slack_nsec,
            "Programmed {0}ns, but it fired at {1}ns  [delta {2}ns < tollerance {3}ns]".format(ztstamp.ticks, block_tstamp.ticks, delta, config.hrt_slack_nsec))


    @unittest.skipIf(config.skip_long_test, "Skip long test")
    def test_fire_relative(self):
        """
        It test that the HRT trigger fires at the given programmed
        time (sec.nsec) relative to the current second. This mean that only
        sec is calculated relative to the current second, the nsec are absolute
        """
        timers = utils.generate_random_ZioTimeStamp(10, 0, 3, 0, 999999999)
        utils.calculate_test_time_timers(timers)

        for ztstamp in timers:
            sys.stdout.write(".")
            sys.stdout.flush()
            self._test_fire_relative(ztstamp)


    def _test_fire_relative(self, ztstamp):
        sec = int(time.time()) + ztstamp.seconds
        self.trigger.attribute["exp-nsec"].set_value(ztstamp.ticks)
        self.trigger.attribute["exp-sec"].set_value(ztstamp.seconds)
        nsec = utils.convert_ZioTimeStamp_to_ns(ztstamp)

        # A new block must appear in the buffer
        ready = self.interface.is_device_ready(ztstamp.seconds + 1)
        self.assertTrue(ready, "Trigger does not fire, or black was lost")

        block_tstamp = self.interface.read_ctrl().tstamp;
        block_nsec = utils.convert_ZioTimeStamp_to_ns(block_tstamp)
        delta = abs(block_tstamp.ticks - ztstamp.ticks)

        self.assertEqual(sec, block_tstamp.seconds,
            "Programmed second {0}, but it fire at {1}".format(sec, block_tstamp.seconds))
        self.assertLess(delta, config.hrt_slack_nsec,
            "programmed {0}ns, fired in {1}ns, delta {2}ns < tollerance {3}ns".format(nsec, block_nsec, delta, config.hrt_slack_nsec))
