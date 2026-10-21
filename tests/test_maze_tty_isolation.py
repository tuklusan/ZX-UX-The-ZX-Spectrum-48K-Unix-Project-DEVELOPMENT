"""Regression: a background Maze1996 must not eat the shell's commands.

Uses the distributed SSX files and the real ZX-UX Z80 kernel in RVM;
no mocked terminal, syscall implementation, or game input handler.
"""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SDK = ROOT / 'dist/sdk/bin/py'
if str(SDK) not in sys.path:
    sys.path.insert(0, str(SDK))
import zxux


class MazeTerminalIsolation(unittest.TestCase):
    def test_maze_game_and_shell_share_no_tty_reads(self):
        source = ROOT / 'src/assets/c48-src/games/maze1996.c'
        code = source.read_text()
        self.assertNotIn('void newest_key_only', code)
        self.assertNotIn('key = getchar(', code)
        self.assertNotIn('0x5B69', code)

        session = zxux.Session(cache=True)
        session.boot()
        paths = ROOT / 'dist/assets/c48-bin/ssx'
        observed = []
        system_hook = session.m.hooks[session.system.syscall]

        def read_string(address):
            chars = []
            for _ in range(48):
                c = session.m.mem[address]
                if not c:
                    break
                chars.append(chr(c))
                address += 1
            return ''.join(chars)

        def audit(machine):
            number = machine.cpu.a
            caller = session.current_pid()
            if number == 11:
                observed.append((caller, 'exec', read_string(machine.cpu.h * 256 + machine.cpu.l)))
            elif number == 35:
                observed.append((caller, 'kill', machine.cpu.h * 256 + machine.cpu.l))
            return system_hook(machine)

        session.m.hooks[session.system.syscall] = audit
        jobs = []
        for name in ('ball', 'maze1996'):
            job = session.launch((paths / (name + '.ssx')).read_bytes(), name, (), True)
            jobs.append(job)
            session.run_until(lambda: job.started is not None, 3500, name + ' loaded')
            session.run_until(lambda: not session.kb.busy(), 1200, 'command typed')

        maze = jobs[1]
        self.assertIsNotNone(session.slot_of(maze.pid))
        session.kb.type('kill %d\n' % jobs[0].pid)
        session.run_until(lambda: not session.kb.busy(), 1400, 'kill typed')
        for _ in range(150):
            session.step()
        self.assertIn((2, 'kill', jobs[0].pid), observed,
                      'maze stole the shell kill command')
        self.assertIsNotNone(session.slot_of(maze.pid), 'maze exited after killing ball')

        session.kb.type('cls\n')
        session.run_until(lambda: any(kind == 'exec' and value == 'cls'
                                      for _, kind, value in observed), 1200,
                          'cls reached the shell')
        session.run_until(lambda: any(kind == 'exec' and value == '/bin/cls'
                                      for _, kind, value in observed), 1200,
                          '/bin/cls was found')
        self.assertIsNotNone(session.slot_of(maze.pid))
        self.assertFalse(any(kind == 'exec' and value in ('ill', 'ls', '/bin/ill')
                             for _, kind, value in observed),
                         'truncated command executed while maze is running')

    def test_gameplay_responds_without_tty_consumption(self):
        s = zxux.Session(cache=True)
        s.boot()
        maze_ssx = ROOT / 'dist/assets/c48-bin/ssx/maze1996.ssx'
        job = s.launch(maze_ssx.read_bytes(), 'maze1996', (), True)
        s.run_until(lambda: job.started is not None, 3500, 'maze started')
        for _ in range(90):
            s.step()
        old = s.m.screen()
        s.kb.add([('press', zxux.char_keys('p'), 24)])
        s.run_until(lambda: not s.kb.busy(), 200, 'play right')
        for _ in range(75):
            s.step()
        new = s.m.screen()
        self.assertGreater(sum(a != b for a, b in zip(old[:6144], new[:6144])), 20)
        self.assertIsNotNone(s.slot_of(job.pid))


if __name__ == '__main__':
    unittest.main()
