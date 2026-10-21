"""Regression: foreground physical-key games cannot replay keys into the shell.

The Z80 kernel, foreground Maze1996 TZX payload (SSX), and real terminal
syscalls run unmodified in the ZX-UX RVM. Checks input semantics and shell
exec syscalls, not merely the screenshot after a game exits.
"""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'dist/sdk/bin/py'))
import zxux


class ForegroundKeyboardDrain(unittest.TestCase):
    def test_maze_exit_discards_game_keys_but_preserves_next_command(self):
        s = zxux.Session(cache=True)
        s.boot()
        syscalls = []
        old = s.m.hooks[s.system.syscall]

        def inspect(m):
            if m.cpu.a == 11:  # exec
                ptr = m.cpu.h * 256 + m.cpu.l
                chars = []
                for i in range(64):
                    val = m.mem[ptr + i]
                    if not val:
                        break
                    chars.append(chr(val))
                syscalls.append(('exec', ''.join(chars)))
            elif m.cpu.a == 31:  # stty
                ptr = m.cpu.d * 256 + m.cpu.e
                syscalls.append(('stty', m.mem[ptr+4]))
            return old(m)

        s.m.hooks[s.system.syscall] = inspect
        job = s.launch((ROOT / 'dist/assets/c48-bin/ssx/maze1996.ssx').read_bytes(),
                       'maze1996', (), False)
        s.run_until(lambda: job.started is not None, 5000, 'maze foreground start')
        s.run_until(lambda: not s.kb.busy(), 1200, 'start command sent')
        # Three game-only movement presses, abort, then Q on end-of-game page.
        s.kb.add([('press', zxux.char_keys('p'), 15),
                  ('press', zxux.char_keys('i'), 15),
                  ('press', zxux.char_keys('z'), 15),
                  ('press', zxux.char_keys('0'), 15),
                  ('wait', 70),
                  ('press', zxux.char_keys('q'), 15)])
        s.run_until(lambda: job.ended is not None, 5000, 'maze exited to shell')
        s.run_until(lambda: not s.kb.busy(), 500, 'all game keys released')
        for _ in range(30):
            s.step()
        ring_head = s.m.mem[0x5B00+104]
        ring_tail = s.m.mem[0x5B00+105]
        self.assertEqual(ring_tail, ring_head,
                         'foreground movement keys leaked into shell raw ring')
        self.assertEqual(s.m.mem[0x5B00+106] & 0x30, 0x10,
                         'cooked echoed tty mode was not restored')
        self.assertIn(('stty', 0x90), syscalls,
                      'foreground child completion did not request ring flush')
        self.assertFalse(any(t == 'exec' and n in ('p', 'q', 'z', 'i', 'not found')
                             for t,n in syscalls), syscalls)
        s.kb.type('cls\n')
        s.run_until(lambda: ('exec', '/bin/cls') in syscalls,
                    1500, 'post-game shell command')


if __name__ == '__main__':
    unittest.main()
