"""
@author: Federico Vaga <federico.vaga@gmail.com>
@copyright: CERN 2013
@license: GPLv2
"""

from PyZio.ZioConfig import devices_path, buffers, triggers
from PyZio.ZioDev import ZioDev
from test import config
import unittest
import time
import os

path = os.path.join(devices_path, "zzero-0000")

@unittest.skipIf(not (os.path.exists(path) and os.path.isdir(path)),
                 "zio zero is not loaded")
@unittest.skipIf(not (config.buf in buffers),
                 "Buffer '" + config.buf + "' " + \
                 "is required for this test")
@unittest.skipIf(not ("timer" in triggers),
                 "Trigger 'timer' is required for this test")
class Flush(unittest.TestCase):

    def setUp(self):
        self.device = ZioDev(devices_path, "zzero-0000")
        if self.device == None:
            self.skipTest("Missing device, cannot run tests")

        # Set and flush buffer
        for cset in self.device.cset:
            cset.set_current_buffer(config.buf)

        # Set and configure 'timer' trigger on all channel set
        for cset in self.device.cset:
            cset.set_current_trigger("timer")
            cset.trigger.attribute["ms-period"].set_value(config.timer_ms_period)
            cset.trigger.enable()

        # Wait a while to fill the buffer
        time.sleep(config.acquisition_wait)

        # Stop acquisition
        for cset in self.device.cset:
            cset.trigger.disable()


    def tearDown(self):
        for cset in self.device.cset:
            cset.set_current_trigger("user")
            cset.set_current_buffer("kmalloc")


    def test_flush(self):
        """
        It tests that flush makes the buffers empty. The channel's buffers
        are filled by the SetUp function.
        """
        for cset in self.device.cset:
            # Flush the buffer of each channel
            for chan in cset.chan:
                chan.buffer.flush()

            for chan in cset.chan:
                # There are different tests for input and for output buffer
                if chan.interface.is_ctrl_readable() and \
                        chan.interface.is_data_readable():
                    # Test flush on input buffer
                    self._test_flush_input(chan)
                elif chan.interface.is_ctrl_writable() and \
                        chan.interface.is_data_writable():
                    # Test flush on output buffer
                    self._test_flush_output(chan)
                else:
                    self.fail("Cannot read/write from current control")


    def _test_flush_input(self, chan):
        """
        It verifies that the buffer is empty by reading it.
        """
        chan.interface.open_ctrl_data(os.O_RDONLY)
        ready = chan.interface.is_device_ready(0)
        chan.interface.close_ctrl_data()

        self.assertFalse(ready, "There should be no blocks")


    def _test_flush_output(self, chan):
        pass
