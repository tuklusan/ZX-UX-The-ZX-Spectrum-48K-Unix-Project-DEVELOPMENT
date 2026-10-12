"""C48 multi-function translation unit verification."""


def populate(runprogram, accepted):
    funcs = ''.join('int f%d(void){return %d;}\n' % (i, i) for i in range(24))
    expr = '+'.join('f%d()' % i for i in range(24))
    code = funcs + 'int main(void){return (' + expr + ')!=276;}\n'
    runprogram('spec15_many_function_translation_unit', [918, 920], code)
    accepted('spec15_many_function_source_accept', [918], code)
