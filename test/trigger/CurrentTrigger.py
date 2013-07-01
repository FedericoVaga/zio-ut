"""
@author: Federico Vaga <federico.vaga@gmail.com>
@copyright: CERN 2013
@license: GPLv2
"""

from PyZio.ZioConfig import devices_path, triggers
from PyZio.ZioDev import ZioDev
from test import config
import unittest
import os

path = os.path.join(devices_path, "zzero-0000")

@unittest.skipIf(not (os.path.exists(path) and os.path.isdir(path)),
                 "zio zero is not loaded")
@unittest.skipIf(not ("timer" in triggers),
                 "Trigger 'timer' is required for this test")
@unittest.skipIf(not ("hrt" in triggers),
                 "Trigger 'hrt' is required for this test")
class CurrentTrigger(unittest.TestCase):

    def setUp(self):
        self.device = ZioDev(devices_path, "zzero-0000")
        if self.device == None:
            self.skipTest("Missing device, cannot run tests")

        self.sw_trigger = ("timer", "hrt", "user")

    def test_change_trigger(self):
        """
        Test trigger hot swap
        """
        self._test_change_trigger(False)

    def test_change_trigger_carefully(self):
        """
        Test trigger hot swap with precaution
        """
        self._test_change_trigger(True)

    def test_stress_change_trigger(self):
        """
        It performs the test_change_trigger 1000 times
        """
        for _i in range(config.stress_repetitions):
            self.test_change_trigger()

    def test_stress_change_trigger_carefully(self):
        """
        It performs the test_change_trigger_carefully 1000 times
        """
        for _i in range(config.stress_repetitions):
            self.test_change_trigger_carefully()


    # # # # # # # # # # # # # # Internal Utility # # # # # # # # # # # # # # #

    def _test_change_trigger(self, careful):
        """
        Test that the trigger type change on a channel set (only sw trigger).

        The careful option is 'True' to perform the test in the most safely way.
        Otherwise, it is 'False' and the test change the trigger without any
        precaution
        """

        # Perform test on every channel set
        for cset in self.device.cset:
            otrig = cset.get_current_trigger()

            for trig in self.sw_trigger:
                if careful:
                    cset.trigger.disable()

                cset.set_current_trigger(trig)
                ctrig = cset.get_current_trigger()

                self.assertEqual(trig, ctrig, \
                    "Setted '{0}' but get '{1}'".format(trig, ctrig))
                if (careful == True):
                    cset.trigger.enable()

            # Restore the origianl trigger
            cset.set_current_trigger(otrig)
