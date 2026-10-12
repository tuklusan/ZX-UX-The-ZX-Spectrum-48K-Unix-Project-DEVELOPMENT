"""Additional Rev 0.11 source-level conformance assertions.

Each paragraph is linked only to the particular observable condition that
its fixture checks. Target-internal ABI and historical-frame requirements
are deliberately excluded.
"""


def populate(add, accepted, rejected, runprogram):
    cases = [
        (157, 'unsigned_arithmetic_is_sixteen_bit',
         'int main(void){unsigned int x;x=65535u;x=x+2u;return x!=1u;}'),
        (229, 'integer_object_bytes_are_little_endian',
         '#include <c48.h>\nint main(void){unsigned int n;unsigned char bytes[2];'
         'n=0x1234u;memcpy(bytes,&n,2);return bytes[0]!=52||bytes[1]!=18;}'),
        (254, 'file_static_object_retains_value',
         'static int n=3;int next(void){n=n+2;return n;}'
         'int main(void){return next()!=5||next()!=7;}'),
        (369, 'bootstrap_arg_vector_has_null_sentinel',
         'int main(int argc,char **argv){return argc!=1||argv[0][0]!=112||argv[argc]!=0;}'),
        (370, 'bootstrap_arg_string_has_null_terminator',
         '#include <c48.h>\nint main(int argc,char **argv){'
         'return argc<1||argv[0][strlen(argv[0])]!=0;}'),
        (372, 'process_exit_low_byte_one',
         'int main(void){return 257;}', 1),
        (372, 'process_exit_low_byte_all_ones',
         'int main(void){return -1;}', 255),
        (801, 'logical_pointer_object_is_sixteen_bits',
         'int main(void){void *v;int *p;char **q;'
         'return sizeof(v)!=2||sizeof(p)!=2||sizeof(q)!=2;}'),
        (795, 'host_independent_sizeof_and_alignment',
         'int main(void){float f;char c;int n;int *p;'
         'return sizeof(f)!=5||sizeof(c)!=1||sizeof(n)!=2||sizeof(p)!=2;}'),
        (1069, 'constant_expression_float_result',
         'float a=(3+1)/8.0;int main(void){int q;float x;q=3;'
         'x=(q+1)/8.0;return x!=a;}'),
        (1076, 'initialized_globals_ready_before_main',
         'int x=12;float y=1.5;int z[3]={5};'
         'int main(void){return x!=12||y!=1.5||z[0]!=5||z[2]!=0;}'),
        (1078, 'pointer_parameter_is_independent_value',
         'int move(int *p){int a[2];p=a;return p[0]=7;}'
         'int main(void){int x;int *p;x=1;p=&x;'
         'return move(p)!=7||p!=&x||x!=1;}'),
        (1079, 'simultaneous_globals_have_distinct_addresses',
         'int a;int b;int main(void){return &a==&b;}'),
        (1079, 'simultaneous_locals_have_distinct_addresses',
         'int main(void){int a,b;return &a==&b;}'),
        (1092, 'canonical_unsigned_char_and_integer_values',
         'int main(void){char c;unsigned char d;short s;unsigned int u;'
         'c=255;d=255;s=-1;u=65535u;'
         'return c!=255||d!=255||s!=-1||u!=65535u;}'),
        (1093, 'void_pointer_round_trip_special_conversion',
         'int main(void){short n;short *p;void *v;short *q;'
         'p=&n;v=p;q=v;return q!=p;}'),
        (1053, 'nonvoid_callee_falls_through',
         'int f(void){int a;a=3;}'
         'int main(void){return f();}', 1),
        (1054, 'float_failure_reports_process_error',
         'int main(void){float a,b;a=2.0;b=0.0;a=a/b;return 0;}', 1),
        (793, 'host_compiler_does_not_adopt_struct',
         'struct Pair {int x;};int main(void){return 0;}'),
    ]
    for item in cases:
        if len(item) == 4:
            paragraph, label, source, status = item
        else:
            paragraph, label, source = item
            status = 0
        if label == 'host_compiler_does_not_adopt_struct':
            rejected('spec12_' + label, [paragraph], source)
        else:
            runprogram('spec12_' + label, [paragraph], source, status)

    rejected('spec12_reject_char_unsigned_char_pointer_implicit', [1092],
             'int main(void){char *a;unsigned char *b;a=b;return 0;}')
    rejected('spec12_reject_incompatible_integer_pointer', [1093],
             'int main(void){int *p;unsigned int *q;p=q;return 0;}')
    rejected('spec12_reject_native_host_long', [796],
             'unsigned long n;int main(void){return 0;}')
    rejected('spec12_public_header_has_no_printf', [1043],
             '#include <c48.h>\nint main(void){printf("hi");return 0;}')
    accepted('spec12_public_header_has_beep_prototype', [925],
             '#include <c48.h>\nint main(void){return beep(0.5,440.0);}')
    rejected('spec12_public_header_checks_beep_arity', [925],
             '#include <c48.h>\nint main(void){return beep(0.5);}')
    add('spec12_host_quoted_include_with_builtin_header', [1055], 'accept',
        '#include "local.h"\nint main(void){return LOCAL_VALUE;}\n',
        extra={'local.h':'#include <c48.h>\n#define LOCAL_VALUE 0\n'})
