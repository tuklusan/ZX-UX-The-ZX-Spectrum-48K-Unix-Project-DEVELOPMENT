"""Direct, individually mapped C48 Rev 0.11 clause assertions.

A passing case establishes the named behavior, not every obligation in a
paragraph. The separate release coverage gate remains authoritative.
"""


def populate(accepted, rejected, runexpr, runprogram):
    """Register new assertions against their actual paragraph identifiers."""
    compile_reject = [
        (300, 'array_zero_bound', 'int a[0]; int main(void){return 0;}'),
        (303, 'array_size_overflow', 'unsigned short a[32768]; int main(void){return 0;}'),
        (302, 'address_of_array', 'int a[2]; int main(void){int **p;p=&a;return 0;}'),
        (309, 'pointer_plus_pointer', 'int main(void){int a[2];int *p;p=a;p=p+p;return 0;}'),
        (310, 'commuted_index', 'int main(void){int a[2];a[0]=1;return 0[a];}'),
        (320, 'nonzero_implicit_pointer', 'int main(void){int *p;p=1;return 0;}'),
        (321, 'pointer_from_integer_cast', 'int main(void){int *p;p=(int*)123;return 0;}'),
        (341, 'empty_function_parameters', 'int f(); int main(void){return 0;}'),
        (344, 'ellipsis_parameter', 'int f(int a,...); int main(void){return 0;}'),
        (366, 'object_main', 'int main;'),
        (376, 'runtime_scalar_initializer', 'int f(void){return 1;} int main(void){int n=f();return n;}'),
        (380, 'nested_initializer', 'int a[2]={{1},{2}};int main(void){return 0;}'),
        (381, 'function_initializer', 'int f(void)=4; int main(void){return 0;}'),
        (392, 'array_string_missing_nul', 'char a[3]="abc";int main(void){return 0;}'),
        (405, 'global_pointer_nonzero_initializer', 'int *p=1;int main(void){return 0;}'),
        (412, 'constant_expression_assignment', 'int a;int n=++a;int main(void){return 0;}'),
        (414, 'constant_division_zero', 'int n=2/0;int main(void){return 0;}'),
        (557, 'pointer_assign_nonzero', 'int main(void){int *p;p=3;return 0;}'),
        (571, 'unsupported_pointer_cast', 'int main(void){int *p;p=(int*)1;return 0;}'),
        (224, 'sizeof_void', 'int main(void){return sizeof(void); }'),
        (145, 'out_of_range_integer', 'int main(void){return 65536u;}'),
        (144, 'unsupported_long_integer', 'int main(void){return 1L;}'),
        (168, 'short_hex_escape', r"int main(void){return '\x4';}"),
        (217, 'signed_char_type', 'signed char c;int main(void){return 0;}'),
        (258, 'block_static_storage', 'int main(void){static int x;return 0;}'),
        (261, 'extern_with_initializer', 'extern int x=2;int main(void){return 0;}'),
        (263, 'extern_function_definition', 'extern int f(void){return 0;} int main(void){return f();}'),
        (289, 'two_function_definitions', 'int f(void){return 1;}int f(void){return 2;}int main(void){return 0;}'),
        (293, 'late_block_declaration', 'int main(void){int a;a=1;int b;return a;}'),
        (294, 'for_decl_initializer', 'int main(void){for(int i=0;i<3;i++){}return 0;}'),
        (303, 'oversized_short_array', 'int a[32768];int main(void){return 0;}'),
    ]
    for paragraph, name, source in compile_reject:
        rejected('spec_batch_reject_' + name, [paragraph], source)

    compile_accept = [
        (307, 'triple_pointer', 'int ***p;int main(void){return 0;}'),
        (368, 'extern_main_prototype', 'extern int main(void);int main(void){return 0;}'),
        (371, 'module_without_main', 'int utility(void){return 2;}'),
        (407, 'string_pointer_initializer', 'char *a="abc";int main(void){return 0;}'),
        (262, 'static_function', 'static int f(void){return 1;}int main(void){return f()-1;}'),
        (271, 'nested_scope_shadowing', 'int n;int main(void){int n;n=1;{int n;n=2;}return n-1;}'),
        (273, 'repeated_prototype', 'int f(int a);int f(int a);int f(int a){return a;}int main(void){return 0;}'),
        (240, 'object_pointer_typing', 'int *a; char **b; int main(void){return 0;}'),
        (298, 'one_dimensional_array', 'int a[3];int main(void){return 0;}'),
    ]
    for paragraph, name, source in compile_accept:
        accepted('spec_batch_accept_' + name, [paragraph], source)

    runtime = [
        (140, 'unary_sign', 'int main(void){int x;x=-1;return (+x)!=(-1); }'),
        (151, 'int_literal_signed', 'int main(void){return (32767 < -1) != 0;}'),
        (152, 'implicit_unsigned_literal', 'int main(void){if(65535 > 1)return 0;return 1;}'),
        (154, 'explicit_unsigned_literal', 'int main(void){return (1u < -1) != 1;}'),
        (155, 'unsigned_literal_upper_bound', 'int main(void){return 65535u != (unsigned int)-1;}'),
        (156, 'hex_octal_literal_values', 'int main(void){return 0xAB != 171 || 077 != 63;}'),
        (164, 'character_escapes', "int main(void){return '\\n'!=10 || '\\t'!=9 || '\\0'!=0;}"),
        (166, 'hex_two_digit_escape', r"int main(void){return '\x41'!=65;}"),
        (175, 'string_bytes', 'int main(void){char *s;s="a\\nb";return s[0]!=97||s[1]!=10||s[2]!=98||s[3]!=0;}'),
        (218, 'signed_short_int', 'int main(void){short x;int y;x=-2;y=-3;return x>=0 || y>=0;}'),
        (315, 'zero_null_pointer_constant', 'int main(void){int *p;p=(1-1);return p!=0;}'),
        (476, 'unsigned_narrowing', 'int main(void){unsigned char x;x=257;return x!=1;}'),
        (477, 'signed_narrowing', 'int main(void){int x;char y;x=(int)65535u;y=257;return x!=-1||y!=1;}'),
        (497, 'char_shift_count_mod8', 'int main(void){unsigned char x;x=1;return (x<<8)!=1;}'),
        (498, 'signed_arithmetic_shift', 'int main(void){int x;x=-1;return (x>>1)!=-1;}'),
        (500, 'negative_shift_count', 'int main(void){unsigned char x;x=1;return (x<<-1)!=128;}'),
        (522, 'logical_and_short_circuit', 'int main(void){int a;a=0;if(0&&++a)return 1;return a!=0;}'),
        (523, 'logical_or_short_circuit', 'int main(void){int a;a=0;if(1||++a){}return a!=0;}'),
        (565, 'pre_post_increment', 'int main(void){int x;x=1;if(x++!=1)return 1;if(++x!=3)return 2;return 0;}'),
        (577, 'sizeof_no_eval', 'int main(void){int n;n=5; if(sizeof(n++)!=2)return 1;return n!=5;}'),
        (572, 'float_to_int_truncation', 'int main(void){float x;x=1.9;return (int)x!=1;}'),
        (587, 'argument_order', 'int n;int next(void){n=n+1;return n;}int f(int a,int b){return 10*a+b;}int main(void){n=0;return f(next(),next())!=12;}'),
        (306, 'two_byte_pointer', 'int main(void){return sizeof(void *)!=2;}'),
        (619, 'return_unsigned_byte', 'unsigned char f(void){return 255;}int main(void){return f()!=255;}'),
    ]
    for paragraph, name, source in runtime:
        runprogram('spec_batch_runtime_' + name, [paragraph], source)
