"""
@author: Federico Vaga <federico.vaga@gmail.com>
@copyright: CERN 2013
@license: GPLv2
"""
import unittest
from test import config
from test.module.GenericModuleLoader import GenericModuleLoader

class ZioModule(unittest.TestCase, GenericModuleLoader):
    def setUp(self):
        self.module_name = "zio"


    def tearDown(self):
        self._do_rmmod(self.module_name)


    def test_load_unload_zio(self):
        """
        It loads and unload the zio core module
        """
        self._test_load_unload(self.module_name)


    @unittest.skipIf(config.skip_long_test, "Skip long test")
    def test_load_unload_zio_stress(self):
        """
        It performs a stress test on the load/unload of the zio core module
        """
        for _i in range(config.nstress):  # stress module load
            self.test_load_unload_zio()
