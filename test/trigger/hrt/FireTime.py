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
from os.path import join, isdir, exists

path = join(devices_path, "zzero-0000")

@unittest.skipIf(not (exists(path) and isdir(path)), \
                 "this test require zio zero")
@unittest.skipIf(not ("hrt" in triggers), \
                 "Trigger 'hrt' is required for this test")
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
        self.trigger.attribute["slack-ns"].set_value(config.hrt_slack_nsec)


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

    def test_fire_past_scalar(self):
        """
        It test that the trigger programmed with the "scalar" parameters will
        fire immediately if programmed in the past
        """
        self._test_fire_past(True, 0, 2)  # about 8s since the epoch

    def test_fire_past_second(self):
        """
        It test that the trigger programmed with the "second" parameters will
        fire immediately if programmed in the past
        """
        self._test_fire_past(False, 0, 10) # 10s since the epoch

    def test_fire_now_scalar(self):
        """
        It test that the trigger programmed with the "scalar" parameters will
        fire immediately
        """
        self._test_fire_now(True)

    def test_fire_now_second(self):
        """
        It test that the trigger programmed with the "second" parameters will
        fire immediately
        """
        self._test_fire_now(False)

    def test_fire_penging_scalar(self):
        """
        It test that the trigger programmed with the "scalar" parameters will
        fire when pending
        """
        self._test_fire_pending(True, 3)

    def test_fire_penging_second(self):
        """
        It test that the trigger programmed with the "second" parameters will
        fire when pending
        """
        self._test_fire_pending(False, 3)


    def _test_fire_past(self, is_scalar, l_val, h_val):
        """
        It tests that the trigger immediately fire if the user program a timer
        in the past
        """
        l_name = "exp-scalar-l" if is_scalar else "exp-nsec"
        h_name = "exp-scalar-h" if is_scalar else "exp-sec"
        self.trigger.attribute[l_name].set_value(l_val)
        self.trigger.attribute[h_name].set_value(h_val)

        ready = self.interface.is_device_ready(0.001)  # wait only 1ms
        self.assertTrue(ready, "Trigger does not fire, or black was lost")


    def _test_fire_now(self, is_scalar):
        """
        It tests that the trigger immediately fire if it is programmed to
        fire now
        """
        l_name = "exp-scalar-l" if is_scalar else "exp-nsec"
        h_name = "exp-scalar-h" if is_scalar else "exp-sec"
        self.trigger.attribute[l_name].set_value(0)
        self.trigger.attribute[h_name].set_value(0)

        ready = self.interface.is_device_ready(0.001)  # wait only 1ms
        self.assertTrue(ready, "Trigger does not fire, or black was lost")


    def _test_fire_pending(self, is_scalar, time_to_wait):
        """
        It test that the trigger immediately fire when a pending trigger fire
        while trigger was disabled
        """
        if time_to_wait > 3:
            time_to_wait = 3

        l_val = time_to_wait * 1000000000 if is_scalar else 0
        h_val = 0 if is_scalar else time_to_wait

        l_name = "exp-scalar-l" if is_scalar else "exp-nsec"
        h_name = "exp-scalar-h" if is_scalar else "exp-sec"
        self.trigger.attribute[l_name].set_value(l_val)
        self.trigger.attribute[h_name].set_value(h_val)

        self.trigger.disable()
        ready = self.interface.is_device_ready(time_to_wait * 2)
        self.assertFalse(ready, "Trigger fired but trigger is disable")

        self.trigger.enable()
        ready = self.interface.is_device_ready(0.001)  # wait only 1ms
        self.assertTrue(ready, "Trigger does not fire, or black was lost")
