"""
@author: Federico Vaga <federico.vaga@gmail.com>
@copyright: Federico Vaga 2012
@license: GPLv2
"""
import unittest
from test import config
from test.module.GenericModuleLoader import GenericModuleLoader

class BufVmallocModule(unittest.TestCase, GenericModuleLoader):
    """
    The test verify the load and the unload of the vmalloc buffer
    """

    def setUp(self):
        """
        It loads all dependencies before start the test
        """
        self.module_name = "zio-buf-vmalloc"
        self.module_dep = ["zio", ]

        for d in self.module_dep:
            err = self._do_insmod(d)
            if err != "":
                self.skipTest("Cannot load dependency " + d + ", " + err)


    def tearDown(self):
        """
        It removes all module to restore the original situation
        """
        self._do_rmmod(self.module_name)
        for d in reversed(self.module_dep):
            self._do_rmmod(d)


    def test_load_unload_vmalloc(self):
        """
        It loads and unload the vmalloc buffer module
        """
        self._test_load_unload(self.module_name)


    @unittest.skipIf(config.skip_long_test, "Skip long test")
    def test_load_unload_vmalloc_stress(self):
        """
        It performs a stress test on the load/unload of the vmalloc buffer
        """
        for _i in range(config.nstress):  # stress module load
            self.test_load_unload_vmalloc()
