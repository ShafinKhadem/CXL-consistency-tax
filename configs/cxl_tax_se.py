import argparse

from gem5.components.boards.simple_board import SimpleBoard
from gem5.components.cachehierarchies.classic.private_l1_private_l2_cache_hierarchy import (
    PrivateL1PrivateL2CacheHierarchy,
)
from gem5.components.memory.simple import SingleChannelSimpleMemory
from gem5.components.processors.simple_processor import SimpleProcessor
from gem5.components.processors.cpu_types import CPUTypes
from gem5.isas import ISA
from gem5.resources.resource import BinaryResource
from gem5.simulate.simulator import Simulator
from gem5.utils.requires import requires

requires(isa_required=ISA.X86)

# ---------- Command-line arguments ----------
parser = argparse.ArgumentParser(description="CXL Tax SE-mode config")
parser.add_argument("--bin",      required=True,       help="Path to static binary")
parser.add_argument("--args",     default="",          help="Space-separated args for binary")
parser.add_argument("--mem-lat",  default="40ns",      help="Memory latency (e.g. 40ns, 300ns)")
parser.add_argument("--mem-bw",   default="100GiB/s",  help="Memory bandwidth (e.g. 100GiB/s)")
parser.add_argument("--mem-size", default="2GiB",      help="Memory size")
parser.add_argument("--clk",      default="3GHz",      help="CPU clock frequency")
parser.add_argument("--cpu-type", default="timing",    choices=["timing", "o3"],
                    help="CPU type: timing (in-order) or o3 (out-of-order)")
parser.add_argument("--rob-size", default=192, type=int,
                    help="ROB entries (O3 only, default 192)")
parser.add_argument("--lq-size",  default=32,  type=int,
                    help="Load queue entries (O3 only, default 32)")
parser.add_argument("--sq-size",  default=32,  type=int,
                    help="Store queue entries (O3 only, default 32)")
# Fault injection arguments
parser.add_argument("--fault-prob",  default=0.0, type=float,
                    help="Per-write fault probability (0.0 = disabled)")
parser.add_argument("--handler",     default="0ns",
                    help="Fault handler penalty latency (e.g. 1us, 5us, 20us)")
parser.add_argument("--rng-seed",    default=42, type=int,
                    help="RNG seed for fault injection reproducibility")
args = parser.parse_args()

# ---------- Cache hierarchy ----------
# If fault injection is enabled, use a subclass that splices in the FaultInjector
if args.fault_prob > 0.0:
    from m5.objects import FaultInjector
    from gem5.components.cachehierarchies.classic.private_l1_private_l2_cache_hierarchy import (
        PrivateL1PrivateL2CacheHierarchy as _BaseCache,
    )
    from gem5.utils.override import overrides
    from gem5.components.cachehierarchies.abstract_cache_hierarchy import (
        AbstractCacheHierarchy,
    )
    from gem5.components.boards.abstract_board import AbstractBoard

    class FaultInjectedCacheHierarchy(_BaseCache):
        """Wraps PrivateL1PrivateL2 and splices FaultInjector between
        the memory bus and the memory controller."""

        def __init__(self, l1d_size, l1i_size, l2_size,
                     fault_prob, handler_penalty, rng_seed):
            super().__init__(l1d_size=l1d_size, l1i_size=l1i_size,
                             l2_size=l2_size)
            self._fault_prob = fault_prob
            self._handler_penalty = handler_penalty
            self._rng_seed = rng_seed

        @overrides(AbstractCacheHierarchy)
        def incorporate_cache(self, board: AbstractBoard) -> None:
            # Create FaultInjector and attach to this hierarchy
            self.fault_injector = FaultInjector(
                fault_prob=self._fault_prob,
                handler_penalty=self._handler_penalty,
                rng_seed=self._rng_seed,
            )

            # Connect system port
            board.connect_system_port(self.membus.cpu_side_ports)

            # Splice: membus → FaultInjector → memory
            for _, port in board.get_mem_ports():
                self.fault_injector.mem_side_port = port
            self.membus.mem_side_ports = self.fault_injector.cpu_side_port

            # Rest is identical to parent (L1/L2 setup)
            from m5.objects import L2XBar
            from gem5.components.cachehierarchies.classic.caches.l1dcache import L1DCache
            from gem5.components.cachehierarchies.classic.caches.l1icache import L1ICache
            from gem5.components.cachehierarchies.classic.caches.l2cache import L2Cache

            self.l2buses = [
                L2XBar() for i in range(board.get_processor().get_num_cores())
            ]

            for i, cpu in enumerate(board.get_processor().get_cores()):
                l2_node = self.add_root_child(
                    f"l2-cache-{i}", L2Cache(size=self._l2_size)
                )
                l1i_node = l2_node.add_child(
                    f"l1i-cache-{i}", L1ICache(size=self._l1i_size)
                )
                l1d_node = l2_node.add_child(
                    f"l1d-cache-{i}", L1DCache(size=self._l1d_size)
                )

                self.l2buses[i].mem_side_ports = l2_node.cache.cpu_side
                self.membus.cpu_side_ports = l2_node.cache.mem_side

                l1i_node.cache.mem_side = self.l2buses[i].cpu_side_ports
                l1d_node.cache.mem_side = self.l2buses[i].cpu_side_ports

                cpu.connect_icache(l1i_node.cache.cpu_side)
                cpu.connect_dcache(l1d_node.cache.cpu_side)

                self._connect_table_walker(i, cpu)

                if board.get_processor().get_isa() == ISA.X86:
                    int_req_port = self.membus.mem_side_ports
                    int_resp_port = self.membus.cpu_side_ports
                    cpu.connect_interrupt(int_req_port, int_resp_port)
                else:
                    cpu.connect_interrupt()

            if board.has_coherent_io():
                self._setup_io_cache(board)

    cache = FaultInjectedCacheHierarchy(
        l1d_size="32KiB",
        l1i_size="32KiB",
        l2_size="256KiB",
        fault_prob=args.fault_prob,
        handler_penalty=args.handler,
        rng_seed=args.rng_seed,
    )
else:
    cache = PrivateL1PrivateL2CacheHierarchy(
        l1d_size="32KiB",
        l1i_size="32KiB",
        l2_size="256KiB",
    )

# ---------- Memory (the CXL knob) ----------
memory = SingleChannelSimpleMemory(
    latency=args.mem_lat,
    latency_var="0ns",
    bandwidth=args.mem_bw,
    size=args.mem_size,
)

# ---------- Processor ----------
if args.cpu_type == "o3":
    cpu_type = CPUTypes.O3
else:
    cpu_type = CPUTypes.TIMING

processor = SimpleProcessor(
    cpu_type=cpu_type,
    isa=ISA.X86,
    num_cores=1,
)

# Configure O3 parameters if using out-of-order CPU
if args.cpu_type == "o3":
    core = processor.get_cores()[0]
    o3cpu = core.get_simobject()
    o3cpu.numROBEntries = args.rob_size
    o3cpu.LQEntries = args.lq_size
    o3cpu.SQEntries = args.sq_size

# ---------- Board ----------
board = SimpleBoard(
    clk_freq=args.clk,
    processor=processor,
    memory=memory,
    cache_hierarchy=cache,
)

# ---------- Workload ----------
binary = BinaryResource(local_path=args.bin)
if args.args.strip():
    board.set_se_binary_workload(binary, arguments=args.args.split())
else:
    board.set_se_binary_workload(binary)

# ---------- Run ----------
sim = Simulator(board)
sim.run()
