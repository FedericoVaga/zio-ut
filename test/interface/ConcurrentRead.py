"""
@author: Federico Vaga <federico.vaga@gmail.com>
@copyright: CERN 2013
@license: GPLv2
"""

from PyZio.ZioConfig import devices_path, triggers, buffers
from PyZio.ZioDev import ZioDev
from PyZio.ZioCharDevice import ZioCharDevice
from test import config
from multiprocessing import Process, Queue
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
class ConcurrentRead(unittest.TestCase):
    """
    It tests the char device interface during concurrent read.
    """

    def setUp(self):
        self.device = ZioDev(devices_path, "zzero-0000")
        if self.device == None:
            self.skipTest("Missing device, cannot run tests")

        # Set channel set and channel to use
        self.cset = self.device.cset[0]  # Use cset input8
        self.chan = self.cset.chan[0]
        self.chan.attribute["alarms"].set_value(0xFF)

        # Set and configure 'hrt' trigger
        self.cset.set_current_trigger("timer")
        self.trigger = self.cset.trigger
        self.trigger.disable()
        self.trigger.attribute["ms-period"].set_value(config.timer_ms_period);

        # Set and flush buffer
        self.cset.set_current_buffer(config.buf)
        self.chan.buffer.flush()
        self.chan.buffer.attribute["max-buffer-len"].set_value(512)


        self.blocks_queue = Queue()
        self.acquired_blocks = []


    def tearDown(self):
        self.trigger.disable()


    def test_concurrent_control_acquisition(self):
        """
        It test that concurrent read does not allow the user to read the same
        block in different process.
        """
        self.process_list = []

        # Enable trigger
        self.trigger.enable()
        time.sleep(0.1 * 512)
        self.trigger.disable()

        for i in range(10):
            p = Process(target = _control_acquisition, args = (i, self.chan, self.blocks_queue))
            self.process_list.append(p)

        # Start all process
        for proc in self.process_list:
            proc.start()

        self._test_concurrent_control_acquisition(self.blocks_queue)


        # Wait the end of all process
        for proc in self.process_list:
            if proc.is_alive():
                proc.join()


    def _test_concurrent_control_acquisition(self, queue):
        """
        It tests that no duplicated block was acquired and that all blocks
        have consecutive sequence number.
        """
        is_duplicated = False
        while True:
            try:
                blocks = queue.get(True, 2)  # Blocking request for 1s
            except:
                break

            proc_id, ctrl, _data = blocks
            if ctrl in self.acquired_blocks:
                is_duplicated = True
            else:
                self.acquired_blocks.append(ctrl)

        self.assertFalse(is_duplicated,
            "Duplicated acquisition at process {0}".format(proc_id))


def _control_acquisition(proc_id, channel, queue):
    """
    It acquires blocks from the channel buffer and put them in the queue shared
    with the other processes
    """
    time.sleep(1)  # Sleep to allow all processes to start
    interface = ZioCharDevice(channel)
    interface.open_ctrl(os.O_RDONLY | os.O_NONBLOCK)
    while interface.is_device_ready(0)[0]:
        try:
            block = (proc_id, interface.read_ctrl(), interface.read_data())
            queue.put(block)
        except:
            print("Some other process stole the block")
            continue
    queue.close()
    interface.close_ctrl()
