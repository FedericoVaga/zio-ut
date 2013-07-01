"""
@author: Federico Vaga <federico.vaga@gmail.com>
@copyright: CERN 2013
@license: GPLv2
"""

from PyZio.ZioConfig import devices_path
from PyZio.ZioDev import ZioDev
import unittest
import os

path = os.path.join(devices_path, "zzero-0000")

@unittest.skipIf(not (os.path.exists(path) and os.path.isdir(path)), "zio zero is not loaded")
class Enable(unittest.TestCase):
    """
    The test is performed on the zio-zero device to test that the core is
    working correctly
    """
    def setUp(self):
        """
        All channels must be enabled before start any test
        """
        self.device = ZioDev(devices_path, "zzero-0000")
        if self.device == None:
            self.skipTest( "Missing device, cannot run tests")
        for cset in self.device.cset:
            cset.enable()
            if cset.is_interleaved():
                cset.interleave.disable()
            for chan in cset.chan:
                if chan.is_interleaved():
                    continue
                chan.enable()


    # # # # # # # # # # # # # # Basic Tests # # # # # # # # # # # # # # #

    def test_enable_device(self):
        """
        Test the sysfs attribute 'enable' on device
        """
        self.toggle_and_set_status(self.device)


    def test_enable_cset(self):
        """
        Test the sysfs attribute 'enable' on channel-sets
        """
        for cset in self.device.cset:
                self.toggle_and_set_status(cset)


    def test_enable_channel(self):
        """
        Test the sysfs attribute 'enable' on channels
        """
        for cset in self.device.cset:
            for chan in cset.chan:
                if chan.is_interleaved():
                    continue
                self.toggle_and_set_status(chan)


    # # # # # # # # # # # # # # Advanced Tests # # # # # # # # # # # # # # #

    def test_enable_cset_channel(self):
        """
        Test the sysfs attribute 'enable' on channel-sets and the effects on
        its channels
        """
        for cset in self.device.cset:           # Disable all Channel sets
            self.set_status(cset, False)
            
        for cset in self.device.cset:           # All channels must be disabled 
            self.all_channel_disabled(cset)

        for cset in self.device.cset:           # Channels cannot become enabled
            self.try_enable_channel(cset)       # Try to enable channels


    def test_enable_device_cset(self):
        """
        Test the sysfs attribute 'enable' on device and the effects on
        its channel-sets
        """
        self.set_status(self.device, False)      # Disable device
        
        for cset in self.device.cset:           # All channel set must be disabled 
            self.assertFalse(cset.is_enable(), "Channel-set '" + cset.fullpath +"' should be disabled")
            self.all_channel_disabled(cset)     # All channels must be disabled

        for cset in self.device.cset:
            cset.enable()                       # Try to force channel-set to
                                                # enable status
            self.assertFalse(cset.is_enable(), "Channel-set cannot be enabled '" + cset.fullpath +"'")
            self.all_channel_disabled(cset)     # All channel set must be disabled
            self.try_enable_channel(cset)       # Try to enable channels


    # # # # # # # # # # # # # # Interleave Tests # # # # # # # # # # # # # # #

    def test_enable_interleave_disabled(self):
        """
        Normal channel must be enabled and the interleaved one must be disabled
        """
        for cset in self.device.cset:
            if not cset.is_interleaved():
                continue                        # Skip non interleaved cset
            
            for chan in cset.chan:
                en = chan.is_enable()
                if chan.is_interleaved():
                    self.assertFalse(en, "Interleaved channel must be disabled")
                else:
                    self.assertTrue(en, "Normal channel must be enabled")


    def test_enable_interleave_enabled(self):
        """
        Normal channel must be disabled and the interleaved one must be enabled
        """
        for cset in self.device.cset:
            if not cset.is_interleaved():
                continue                        # Skip non interleaved cset
            
            cset.interleave.enable()
            self.all_channel_disabled(cset)


    def test_enable_interleave_change(self):
        """
        Normal channel cannot change their status until interleaved channels is
        disables
        """
        for cset in self.device.cset:
            if not cset.is_interleaved():
                continue                        # Skip non interleaved cset
                
            cset.interleave.disable()
            for chan in cset.chan:
                if chan.is_interleaved():
                    continue
                
                chan.enable()
                self.assertFalse(chan.is_enable(), "Channel '" + chan.fullpath +"' should be disabled")


    # # # # # # # # # # # # # # Internal Utility # # # # # # # # # # # # # # #

    def try_enable_channel(self, cset):
        for chan in cset.chan:
            if chan.is_interleaved():
                continue
            chan.enable()                   # Try to force channel to
                                            # enable status
            self.assertFalse(chan.is_enable(), "Channel cannot be enabled '" + chan.fullpath +"'")

    def all_channel_disabled(self, cset):
        """
        It tests that all channels are disabled
        """
        for chan in cset.chan:
            if chan.is_interleaved():
                self.assertTrue(chan.is_enable(), "Channel '" + chan.fullpath +"' should be enabled")
            
            self.assertFalse(chan.is_enable(), "Channel '" + chan.fullpath +"' should be disabled")

    def toggle_and_set_status(self, obj):
        """
        This function toggle the status of the given object two times and then
        it set its status to False and True again
        """ 
        self._toggle_status(self.device)         # Toggle the status
        self._toggle_status(self.device)         # and toggle back again
        self.set_status(self.device, False)      # Force the status to False
        self.set_status(self.device, True)       # and then to True again
        
    def _toggle_status(self, zobj):
        """
        This function swaps the enable status of a given object
        """
        rd1 = zobj.is_enable()
        if rd1:
            zobj.disable()
        else:
            zobj.enable()
        rd2 = zobj.is_enable()
        self.assertNotEqual(rd1, rd2, zobj.name + " didn't change")


    def set_status(self, zobj, st):
        """
        The function force a given object to a given enable status and it
        tests that it is correct
        """
        if st:
            zobj.enable()
            new_st = zobj.is_enable()
            self.assertTrue(new_st, "Cannot enable object '" + zobj.fullpath +"'")
        else:
            zobj.disable()
            new_st = zobj.is_enable()
            self.assertFalse(new_st, "Cannot disable object '" + zobj.fullpath +"'")
        return new_st

