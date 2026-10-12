"""Direct C48 Rev 0.11 call, conversion and evaluation-order assertions.

These programs exercise observable SDK semantics in both backends. They do
not claim to prove register-level ABI details from source-level results.
"""


def populate(rejected, runprogram):
    run = [
        (467, 'mixed_scalar_conversion',
         'int main(void){unsigned char c;short i;float f;'
         'c=255;i=-2;f=i+2.5;return !(f==1.0/2.0)||!(c>i); }'),
        (478, 'negative_to_unsigned_narrowing',
         'int main(void){unsigned char c;short s;s=-1;c=s;'
         'return c!=255;}'),
        (501, 'shift_count_mask_16',
         'int main(void){int i;char b;i=5;b=1;'
         'return (i<<16)!=5||(b<<8)!=1;}'),
        (509, 'logical_operator_values',
         'int main(void){int i;i=1;'
         'return !(i&&5)||(i||0)!=1||!0!=1||!i!=0;}'),
        (548, 'implicit_assignment_parameter_return_conversions',
         'float f(short x){return x+0.5;} int g(float x){return x;}'
         'int main(void){unsigned char c;short s;c=255;s=-2;'
         'return f(s)!=-1.5||g(f(c))!=255;}'),
        (585, 'operand_evaluation_left_to_right',
         'int count;int next(void){count=count+1;return count;}'
         'int main(void){int x;count=0;x=next()*10+next();'
         'return x!=12||count!=2;}'),
        (590, 'nested_expression_evaluation_order',
         'int count;int next(void){count=count+1;return count;}'
         'int main(void){int x;count=0;x=(next()+next())*next();'
         'return x!=9||count!=3;}'),
        (602, 'call_arguments_left_to_right',
         'int count;int next(void){count=count+1;return count;}'
         'int choose(int x,int y,int z){return x*100+y*10+z;}'
         'int main(void){count=0;return choose(next(),next(),next())!=123'
         '||count!=3;}'),
        (604, 'float_parameters_have_value_semantics',
         'float combine(float a,float b){a=a+1.0;return a*10.0+b;}'
         'int main(void){float a,b;a=1.0;b=2.0;'
         'return combine(a,b)!=22.0||a!=1.0||b!=2.0;}'),
        (605, 'unsigned_char_argument_full_value',
         'int pick(int a,char b,int c){return b;}'
         'int main(void){char c;c=255;return pick(2,c,3)!=255;}'),
        (616, 'float_result_preserves_explicit_parameters',
         'float blend(int a,float b,int c){return a+b+c;}'
         'int main(void){float f;f=blend(2,1.5,3);return f!=6.5;}'),
        (604, 'three_float_arguments_preserved',
         'float f(float a,float b,float c){return a+b+c;}'
         'int main(void){float v;v=f(1.0,2.0,3.0);return v!=6.0;}'),
        (606, 'mixed_arguments_restore_caller_stack',
         'float f(float a,short b,float c){return a+b+c;}'
         'int main(void){return f(1.0,2,3.0)!=6.0;}'),
        (607, 'recursive_frame_float_argument',
         'float f(float a,int n){if(n<=0)return a;return f(a+1.0,n-1);}'
         'int main(void){return f(1.0,2)!=3.0;}'),
        (618, 'independent_float_results_survive_later_calls',
         'float f(void){return 1.25;}float g(void){return 2.5;}'
         'int main(void){float a,b;a=f();b=g();'
         'return a!=1.25||b!=2.5||a+b!=3.75;}'),
    ]
    for paragraph, name, source in run:
        runprogram('spec10_' + name, [paragraph], source)
    rejected('spec10_no_cdecl_attribute', [610],
             'int __cdecl f(void){return 1;}int main(void){return f();}')
    rejected('spec10_no_regcall_attribute', [609],
             'int C48_REGCALL f(void){return 1;}int main(void){return f();}')
