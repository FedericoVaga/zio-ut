"""
@author: Federico Vaga <federico.vaga@gmail.com>
@copyright: CERN 2013
@license: GPLv2
"""

# Number of repetitions of a test on stress test
stress_repetitions = 100

# ms-period of trigger timer when used
timer_ms_period = 100

# Time to wait (seconds) before reading the acquisition. Usually used with
# trigger timer to allow the trigger to fill the buffer
acquisition_wait = 0.5

# Time to wait (seconds) on select() system call
select_wait = 1

# Time to wait (seconds) between insmod and rmmod
wait_insmod_rmmod = 0

# True if you want to skip long test (> 1min)
skip_long_test = False

# Number of block to load when you need a filled buffer
n_block_load = 10
