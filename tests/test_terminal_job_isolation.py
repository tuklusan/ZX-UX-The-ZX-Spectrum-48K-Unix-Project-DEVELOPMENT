"""Real ZX-UX/RVM terminal regression for background C48 jobs and shell.

Uses compiled distributed programs, the actual Z80 kernel and shell, and
unaltered syscall execution.  No host-side stub is substituted for tty reads.
"""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'dist/sdk/bin/py'))
import zxux


class TerminalIsolation(unittest.TestCase):
    def setUp(self):
        self.s = zxux.Session(cache=True)
        self.s.boot()
        self.execs = []
        self.reads = []
        saved = self.s.m.hooks[self.s.system.syscall]

        def spy(m):
            a = m.cpu.a
            pid = self.s.current_pid()
            if a == 11:
                addr = (m.cpu.h << 8) | m.cpu.l
                name = []
                for i in range(48):
                    c = m.mem[addr+i]
                    if not c:
                        break
                    name.append(chr(c))
                self.execs.append((pid, ''.join(name)))
            if a == 3 and m.cpu.h == 0 and m.cpu.l == 0:
                self.reads.append(pid)
            return saved(m)

        self.s.m.hooks[self.s.system.syscall] = spy

    def load(self, name):
        data = (ROOT / 'dist/assets/c48-bin/ssx' / (name + '.ssx')).read_bytes()
        j = self.s.launch(data, name, (), True)
        self.s.run_until(lambda: j.started is not None, 3500, name + ' start')
        self.s.run_until(lambda: not self.s.kb.busy(), 1500, name + ' command input done')
        return j

    def command(self, command='cls'):
        s = self.s
        for _ in range(45):
            s.step()
        s.kb.type(command + '\n')
        s.run_until(lambda: not s.kb.busy(), 2000, 'command typed')
        s.run_until(lambda: any(name == '/bin/' + command for pid, name in self.execs),
                    1600, command + ' reached executable')
        self.assertEqual(s.m.mem[(s.system.sym['p_stat'] + 106)] & 0x30, 0x10,
                         'shell must restore cooked/echo terminal mode')

    def test_background_text_game_cannot_consume_shell_commands(self):
        j = self.load('fortune')
        self.command()
        # Background libc may attempt read(0), but its closed descriptor
        # must fail before it reaches the terminal ring.
        self.assertIsNotNone(self.s.slot_of(j.pid))

    def test_background_text_app_cannot_consume_shell_commands(self):
        self.load('gp82')
        self.command()

    def test_background_visual_demo_retains_shell_input(self):
        self.load('ball')
        self.command()

    def test_game_has_nonconsuming_hardware_fallback(self):
        j = self.load('fortune')
        self.assertIsNotNone(self.s.slot_of(j.pid))
        self.s.kb.add([('press', zxux.char_keys('n'), 25)])
        self.s.run_until(lambda: not self.s.kb.busy(), 600, 'physical key release')
        for _ in range(70):
            self.s.step()
        self.assertIsNotNone(self.s.slot_of(j.pid))
        # Physical polling deliberately does not remove keys from the tty;
        # submit the shell's copy of the key before the next command.
        self.s.kb.type('\n')
        self.s.run_until(lambda: not self.s.kb.busy(), 600, 'line submitted')
        for _ in range(70):
            self.s.step()
        self.command()


if __name__ == '__main__':
    unittest.main()
