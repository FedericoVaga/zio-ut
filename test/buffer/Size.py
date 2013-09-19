"""
@author: Federico Vaga <federico.vaga@gmail.com>
@copyright: CERN 2013
@license: GPLv2
"""

from PyZio.ZioConfig import devices_path, triggers, buffers
from PyZio.ZioDev import ZioDev
from test import config
from test import utils
import unittest
import sys
import os

path = os.path.join(devices_path, "zzero-0000")

@unittest.skipIf(not (os.path.exists(path) and os.path.isdir(path)),
                 "zio zero is not loaded")
@unittest.skipIf(not (config.buf in buffers), "Buffer '" + config.buf + "' " + \
                 "is required for this test")
@unittest.skipIf(not ("hrt" in triggers),
                 "Trigger 'hrt' is required for this test")
class Size(unittest.TestCase):
    """
    It tests the buffer size limit (number of blocks). These tests require
    'zio-zero' device and 'hrt' trigger; they also require that the buffer
    module to test is loaded.
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

        # Set and flush buffer
        self.cset.set_current_buffer(config.buf)
        self.chan.buffer.flush()
        self.chan.attribute["alarms"].set_value(0xFF)

        # Open control char device
        self.interface.open_ctrl_data(os.O_RDONLY)

        # Enable trigger
        self.trigger.enable()


    def tearDown(self):
        self.trigger.disable()
        self.interface.close_ctrl_data()  # Close control cdev


    def test_random_buffer_size_empty(self):
        """
        It tests the buffer resize according to a given value randomly
        generated. The test is performed with an empty buffer.
        """
        sys.stdout.write("\n")
        sizes = utils.random_list(1, 1024, config.nrandom)
        prev = 16
        for size in sizes:
            sys.stdout.write(".")
            sys.stdout.flush()
            self.chan.buffer.flush()
            self._test_resize_buffer(0, prev, size)
            prev = size
        sys.stdout.write("\n")


    def test_decrease_buffer_under_filled(self):
        """
        It verifies that kmalloc buffer remove extra blocks on decrease
        """
        self._test_resize_buffer(15, 16, 8)

    def test_decrease_buffer_under_empty(self):
        self._test_resize_buffer(0, 16, 8)


    def test_decrease_buffer_above_filled(self):
        """
        It verifies that kmalloc buffer does not remove blocks on decrease when
        there is enought space for the blocks already stored
        """
        self._test_resize_buffer(5, 16, 8)

    def test_decrease_buffer_above_empty(self):
        self._test_resize_buffer(0, 16, 8)


    def test_increase_buffer_filled(self):
        """
        It verifies that kmalloc buffer does not remove blocks when the user
        increases the buffer size
        """
        self._test_resize_buffer(5, 16, 32)

    def test_increase_buffer_empty(self):
        self._test_resize_buffer(0, 16, 32)


    def _test_resize_buffer(self, nfill, init_size, target_size):
        if config.buf == "kmalloc":
            self._test_resize_kmalloc_buffer(nfill, init_size, target_size);
        elif config.buf == "vmalloc":
            self._test_resize_vmalloc_buffer(nfill, init_size, target_size);


    def _test_resize_kmalloc_buffer(self, nfill, init_size, target_size):
        """
        It verifies that kmalloc buffer does not remove blocks on decrease if
        there is enought space for the blocks already stored
        """
        # Set buffer size and fill it
        self.chan.buffer.attribute['max-buffer-len'].set_value(init_size)
        utils.trigger_hrt_fill_buffer(self.trigger, nfill)

        # Descrase buffer size in order to remove some blocks from it
        self.chan.buffer.attribute['max-buffer-len'].set_value(target_size)
        rb = int(self.chan.buffer.attribute['max-buffer-len'].get_value())
        self.assertEqual(target_size, rb,
            "'max-buffer-len' should be {1}, but it is {0}".format(rb, target_size))

        i = 0
        while self.interface.is_device_ready(0.1):
            i += 1
            self.interface.read_ctrl()

        self.assertEqual(i, nfill, "'kmalloc' does not remove blocks on resize")


    def _test_resize_vmalloc_buffer(self, nfill, init_size, target_size):
        """
        It verifies that vmalloc buffer flush stored blocks and set the new
        size
        """
        # Set buffer size and fill it
        self.chan.buffer.attribute['max-buffer-kb'].set_value(init_size)
        utils.trigger_hrt_fill_buffer(self.trigger, nfill)


        # Descrase buffer size in order to remove some blocks from it
        self.chan.buffer.attribute['max-buffer-kb'].set_value(target_size)
        rb = int(self.chan.buffer.attribute['max-buffer-kb'].get_value())
        self.assertEqual(target_size, rb,
            "'max-buffer-kb' should be {1}, but it is {0}".format(rb, target_size))

        ready = self.interface.is_device_ready()
        self.assertFalse(ready, "'vmalloc' should be empty")
