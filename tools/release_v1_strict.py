#!/usr/bin/env python3
"""Run ZX-UX release_v1 with a bound independent FUSE login proof.

Provide the same options as tools/release_v1.py. This strict launcher
validates the FUSE command before starting a build, and checks the
actual capture and tape fingerprints before a release can be copied.
"""
import sys

import release_v1
from fuse_release_gate import validate_boot_command, validate_boot_proof


def command_value(argv):
    """Extract the sole FUSE verification command without executing it."""
    flag = '--fuse-test-command'
    if argv.count(flag) != 1:
        raise RuntimeError('Require one FUSE verification command')
    position = argv.index(flag)
    if position + 1 >= len(argv):
        raise RuntimeError('Missing FUSE verification command value')
    return argv[position + 1]


def main():
    command = command_value(sys.argv[1:])
    expected_argv, paths = validate_boot_command(
        command, release_v1.ROOT, release_v1.BUILD, release_v1.PYTHON)
    original_run = release_v1.run
    observed = [False]

    def audited_run(cmd, env=None, log=None):
        result = original_run(cmd, env=env, log=log)
        if list(map(str, cmd)) == expected_argv:
            if observed[0]:
                raise RuntimeError('FUSE verification repeated')
            validate_boot_proof(paths, release_v1.validated_file)
            observed[0] = True
        return result

    release_v1.run = audited_run
    release_v1.main()
    if not observed[0]:
        raise RuntimeError('Independent FUSE proof was not completed')


if __name__ == '__main__':
    try:
        main()
    except (RuntimeError, OSError, ValueError) as error:
        print('RELEASE STOPPED:', error, file=sys.stderr)
        sys.exit(1)
