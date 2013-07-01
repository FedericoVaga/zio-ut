"""
@author: Federico Vaga <federico.vaga@gmail.com>
@copyright: CERN 2013
@license: GPLv2
"""

from PyZio.ZioConfig import devices_path, buffers
from PyZio.ZioDev import ZioDev
from test import config
import unittest
import os

path = os.path.join(devices_path, "zzero-0000")

@unittest.skipIf(not (os.path.exists(path) and os.path.isdir(path)),
                 "zio zero is not loaded")
@unittest.skipIf(not ("vmalloc" in buffers),
                 "Buffer 'vmalloc' is required for this test")
class CurrentBuffer(unittest.TestCase):

    def setUp(self):
        self.device = ZioDev(devices_path, "zzero-0000")
        if self.device == None:
            self.skipTest("Missing device, cannot run tests")

        self.sw_buffer = ("vmalloc", "kmalloc")


    def test_change_buffer(self):
        """
        Test buffer hot swap without precaution.
        """
        self._test_change_buffer(False)


    def test_change_buffer_carefully(self):
        """
        Test buffer hot swap with precaution.
        """
        self._test_change_buffer(True)


    def test_stress_change_buffer(self):
        """
        It performs the test_change_buffer 1000 times
        """
        for _i in range(config.stress_repetitions):
            self.test_change_buffer()


    def test_stress_change_buffer_carefully(self):
        """
        It performs the test_change_buffer_carefully 1000 times
        """
        for _i in range(config.stress_repetitions):
            self.test_change_buffer_carefully()


    def _test_change_buffer(self, careful):
        """
        Test that the buffer type change on a channel set (only sw buffer).

        If the careful option is 'True' it performs the test in the most
        safely way. Otherwise, it is 'False' and the test change the buffer
        without any precaution
        """

        # Perform test on every channel set
        for cset in self.device.cset:
            obuf = cset.get_current_buffer()

            for buf in self.sw_buffer:
                if careful:
                    cset.trigger.disable()

                cset.set_current_buffer(buf)
                cbuf = cset.get_current_buffer()
                self.assertEqual(buf, cbuf, \
                        "Setted '{0}' but get '{1}'".format(buf, cbuf))

                if careful:
                    cset.trigger.enable()

            # Restore the origianl buffer
            cset.set_current_buffer(obuf)
