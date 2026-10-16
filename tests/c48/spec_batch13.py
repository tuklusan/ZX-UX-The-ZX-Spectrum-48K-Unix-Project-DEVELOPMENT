"""C48 Rev 0.11 SDK compiler regression programs in both modes.

Test links describe checked behavior rather than complete coverage of a
umbrella paragraph. External compilers and real target calling rules remain separate.
"""


def populate(add, accepted, rejected, runprogram):
    source = 'int main(void){return 0;}\n'
    add('spec13_canonical_source_to_ssx', [16, 1056, 828], 'cli', source,
        note='default_ssx')
    add('spec13_canonical_source_to_sso', [287, 1056], 'cli', source,
        note='default_obj')
    for key, paragraph, code in (
        ('unsupported_type_keyword', 34, 'struct item {int x;}; int main(void){return 0;}'),
        ('no_source_extensions', 28, 'int main(void){int x;x=1;x+=2;return x;}'),
        ('reserved_iso_feature', 18, 'int main(void){int a[2];return sizeof(int[2]);}'),
        ('forbidden_structural_extension', 747, 'int main(void){int x;goto done;done:return 0;}'),
        ('canonical_type_only', 933, 'unsigned long x;int main(void){return 0;}'),
        ('no_backend_extensions', 919, 'int main(void){int x;x=2;return x?1:0;}'),
        ('no_host_extensions', 816, 'int main(void){long x;return 0;}'),
        ('unsupported_feature_guard', 825, 'int main(void){double x;return 0;}'),
        ('compiler_no_implicit_iso', 980, 'int main(void){char *p;p=(char *)1;return 0;}'),
        ('unrecognized_reserved_word', 113, 'int main(void){typedef int MYINT;return 0;}'),
        ('reserved_identifiers', 88, 'int __private;int main(void){return 0;}'),
        ('source_identifier_no_alias', 93, 'int abcdefghijklmno;int abcdefghijklmnop;int main(void){return 0;}'),
        ('canonical_declarators_only', 235, 'int (*handler)(void);int main(void){return 0;}'),
        ('function_parameter_declarator', 1025, 'int f(int a[2]){return a[0];}int main(void){return 0;}'),
        ('static_initializer_is_pure', 1036, 'int f(void){return 7;}int x=f();int main(void){return 0;}'),
        ('literal_must_have_suffix', 136, 'int main(void){return 12LL;}'),
        ('unsupported_compound_punctuation', 999, 'int main(void){int x;x=0;x<<=1;return 0;}'),
        ('forbidden_directive', 699, '#ifdef FLAG\nint x;\n#endif\nint main(void){return 0;}'),
        ('builtin_only', 727, '#include <stdio.h>\nint main(void){return 0;}'),
        ('reject_implicit_new_types', 926, 'int main(void){size_t n;return 0;}'),
        ('no_void_binary_relation', 1074, 'int main(void){void *a;void *b;return a<b;}'),
        ('reject_pointer_to_array', 1022, 'int main(void){int (*a)[3];return 0;}'),
    ):
        rejected('spec13_reject_' + key, [paragraph], code)
    for name, links, src in (
        ('source_byte_identifier_limit', [86, 967],
         'int abcdefghijklmno;int main(void){abcdefghijklmno=1;return abcdefghijklmno!=1;}'),
        ('scope_file_and_parameter', [266, 267, 268],
         'int v=7;int f(int v){return v+1;}int main(void){return f(3)!=4||v!=7;}'),
        ('namespaces_no_tag', [276],
         'int x;int f(int x){return x+1;}int main(void){return f(3)!=4;}'),
        ('function_definition_declarator', [351, 353, 354],
         'void noop(void){return;}int f(char x){return x+1;}int main(void){noop();return f(5)!=6;}'),
        ('literals_source_forms', [141, 162],
         'int main(void){return 077!=63||0Xffu!=255||\'\\n\'!=10||\'\\x41\'!=65;}'),
        ('unsigned_parse_and_value', [158],
         'int main(void){unsigned int v;v=65535u;return v+1u!=0u;}'),
        ('direct_array_brace_initializer', [423, 1028],
         'int a[3]={1,2,};int main(void){return a[0]!=1||a[1]!=2||a[2]!=0;}'),
        ('pointer_constant_initializer', [1036],
         'int n=7;int *p=&n;int main(void){return *p!=7;}'),
        ('external_and_static_resolution', [287, 288, 768],
         'static int local=4;extern int global;int global=7;'
         'int next(void){return local+global;}int main(void){return next()!=11;}'),
        ('no_implicit_alias_optimizing', [332],
         '#include <c48.h>\nint main(void){unsigned char *p;int *q;'
         'void *v;v=malloc(4);p=v;q=v;*q=0x1234;return p[0]!=52||p[1]!=18;}'),
        ('heap_valid_aligned_pointer', [330],
         '#include <c48.h>\nint main(void){int *p;p=malloc(4);'
         '*p=123;return *p!=123;}'),
        ('same_array_relational_pointer', [534],
         'int main(void){int a[3];int *p;int *q;p=&a[0];q=&a[2];return !(p<q); }'),
        ('operator_arithmetic_set', [121, 997],
         'int main(void){int a,b;a=7;b=3;'
         'return a+b!=10||a - b !=4||a * b !=21||a / b !=2||a % b !=1||'
         '(a<<1)!=14||(a>>1)!=3||(a&b)!=3||(a|b)!=7||'
         '(a ^ b) !=4||(!0)!=1||(~0)!=-1;}'),
        ('evaluation_precedence', [434, 1072],
         'int main(void){return 2+3*4!=14||(2+3)*4!=20||'
         '1+2<<3!=24||3<4&&5>4!=1;}'),
        ('canonical_char_and_int_storage', [1005, 970],
         'int main(void){char a;short b;int c;unsigned int d;float f;'
         'a=255;b=-1;c=300;d=65535u;f=1.0;return sizeof(a)!=1||'
         'sizeof(b)!=2||sizeof(c)!=2||sizeof(d)!=2||sizeof(f)!=5||a!=255;}'),
        ('no_host_promotion_shift', [1008],
         'int main(void){char a;int b;a=1;b=1;return (a<<8)!=1||(b<<16)!=1;}'),
        ('numeric_float_storage', [196, 198, 199, 200, 201, 202, 203],
         '#include <c48.h>\nfloat f=1.25;int main(void){unsigned char b[5];'
         'memcpy(b,&f,5);return sizeof(f)!=5||b[0]!=129||b[1]!=32||'
         'b[2]!=0||b[3]!=0||b[4]!=0;}'),
        ('pointer_array_offset_order', [952],
         'int main(void){int a[3];int *p;int *q;p=&a[0];q=p+2;'
         'return q-p!=2;}'),
        ('observable_initialization', [955],
         'int a=7;int b[2]={5};int main(void){return a!=7||b[0]!=5||b[1]!=0;}'),
        ('scalar_return_parameters', [957],
         'int f(int a,int b){return a*10+b;}int main(void){return f(2,3)!=23;}'),
        ('scalar_integer_equivalence', [949, 950, 953],
         'int main(void){int x;x=300;return x!=300||sizeof(x)!=2;}'),
        ('argument_side_effect_order', [954, 977],
         'int i;int next(void){i=i+1;return i;}'
         'int f(int a,int b){return a*10+b;}'
         'int main(void){return f(next(),next())!=12||i!=2;}'),
        ('supported_flow_and_statements', [978, 1001],
         'int main(void){int i,n;i=0;n=0;while(i<5){'
         'if(i==3){i=i+1;continue;}n=n+i;i=i+1;}'
         'return n!=7;}'),
        ('literal_negative_boundary_distinguished', [1049],
         'int main(void){int n;unsigned int x;n=-32768;x=(int)0x8000u;'
         'return n!=-32768||x!=32768u;}'),
    ):
        runprogram('spec13_' + name, links, src)
    accepted('spec13_operator_and_keywords_present', [993, 995],
             'int main(void){unsigned int x;char y;float z;'
             'x=1u;y=2;z=1.0;return x+y-3;}')
    accepted('spec13_preprocessor_builtin_header', [1003, 979],
             '#define X 3\n#include <c48.h>\nint main(void){return X-3;}')
    rejected('spec13_preprocessor_not_translated', [956],
             '#define A B\n#define B 1\nint main(void){return A;}')

    add('spec13_object_symbol_identity', [277, 287, 288, 768], 'format',
        'extern int External;static int hidden;int PublicVar;int publicvar;'
        'int main(void){return External+PublicVar+publicvar+hidden;}',note='symbols')
    add('spec13_native_register_iy_guard', [624], 'format',
        'float f(float x){return x+1.0;}int main(void){return f(1.0)!=2.0;}', note='iy')
    add('spec13_ssx_header_and_checksum', [767, 1089], 'format',
        'int main(void){return 0;}',note='ssx')
    add('spec13_current_tape_payload', [765, 1084], 'format',
        'int main(void){return 0;}',note='tape')
    rejected('spec13_unbroken_lines_not_a_token', [59],
             'int ma\n in(void){return 0;}')

    runprogram('spec13_complete_comparison_and_update_tokens', [833, 968],
        'int main(void){int a,b;a=3;b=4;'
        'if(!(a<b&&a<=b&&b>a&&b>=a&&a!=b&&a==3))return 1;'
        'a++;b--;if(a!=4||b!=3)return 2;'
        '++a;--b;return a!=5||b!=2;}')
