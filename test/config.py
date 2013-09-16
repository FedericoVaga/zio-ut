"""
@author: Federico Vaga <federico.vaga@gmail.com>
@copyright: CERN 2013
@license: GPLv2
"""

# # # # # # SYSFS configuration # # # # # # # #

# default buffer and trigger
trig = "timer"
buf = "kmalloc"

# The buffer maximum lenght
buffer_max_len = 16

# The buffer maximum kb lenght
buffer_max_kb = 128

# Number of block add over the buffer limit
n_block_overflow = 100

kb_overflow = 128

# Number of repetitions of a test on stress test
nstress = 100

# ms-period of trigger timer when used
timer_ms_period = 100
timer_ms_period_fast = 50

# time tollerance (nsec)
hrt_slack_nsec = 10000000
time_tollerance_nsec = 20000000
time_tollerance_msec = time_tollerance_nsec / 1000000

# Time to wait (seconds) before reading the acquisition. Usually used with
# trigger timer to allow the trigger to fill the buffer
acquisition_wait = 0.5

# Time to wait (seconds) on select() system call
select_wait = 1

# Time to wait (seconds) between insmod and rmmod
wait_insmod_rmmod = 0

# True if you want to skip long test (> 1min)
skip_long_test = False

# True if you want to skip very long test (> 1 hour)
skip_very_long_test = True

# Number of block to load when you need a filled buffer
n_block_load = 10
