"""
@author: Federico Vaga <federico.vaga@gmail.com>
@copyright: CERN 2013
@license: GPLv2
"""

from PyZio.ZioConfig import devices_path, buffers
from PyZio.ZioDev import ZioDev
from test import config, utils
import os, sys, unittest

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

        # Set channel set and channel to use
        self.cset = self.device.cset[0]  # Use cset input8
        self.chan = self.cset.chan[0]
        self.interface = self.chan.interface

        # Set and configure 'hrt' trigger
        self.cset.set_current_trigger("hrt")
        self.trigger = self.cset.trigger

        # Enable trigger
        self.trigger.enable()

        self.sw_buffer = ("vmalloc", "kmalloc")


    def tearDown(self):
        self.trigger.disable()
        self.interface.close_ctrl_data()  # Close control cdev


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
        sys.stdout.write("\n")
        for _i in range(config.nstress):
            sys.stdout.write(".")
            sys.stdout.flush()
            self.test_change_buffer()
        sys.stdout.write("\n")


    def test_stress_change_buffer_carefully(self):
        """
        It performs the test_change_buffer_carefully 1000 times
        """
        sys.stdout.write("\n")
        for _i in range(config.nstress):
            sys.stdout.write(".")
            sys.stdout.flush()
            self.test_change_buffer_carefully()
        sys.stdout.write("\n")


    def _test_change_buffer(self, careful):
        """
        Test that the buffer type change on a channel set (only sw buffer).

        If the careful option is 'True' it performs the test in the most
        safely way. Otherwise, it is 'False' and the test change the buffer
        without any precaution
        """

        obuf = self.cset.get_current_buffer()

        for buf in self.sw_buffer:
            if careful:
                self.trigger.disable()

            utils.trigger_hrt_fill_buffer(self.trigger, 5)

            self.cset.set_current_buffer(buf)
            cbuf = self.cset.get_current_buffer()
            self.assertEqual(buf, cbuf, \
                    "Setted '{0}' but get '{1}'".format(buf, cbuf))

            if obuf != cbuf:
                # Open control char device
                self.interface.open_ctrl_data(os.O_RDONLY)
                ready = self.interface.is_device_ready(1)
                self.interface.close_ctrl_data()  # Close control cdev

                self.assertFalse(ready, "Buffer should be empty on change")

            if careful:
                self.cset.trigger.enable()

        # Restore the origianl buffer
        self.cset.set_current_buffer(obuf)

