import argparse
import time
from pathlib import Path

import m5
from m5.objects.FuncUnitConfig import *

from gem5.components.boards.simple_board import SimpleBoard
from gem5.components.cachehierarchies.classic.private_l1_cache_hierarchy import (
    PrivateL1CacheHierarchy,
)
from gem5.components.memory.simple import SingleChannelSimpleMemory
from gem5.components.processors.base_cpu_core import BaseCPUCore
from gem5.components.processors.base_cpu_processor import BaseCPUProcessor
from gem5.isas import ISA
from gem5.resources.resource import BinaryResource
from gem5.simulate.simulator import Simulator
from gem5.utils.requires import requires


def parse_args():
    parser = argparse.ArgumentParser(
        description="Gem5 SE (syscall emulation) binary workload Runner",
    )
    parser.add_argument(
        "--binary-path", type=str, required=True, help="Path to the binary to run"
    )
    parser.add_argument(
        "--binary-args",
        type=str,
        help="Arguments passed to the binary",
    )
    parser.add_argument(
        "--isa",
        type=str,
        default="X86",
        choices=["X86", "ARM"],
        help="ISA to use (X86 or ARM)",
    )
    parser.add_argument(
        "--rob-size",
        type=int,
        default=512,
        help="Number of entries in the reorder buffer (ROB)",
    )
    parser.add_argument(
        "--lq-size",
        type=int,
        default=32,
        help="Number of entries in the load queue (LQ)",
    )
    parser.add_argument(
        "--sq-size",
        type=int,
        default=32,
        help="Number of entries in the store queue (SQ)",
    )
    return parser.parse_args()


args = parse_args()


# Print all parameters before running
print("Parameters:")
print(f"  binary-path: {args.binary_path}")
print(f"  binary_args: {args.binary_args}")
print(f"  isa: {args.isa}")
print(f"  rob-size: {args.rob_size}")
print(f"  lq-size: {args.lq_size}")
print(f"  sq-size: {args.sq_size}")

# Map string to ISA enum
isa_map = {
    "X86": ISA.X86,
    "ARM": ISA.ARM,
}

isa = isa_map.get(args.isa.upper(), ISA.X86)

# We check for the required gem5 build.
requires(isa_required=isa)

# Setting up all the fixed system parameters here


# Caches: Private L1 caches.
cache_hierarchy = PrivateL1CacheHierarchy(
    l1d_size="16KiB",
    l1i_size="16KiB",
)

# Memory: Mimicking a CXL-attached memory with 250ns latency and 32 GiB/s bandwidth.

memory = SingleChannelSimpleMemory(
    size="2GiB",
    latency="250ns",  # Total latency (Local + CXL Hop)
    latency_var="0ns",  # Unrealistic but makes latency deterministic
    bandwidth="32GiB/s",  # PCIe Gen 5 x16
)

# O3CPUCore extends X86O3CPU / ArmO3CPU. These are gem5's internal models
# that implement an out of order pipeline. Please refer to
#   https://www.gem5.org/documentation/general_docs/cpu_models/O3CPU
# to learn more about O3CPU.

# Select the correct base CPU class based on ISA
if isa == ISA.ARM:
    from m5.objects import ArmO3CPU

    BaseO3CPU = ArmO3CPU
else:
    from m5.objects import X86O3CPU

    BaseO3CPU = X86O3CPU


class O3CPUCore(BaseO3CPU):
    def __init__(self, width, rob_size, lq_size, sq_size):
        """
        :param width: sets the width of fetch, decode, raname, issue, wb, and
        commit stages.
        :param rob_size: determine the number of entries in the reorder buffer.
        :param lq_size: determines the size of the load queue.
        :param sq_size: determines the size of the store queue.
        register file.
        """
        super().__init__()
        self.fetchWidth = width
        self.decodeWidth = width
        self.renameWidth = width
        self.issueWidth = width
        self.wbWidth = width
        self.commitWidth = width

        self.numROBEntries = rob_size

        self.LQEntries = lq_size
        self.SQEntries = sq_size

        self.numPhysIntRegs = 256
        self.numPhysFloatRegs = 256


# Along with BaseCPUCore, CPUStdCore wraps CPUCore to a core compatible
# with gem5's standard library. Please refer to
#   gem5/src/python/gem5/components/processors/base_cpu_core.py
# to learn more about BaseCPUCore.


class O3CPUStdCore(BaseCPUCore):
    def __init__(self, width, rob_size, lq_size, sq_size):
        """
        :param width: sets the width of fetch, decode, raname, issue, wb, and
        commit stages.
        :param rob_size: determine the number of entries in the reorder buffer.
        :param lq_size: determines the size of the load queue.
        :param sq_size: determines the size of the store queue.
        register file.
        """
        core = O3CPUCore(width, rob_size, lq_size, sq_size)
        super().__init__(core, isa)


# O3CPU along with BaseCPUProcessor wraps CPUCore to a processor
# compatible with gem5's standard library. Please refer to
#   gem5/src/python/gem5/components/processors/base_cpu_processor.py
# to learn more about BaseCPUProcessor.


class O3CPU(BaseCPUProcessor):
    def __init__(self, width, rob_size, lq_size, sq_size):
        """
        :param width: sets the width of fetch, decode, raname, issue, wb, and
        commit stages.
        :param rob_size: determine the number of entries in the reorder buffer.
        :param lq_size: determines the size of the load queue.
        :param sq_size: determines the size of the store queue.
        """
        cores = [O3CPUStdCore(width, rob_size, lq_size, sq_size)]
        super().__init__(cores)


processor = O3CPU(
    width=4,
    rob_size=args.rob_size,
    lq_size=args.lq_size,
    sq_size=args.sq_size,
)

board = SimpleBoard(
    clk_freq="3GHz",
    processor=processor,
    memory=memory,
    cache_hierarchy=cache_hierarchy,
)


board.set_se_binary_workload(
    binary=BinaryResource(local_path=Path(args.binary_path).as_posix()),
    env_list=(
        [
            # Set LD_LIBRARY_PATH for dynamic libraries
            "LD_LIBRARY_PATH=/usr/aarch64-linux-gnu/lib:/lib/aarch64-linux-gnu:/lib64:/usr/lib/aarch64-linux-gnu",
        ]
        if isa == ISA.ARM
        else []
    ),
    arguments=args.binary_args.split() if args.binary_args else [],
)


simulator = Simulator(
    board=board,
)

# We maintain the wall clock time.

globalStart = time.time()

print("Running the simulation")
print("Using O3 cpu")


# We start the simulation
simulator.run()

print("All simulation events were successful.")

print(
    "Done with the simulation after %.2f seconds of wall clock time!"
    % (time.time() - globalStart)
)
