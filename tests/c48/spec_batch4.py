"""Direct C48 Rev 0.11 assertions for types, conversions, and pointers.

Every case targets one stated semantic requirement; this is not a claim
that a whole specification paragraph has been exhaustively exercised.
"""


def populate(accepted, rejected, runprogram):
    valid = [
        (237, 'pointer_array_declarator', 'int a[2];int *p;int main(void){return 0;}'),
        (244, 'comma_declarators', 'int a,b;int main(void){return 0;}'),
        (410, 'pure_integer_bound', 'int a[(2*3)-4];int main(void){return 0;}'),
        (426, 'array_of_pointer_constants', 'char *p[2]={"hi","lo"};int main(void){return 0;}'),
        (427, 'array_of_float_constants', 'float f[2]={1.0,2.5};int main(void){return 0;}'),
    ]
    for paragraph, name, source in valid:
        accepted('spec4_accept_' + name, [paragraph], source)

    bad = [
        (504, 'bitwise_float', 'int main(void){float x;x=2.0;return x&1;}'),
        (582, 'oversized_array', 'unsigned char big[65536];int main(void){return 0;}'),
        (594, 'wrong_arity', 'int f(int a){return a;}int main(void){return f(1,2);}'),
        (597, 'variadic_decl', 'int f(int a,...);int main(void){return 0;}'),
        (631, 'unsupported_label', 'int main(void){here:return 0;}'),
    ]
    for paragraph, name, source in bad:
        rejected('spec4_reject_' + name, [paragraph], source)

    runtime = [
        (190, 'unary_float_sign', 'int main(void){float f;f=-1.5;return f!=-1.5;}'),
        (228, 'int_array_compact_size', 'int main(void){int a[3];return sizeof(a)!=6;}'),
        (231, 'array_element_stride', 'int main(void){int a[3];return (&a[2]-&a[1])!=1;}'),
        (232, 'implicit_bss_zero', 'int a;unsigned char b[3];int main(void){return a!=0||b[0]!=0||b[2]!=0;}'),
        (313, 'null_pointer_zero_bytes', '#include <c48.h>\nint main(void){int *p;unsigned char b[2];p=0;memcpy(b,&p,2);return b[0]!=0||b[1]!=0;}'),
        (316, 'null_pointer_assign_compare', 'int main(void){int *p;p=0;return p!=0;}'),
        (319, 'null_macro_in_header', '#include <c48.h>\nint main(void){int *p;p=NULL;return p!=0;}'),
        (382, 'global_and_automatic_initializers', 'int g=6;int f(void){int x=1;x=x+1;return x;}int main(void){return g!=6||f()!=2||f()!=2;}'),
        (383, 'implicit_float_integer_conversion', 'int main(void){float f;int x;f=2.0;x=f;return x!=2;}'),
        (400, 'file_scope_null_pointer_initialization', 'int *p=0;int main(void){return p!=0;}'),
        (401, 'integer_constant_null_pointer', 'int *p=3-3;int main(void){return p!=0;}'),
        (402, 'global_pointer_to_string', 'char *p="hi";int main(void){return p[0]!=104||p[1]!=105;}'),
        (403, 'global_pointer_to_object', 'int g;int *p=&g;int main(void){return p!=&g;}'),
        (404, 'global_pointer_with_offset', 'int a[3];int *p=a+1;int main(void){return p!=&a[1];}'),
        (417, 'float_constant_expression', 'float f=1.5+2.25;int main(void){return f!=3.75;}'),
        (460, 'promoted_unsigned_byte', 'int main(void){unsigned char c;c=255;return sizeof(c+1)!=2;}'),
        (463, 'unpromoted_shift_byte', 'int main(void){unsigned char c;c=1;return (c<<8)!=1;}'),
        (468, 'float_mixed_arithmetic', 'int main(void){float f;f=2+0.5;return f!=2.5;}'),
        (471, 'int_and_short_type', 'int main(void){int a;short b;a=3;b=5;return a+b!=8;}'),
        (473, 'unsigned_int_comparison', 'int main(void){unsigned int u;u=65535u;return (u==-1)!=1;}'),
        (479, 'float_to_integer_truncate', 'int main(void){float f;int i;f=2.9;i=f;return i!=2;}'),
        (480, 'signed_int_to_float', 'int main(void){short a;float b;a=-2;b=a;return b!=-2.0;}'),
        (485, 'integer_binary_width', 'int main(void){int a;a=-1;return a+2!=1;}'),
        (486, 'narrow_unsigned_assignment', 'int main(void){unsigned char c;c=258;return c!=2;}'),
        (490, 'min_int_signed_division', 'int main(void){int x,y;x=(int)0x8000u;y=x/-1;return y!=(int)0x8000u;}'),
        (493, 'unsigned_division_remainder', 'int main(void){unsigned int a;a=65535u;return a/2!=32767u||a%2!=1u;}'),
        (505, 'bitwise_integer_promotions', 'int main(void){unsigned char c;c=1;return sizeof(~c)!=2;}'),
        (513, 'zero_is_false', 'int main(void){return !!0;}'),
        (519, 'logical_int_result', 'int main(void){return (2&&3)!=1||sizeof(2&&3)!=2;}'),
        (521, 'logical_short_circuit', 'int main(void){int x;x=0;0&&++x;return x!=0;}'),
        (527, 'float_relational_comparison', 'int main(void){float a,b;a=1.5;b=2.5;return !(a<b);}'),
        (529, 'same_object_pointer_equality', 'int main(void){int a;int *p,*q;p=&a;q=&a;return p!=q;}'),
        (531, 'void_pointer_equality', 'int main(void){int x;int *p;void *v;p=&x;v=p;return v!=p;}'),
        (533, 'same_array_pointer_order', 'int main(void){int a[2];return !(&a[0]<&a[1]);}'),
        (535, 'pointer_bits_equal', 'int main(void){int a;int *p;void *q;p=&a;q=p;return p!=q;}'),
        (540, 'pointer_subtraction_elements', 'int main(void){int a[4];return (&a[3]-&a[1])!=2;}'),
        (563, 'pointer_postincrement', 'int main(void){int a[3];int *p;p=a;p++;return p!=&a[1];}'),
        (579, 'sizeof_parenthesized_array', 'int main(void){int a[3];return sizeof((a))!=6;}'),
        (586, 'left_to_right_argument_evaluation', 'int f(int a,int b){return a*10+b;}int main(void){int x;x=0;return f(++x,++x)!=12;}'),
    ]
    for paragraph, name, source in runtime:
        runprogram('spec4_runtime_' + name, [paragraph], source)
