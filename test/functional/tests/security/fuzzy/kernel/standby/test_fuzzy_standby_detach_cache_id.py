#
# Copyright(c) 2023 Intel Corporation
# SPDX-License-Identifier: BSD-3-Clause
#

import pytest
from api.cas.cache_config import (
    CacheLineSize,
    CacheMode,
    KernelParameters,
    UnalignedIo,
    UseIoScheduler,
)
from api.cas import casadm
from api.cas.cli import standby_detach_cmd
from core.test_run import TestRun
from storage_devices.disk import DiskType, DiskTypeSet
from test_tools.peach_fuzzer.peach_fuzzer import PeachFuzzer
from api.cas.cli_messages import  cache_already_detached
from tests.security.fuzzy.kernel.standby.standby_common import run_and_validate
from tests.security.fuzzy.kernel.common.common import (
    get_fuzz_config,
)
mount_point = "/mnt/test"
config_file = "cache_id.yml"
iterations_count = 1000

@pytest.mark.require_disk("cache", DiskTypeSet([DiskType.optane, DiskType.nand]))
@pytest.mark.parametrizex("cache_line_size", CacheLineSize)
@pytest.mark.parametrizex("unaligned_io", UnalignedIo)
@pytest.mark.parametrizex("use_io_scheduler", UseIoScheduler)
def test_fuzzy_standby_detach_cache_id(cache_line_size, unaligned_io, use_io_scheduler):
    """
    title: Fuzzy test for casadm 'standby detach' command.
    description: Using Peach Fuzzer check CAS ability of handling wrong cache id in
        'standby detach' command.
    pass criteria:
        - System did not crash
        - Open CAS still works.
    """

    with TestRun.step("Prepare CAS instance"):
        kernel_params = KernelParameters(unaligned_io, use_io_scheduler)
        cache_dev = TestRun.disks['cache']
        cache = casadm.standby_init(
            cache_dev = cache_dev,
            cache_id = 1,
            cache_line_size=cache_line_size,
            kernel_params=kernel_params,
            force=True
        )
        TestRun.executor.run_expect_success("udevadm settle")
    
    with TestRun.step("Prepare Peach fuzzer to create 'standby detach' command and then run it"):
        valid_values = [str(cache.cache_id).encode("ascii")] 
        PeachFuzzer.generate_config(get_fuzz_config("cache_id.yml"))
        base_cmd = standby_detach_cmd(cache_id="{param}").encode("ascii")
        commands = PeachFuzzer.get_fuzzed_command(base_cmd, iterations_count)
  
        for index, cmd in TestRun.iteration(
            enumerate(commands), f"Run command {iterations_count} times" 
        ):
            with TestRun.step(f"Iteration {index+1}"):
                run_and_validate(cmd, valid_values, 
                    expected_error_messages=cache_already_detached)
         