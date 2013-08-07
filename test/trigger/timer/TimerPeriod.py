"""
@author: Federico Vaga <federico.vaga@gmail.com>
@copyright: CERN 2013
@license: GPLv2
"""

from PyZio.ZioConfig import devices_path, triggers
from PyZio.ZioDev import ZioDev

import unittest
import random
import os

path = os.path.join(devices_path, "zzero-0000")

@unittest.skipIf(not (os.path.exists(path) and os.path.isdir(path)), "this test require zio zero")
@unittest.skipIf(not ("timer" in triggers), "Trigger 'timer' is required for this test")
class TimerPeriod(unittest.TestCase):
    """
    This TestCase tests the 'ms-period' attribute of the trigger 'timer'. The
    test generate a set of 10 random periods in the range [50, 1500]. Then, for
    each period it:
    - set 'ms-period'
    - read the timestamp from the control
    - calculate the timestamp difference from the previous block
    if the difference (t2 - t1) > 15ms then the test fails
    """

    def setUp(self):
        self.n_block_test = 6
        self.period_tollerance = 15
        
        self.device = ZioDev(devices_path, "zzero-0000")
        if self.device == None:
            self.skipTest( "Missing device, cannot run tests")
        
        for cset in self.device.cset:               # Disable all trigger
            cset.trigger.disable()
        
        self.cset = self.device.cset[0]             # Use cset input8
        self.cset.set_current_trigger("timer")      # Set trigger 'timer'
        self.trigger = self.cset.trigger
        self.chan = self.cset.chan[0]               # Use channel 0
        self.interface = self.chan.interface
        
        self.trigger.disable()                      # Disable the trigger
        for chan in self.cset.chan:                 # Flush all buffers
            chan.buffer.flush()
        
        self.chan.interface.open_ctrl_data(os.O_RDONLY)  # Open control cdev

    def tearDown(self):
        self.chan.interface.close_ctrl_data()            # Close control cdev
        self.trigger.disable()

    def test_periods(self):
        """
        It tests that trigger fires at given periods
        """
        periods = []
        total = 0
        for _i in range(10):
            rnd = random.randrange(50, 1500, 50)    # Create random period
            periods.append(rnd)                     # and append to a list
            total += (rnd * self.n_block_test)
        
        print("It can take about " + str(total/1000) + " second")
        for p in periods:                           # Run a test with all
            self.__test_period(p)                   # periods

    def __test_period(self, period):
        """
        Test that trigger fires with a given period
        """
        time_old = None
        time_new = None
        
        self.trigger.disable()                      # Disable the trigger
        self.trigger.attribute["ms-period"].set_value(period)
        self.chan.buffer.flush()                    # Flush buffer
        self.trigger.enable()                       # Enable the trigger
        
        for _i in range(self.n_block_test):
            wait = period/1000 + 2
            if self.interface.is_device_ready(wait) == False:
                self.fail("Select timeout")
            
            ctrl = self.interface.read_ctrl()       # Read Control
            if ctrl == None:
                self.skipTest("Invalid Control")

            time_old = time_new
            time_new = (ctrl.tstamp.seconds, ctrl.tstamp.ticks)
            if time_old == None or time_new== None:
                continue    # First time

            t1 = self._convert_ns_to_ms(time_old)
            t2 = self._convert_ns_to_ms(time_new)
            ms = t2 - t1                            # t2 - t1 = period
            self.assertAlmostEqual(period, ms, delta=self.period_tollerance)
        self.trigger.disable()

    def _convert_ns_to_ms(self, time):
        """
        Convert time to ms
        """

        return time[0] * 1000 + time[1] / 1000000
