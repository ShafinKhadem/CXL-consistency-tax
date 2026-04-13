# -*- coding: utf-8 -*-
# Copyright (c) 2019 The Regents of the University of California.
# All rights reserved.
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met: redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer;
# redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in the
# documentation and/or other materials provided with the distribution;
# neither the name of the copyright holders nor the names of its
# contributors may be used to endorse or promote products derived from
# this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# Authors: Jason Lowe-Power, Mahyar Samani
# Updated for gem5 25.1 stable release

"""Script to run PARSEC benchmarks with gem5 25.1.

The script expects kernel, diskimage, cpu (kvm, timing, or o3),
benchmark, benchmark size, and number of cpu cores as arguments.
This script is best used with disk-images that have workloads with
ROI annotations compliant with m5 utility. You can use the script in
../disk-images/parsec/ with the parsec-benchmark repo at
https://github.com/darchr/parsec-benchmark.git to create a working
disk-image for this script.
"""
import argparse
import os
import sys
import time

import m5
from system import MySystem

from gem5.simulate.exit_event import ExitEvent
from gem5.simulate.simulator import Simulator


def writeBenchScript(dir, bench, size):
    """
    Create a script in dir to run a PARSEC benchmark.

    This script will be executed in the simulated system at bootup.
    """
    # Ensure the directory exists
    os.makedirs(dir, exist_ok=True)

    file_name = "{}/run_{}".format(dir, bench)
    with open(file_name, "w+") as bench_file:
        bench_file.write("#!/bin/bash\n")
        bench_file.write("cd /home/gem5/parsec-benchmark\n")
        bench_file.write("source env.sh\n")
        bench_file.write(
            "parsecmgmt -a run -p {} -c gcc-hooks -i {}\n".format(bench, size)
        )
        # Sleeping ensures benchmark output is printed properly
        bench_file.write("sleep 5\n")
        bench_file.write("m5 exit\n")

    return file_name


def handle_workbegin(system_obj):
    """Handle workbegin exit event."""
    print("Reached beginning of ROI - starting detailed simulation")
    print("Resetting stats at the start of ROI!")
    m5.stats.reset()
    return False  # Continue simulation


def handle_workend(system_obj):
    """Handle workend exit event."""
    print("Reached end of ROI - switching back to fast CPU")
    print("Dumping stats at the end of the ROI!")
    m5.stats.dump()
    return True  # Exit simulation


