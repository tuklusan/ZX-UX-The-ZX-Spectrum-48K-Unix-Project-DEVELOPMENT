"""Rev 0.11 clause-specific cross-backend assertions.

Each mapping is to the tested behavior, not to a whole section's duties.
Undefined operations and resource limits are not treated as passes.
"""


def populate(add, accepted, rejected, runprogram):
    # Accepted and rejected source syntax are separate assertions.
    accepted('spec11_argv_first_char', [1051],
             'int main(int argc,char **argv){ if(argc>1) return argv[1][0]==0; return 0;}')
    rejected('spec11_reversed_index', [1051],
             'int main(int argc,char **argv){return 1[argv][0];}')
    accepted('spec11_supported_array_initializer', [425],
             'int x[3]={1,2,3};int main(void){return 0;}')
    rejected('spec11_unsupported_array_initializer', [431],
             'int x[3]={[1]=5};int main(void){return 0;}')
    rejected('spec11_no_integer_longer_than_16', [149],
             'long x;int main(void){return 0;}')
    accepted('spec11_void_pointer_header', [735],
             '#include <c48.h>\nint main(void){return 0;}')
    accepted('spec11_main_prototype', [1067],
             'int main(void);int main(void){return 0;}')
    rejected('spec11_main_object', [1067],
             'int main;')
    rejected('spec11_no_vendor_keyword', [789],
             'int main(void){__asm("nop");return 0;}')
    rejected('spec11_no_host_escape', [790],
             'int main(void){return __builtin_clz(1);}')
    rejected('spec11_no_compiler_extension', [788],
             'int main(void){int x=0;return x?:1;}')
    rejected('spec11_void_ordering', [1058],
             'int main(void){void *a;void *b;return a<b;}')
    # Observable source-level values, checked independently in both backends.
    cases = [
        (1050, 'sizeof_array_is_whole_object',
         'int main(void){int a[3];return sizeof(a)!=6||sizeof(a[0])!=2;}'),
        (1052, 'postincrement_assignment_order',
         'int main(void){int i;i=7;i=i++;return i!=7;}'),
        (1057, 'zero_initialized_globals',
         'int x;int *p;float f;int main(void){return x!=0||p!=0||f!=0.0;}'),
        (1058, 'pointer_equality_exact',
         'int main(void){int a[2];int *x;int *y;x=&a[0];y=&a[1];'
         'return (x==y)||(x!=&a[0]);}'),
        (1059, 'unsigned_division_and_remainder',
         'int main(void){unsigned int n;n=65535u;'
         'return n/10u!=6553u||n%10u!=5u;}'),
        (1060, 'float_to_unsigned_char_narrows',
         'int main(void){float f;char x;f=258.0;x=f;return x!=2;}'),
        (1061, 'float_value_parameter_is_copy',
         'float alter(float x){x=5.0;return x;}int main(void){float f;'
         'f=1.0;return alter(f)!=5.0||f!=1.0;}'),
        (1062, 'unsigned_char_return_promotes',
         'char choose(void){return 255;}int main(void){int x;x=choose();'
         'return x!=255;}'),
        (1077, 'block_automatic_initializer_repeats',
         'int check(void){int x=4;x=x+1;return x;}'
         'int main(void){return check()+check()!=10;}'),
        (541, 'same_array_element_pointer_subtraction',
         'int main(void){int a[5];return (&a[4]-&a[1])!=3;}'),
        (544, 'backward_same_array_pointer_subtraction',
         'int main(void){int a[5];return (&a[1]-&a[4])!=-3;}'),
        (393, 'explicit_char_array_terminator',
         'int main(void){char x[4]="abc";return sizeof(x)!=4||x[3]!=0;}'),
        (396, 'char_pointer_literal_access',
         'int main(void){char *x;x="abc";return x[2]!=99||x[3]!=0;}'),
    ]
    for index, label, source in cases:
        runprogram('spec11_' + label, [index], source)
    add('spec11_repeatable_executable', [1065], 'repeat',
        'int main(void){int x;x=20;return x-20;}')
    add('spec11_empty_translation_object', [1066], 'object',
        '/* intentionally empty */\n')
