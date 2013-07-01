"""
@author: Federico Vaga <federico.vaga@gmail.com>
@copyright: CERN 2013
@license: GPLv2
"""

from PyZio.ZioConfig import devices_path, zio_bus_path, triggers, buffers
from PyZio import ZioUtil
import unittest
import os

class Basic(unittest.TestCase):
    
    def setUp(self):
        pass

    def tearDown(self):
        pass
    
    def test_zio_loaded(self):
        """
        Test if ZIO is loaded
        """
        exist = os.path.exists(zio_bus_path)
        self.assertTrue(exist, "ZIO must be loaded to run tests")
        
    def test_zio_zero_load(self):
        """
        Test if zio-zero device is loaded
        """
        path = os.path.join(devices_path, "zzero-0000")
        exist = os.path.exists(path) and os.path.isdir(path)
        self.assertTrue(exist, "Missing 'zio-zero' device, it is used in most of these tests")

    def test_zio_trig_user(self):
        """
        Test if trigger 'user' is loaded
        """
        ZioUtil.update_triggers()
        self.assertTrue("user" in triggers, "Missing trigger 'user'. It is part of the core")

    def test_zio_buf_kmalloc(self):
        """
        Test if buffer 'kmalloc' is loaded
        """
        ZioUtil.update_buffers()
        self.assertTrue("kmalloc" in buffers, "Missing buffer 'kmalloc'. It is part of the core")