if __name__ == "__m5_main__":
    parser = argparse.ArgumentParser(description="Run PARSEC benchmarks with gem5 25.1")

    parser.add_argument(
        "kernel",
        help="Path to the kernel image",
    )
    parser.add_argument(
        "disk",
        help="Path to the disk image",
    )
    parser.add_argument(
        "cpu",
        choices=["kvm", "timing", "o3"],
        help="CPU type for detailed simulation (after workbegin)",
    )
    parser.add_argument(
        "benchmark",
        help="PARSEC benchmark to run",
    )
    parser.add_argument(
        "size",
        help="Input size (simsmall, simmedium, simlarge)",
    )
    parser.add_argument(
        "num_cpus",
        type=int,
        help="Number of CPU cores",
    )

    # Parse arguments - support both old and new style
    if len(sys.argv) > 1 and sys.argv[1] == "__m5_main__":
        # old SimpleOpts style - skip m5
        args = parser.parse_args(sys.argv[2:])
    else:
        args = parser.parse_args()

    kernel = args.kernel
    disk = args.disk
    cpu = args.cpu
    benchmark = args.benchmark
    size = args.size
    num_cpus = args.num_cpus

    # Create options object for system configuration
    class SystemOpts:
        no_host_parallel = False
        second_disk = ""
        l1i_size = None
        l1d_size = None
        l2_size = None

    opts = SystemOpts()

    # Create the system for PARSEC simulation
    system = MySystem(kernel, disk, num_cpus, opts, no_kvm=False)

    # Create the workload script
    workload_script = writeBenchScript(m5.options.outdir, benchmark, size)

    # Read the workload script and pass it to the system
    with open(workload_script, "r") as f:
        workload_contents = f.read()

    # Set the workload
    system.set_kernel_disk_workload(workload_contents)

    # Disable long-running job listeners
    m5.disableAllListeners()

    # Required when using Standard Library boards with legacy m5.instantiate.
    root = system.board._pre_instantiate()

    if system.getHostParallel():
        # Required for running KVM on multiple host cores.
        # Uses gem5's parallel event queue feature.
        # Note: The simulator is quite picky about this number!
        root.sim_quantum = int(1e9)  # 1 ms

    # Instantiate all of the objects we've created
    m5.instantiate()

    global_start = time.time()

    print("Running the simulation")
    print("Using KVM CPU for boot")
    print("Benchmark:", benchmark)
    print("Benchmark size:", size)
    print("Number of cores:", num_cpus)

    # Reset stats before simulation
    m5.stats.reset()

    # Start the simulation and look for workbegin
    start_tick = m5.curTick()
    end_tick = m5.curTick()
    start_insts = system.totalInsts()
    end_insts = system.totalInsts()

    print("\nWaiting for workbegin()...")
    exit_event = m5.simulate()

    if exit_event.getCause() == "workbegin":
        # Reached the start of ROI
        # start of ROI is marked by an
        # m5_work_begin() call
        print("Resetting stats at the start of ROI!")
        m5.stats.reset()
        start_tick = m5.curTick()
        start_insts = system.totalInsts()

        # Switch to detailed CPU model for the ROI
        print(f"Switching to {cpu} CPU model for detailed simulation...")
        if cpu == "timing":
            system.switchCpus(system.cpu, system.timingCpu)
        elif cpu == "o3":
            system.switchCpus(system.cpu, system.o3Cpu)
    else:
        print("Unexpected termination of simulation!")
        print()
        m5.stats.dump()
        end_tick = m5.curTick()
        end_insts = system.totalInsts()
        m5.stats.reset()
        print("Performance statistics:")

        print("Simulated time: %.2fs" % ((end_tick - start_tick) / 1e12))
        print("Instructions executed: %d" % ((end_insts - start_insts)))
        print("Ran a total of", m5.curTick() / 1e12, "simulated seconds")
        print(
            "Total wallclock time: %.2fs, %.2f min"
            % (time.time() - globalStart, (time.time() - globalStart) / 60)
        )
        exit(1)

    # Simulate the ROI
    exit_event = m5.simulate()

    # Reached the end of ROI
    # Finish executing the benchmark with kvm cpu
    if exit_event.getCause() == "workend":
        # Reached the end of ROI
        # end of ROI is marked by an
        # m5_work_end() call
        print("Dump stats at the end of the ROI!")
        m5.stats.dump()
        end_tick = m5.curTick()
        end_insts = system.totalInsts()
        m5.stats.reset()
        # switch back to boot cpu model after the ROI
        if cpu == "timing":
            system.switchCpus(system.timingCpu, system.cpu)
        elif cpu == "o3":
            system.switchCpus(system.o3Cpu, system.cpu)
    else:
        print("Unexpected termination of simulation!")
        print()
        m5.stats.dump()
        end_tick = m5.curTick()
        end_insts = system.totalInsts()
        m5.stats.reset()
        print("Performance statistics:")

        print("Simulated time: %.2fs" % ((end_tick - start_tick) / 1e12))
        print("Instructions executed: %d" % ((end_insts - start_insts)))
        print("Ran a total of", m5.curTick() / 1e12, "simulated seconds")
        print(
            "Total wallclock time: %.2fs, %.2f min"
            % (time.time() - globalStart, (time.time() - globalStart) / 60)
        )
        exit(1)

    # Simulate the remaning part of the benchmark
    exit_event = m5.simulate()

    print("Done with the simulation")
    print()
    print("Performance statistics:")

    print("Simulated time in ROI: %.2fs" % ((end_tick - start_tick) / 1e12))
    print("Instructions executed in ROI: %d" % ((end_insts - start_insts)))
    print("Ran a total of", m5.curTick() / 1e12, "simulated seconds")
    print(
        "Total wallclock time: %.2fs, %.2f min"
        % (time.time() - globalStart, (time.time() - globalStart) / 60)
    )
