# -*- coding: utf-8 -*-
# Copyright (c) 2018 The Regents of the University of California
# All Rights Reserved.
#
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
# Authors: Jason Lowe-Power
# Updated for gem5 25.1 stable release

"""
MySystem: An X86 system configuration for PARSEC benchmarking.

This configuration uses gem5 25.1's component library to set up
a modern, modular system with switchable CPU types suitable for
running PARSEC benchmarks with full system simulation.
"""

import m5

from gem5.coherence_protocol import CoherenceProtocol
from gem5.components.boards.x86_board import X86Board
from gem5.components.memory import DualChannelDDR4_2400
from gem5.components.processors.cpu_types import CPUTypes
from gem5.components.processors.simple_switchable_processor import (
    SimpleSwitchableProcessor,
)
from gem5.isas import ISA

from .caches import CacheHierarchy


class MySystem:
    """
    A simple X86 system with switchable CPUs for PARSEC benchmarking.

    This class wraps gem5 25.1's X86Board to provide a compatible interface
    with the legacy system.py API while using modern gem5 components.
    """

    def __init__(self, kernel, disk, num_cpus, opts, no_kvm=False):
        """
        Create a new MySystem for running PARSEC benchmarks.

        Parameters
        ----------
        kernel : str
            Path to the kernel image
        disk : str
            Path to the disk image
        num_cpus : int
            Number of CPU cores
        opts : object
            Options object with configuration parameters
        no_kvm : bool
            If True, use AtomicSimpleCPU instead of KVM (default: False)
        """
        self._kernel = kernel
        self._disk = disk
        self._num_cpus = num_cpus
        self._opts = opts
        self._no_kvm = no_kvm
        self._host_parallel = not (
            hasattr(opts, "no_host_parallel") and opts.no_host_parallel
        )

        # Determine the starting CPU type
        starting_cpu_type = CPUTypes.ATOMIC if no_kvm else CPUTypes.KVM

        # Set up the processor with switchable core types
        # KVM for boot, O3 for ROI (detailed simulation)
        self.processor = SimpleSwitchableProcessor(
            starting_core_type=starting_cpu_type,
            switch_core_type=CPUTypes.O3,
            isa=ISA.X86,
            num_cores=num_cpus,
        )

        # Some hosts block perf_event_open for unprivileged users. Disable
        # KVM perf counters to avoid startup panic when booting with KVM cores.
        if starting_cpu_type == CPUTypes.KVM:
            for proc in self.processor.start:
                proc.core.usePerf = False

        # Set up memory (3GiB max for X86Board due to I/O hole)
        self.memory = DualChannelDDR4_2400(size="2GiB")

        # Set up cache hierarchy with configurable sizes
        cache_hierarchy = CacheHierarchy(opts)

        # Create the X86Board with all components
        self.board = X86Board(
            clk_freq="2.3GHz",
            processor=self.processor,
            memory=self.memory,
            cache_hierarchy=cache_hierarchy,
        )

        # Store kernel and disk paths for later use
        # Don't set the workload yet - it will be set when readfile_contents is provided
        self._kernel_path = kernel
        self._disk_path = disk

        # Store mem_mode for compatibility
        self.mem_mode = "atomic_noncaching" if not no_kvm else "timing"

    @property
    def cpu(self):
        """Get the current (boot) CPUs. Accessed after instantiation."""
        return [core.get_simobject() for core in self.processor.get_cores()]

    @property
    def timingCpu(self):
        """Get the timing CPUs for ROI. Alias for backward compatibility."""
        return self.cpu

    @property
    def o3Cpu(self):
        """Get the O3 CPUs (which are the switch cores in this setup)."""
        return self.cpu

    def set_kernel_disk_workload(self, readfile_contents):
        """
        Set the kernel disk workload with custom readfile contents.

        Wraps local file paths in proper gem5 Resource objects.

        Parameters
        ----------
        readfile_contents : str
            The command/script to execute in the simulated system
        """
        from gem5.resources.resource import BinaryResource, DiskImageResource

        # Wrap file paths in Resource objects that have get_local_path() method
        kernel_resource = BinaryResource(local_path=self._kernel_path)
        disk_resource = DiskImageResource(local_path=self._disk_path)

        # Set up the workload with Resource objects
        self.board.set_kernel_disk_workload(
            kernel=kernel_resource,
            disk_image=disk_resource,
            readfile_contents=readfile_contents,
        )

    def getHostParallel(self):
        """
        Check if host parallel execution is enabled.

        Returns
        -------
        bool
            True if KVM can run on multiple host threads, False otherwise
        """
        return self._host_parallel

    def totalInsts(self):
        """
        Get the total number of instructions executed across all CPUs.

        Returns the committed instructions from all cores.

        Returns
        -------
        int
            Total instructions executed by all cores
        """
        return self.processor.get_total_instructions()

    def switchCpus(self, old, new):
        """
        Switch from one set of CPUs to another.

        This is typically used to switch from KVM (fast) CPUs during boot
        to more detailed timing/O3 CPUs for detailed performance analysis.

        Parameters
        ----------
        old : list
            List of CPUs to switch from
        new : list
            List of CPUs to switch to
        """
        # In stdlib this processor manages switching internally.
        self.processor.switch()
