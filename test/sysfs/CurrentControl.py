"""
@author: Federico Vaga <federico.vaga@gmail.com>
@copyright: CERN 2013
@license: GPLv2
"""

from PyZio.ZioConfig import devices_path, triggers
from PyZio.ZioDev import ZioDev
from test import utils, config
import unittest
import os

path = os.path.join(devices_path, "zzero-0000")

@unittest.skipIf(not (os.path.exists(path) and os.path.isdir(path)),
                 "zio zero is not loaded")
@unittest.skipIf(not ("hrt" in triggers),
                 "Trigger 'hrt' is required for this test")
class CurrentControl(unittest.TestCase):
    """
    It performs tests on the current-control sysfs attribute
    """

    def setUp(self):
        self.device = ZioDev(devices_path, "zzero-0000")
        if self.device == None:
            self.skipTest("Missing device, cannot run tests")

        # Set channel set and channel to use
        self.cset = self.device.cset[0]  # Use cset input8
        self.chan = self.cset.chan[0]
        self.interface = self.chan.interface

        # Set and configure 'hrt' trigger
        self.cset.set_current_trigger("hrt")
        self.trigger = self.cset.trigger
        self.trigger.attribute["slack-ns"].set_value(config.hrt_slack_nsec);

        # Empty buffer
        self.chan.buffer.flush()

        # Open control char device
        self.interface.open_ctrl_data(os.O_RDONLY)

        self.trigger.enable()


    def tearDown(self):
        self.interface.close_ctrl_data()  # Close control cdev
        self.trigger.disable()


    def test_cmp_cdev_current_control(self):
        """
        It fills the buffer with a given number of blocks. Then, it disable the
        trigger and it reads all blocks from the buffer. Only the last block
        must have the control side equal to the current-control of the same
        channel
        """

        ctrl_prev = None

        # Read control one by one
        for i in range(config.n_block_load):
            utils.trigger_hrt_fill_buffer(self.trigger, 1)

            ready = self.interface.is_device_ready(config.select_wait)
            self.assertTrue(ready, "Trigger {0} does not fire, or black was lost".format(i))

            ctrl_cdev = self.interface.read_ctrl()
            ctrl_curr = self.chan.get_current_ctrl()

            self.assertNotEqual(ctrl_prev, ctrl_curr,
                    "Previous control (block) cannot be equal to the current-control")
            self.assertEqual(ctrl_cdev, ctrl_curr,
                    "Last control (block) must be equal to current-control")

            ctrl_prev = ctrl_cdev

    def test_from_attr_to_cur_ctrl(self):
        """
        It tests that user value written on a trigger sysfs attribute will be
        written also on the current control.
        """
        self.cset = self.device.cset[2]  # Use cset input32
        self.chan = self.cset.chan[0]
        test_attr = (("resolution-bits", 0),
                     ("gain_factor", 1),
                     ("offset", 2),
                     ("max-sample-rate", 3),
                     ("vref-src", 4),
                     ("nshots", 0),
                     ("post-samples", 1),
                     ("pre-samples", 2)
                    )

        for attr_name, attr_idx in test_attr:
            # Find the attribute within the zio device hierachy
            in_trig = False
            if attr_name in self.device.attribute:
                attr = self.device.attribute[attr_name]
            elif attr_name in self.cset.attribute:
                attr = self.cset.attribute[attr_name]
            elif attr_name in self.chan.attribute:
                attr = self.chan.attribute[attr_name]
            elif attr_name in self.trigger.attribute:
                attr = self.trigger.attribute[attr_name]
                in_trig = True
            else:
                continue

            # Do no continue if the attribute is read-only
            if not attr.is_writable():
                continue

            print("    Test attribute '{0}'".format(attr_name))

            # Do some writes
            increment = 1
            for _i in range(config.nstress):
                new_val = 2 + increment
                attr.set_value(new_val)
                self._compare_with_cur_ctrl(self.cset, attr_idx, new_val, in_trig)
                increment = -1 if increment == 1 else 1


    def _compare_with_cur_ctrl(self, cset, index, value, in_trig):
        """
        It test that a given value is equal to the value in current control
        associated to a given index

        value == cur_ctrl.attribute[index]
        """
        # Read the channel current control
        for chan in cset.chan:
            cur_ctrl = chan.get_current_ctrl()
            if in_trig:
                cur_ctrl_val = cur_ctrl.attr_trigger.std_val[index]
            else:
                cur_ctrl_val = cur_ctrl.attr_channel.std_val[index]

            self.assertEqual(value, cur_ctrl_val,
                "Sysfs attribute '{0}' and current control value '{1}'".format(value, cur_ctrl_val))
