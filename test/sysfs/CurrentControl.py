"""
@author: Federico Vaga <federico.vaga@gmail.com>
@copyright: CERN 2013
@license: GPLv2
"""

from PyZio.ZioConfig import devices_path, triggers
from PyZio.ZioDev import ZioDev
from test import utils
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

        self.cset = self.device.cset[0]  # Use cset input8
        self.cset.set_current_trigger("hrt")  # Set trigger 'hrt'
        self.trigger = self.cset.trigger
        self.chan = self.cset.chan[0]  # Use channel 0
        self.interface = self.chan.interface

        self.trigger.disable()
        self.interface.open_ctrl_data(os.O_RDONLY)  # Open control cdev

        # Empty buffer
        self.chan.buffer.flush()

    def tearDown(self):
        self.interface.close_ctrl_data()  # Close control cdev
        self.trigger.disable()


    def test_cmp_cdev_current_control_(self):
        """
        It performs the 'test_cmp_cdev_current_control' test with a set of a
        random number of blocks within the buffer.
        """

        for n_block in range(2, 10):
            print("    test with " + str(n_block) + " blocks in the buffer")
            self.test_cmp_cdev_current_control(n_block)


    def test_cmp_cdev_current_control(self, n_block = 1):
        """
        It fills the buffer with a given number of blocks. Then, it disable the
        trigger and it reads all blocks from the buffer. Only the last block
        must have the control side equal to the current-control of the same
        channel
        """

        # Fill buffer
        utils.trigger_hrt_fill_buffer(self.trigger, n_block, True)

        # Read control one by one
        for i in range(n_block):
            ctrl_cdev = self.interface.read_ctrl()
            ctrl_curr = self.chan.get_current_ctrl()

            if i < n_block - 1:
                self.assertFalse(ctrl_cdev == ctrl_curr,
                        "Except the last control (block), they cannot be equal to the current-control")
            else:
                self.assertTrue(ctrl_cdev == ctrl_curr,
                        "Last control (block) must be equal to current-control")
