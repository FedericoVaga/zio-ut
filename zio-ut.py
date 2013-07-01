#!/usr/bin/python
"""
@author: Federico Vaga <federico.vaga@gmail.com>
@copyright: CERN 2013
@license: GPLv2
"""
from PyZio.ZioConfig import devices_path, triggers

import unittest
import sys
from PyZio import ZioUtil

# List of all tests
test_list = [
    "test.module.CoreModule.ZioModule",
    "test.module.BufferModule.BufVmallocModule",
    "test.module.TriggerModule.TrigTimerModule",
    "test.module.TriggerModule.TrigHrtModule",
    "test.sysfs.Enable",
    "test.trigger.CurrentTrigger",
             ]

def zio_test_help():
    """
    Print usage information about this unit-test
    """
    print("zio-ut [TESTS]")
    print("")
    print("[TESTS]: list of tests to perform. It can be the name of a specific test, or the name of a module of tests")
    print("         In alternative, you che use the test code:")
    print("Code          test case")
    print("- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - ")
    i = 0
    for t in test_list:
        print(str(i) + "  " + t)
        i = i + 1

if __name__ == '__main__':
    # The program accept at least one argument
    if len(sys.argv[1:]) == 0:
        zio_test_help()
        exit()

    # Prepare the list of all tests to perform
    module_list = []
    for arg in sys.argv[1:]:
        index = int(arg);
        module_list.append(test_list[index])

    # If the ZIO framework is loaded, then load device, trigger and buffer
    # information
    if ZioUtil.is_loaded():
        ZioUtil.update_all_zio_objects()

    # Load a set of tests by using the module name
    try:
        suite = unittest.TestLoader().loadTestsFromNames(module_list)
    except:
        print("Invalid module name in: ")
        print(module_list)
        exit()

    # Perform tests of retrieved modules
    for s in suite:
        unittest.TextTestRunner(verbosity = 2).run(s)
