#
# Copyright(c) 2023 Intel Corporation
# SPDX-License-Identifier: BSD-3-Clause
#
from core.test_run import TestRun
from api.cas.cli_messages import  check_stderr_msg



def run_and_validate(cmd, valid_values, expected_error_messages: list = None ):
    TestRun.LOGGER.info(f"Output format: {cmd.param}")
    TestRun.LOGGER.info(f"Encoded command: {cmd.command}")
    output = TestRun.executor.run(cmd.command)
    valid_param = cmd.param in valid_values
    param = cmd.param
    if output.exit_code == 0 and not valid_param :
                    TestRun.LOGGER.error(f" {param} value is not valid")
    elif output.exit_code != 0 and valid_param:
            if expected_error_messages:
                if check_stderr_msg(output, expected_error_messages):
                    return 
            TestRun.LOGGER.error(f" {param} value is valid but command returned with"
                                f" {output.exit_code} exit code\n"
                                f"error: {repr(output.stderr)}")   