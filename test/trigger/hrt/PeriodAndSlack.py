"""
@author: Federico Vaga <federico.vaga@gmail.com>
@copyright: CERN 2013
@license: GPLv2
"""

from PyZio.ZioConfig import devices_path, triggers
from PyZio.ZioCtrl import ZioTimeStamp
from PyZio.ZioDev import ZioDev
from test import utils, config
import unittest
import time
import sys
import os

path = os.path.join(devices_path, "zzero-0000")

@unittest.skipIf(not (os.path.exists(path) and os.path.isdir(path)),
                 "this test require zio zero")
@unittest.skipIf(not ("hrt" in triggers),
                 "Trigger 'hrt' is required for this test")
class PeriodAndSlack(unittest.TestCase):
    """
    It runs test about the 'HRT' trigger attributes 'period-ns' and 'slack-ns'.
    This test use the same procedure to test both attributes.
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

        # Set and configure 'kmalloc' buffer
        self.cset.set_current_buffer("kmalloc")
        self.chan.buffer.attribute["max-buffer-len"].set_value(16)

        # Open control char device
        self.interface.open_ctrl_data(os.O_RDONLY)


    def tearDown(self):
        self.trigger.disable()
        self.interface.close_ctrl_data()  # Close control cdev
        sys.stdout.write("\n")


    def test_fire_periodic(self):
        """
        It tests that the HRT trigger fires with a given period. The test
        prepare some random periods to test. The real test is performed by
        the internal function '_test_period()'
        """
        timers = utils.generate_random_ZioTimeStamp(config.nrandom, 0, 4, 1000, 999999999)

        extra_time = 0.0
        for period in timers:
            period_ns = utils.convert_ZioTimeStamp_to_ns(period)
            extra_time += ((period_ns / 1000000000) + 1) * 10
        utils.calculate_test_time_timers(timers, extra_time)

        for period in timers:
            sys.stdout.write(".")
            sys.stdout.flush()
            self._test_period_value(period)
            self._test_period_and_slack(period, config.hrt_slack_nsec)


    def _test_period_value(self, period):
        period_ns = utils.convert_ZioTimeStamp_to_ns(period)
        self.trigger.attribute["period-ns"].set_value(period_ns);
        p = int(self.trigger.attribute["period-ns"].get_value()) & 0xFFFFFFFF

        self.assertEqual(period_ns, p,
            "'period-ns' should be {0}, but it is {1}".format(period_ns, p))
        self.trigger.attribute["period-ns"].set_value(0);


    def test_slack(self):
        """
        It test that the HRT trigger slack is observed by the timer. The test
        uses 'config.time_tollerance_period_ns' as first slack to test, following
        test iterations will use half the time of the previous one.
        """
        slack_list = [1000000000,
                      16000000, 8000000, 4000000, 2000000, 1000000,
                      512000, 256000, 128000, 64000, 32000, 16000, 8000, 4000, 2000 , 1000,
                      512, 256, 128, 64, 32, 16, 8, 4, 2,
                      ]

        for slack in slack_list:
            sys.stdout.write(str(slack) + ", ")
            sys.stdout.flush()
            self._test_slack_value(slack)
            tstamp = ZioTimeStamp(0, 100000000, 0);
            self._test_period_and_slack(tstamp, slack)


    def _test_slack_value(self, slack):
        self.trigger.attribute["slack-ns"].set_value(slack);
        sl = int(self.trigger.attribute["slack-ns"].get_value())
        self.assertEqual(slack, sl,
            "'slack-ns' should be {0}, but it is {1}".format(slack, sl))


    def _test_period_and_slack(self, period, slack):
        """
        The test sets the period to verify, then it fires immediatly to start
        the periodical fire. The test sleep the necessary time to fill the
        buffer with 10 blocks. Then, it reads all blocks and verify that
        the difference of the timestamp of two coperiod_nsutive blocks is almost
        equal to the configured period
        """
        # Buffer must be empty
        self.trigger.disable()
        self.chan.buffer.flush()
        self.trigger.enable()


        # Program the trigger
        period_ns = utils.convert_ZioTimeStamp_to_ns(period)
        self.trigger.attribute["slack-ns"].set_value(slack);
        self.trigger.attribute["period-ns"].set_value(period_ns)
        self.trigger.attribute["exp-scalar-l"].set_value(1000000000)
        self.trigger.attribute["exp-scalar-h"].set_value(0)

        # wait some seconds to fill the buffer
        time.sleep((period.seconds + 1) * 10)
        self.trigger.attribute["period-ns"].set_value(0)
        self.trigger.disable()

        ready = self.interface.is_device_ready(0.01)
        self.assertTrue(ready, "At least one block must be in the buffer")

        tstamp = self.interface.read_ctrl().tstamp;
        fire_old = utils.convert_ZioTimeStamp_to_ns(tstamp)

        # Read all blocks from the buffer
        i = 0
        while self.interface.is_device_ready(0.01):
            i += 1
            tstamp = self.interface.read_ctrl().tstamp;
            fire_new = utils.convert_ZioTimeStamp_to_ns(tstamp)

            measured_period = fire_new - fire_old;
            delta = abs(measured_period - period_ns)
            self.assertLess(delta, slack,
                            "{4}) period {0}, measured period {1}, delta {2}, tollerance {3}".format(period_ns, measured_period, delta, slack, i))
            fire_old = fire_new
