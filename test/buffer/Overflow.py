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
import os

path = os.path.join(devices_path, "zzero-0000")

@unittest.skipIf(not (os.path.exists(path) and os.path.isdir(path)),
                 "zio zero is not loaded")
@unittest.skipIf(not (config.buf in buffers),
                 "Buffer '" + config.buf + "' " + \
                 "is required for this test")
@unittest.skipIf(not ("hrt" in triggers),
                 "Trigger 'hrt' is required for this test")
class Overflow(unittest.TestCase):
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
        self.chan.attribute["alarms"].set_value(0xFF)

        # Set and configure 'hrt' trigger
        self.cset.set_current_trigger("hrt")
        self.trigger = self.cset.trigger

        # Set and flush buffer
        self.trigger.disable()
        self.cset.set_current_buffer(config.buf)
        self.chan.buffer.flush()

        # Open control char device
        self.interface.open_ctrl_data(os.O_RDONLY)

        # Enable trigger
        self.trigger.enable()


    def tearDown(self):
        self.trigger.disable()
        self.interface.close_ctrl_data()  # Close control cdev


    def test_overflow_config_value(self):
        self._test_overflow(config.buffer_max_len, config.buffer_max_kb, 0.050)


    def test_overflow_random_stress(self):
        """
        It tests the buffer overflow with a random combination of lenght and
        buffer size.
        """
        lst1 = utils.random_list(1, 32, config.nrandom)
        lst2 = utils.random_list(1, 32, config.nrandom)
        for buf_len, buf_kb in zip(lst1, lst2):
            self._test_overflow(buf_len, buf_kb, 0.050)


    def _test_overflow(self, buffer_max_len, buffer_max_kb, s_fire):
        """
        It tests that the buffer handles correctly the overflow. The buffer
        must discard incoming block if it is full, then accepts block again
        when it has free space.

        The test fill the buffer and it tires to write more blocks. The
        'current-control' sequence number must count all blocks that the test
        tried to write in the buffer.

        Then the test reads all blocks in the buffer; their sequence number
        must be sequential. After this no more block should be in the buffer.

        Now, if we read one block it must has the same sequence number of the
        'current-control' and it is not sequentially with the previous ones.
        """
        buf_max_len_list = []
        n_block = []

        # In order to do this test correctly, the buffer must be empty
        self.trigger.disable()
        self.chan.buffer.flush()
        self.chan.attribute["alarms"].set_value(0xFF)
        self.trigger.enable()

        # Configure the buffer len
        if "max-buffer-len" in self.chan.buffer.attribute:
            self.chan.buffer.attribute["max-buffer-len"].set_value(buffer_max_len)
            n_block.append(config.n_block_overflow)
            buf_max_len_list.append(buffer_max_len)

        # Configure the buffer size
        if "max-buffer-kb" in self.chan.buffer.attribute:
            self.chan.buffer.attribute["max-buffer-kb"].set_value(buffer_max_kb)
            # We are using zio-zero input-8, so each byte is a sample (1Kb)
            post_sample = 1024
            self.trigger.attribute["post-samples"].set_value(post_sample)
            n_block.append(config.kb_overflow * 1024 / post_sample)
            buf_max_len_list.append(buffer_max_kb * 1024 / post_sample)
        else:
            buffer_max_kb = 0


        # Get the current status before filling the buffer
        ctrl_curr_pre = self.chan.get_current_ctrl()

        # Fill buffer with 'n_block' blocks. Wait 's_fire' seconds after
        # each fire
        print("\n\tBuffer length = {0} ({1}kb), block overflow = {2}".format(min(buf_max_len_list), buffer_max_kb, max(n_block)))
        print("\tIt can take about {0} seconds".format((max(n_block) + 1) * s_fire))

        # Fill the whole buffer (no overflow)
        for i in range(min(buf_max_len_list)):
            utils.trigger_hrt_fill_buffer(self.trigger, 1)
            self._test_lost_block_alarm(i, False)

        # Try to put other blocks (overflow)
        for i in range(max(n_block)):
            utils.trigger_hrt_fill_buffer(self.trigger, 1)
            self._test_lost_block_alarm(i, True)


        # Get the current status after filling the buffer
        ctrl_curr_post = self.chan.get_current_ctrl()

        # The sequence number does not suffer the overflow effect
        total_block = min(buf_max_len_list) + max(n_block)
        self.assertEqual(ctrl_curr_pre.seq_num + total_block, ctrl_curr_post.seq_num,
            "Sequence number should be {0}, but it is {1}".format(ctrl_curr_pre.seq_num + max(n_block), ctrl_curr_post.seq_num,))

        # It verifies that the buffer is full. It reads all blocks within the
        # buffer to verify if it effectively stopped to store blocks on overflow
        for i in range(min(buf_max_len_list)):
            ready = self.interface.is_device_ready(config.select_wait)
            self.assertTrue(ready, "Missing block {0}/{1}".format(i + 1, buffer_max_len))
            self.interface.read_ctrl()
            self.interface.read_data()


        # Now, no more block should be in the buffer
        ready = self.interface.is_device_ready(config.select_wait)
        self.assertFalse(ready, "No more blocks should be in the buffer")

        # Fill the buffer with one block and then get the control that must has
        # the same sequence number of the current block and it is not
        # sequential with previous blocks
        utils.trigger_hrt_fill_buffer(self.trigger, 1)
        ready = self.interface.is_device_ready(config.select_wait)
        self.assertTrue(ready, "There should be one block")
        ctrl_cdev = self.interface.read_ctrl()

        self.assertEqual(ctrl_curr_post.seq_num + 1, ctrl_cdev.seq_num,
            "Sequence number should be {0}, but it is {1}".format(ctrl_curr_post.seq_num + 1, ctrl_cdev.seq_num))

    def _test_lost_block_alarm(self, index, is_overflow):
        """
        It tests that the "lost block" alarm is consistent with the overflow
        condition. On overflow ,the lost block alarm is raised.
        """
        alarms = self.chan.attribute["alarms"].get_value().split()
        alarms_zio = int(alarms[0])
        lost_block_alarm = False if alarms_zio & 0x1 == 0 else True

        if is_overflow:
            self.assertTrue(lost_block_alarm,
                "Alarm flag must be set on overflow (block {0})".format(index))
        else:
            self.assertFalse(lost_block_alarm,
                "Alarm flag must be clear if no overflow (block {0})".format(index))

        self.chan.attribute["alarms"].set_value(1)
