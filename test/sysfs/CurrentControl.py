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
