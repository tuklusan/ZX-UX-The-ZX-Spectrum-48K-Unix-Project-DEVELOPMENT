"""Five-byte ZX Spectrum ROM floating-value regression corpus for C48.

Reference bytes were read by the checked Spectrum 48K ROM number parser
and calculator running under the checked SkoolKit Z80 simulator.
ROM SHA-256: d55daa439b673b0e3f5897f99ac37ecb45f974d1862b4dadb85dec34af99cb42.
These fixed golden results are compared with each new-SDK runtime backend.
"""

ROM_BYTES = (
    ('zero', '0.0', '0000000000'),
    ('one', '1.0', '0000010000'),
    ('negative_one', '-1.0', '00ffffff00'),
    ('half', '.5', '7f7fffffff'),
    ('quarter', '0.25', '7e7fffffff'),
    ('one_point_two_five', '1.25', '8120000000'),
    ('two', '2.0', '0000020000'),
    ('ten', '10.0', '00000a0000'),
    ('negative_twelve', '-12.0', '00fff4ff00'),
    ('one_tenth', '0.1', '7d4ccccccc'),
    ('fraction', '123.456', '8776e978d6'),
    ('negative_exponent', '1e-3', '7703126e97'),
    ('positive_exponent', '3e2', '00002c0100'),
    ('unsigned_boundary', '65535.0', '0000ffff00'),
    ('signed_boundary', '32767.0', '0000ff7f00'),
    ('small_fraction', '0.00001', '7027c5ac46'),
    ('large_exponent', '1e15', 'b2635fa932'),
)


def _byte_assertion(expression, hexbytes):
    vals = bytes.fromhex(hexbytes)
    check = '||'.join('seen[%s]!=%s' % (i, v) for i, v in enumerate(vals))
    return ('#include <c48.h>\nfloat sample=%s;\n'
            'int main(void){unsigned char seen[5];'
            'memcpy(seen,&sample,5);return %s;}\n') % (expression, check)


def _verify_reference_rom():
    import hashlib
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'sdk'))
    from skoolkit import ROM48
    from rcc.romfp import rom, NEG, ADD, DIV, SQR, FPError
    expected_rom = 'd55daa439b673b0e3f5897f99ac37ecb45f974d1862b4dadb85dec34af99cb42'
    if hashlib.sha256(Path(ROM48).read_bytes()).hexdigest() != expected_rom:
        raise RuntimeError('C48 float reference ROM checksum differs')
    r = rom()
    for name, expr, golden in ROM_BYTES:
        data = (r.op(NEG, r.from_text(expr[1:]))
                if expr.startswith('-') else r.from_text(expr))
        if data != bytes.fromhex(golden):
            raise RuntimeError('C48 ROM golden byte mismatch: ' + name)
    a, b, c = (r.from_text(s) for s in ('0.1', '0.2', '0.3'))
    if r.op(ADD, r.op(ADD, a, b), c).hex() != '8019999999':
        raise RuntimeError('C48 ROM chained arithmetic bytes differ')
    for op, left, right in ((DIV, r.from_text('1.0'), r.from_text('0.0')),
                            (SQR, r.op(NEG, r.from_text('1.0')), None)):
        try:
            r.op(op, left, right)
        except FPError:
            continue
        raise RuntimeError('C48 ROM numeric error was not raised')


def populate(runprogram):
    _verify_reference_rom()
    for name, expr, golden in ROM_BYTES:
        runprogram('spec7_rom_float_' + name, [204],
                   _byte_assertion(expr, golden))

    runprogram('spec7_rom_float_object_model', [193],
               _byte_assertion('1.25', '8120000000'))
    # This fixture spans integer, fractional, negative and exponent forms.
    checks = []
    for i, (name, expr, golden) in enumerate(ROM_BYTES):
        checks.append('float f%d=%s;\n' % (i, expr))
    comparisons = []
    for i, (name, expr, golden) in enumerate(ROM_BYTES):
        comparisons.append('memcpy(seen,&f%d,5);' % i)
        comparisons.extend('if(seen[%d]!=%d)return %d;' % (j, n, i+1)
                           for j,n in enumerate(bytes.fromhex(golden)))
    source = ('#include <c48.h>\n'+''.join(checks)+
              'int main(void){unsigned char seen[5];'+
              ''.join(comparisons)+'return 0;}')
    runprogram('spec7_rom_float_diverse_golden_inventory', [906, 907], source)
    # Verify runtime intermediate materialization, not just constants.
    runprogram('spec7_rom_float_chained_runtime_rounded', [807],
               '#include <c48.h>\n'
               'int main(void){float a,b,c,x;unsigned char seen[5];'
               'a=0.1;b=0.2;c=0.3;x=(a+b)+c;memcpy(seen,&x,5);'
               'return seen[0]!=128||seen[1]!=25||seen[2]!=153||'
               'seen[3]!=153||seen[4]!=153;}')
    # The ROM's arithmetic and domain/range traps must be observable.
    runprogram('spec7_rom_float_divide_by_zero_status', [208, 907],
               'int main(void){float a,b;a=1.0;b=0.0;a=a/b;return 0;}', 1)
    runprogram('spec7_rom_float_invalid_sqrt_status', [573, 907],
               '#include <c48.h>\nint main(void){float x;x=-1.0;'
               'x=sqrt(x);return 0;}', 1)
