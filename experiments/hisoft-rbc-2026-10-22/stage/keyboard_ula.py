"""Provide an idle-high EAR input for isolated native game comparisons.

The preserved Sinclair BASIC Galaxians game uses IN 65278 = 251/253 and
IN 32766 = 251 for x/z/m. The ZX-UX test machine currently holds bit 6
low when no cassette pulses are present, so those comparisons never match.
This hook affects only the test runner, not the compiled game or ZX-UX SDK.
Cassette pulses still use the machine's own EAR-bit implementation.
"""


def idle_ear_high(machine):
    """Make unconnected tape input idle high on even Spectrum port reads.

    Returns a restore function. Call only after the kernel's tape boot has
    completed and before running the game being tested.
    """
    previous = machine.cpu.read_port

    def read_port(port):
        value = previous(port)
        if not port & 1 and machine.pulses is None:
            return value | 0x40
        return value

    machine.cpu.read_port = read_port

    def restore():
        machine.cpu.read_port = previous

    return restore
