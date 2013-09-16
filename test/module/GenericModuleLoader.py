"""
@author: Federico Vaga <federico.vaga@gmail.com>
@copyright: CERN 2013
@license: GPLv2
"""
from test import config
import subprocess
import time

class GenericModuleLoader:
    """
    It provides a set of common functions to test load/unload of a module
    """

    def _test_load_unload(self, module_name):
        """
        It test the load and the unload of a given module
        """
        self._test_insmod(module_name)
        time.sleep(config.wait_insmod_rmmod)
        self._test_rmmod(module_name)


    def _test_insmod(self, module_name):
        err = self._do_insmod(module_name)
        self.assertEqual(err, "", "insmod error: " + err)


    def _test_rmmod(self, module_name):
        err = self._do_rmmod(module_name)
        self.assertEqual(err, "", "rmmod error: " + err)


    def _do_insmod(self, module_name):
        cmd = "insmod " + module_name + ".ko"
        p = subprocess.Popen(cmd, shell = True, stdin = subprocess.PIPE, \
                     stdout = subprocess.PIPE, stderr = subprocess.PIPE, \
                     close_fds = True)
        return p.stderr.read()


    def _do_rmmod(self, module_name):
        cmd = "rmmod " + module_name
        p = subprocess.Popen(cmd, shell = True, stdin = subprocess.PIPE, \
                     stdout = subprocess.PIPE, stderr = subprocess.PIPE, \
                     close_fds = True)
        return p.stderr.read()


    def _get_all_modules(self):
        cmd = "ls zio*.ko"
        p = subprocess.Popen(cmd, shell = True, stdin = subprocess.PIPE, \
                     stdout = subprocess.PIPE, stderr = subprocess.STDOUT, \
                     close_fds = True)
        out = p.stdout.read()
        return out.split()
