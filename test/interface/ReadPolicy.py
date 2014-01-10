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
@unittest.skipIf(not (config.buf in buffers),
                 "Buffer '" + config.buf + "' " + \
                 "is required for this test")
@unittest.skipIf(not ("hrt" in triggers),
                 "Trigger 'hrt' is required for this test")
class ReadPolicy(unittest.TestCase):
    """
    It tests that the char device interface retrieve blocks correctly.
    """

    def setUp(self):
        self.device = ZioDev(devices_path, "zzero-0000")
        if self.device == None:
            self.skipTest("Missing device, cannot run tests")

        # Set channel set and channel to use
        self.cset = self.device.cset[0]  # Use cset input8
        self.chan = self.cset.chan[0]
        self.interface = self.chan.interface
        self.chan.attribute["alarms"].set_value(0xFF)

        # Set and configure 'hrt' trigger
        self.cset.set_current_trigger("hrt")
        self.trigger = self.cset.trigger

        # Set and flush buffer
        self.cset.set_current_buffer(config.buf)
        self.chan.buffer.flush()

        # Enable trigger
        self.trigger.enable()

        sys.stdout.write("\n")


    def tearDown(self):
        self.trigger.disable()
        self.interface.close_ctrl_data()
        sys.stdout.write("\n")


    def test_read(self):
        """
        It simply verify that the read procedure works. The procedure to read
        a full zio block is:
        - read the control block from ctrl char device
        - read the N bytes from data char device. The number of bytes to read
          N is calculated with control information (ssize * nsamples)
        The data char device can return fewer bytes than you request. This is
        not a problem if you are reading, for example, byte by byte the block.
        This is a bug when you request the whole data but it returns less bytes.
        """

        # Fill the buffer
        utils.trigger_hrt_fill_buffer(self.trigger, 1, 0, 1, 0.1, True)

        self.interface.open_ctrl_data(os.O_RDONLY)
        ready = self.interface.is_device_ready(0.01)
        self.assertTrue(ready[0], "A block must be in the buffer")
        ctrl, data = self.interface.read_block(True, True)

        self.assertEqual(ctrl.nsamples, len(data),
            "The number of sample should be {0}, but it is {1}".format(ctrl.nsamples, len(data)))


    def test_read_stress(self):
        """
        It repeats the test_read a number of times specified by the
        configuration parameter stress_repetitions
        """
        for _i in range(config.nstress):
            self.test_read()
            self.interface.close_ctrl_data()


    def test_double_read_control(self):
        """
        The test verify that you retrieve a new block each time you read the
        control char device. So, the new control must be different by the
        previous one; the sequence number of the new block must be
        consecutive of the previous one.
        """
        n_block = 10

        # Fill the buffer
        utils.trigger_hrt_fill_buffer(self.trigger, n_block, 0, 1, 0.1, True)

        ctrl_old = None
        self.interface.open_ctrl(os.O_RDONLY)
        for _i in range(n_block):
            ready = self.interface.is_device_ready(0.01)
            self.assertTrue(ready[0], "Blocks must be available")
            ctrl_new = self.interface.read_ctrl()

            if ctrl_old == None:
                ctrl_old = ctrl_new
                continue
            # Further tests
            self.assertNotEqual(ctrl_old, ctrl_new,
                "Control must be different from the previous one")
            self.assertEqual(ctrl_old.seq_num + 1, ctrl_new.seq_num,
                "Block should be consecutive")
            ctrl_old = ctrl_new

        ready = self.interface.is_device_ready(0.01)
        self.assertFalse(ready[0], "Buffer must be empty")


    def test_dobule_read_data(self):
        """
        The test verify that you retrieve a new block each time you completely
        read all samples of a block (data char device).
        During data reading, we open only the data char device because the
        select can retrieve a new block also from control char device, but we
        want to test only the data char device.
        """
        n_block = 10

        # Fill the buffer
        utils.trigger_hrt_fill_buffer(self.trigger, n_block, 0, 1, 0.1, True)


        self.interface.open_ctrl_data(os.O_RDONLY)
        ready = self.interface.is_device_ready(10)
        self.assertTrue(ready[0], "Blocks must be available")
        self.interface.read_block(True, True)
        self.interface.close_ctrl_data()

        self.interface.open_data(os.O_RDONLY)
        for _i in range(n_block - 1):
            ready = self.interface.is_device_ready(10)
            self.assertTrue(ready[0], "Blocks must be available")
            _data = self.interface.read_data()

        ready = self.interface.is_device_ready(10)
        self.assertFalse(ready[0], "Buffer must be empty")


    def test_control_read_size(self):
        """
        It tests that you can request to the control char device only 512byte
        at time, no more, no less.
        """

        utils.trigger_hrt_fill_buffer(self.trigger, config.n_block_load, 0.1, True)

        self.interface.open_ctrl_data(os.O_RDONLY)
        fd = self.interface.fileno_ctrl()

        if self.interface.is_device_ready(10)[0]:
            with self.assertRaises(OSError):
                os.read(fd, 256)

        if self.interface.is_device_ready(10)[0]:
            try:
                os.read(fd, 512)
            except:
                self.fail("Reading 512byte should not fail")

        if self.interface.is_device_ready(10)[0]:
            with self.assertRaises(OSError):
                os.read(fd, 1024)

        self.interface.close_ctrl_data()
