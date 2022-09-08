#
# Copyright(c) 2022 Intel Corporation
# SPDX-License-Identifier: BSD-3-Clause
#


import pytest
import pdb

from api.cas import casadm
from storage_devices.disk import DiskType, DiskTypeSet, DiskTypeLowerThan
from core.test_run import TestRun
from storage_devices.raid import Raid, RaidConfiguration, MetadataVariant, Level
from test_utils.size import Size, Unit
from test_tools.disk_utils import Filesystem
from test_tools.fs_utils import create_random_test_file
from api.cas.cache_config import CacheLineSize

mount_point = "/mnt/test"
test_file_path = f"{mount_point}/test_file"

@pytest.mark.require_disk("cache", DiskTypeSet([DiskType.optane, DiskType.nand]))
@pytest.mark.require_disk("raid_1",  DiskTypeSet([DiskType.nand]))
@pytest.mark.require_disk("raid_2",  DiskTypeSet([DiskType.hdd]))
@pytest.mark.require_disk("raid_3",  DiskTypeSet([DiskType.hdd]))
@pytest.mark.require_disk("raid_4",  DiskTypeSet([DiskType.hdd]))
@pytest.mark.require_disk("raid_5",  DiskTypeSet([DiskType.hdd]))
def test_create_filesystem_on_16TB():
    """
    title:
      Create filesystem on CAS device with core bigger than 16TiB
    description:
      CAS Linux should be able to use volume with size over 16TiB and filesystem.
      Filesystem created on intel CAS device
    pass criteria:
      - Created 16TB RAID0
      - Created filesystem on CAS core
      - Created file in filesystem 
    """
    with TestRun.step("Preparing devices"):
      cache = TestRun.disks["cache"]

      raid_memb = [TestRun.disks["raid_1"], TestRun.disks["raid_2"], 
      TestRun.disks["raid_3"], TestRun.disks["raid_4"], TestRun.disks["raid_5"]]
      # for d in raid_memb:
      #    d.create_partitions([Size(3.2, Unit.TebiByte)]) 
      TestRun.LOGGER.info("Devices prepared")

    with TestRun.step("Creating RAID0 volume"):
        config = RaidConfiguration(
            level=Level.Raid0,
            metadata=MetadataVariant.Legacy,
            number_of_devices=len(raid_memb),
            )
        # pdb.set_trace()
        raid_volume = Raid.create(config, raid_memb) #[d.partitions[0] for d in raid_memb])
        TestRun.LOGGER.info("Created RAID0 volume")

    with TestRun.step("Start cache device and add raid as its core"):
        cache = casadm.start_cache(cache, force=True, cache_line_size=CacheLineSize.LINE_8KiB)
        core = cache.add_core(raid_volume)

    with TestRun.step("Create filesystem and mount it"):    
        core.create_filesystem(Filesystem.xfs, blocksize = int(Size(1, Unit.Blocks4096)))
        core.mount(mount_point)
    
    with TestRun.step("Check if file can be putted in filesystem"):
        test_file = create_random_test_file(test_file_path)
        TestRun.LOGGER.info("Created file successfully")

    with TestRun.step("Unmount core"):
        core.unmount()