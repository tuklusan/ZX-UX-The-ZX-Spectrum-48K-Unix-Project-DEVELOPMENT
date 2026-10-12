"""Individually linked C48 Rev 0.11 syntax, scope, and runtime assertions.

Each case establishes its stated assertion, not exhaustive paragraph coverage.
The historical SDK and obsolete object formats are not used.
"""


def populate(accepted, rejected, runprogram, add):
    bad = [
        (60, 'physical_line_splice', 'int main(void){return 1\\\n+2;}'),
        (117, 'internal_double_underscore', 'int __brandnew; int main(void){return 0;}'),
        (207, 'overflow_float_literal', 'float f=1e999;int main(void){return 0;}'),
        (278, 'parameter_redeclared_outer_block',
         'int f(int a){int a;return 0;}int main(void){return 0;}'),
        (281, 'prototype_plain_char_distinct_unsigned_char',
         'int f(char c);int f(unsigned char c){return c;}int main(void){return 0;}'),
        (282, 'prototype_void_pointer_not_exact_type',
         'int f(void *p);int f(int *p){return 0;}int main(void){return 0;}'),
        (454, 'assignment_requires_modifiable_lvalue',
         'int main(void){int a,b;a=1;b=2;(a+b)=3;return 0;}'),
        (547, 'assignment_result_not_an_lvalue',
         'int main(void){int a,b;(a=b)=2;return 0;}'),
        (701, 'directive_block_comment_crosses_newline',
         '#define A 1 /* comment\n end */\nint main(void){return 0;}'),
        (708, 'function_like_macro_disallowed',
         '#define F(x) 1\nint main(void){return 0;}'),
        (736, 'const_modifier_not_supported',
         '#include <c48.h>\nconst int value=2;int main(void){return value;}'),
    ]
    for paragraph, name, source in bad:
        rejected('spec5_reject_' + name, [paragraph], source)

    good = [
        (115, 'ordinary_alternate_identifier',
         'int alignof;int _Boolx;int main(void){return 0;}'),
        (252, 'file_scope_storage_forms',
         'static int local;extern int external;int external;int main(void){return 0;}'),
        (259, 'implicit_local_automatic',
         'int f(void){int a;a=1;return a;}int main(void){return f()!=1;}'),
        (283, 'prototype_renamed_parameters',
         'int f(int first,char second);int f(int a,char b){return a+b;}int main(void){return 0;}'),
    ]
    for paragraph, name, source in good:
        accepted('spec5_accept_' + name, [paragraph], source)

    run = [
        (96, 'case_sensitive_independent_objects',
         'int Alpha,alpha;int main(void){Alpha=3;alpha=4;return Alpha+alpha!=7;}'),
        (150, 'plain_decimal_32768_unsigned',
         'int main(void){return !(32768>32767);}'),
        (153, 'unsigned_literal_65535_value',
         'int main(void){return 65535U!=0xffffu;}'),
        (185, 'scientific_decimal_float',
         'int main(void){float a;a=1.25e2;return a!=125.0;}'),
        (188, 'upper_float_suffix',
         'int main(void){float a;a=0.5F;return a!=.5f;}'),
        (326, 'heap_void_pointer_implicit_conversion',
         '#include <c48.h>\nint main(void){void *p;int *q;p=malloc(4);if(p==0)return 1;q=p;q[0]=11;q[1]=12;free(p);return 0;}'),
        (389, 'string_array_four_elements',
         'char s[]="abc";int main(void){return sizeof(s)!=4||s[3]!=0;}'),
        (418, 'pure_float_init_runtime_agrees',
         'float g=(1.25+0.75)*2.0;int main(void){float x;x=(1.25+0.75)*2.0;return x!=g;}'),
        (462, 'byte_integer_promotes_signed',
         'int main(void){unsigned char c;c=0;return c-1!=-1;}'),
        (469, 'usual_conversion_integer_operands',
         'int main(void){unsigned short a;short b;a=65535u;b=-1;return a+b!=65534u;}'),
        (481, 'float_to_char_unsigned_narrow',
         'int main(void){char a;a=(char)300.0;return a!=44;}'),
        (492, 'min_int_division_wrap',
         'int main(void){int a;a=(int)0x8000u;return a/-1!=(int)0x8000u;}'),
        (499, 'negative_shift_count_mask',
         'int main(void){unsigned char a;a=3;return (a<<-1)!=128;}'),
        (506, 'bitwise_promoted_byte',
         'int main(void){unsigned char a;a=0;return sizeof(~a)!=2;}'),
        (511, 'float_scalar_truth',
         'int main(void){float f;f=0.5;return !(f&&2)||(!f)!=0;}'),
        (530, 'pointer_equality_compatible_types',
         'int main(void){int a;int *p,*q;p=&a;q=p;return !(p==q);}'),
        (542, 'one_past_pointer_equals_array_plus_size',
         'int main(void){int a[2];int *p;p=a+2;return p!=&a[1]+1;}'),
        (551, 'float_to_integer_truncation',
         'int main(void){float f;int i;f=7.99;i=f;return i!=7;}'),
        (560, 'postincrement_assignment_restores_old_value',
         'int main(void){int i;i=7;i=i++;return i!=7;}'),
        (588, 'binary_left_to_right',
         'int main(void){int i;i=0;return (++i)*10+(++i)!=12;}'),
        (589, 'postincrement_side_effect_in_expression',
         'int main(void){int i,j;i=3;j=i++;return i!=4||j!=3;}'),
        (637, 'nested_compound_scope_shadow',
         'int main(void){int i;i=2;{int i;i=3;}return i!=2;}'),
        (660, 'while_scalar_float_condition',
         'int main(void){float f;int i;f=2.5;i=0;while(f){i++;f=0.0;}return i!=1;}'),
        (666, 'do_while_scalar_float_condition',
         'int main(void){float f;int i;f=0.0;i=0;do{i++;}while(f);return i!=1;}'),
        (674, 'for_scalar_float_condition',
         'int main(void){float f;int i;f=1.0;i=0;for(;f;){i++;f=0.0;}return i!=1;}'),
        (679, 'break_nearest_enclosing_loop',
         'int main(void){int i,j;i=0;j=0;while(i<2){i++;while(1){j++;break;}}return i!=2||j!=2;}'),
        (688, 'continue_do_while_checks_trailer',
         'int main(void){int i;i=0;do{i++;continue;}while(i<3);return i!=3;}'),
        (695, 'nonvoid_fallthrough_status_one',
         'int main(void){int a;a=1;}'),
        (702, 'function_define_visible_later',
         'int f(void){\n#define NEWVALUE 7\nreturn NEWVALUE;}\nint main(void){return NEWVALUE!=7;}'),
        (715, 'macro_does_not_replace_subidentifier',
         '#define TOKEN 3\nint main(void){int TOKENx;TOKENx=5;return TOKENx!=5;}'),
        (721, 'macro_use_site_constant_expansion',
         '#define TEN (5+5)\nint main(void){return TEN!=10;}'),
    ]
    for paragraph, name, source in run:
        expected = 1 if paragraph == 695 else 0
        runprogram('spec5_runtime_' + name, [paragraph], source, expected)

    add('spec5_accept_include_macro_in_scope', [728], 'accept',
        '#include "defs.h"\nint main(void){return MORE!=9;}\n',
        extra={'defs.h':'#define MORE 9\n'})
    add('spec5_reject_repeat_include_duplicate_definition', [729], 'reject',
        '#include "defs.h"\n#include "defs.h"\nint main(void){return 0;}\n',
        extra={'defs.h':'int count;\n'})
