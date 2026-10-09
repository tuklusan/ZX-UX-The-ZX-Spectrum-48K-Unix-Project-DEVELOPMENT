"""Run the suite with sentinel-filled low-memory candidates; report writes."""
import sys, os
ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
sys.path.insert(0, ROOT + '/tests'); sys.path.insert(0, ROOT + '/tools')
import suite, zxrun
PAT = 0xA5
REG = {


       '5F00': (0x5F00, 0x5F01)}
KV2END = int(sys.argv[1], 16) if len(sys.argv) > 1 else 0x5D98
stats = {}
orig_until = suite.Session.until
class S(suite.Session):
    patched = False
    def until(self, text, frames=3000):
        r = orig_until(self, text, frames)
        if not self.patched and 'kernel ok' in self.screen():
            self.patch()
        return r
    def patch(self):
        m = self.zx.mem
        for a, b in REG.values():
            for x in range(a, b): m[x] = PAT
        sp = self.zx.sim.registers[12]
        top = min(sp, 0x5F00) if KV2END <= sp <= 0x5F00 else 0x5F00
        for x in range(KV2END, top - 2): m[x] = PAT
        print("    SP at patch %04X" % sp)
        self.patched = True
fails = 0
for f in suite.TESTS:
    s = S(ROOT + '/build/test.z80')
    s.until('kernel ok', 2000)
    try:
        f(s); res = 'PASS'
    except suite.Fail as e:
        res = 'FAIL'; fails += 1
    m = s.zx.mem
    w = {k: [hex(x) for x in range(a, b) if m[x] != PAT] for k, (a, b) in REG.items()}
    low = next((x for x in range(KV2END, 0x5F00) if m[x] != PAT), None)
    print('%s %-18s stack low-water %s  writes: %s' % (res, f.__name__,
          hex(low) if low else '-', {k: len(v) for k, v in w.items()}))
    for k, v in w.items():
        if v: print('    ', k, v[:8])
print(fails, 'failed')
