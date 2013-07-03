"""
@author: Federico Vaga <federico.vaga@gmail.com>
@copyright: CERN 2013
@license: GPLv2
"""
from PyZio.ZioConfig import devices_path, triggers
from PyZio.ZioDev import ZioDev
from test import config
from test import utils
import unittest
import time
import os

path = os.path.join(devices_path, "zzero-0000")

@unittest.skipIf(not (os.path.exists(path) and os.path.isdir(path)),
                 "zio zero is not loaded")
@unittest.skipIf(not (config.pre_post_sample_trigger in triggers),
                 "Trigger '" + config.pre_post_sample_trigger + "'" + \
                 "is required for this test")
class PrePostSample(unittest.TestCase):
    """
    It performs tests on the trigger attributes 'post-samples' and 'pre-samples'
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

        self.cset.set_current_trigger(config.pre_post_sample_trigger)
        self.trigger = self.cset.trigger

        self.trigger.disable()
        self.chan.buffer.flush()
        self.trigger.enable()

        self.chan.interface.open_ctrl_data(os.O_RDONLY)  # Open control cdev

        if config.pre_post_sample_trigger == "timer":
            self.trigger.attribute["ms-period"].set_value(config.timer_ms_period_fast)


    def tearDown(self):
        self.chan.interface.close_ctrl_data()  # Close control cdev
        self.trigger.disable()


    def test_pre_samples(self):
        """
        It tests that the trigger acquires a given number of pre-samples
        """

        if not "pre-samples" in self.trigger.attribute:
            self.skipTest("No pre-samples to set.")

        pre = utils.random_list(2, 1024, 100)  # Get a random list of value
        for p in pre:
            self._test_sysfs_value(self.trigger, "pre-samples", p)
            if "post-samples" in self.trigger.attribute:  # Disable 'post-sample'
                self.trigger.attribute["post-samples"].set_value(0)
            self.__test_n_samples(self.trigger, self.interface, p, 0)  # Run the test


    def test_post_samples(self):
        """
        It test that the trigger acquires a given number of post-samples
        """

        if not "post-samples" in self.trigger.attribute:
            self.skipTest("No post-samples to set.")

        post = utils.random_list(2, 1024, 100)  # Get a random list of value
        for p in post:
            self._test_sysfs_value(self.trigger, "post-samples", p)
            if "pre-samples" in self.trigger.attribute:  # Disable 'pre-sample'
                self.trigger.attribute["pre-samples"].set_value(0)
            self.__test_n_samples(self.trigger, self.interface, 0, p)  # Run the test


    def test_pre_post_samples(self):
        """
        It tests that the trigger acquires the given number of
        {pre|post}-samples
        """

        if not (("pre-samples" in self.trigger.attribute) and \
                ("post-samples" in self.trigger.attribute)):
            self.skipTest("No pre-samples and post-samples to set.")

        pres = utils.random_list(2, 1024, 100)
        posts = utils.random_list(2, 1024, 100)

        for pre, post in zip(pres, posts):
            self._test_sysfs_value(self.trigger, "pre-samples", pre)
            self._test_sysfs_value(self.trigger, "post-samples", post)
            self.__test_n_samples(self.trigger, self.interface, pre, post, self.force_fire)


    def _test_sysfs_value(self, trigger, sysfs_attr, n_sample):
        """
        It writes the given number of sample 'n_sample' into the sysfs attribute
        specified 'sysfs_attr'. The read back value must be the same
        """
        trigger.attribute[sysfs_attr].set_value(n_sample)
        c = int(trigger.attribute[sysfs_attr].get_value())
        self.assertEqual(n_sample, c, \
                sysfs_attr + " should be {0} but it is {1}".format(n_sample, c))


    def program_fires(self):
        if config.pre_post_sample_trigger == "hrt":
            self.trigger.attribute["exp-scalar-h"].set_value(0)  # Fire now
        elif config.pre_post_sample_trigger == "timer":
            time.sleep(config.timer_ms_period_fast / 500.0)


    def __test_n_samples(self, trigger, interface, pre, post):
        """
        It perform the test with a particular configuration of pre-samples
        and post-samples
        """
        self.chan.buffer.flush()

        for _i in range(10):
            self.program_fires()
            ready = self.interface.is_device_ready(1)
            self.assertTrue(ready, "Trigger does not fire, or black was lost")

            ctrl = self.interface.read_ctrl()

            # ZIO allow to change ctrl.nsamples to return less samples then required
            expected_samples = pre + post
            self.assertLessEqual(ctrl.nsamples, expected_samples, "The number of samples should less or equal to {0} but it is {1}".format(expected_samples, ctrl.nsamples))

            # but attributes must be the same
            if ctrl.attr_trigger.std_mask & (1 << 1):
                self.assertEqual(post, ctrl.attr_trigger.std_val[1], "The number of expected post samples should be {0} but it is {1}".format(post, ctrl.attr_trigger.std_val[1]))
            if ctrl.attr_trigger.std_mask & (1 << 2):
                self.assertEqual(pre, ctrl.attr_trigger.std_val[2], "The number of expecte pre samples should be {0} but it is {1}".format(pre, ctrl.attr_trigger.std_val[2]))
