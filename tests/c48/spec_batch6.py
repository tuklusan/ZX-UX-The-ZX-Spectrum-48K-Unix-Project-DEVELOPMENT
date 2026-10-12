"""Rev 0.11 pointer and initializer corpus: one requirement per assertion.

The source is compiled through the new SDK in both backend modes where it
executes. No old-kernel format or historical compiler is used.
"""


def populate(accepted, rejected, runprogram):
    bad = [
        (866, 'address_of_array_designator',
         'int main(void){int a[2];int *p;p=&a;return 0;}'),
        (867, 'index_pointer_commutation',
         'int main(void){int a[2];a[1]=3;return 1[a];}'),
        (869, 'void_pointer_dereference',
         'int main(void){void *p;return *p;}'),
        (869, 'void_pointer_arithmetic',
         'int main(void){void *p;p=p+1;return 0;}'),
        (870, 'integer_cast_to_pointer',
         'int main(void){int *p;p=(int *)1;return 0;}'),
        (871, 'function_pointer_type',
         'int (*f)(void);int main(void){return 0;}'),
        (872, 'two_dimensional_array',
         'int a[2][3];int main(void){return 0;}'),
        (896, 'explicit_string_bound_requires_terminator',
         'char a[2]="ab";int main(void){return 0;}'),
        (897, 'designated_array_initializer',
         'int a[2]={[1]=3};int main(void){return 0;}'),
        (898, 'nested_array_initializer',
         'int a[2]={{1},{2}};int main(void){return 0;}'),
        (928, 'const_keyword_not_promoted',
         'int main(void){const int a=1;return a;}'),
        (931, 'host_pseudocode_const_not_source',
         'const char *p="ab";int main(void){return 0;}'),
    ]
    for idx, name, source in bad:
        rejected('spec6_reject_' + name, [idx], source)

    run = [
        (845, 'signed_unsigned_literal_boundary',
         'int main(void){return ((-32768)<0)||!(((int)0x8000u)<0)||!(32768u>32767); }'),
        (802, 'pointer_size_independent_of_host',
         'int main(void){int *p;char **q;float *r;void *v;return sizeof(p)!=2||sizeof(q)!=2||sizeof(r)!=2||sizeof(v)!=2;}'),
        (859, 'integer_plus_pointer_and_pointer_minus_integer',
         'int main(void){int a[4];int *p,*q;p=1+a;q=(p+2)-2;return p!=&a[1]||q!=p;}'),
        (860, 'increment_and_decrement_pointer',
         'int main(void){int a[3];int *p;p=a;p++;p++;p--;return p!=&a[1];}'),
        (863, 'object_void_pointer_roundtrip',
         'int main(void){int a;int *p;void *v;int *q;p=&a;v=p;q=v;return q!=p;}'),
        (864, 'decay_array_function_argument',
         'int pick(int *p){return p[1];}int main(void){int a[2];a[1]=7;return pick(a)!=7;}'),
        (865, 'sizeof_suppresses_array_decay',
         'int main(void){int a[4];int *p;p=a;return sizeof(a)!=8||sizeof(p)!=2;}'),
        (867, 'base_index_positive',
         'int main(void){int a[2];a[0]=8;a[1]=3;return a[1]!=3;}'),
        (868, 'repeated_pointer_indexing',
         'int main(void){char *s[2];char **p;s[0]="ab";s[1]="cd";p=s;return p[1][0]!=99||p[0][1]!=98;}'),
        (877, 'pointer_return_bindings',
         'char *arr[8];char **arr2[8];char *f(void){return "A";}char **g(void){return arr;}int main(void){return sizeof(arr)!=16||sizeof(arr2)!=16||f()[0]!=65||g()!=arr;}'),
        (884, 'signed_scalar_initializer',
         'int s=-11;int main(void){return s!=-11;}'),
        (885, 'unsigned_scalar_initializer',
         'unsigned int u=65535u;int main(void){return u!=65535u;}'),
        (886, 'char_scalar_initializer',
         'char ch=255;int main(void){return ch!=255;}'),
        (887, 'float_scalar_initializer',
         'float f=1.5;int main(void){return f!=1.5;}'),
        (889, 'string_pointer_initializer',
         'char *p="cat";int main(void){return p[0]!=99||p[2]!=116||p[3]!=0;}'),
        (890, 'global_object_address_initializer',
         'int x=11;int *p=&x;int main(void){return *p!=11;}'),
        (891, 'fixed_size_array_initializer',
         'int a[3]={4,5,6};int main(void){return sizeof(a)!=6||a[2]!=6;}'),
        (892, 'inferred_size_array_initializer',
         'int a[]={1,2,3,4};int main(void){return sizeof(a)!=8||a[3]!=4;}'),
        (893, 'partial_array_initializer_zero_fill',
         'int a[4]={17};int main(void){return a[0]!=17||a[1]!=0||a[3]!=0;}'),
        (894, 'trailing_array_initializer_comma',
         'int a[2]={8,9,};int main(void){return a[0]!=8||a[1]!=9;}'),
        (895, 'character_array_string_initializer',
         'char a[]="hi";int main(void){return sizeof(a)!=3||a[2]!=0;}'),
    ]
    for idx, name, source in run:
        runprogram('spec6_runtime_' + name, [idx], source)
