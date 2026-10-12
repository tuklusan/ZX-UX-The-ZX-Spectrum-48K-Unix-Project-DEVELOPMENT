#!/usr/bin/env python3
"""Specification-led, self-contained C48 acceptance and execution verifier.

Contract: docs/04-C48 Language Specification Rev 0.11.docx (SHA-256 in
traceability.json). Does not use historical compiler, binaries or kernel.
All generated cases and build outputs live in a temporary directory.

  toolbox/run.sh python3 tests/c48/conformance.py --report build/logs/c48-conformance.json

Clauses without explicit test coverage are recorded as untested.
"""
import argparse
from dataclasses import dataclass, field
from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / 'docs' / '04-C48 Language Specification Rev 0.11.docx'
TRACE = Path(__file__).with_name('traceability.json')
RCC = ROOT / 'sdk' / 'bin' / 'rcc'

@dataclass(frozen=True)
class Case:
    ident: str
    paragraphs: tuple
    kind: str
    source: bytes
    expected: int = 0
    extra: dict = field(default_factory=dict)
    note: str = ''

CASES = []
def add(ident, paras, kind, source, expected=0, extra=None, note=''):
    if isinstance(source, str):
        source = source.encode('ascii')
    assert kind in ('accept', 'reject', 'run', 'object', 'repeat', 'cli')
    CASES.append(Case(ident, tuple(paras), kind, source, expected, extra or {}, note))

def accepted(ident, p, s): add(ident, p, 'accept', s)
def rejected(ident, p, s): add(ident, p, 'reject', s)
def runexpr(ident, p, expression, value=0):
    add(ident, p, 'run', 'int main(void) { return (' + expression + ') != (' + str(value) + '); }\n')
def runprogram(ident, p, source, expected=0): add(ident, p, 'run', source, expected)

# Lexical contract: positive and negative numeric, character, string and syntax.
for ident, val in [('decimal_zero','0'),('decimal_boundary','32767'),('unsigned_implicit','32768'),
                   ('decimal_max','65535'),('unsigned_suffix','65535u'),('octal','077'),
                   ('hex','0xff'),('hex_upper','0XABCDU'),('character','\'A\''),
                   ('char_newline',r"'\n'"),('char_zero',r"'\0'"),('char_hex',r"'\xff'"),
                   ('float_zero','0.0'),('float_dot','1.'),('float_fraction','.5'),
                   ('float_exponent','1e3'),('float_exp_signed','1E-3'),('float_suffix','1.25f')]:
    accepted('lex_ok_'+ident,[134,138,148,160,166,174,184,188,831,832],
             'int main(void) { '+ ('float' if 'float_' in ident else 'int')+' n; n = '+val+'; return 0; }\n')
for ident, token in [('range_dec','65536'),('range_hex','0x10000'),('bad_octal','08'),
                     ('long_suffix','1L'),('unsigned_long','1UL'),('float_long','1.0L'),
                     ('float_hex','0x1.0p0'),('empty_char',"''"),('two_char',"'AB'"),
                     ('octal_escape',r"'\123'"),('short_hex_escape',r"'\x4'"),
                     ('unknown_escape',r"'\q'"),('digit_identifier','123abc'),
                     ('float_identifier','1.0foo'),('binary','0b101'),('digit_separator',"1'000")]:
    rejected('lex_bad_'+ident,[131,138,143,144,145,166,168,169,170,189,835,837],
             'int main(void) { return '+token+'; }\n')
for ident, source in [('bad_comment','int main(void){ /* unterminated\n'),
                     ('bad_splice','int main(void) { return 1\\\n+2; }'),
                     ('bad_control',b'int main(void){return 0;}\x00'),
                     ('bad_nonascii',b'int main(void){return 0;}\xc3\xa9'),
                     ('bad_hash','int main(void) { return # 1; }')]:
    rejected('lex_'+ident,[38,42,45,51,56,60,69,76,77,132],source)
accepted('lex_valid_comments',[69,70,72,74,75,78,79],
         '/* a block\n comment */\nint main(void) { // line comment\n return 0; }')
accepted('lex_final_no_lf',[54,55],'int main(void){return 0;}')
accepted('lex_crlf_host_convenience',[46],'int main(void) {\r\nreturn 0;\r\n}')
accepted('lex_15_identifier',[81,85,87], 'int abcdefghijklmno; int main(void){return 0;}')
rejected('lex_16_identifier',[85,87],'int abcdefghijklmnop; int main(void){return 0;}')
accepted('lex_case_sensitive',[84,96],'int Abc, abc, ABC; int main(void){return 0;}')
accepted('lex_single_underscore',[115,116],'int _ok; int main(void){return 0;}')
for name in ('bool','true','false','nullptr','alignas','typeof'):
    accepted('lex_regular_identifier_'+name,[114,115],f'int {name}; int main(void){{return 0;}}')
for word in ('auto','case','const','default','double','enum','goto','long','register','signed','struct','switch','typedef','union','volatile','inline','restrict','_Alignas','_Alignof','_Atomic','_Bool','_Complex','_Generic','_Imaginary','_Noreturn','_Static_assert','_Thread_local'):
    rejected('keyword_reject_'+word,[106,107,109,111,112,838],f'int {word}; int main(void){{return 0;}}')
for word in ('__heap','__abc','_start'):
    rejected('implementation_reserved_'+word,[116,117],f'int {word}; int main(void){{return 0;}}')
for token in ('+=','-=','*=','/=','%=','<<=','>>=','&=','|=','^=','->','?',':','...'):
    rejected('operator_unsupported_'+{'?':'question',':':'colon','...':'ellipsis'}.get(token,token.replace('=','eq').replace('<','l').replace('>','g').replace('-','minus').replace('*','star').replace('/','slash').replace('%','mod').replace('&','and').replace('|','or').replace('^','xor')),
             [126,127,129,835,837],'int main(void){int x; x = 1; x '+token+' 2; return 0;}')
rejected('operator_member',[126,127],'int main(void){int x; return x.y;}')
rejected('operator_comma_expression',[125,746],'int main(void){return (1,2);}')

# Data-model, declarations, function signatures, initialization and pointers.
for ident, source in [
    ('fundamental_types','char a; unsigned char b; short c; unsigned short d; int e; unsigned int f; float g; int main(void){return 0;}'),
    ('pointer_array','char *a[8]; char **b[8]; int main(void){return sizeof(a)==16 && sizeof(b)==16;}'),
    ('pointer_return','char *get(void); char **get2(void); int main(void){return 0;}'),
    ('pointer_double','int main(int argc, char **argv) { return 0; }'),
    ('extern_before','extern int x; int x; int main(void){return 0;}'),
    ('extern_after','int x; extern int x; int main(void){return 0;}'),
    ('extern_repeat','extern int x; extern int x; int x; extern int x; int main(void){return 0;}'),
    ('static_globals','static int x; static int f(void){return x;} int main(void){return f();}'),
    ('int_main','int main(int argc, char **argv) {return 0;}'),
    ('main_prototype','int main(void); int main(void){return 0;}'),
    ('no_main_tu','extern int another(void);'),
    ('empty_tu',' /* comments only */\n'),
    ('multiple_declarators','int a,b,c; int main(void){int x,y; return 0;}'),
    ('shadow_nested','int f(int x) { {int x; x=2;} return x; } int main(void) {return 0;}'),
    ('array_literal','char s[4]="abc"; int main(void){return 0;}'),
    ('char_inferred','char s[]="abc"; int main(void){return 0;}'),
    ('array_inferred','int a[]={1,2,3}; int main(void){return 0;}'),
    ('array_trailing_comma','int a[3]={1,2,3,}; int main(void){return 0;}'),
    ('array_partial','int a[3]={1}; int main(void){return 0;}'),
    ('global_address','int a; int *p=&a; int main(void){return 0;}'),
    ('global_string_pointer','char *p="hello"; int main(void){return 0;}'),
    ('global_null_pointer','int *p=0; int main(void){return 0;}'),
    ('function_two_args','int f(int a,int b){return a+b;} int main(void){return f(1,2)!=3;}'),
]: accepted('decl_'+ident,[210,213,220,222,234,236,240,243,247,248,265,274,280,286,290,297,305,312,329,350,365,374,385,399,409,421,874,875,877,878,879,880,882,883,1001],source)
for ident, source in [
    ('block_static','int main(void){static int a;return a;}'),
    ('invalid_void_main','void main(void){return;}'),
    ('invalid_type_short_int','short int x; int main(void){return 0;}'),
    ('invalid_unsigned_only','unsigned x; int main(void){return 0;}'),
    ('void_object','void x; int main(void){return 0;}'),
    ('pointer_to_array','char (*p)[8]; int main(void){return 0;}'),
    ('pointer_to_function','char (*p)(void); int main(void){return 0;}'),
    ('multi_array','char a[3][2]; int main(void){return 0;}'),
    ('duplicate_def','int a; int a; int main(void){return 0;}'),
    ('static_extern_conflict','static int a; extern int a; int main(void){return 0;}'),
    ('extern_static_conflict','extern int a; static int a; int main(void){return 0;}'),
    ('incompatible_extern','extern char a; int a; int main(void){return 0;}'),
    ('proto_int_short','int f(short a); int f(int a){return 0;} int main(void){return 0;}'),
    ('proto_char_uchar','int f(char a); int f(unsigned char a){return 0;} int main(void){return 0;}'),
    ('proto_short_int','short f(void); int f(void){return 0;} int main(void){return 0;}'),
    ('proto_ptr_void','int f(int *p); int f(void *p){return 0;} int main(void){return 0;}'),
    ('proto_arg_count','int f(int x); int main(void){return f();}'),
    ('old_style','int f(){return 0;} int main(void){return 0;}'),
    ('block_function','int main(void){int f(void);return 0;}'),
    ('undeclared_call','int main(void){return miss(1);}'),
    ('duplicate_param','int f(int x){int x;return x;} int main(void){return 0;}'),
    ('static_main','static int main(void){return 0;}'),
    ('object_main','int main;'),
    ('literal_too_big','char a[3]="abc"; int main(void){return 0;}'),
    ('array_overflow','int a[32768]; int main(void){return 0;}'),
    ('nested_initializer','int a[2]={{1},{2}}; int main(void){return 0;}'),
    ('designated_initializer','int a[2]={[0]=1}; int main(void){return 0;}'),
    ('void_size','int main(void){return sizeof(void); }'),
    ('array_type_size','int main(void){return sizeof(int[3]); }'),
    ('array_address','int a[2]; int main(void){int *p; p=&a; return 0;}'),
    ('void_pointer_math','int main(void){void *p; p=p+1; return 0;}'),
    ('void_pointer_deref','int main(void){void *p; return *p;}'),
    ('int_pointer_cast','int main(void){int *p; p=(int *)1;return 0;}'),
    ('index_commute','int main(void){int a[2];return 1[a];}'),
]: rejected('decl_bad_'+ident,[213,214,220,224,235,239,241,247,248,265,280,286,297,305,312,323,329,350,365,374,385,421,574,581,866,869,870,871,872,876,878,879,880,896,897,898],source)

# Explicit expression semantics with real linked executables in the ROM-backed VM.
for ident, expr, want, paras in [
    ('size_char','sizeof(char)',1,[220,222,574,578]),
    ('size_uchar','sizeof(unsigned char)',1,[220,222,574,578]),
    ('size_int','sizeof(int)',2,[220,222,574,578]),
    ('size_short','sizeof(short)',2,[220,222,574,578]),
    ('size_ptr','sizeof(void *)',2,[220,222,574,578]),
    ('size_float','sizeof(float)',5,[192,194,220,222,574,578]),
    ('size_string','sizeof("abc")',4,[174,177,574,578]),
    ('signed_div','(-7)/3',-2,[483,488,495,843]),
    ('signed_rem','(-7)%3',-1,[488,495,843]),
    ('neg_div','7/(-3)',-2,[488,495,843]),
    ('neg_rem','7%(-3)',1,[488,495,843]),
    ('unsigned_wrap','65535u+1u',0,[148,154,483,843]),
    ('signed_wrap','32767+1',(1<<15),[44,483,843]),
    ('signed_min','(-32767-1)-1',32767,[44,483,843]),
    ('literal_negative_min','-32768',32768,[146,148,845,1049]),
    ('char_left_shift','((char)1)<<8',1,[46,503,844,1047]),
    ('int_shift_mask','((int)1)<<16',1,[46,503,844,1048]),
    ('unsigned_cmp','(int)0x8000u < 0',1,[148,475,525,845]),
    ('bitwise','(0x55 & 0x0f) ^ 0x02',7,[47,503]),
]: runexpr('runtime_'+ident,paras,expr,want)
for ident, source in [
    ('shift_char_variable','int main(void){char c;c=1;return (c << 8) != 1;}'),
    ('shift_int_variable','int main(void){int c;c=1;return (c << 16) != 1;}'),
    ('char_narrowing','int main(void){char c;c=255;c=c+1;return c != 0;}'),
    ('size_array','int main(void){int a[4];return sizeof(a)!=8;}'),
    ('size_array_paren','int main(void){int a[4];return sizeof((a))!=8;}'),
    ('size_no_side_effect','int main(void){int a[4];int i;i=0;return sizeof(a[i++])!=2 || i!=0;}'),
    ('size_null_pointer','int main(void){int *p;p=0;return sizeof *p!=2;}'),
    ('eval_left_to_right','int log;int a(void){log=log*10+1;return 2;} int b(void){log=log*10+2;return 3;}int main(void){return a()+b()!=5 || log!=12;}'),
    ('eval_args','int log;int a(void){log=log*10+1;return 1;}int b(void){log=log*10+2;return 2;}int c(void){log=log*10+3;return 3;}int f(int x,int y,int z){return x*100+y*10+z;}int main(void){return f(a(),b(),c())!=123 || log!=123;}'),
    ('eval_capture','int f(int x,int y){return x*10+y;}int main(void){int i;i=1;return f(i++,i)!=12;}'),
    ('eval_self_assign','int main(void){int i;i=7;i=i++;return i!=7;}'),
    ('eval_shortcircuit','int i;int bump(void){i++;return 1;}int main(void){i=0;0 && bump();1 || bump();return i!=0;}'),
    ('pointer_int_stride','int main(void){int a[4];int *p;char *c;char *d;void *v;p=a;v=p+1;c=v;v=p;d=v;return ((p+1)-p)!=1 || c-d!=2;}'),
    ('pointer_char_stride','int main(void){char a[4];char *p;p=a;return ((p+1)-p)!=1;}'),
    ('pointer_float_stride','int main(void){float a[3];float *p;char *c;char *d;void *v;p=a;v=p+1;c=v;v=p;d=v;return c-d!=5;}'),
    ('pointer_distances','int main(void){int a[4];return (&a[3]-&a[1])!=2 || (&a[1]-&a[3])!= -2;}'),
    ('pointer_subscript','int main(void){int a[2];a[1]=5;return a[1]!=5;}'),
    ('pointer_double_index','int main(int argc,char **argv){return argv[0][0]!=\'p\';}'),
    ('global_zero','int a;static float b;int main(void){return a!=0 || b!=0.0;}'),
    ('global_array_zero','int a[3]={1};int main(void){return a[0]!=1 || a[1]!=0 || a[2]!=0;}'),
    ('pass_by_value','int f(int x){x=10;return x;}int main(void){int x;x=2;f(x);return x!=2;}'),
    ('pointer_write','int f(int *p){*p=9;return 0;}int main(void){int x;x=0;f(&x);return x!=9;}'),
    ('nested_shadow','int f(int x){{int x;x=99;}return x;}int main(void){return f(2)!=2;}'),
    ('local_init_repeat','int f(void){int a=5;a++;return a;}int main(void){return f()!=6 || f()!=6;}'),
    ('if_else','int main(void){int i;i=1;if(i) if(0)i=9;else i=2;return i!=2;}'),
    ('while_break','int main(void){int i;i=0;while(1){i++;if(i==3)break;}return i!=3;}'),
    ('do_once','int main(void){int i;i=0;do{i++;}while(0);return i!=1;}'),
    ('for_continue','int main(void){int i,s;s=0;for(i=0;i<5;i++){if(i==2)continue;s=s+i;}return s!=8;}'),
    ('void_function','void f(void){return;} int main(void){f();return 0;}'),
    ('string_distinct','char *a="hello";char *b="hello";int main(void){return a==b;}'),
    ('string_suffix_distinct','char *a="hello";char *b="llo";int main(void){return a+2==b;}'),
    ('logic_dynamic_and','int main(void){int z;z=0;return (0 && (1/z))!=0;}'),
    ('logic_dynamic_or','int main(void){int z;z=0;return (1 || (1/z))!=1;}'),
    ('string_concatenate','int main(void){return sizeof("a" "b")!=3;}'),
    ('null_equality','int main(void){int *p;p=0;return p!=0;}'),
    ('main_low_status','int main(void){return 256;}'),
]:
    p=[220,243,265,275,297,305,312,329,374,385,433,459,466,475,483,495,503,508,525,537,546,562,574,584,592,599,612,628,636,648,656,662,669,677,685,692,874,882,888,889,892,893,894,848,849,850,851,852,854,855,856,857,858,859,861,862,864,865,868,1077,1078]
    runprogram('runtime_'+ident,p,source)
# This case deliberately tests the 8-bit process exit status, not a boolean wrapper.
CASES[-1] = Case('runtime_main_low_status',(692,1063), 'run', b'int main(void){return 256;}\n',0)
for ident, source in [
    ('void_return_value','void f(void){return 1;} int main(void){return 0;}'),
    ('void_used_value','void f(void){return;} int main(void){return f();}'),
    ('void_expr_condition','void f(void){return;}int main(void){if(f())return 1;return 0;}'),
    ('declaration_after_stmt','int main(void){int x;x=1;int y;return 0;}'),
    ('out_of_loop_break','int main(void){break;return 0;}'),
    ('out_of_loop_continue','int main(void){continue;return 0;}'),
    ('ternary','int main(void){return 1?2:3;}'),
    ('function_arity','int f(int a,int b){return a;}int main(void){return f(1);}'),
    ('function_variadic','int f(int a,...); int main(void){return 0;}'),
]: rejected('sem_bad_'+ident,[628,634,636,639,677,685,692,592,594,597,835,839],source)

# Directive processing, header symbol identity and source-byte boundaries.
for ident,source in [
    ('integer','#define N 3\nint main(void){return N-3;}'),
    ('floating','#define F .5\nint main(void){float v;v=F;return v!=.5;}'),
    ('char',r"#define C '\x41'"+'\nint main(void){return C!=65;}'),
    ('string','#define S "hi"\nint main(void){return sizeof(S)!=3;}'),
    ('expr','#define N (2 + 3)\nint main(void){return N!=5;}'),
    ('backward','#define A 2\n#define B (A + 4)\nint main(void){return B!=6;}'),
    ('same_redefinition','#define A 2\n#define A 2\nint main(void){return A!=2;}'),
    ('nonexpand_literal','#define HI 4\nint main(void){return sizeof("HI")!=3;}'),
    ('builtin_header','#include <c48.h>\nint main(void){return sizeof(int)!=2;}'),
]:accepted('pp_'+ident,[698,705,706,709,714,715,716,717,718,719,720,731,732,733,734,900,901,902,903],source)
for ident, source in [
    ('forward','#define B A\n#define A 2\nint main(void){return 0;}'),
    ('self','#define A A\nint main(void){return 0;}'),
    ('diff_redefinition','#define A 1\n#define A 2\nint main(void){return 0;}'),
    ('func_like','#define X(a) 5\nint main(void){return 0;}'),
    ('nonconstant','#define A int\nint main(void){return 0;}'),
    ('unsupported_if','#if 1\nint main(void){return 0;}'),
    ('unsupported_undef','#define A 1\n#undef A\nint main(void){return 0;}'),
    ('unknown_header','#include <stdio.h>\nint main(void){return 0;}'),
    ('include_trailer','#include <c48.h> extra\nint main(void){return 0;}'),
    ('header_clash','int putchar(float a);\n#include <c48.h>\nint main(void){return 0;}'),
    ('reserved_macro','#define __bad 3\nint main(void){return 0;}'),
]: rejected('pp_bad_'+ident,[705,708,709,711,714,718,719,720,731,732,734,738,739,741,742,900,902,903],source)
for directive in ('if','ifdef','ifndef','elif','else','endif','error','line','pragma'):
    rejected('pp_unsupported_'+directive,[738,739,741,838],f'#{directive} ABC\nint main(void){{return 0;}}')
add('pp_local_include',[723,724,725,727,728,729,902,903],'accept',
    '#include "values.h"\nint main(void){return INCLUDED!=7;}\n',extra={'values.h':'#define INCLUDED 7\n'})
add('pp_include_inherit',[714,717,723,728,902,903],'accept',
    '#define START 4\n#include "included.h"\nint main(void){return OTHER!=5;}\n',extra={'included.h':'#define OTHER (START + 1)\n'})

# CLI/object conformance: real assembler and linker bytes, no historical formats.
add('object_sso_header',[755,757,761,779,1081,1082,1090],'object',
    'int main(void){return 0;}\n')
add('object_repeatable_ssx',[755,757,761,779,1065,1082,1088,1090],'repeat',
    'int main(void){return 0;}\n')



# Associate each individual fixture with one precisely selected requirement.
CLAUSE_FOR_CASE = {
    'lex_valid_comments': 70, 'lex_final_no_lf': 55,
    'lex_crlf_host_convenience': 46, 'lex_15_identifier': 85,
    'lex_16_identifier': 87, 'lex_case_sensitive': 84,
    'lex_single_underscore': 82, 'lex_bad_comment': 77,
    'lex_bad_splice': 56, 'lex_bad_control': 44,
    'lex_bad_nonascii': 49, 'lex_bad_hash': 120,
    'operator_member': 126, 'operator_comma_expression': 125,
    'runtime_size_char': 221, 'runtime_size_uchar': 221,
    'runtime_size_int': 221, 'runtime_size_short': 221,
    'runtime_size_ptr': 225, 'runtime_size_float': 194,
    'runtime_size_string': 177,
    'runtime_signed_div': 489, 'runtime_signed_rem': 489,
    'runtime_neg_div': 489, 'runtime_neg_rem': 489,
    'runtime_unsigned_wrap': 484, 'runtime_signed_wrap': 484,
    'runtime_signed_min': 484, 'runtime_literal_negative_min': 146,
    'runtime_char_left_shift': 496, 'runtime_int_shift_mask': 496,
    'runtime_unsigned_cmp': 526, 'runtime_bitwise': 496,
    'runtime_shift_char_variable': 844, 'runtime_shift_int_variable': 844,
    'runtime_char_narrowing': 216, 'runtime_size_array': 226,
    'runtime_size_array_paren': 226, 'runtime_size_no_side_effect': 851,
    'runtime_size_null_pointer': 852, 'runtime_eval_left_to_right': 848,
    'runtime_eval_args': 850, 'runtime_eval_capture': 850,
    'runtime_eval_self_assign': 848, 'runtime_eval_shortcircuit': 851,
    'runtime_logic_dynamic_and': 851, 'runtime_logic_dynamic_or': 851,
    'runtime_pointer_int_stride': 857, 'runtime_pointer_char_stride': 856,
    'runtime_pointer_float_stride': 858, 'runtime_pointer_distances': 861,
    'runtime_pointer_subscript': 227, 'runtime_pointer_double_index': 240,
    'runtime_global_zero': 249, 'runtime_global_array_zero': 249,
    'runtime_pass_by_value': 342, 'runtime_pointer_write': 325,
    'runtime_nested_shadow': 880, 'runtime_local_init_repeat': 248,
    'runtime_if_else': 654, 'runtime_while_break': 659,
    'runtime_do_once': 665, 'runtime_for_continue': 675,
    'runtime_void_function': 693, 'runtime_string_distinct': 181,
    'runtime_string_suffix_distinct': 181,
    'runtime_string_concatenate': 178, 'runtime_null_equality': 862,
    'runtime_main_low_status': 1063,
    'object_sso_header': 763, 'object_repeatable_ssx': 766,
    'pp_integer': 706, 'pp_floating': 706, 'pp_char': 706,
    'pp_string': 706, 'pp_expr': 709, 'pp_backward': 709,
    'pp_same_redefinition': 719, 'pp_nonexpand_literal': 902,
    'pp_builtin_header': 732, 'pp_bad_header_clash': 734,
    'pp_bad_forward': 718, 'pp_bad_self': 718,
    'pp_bad_diff_redefinition': 719, 'pp_bad_func_like': 741,
    'pp_bad_nonconstant': 711, 'pp_bad_unsupported_if': 739,
    'pp_bad_unsupported_undef': 739,
    'pp_bad_unknown_header': 732, 'pp_bad_include_trailer': 742,
    'pp_bad_reserved_macro': 116, 'pp_local_include': 724,
    'pp_include_inherit': 717,
    'decl_array_trailing_comma': 378, 'decl_array_partial': 422,
    'decl_global_address': 375, 'decl_global_string_pointer': 375,
    'decl_global_null_pointer': 888,
    'decl_fundamental_types': 211, 'decl_pointer_array': 236,
    'decl_pointer_return': 240, 'decl_pointer_double': 240,
    'decl_extern_before': 879, 'decl_extern_after': 879,
    'decl_extern_repeat': 248, 'decl_static_globals': 247,
    'decl_int_main': 693, 'decl_main_prototype': 335,
    'decl_no_main_tu': 769, 'decl_empty_tu': 769,
    'decl_multiple_declarators': 246, 'decl_shadow_nested': 880,
    'decl_array_literal': 375, 'decl_char_inferred': 375,
    'decl_array_inferred': 375, 'decl_pointer_global': 375,
    'decl_function_two_args': 335,
    'decl_bad_block_static': 291, 'decl_bad_invalid_void_main': 693,
    'decl_bad_invalid_type_short_int': 213,
    'decl_bad_invalid_unsigned_only': 213,
    'decl_bad_void_object': 223, 'decl_bad_pointer_to_array': 239,
    'decl_bad_pointer_to_function': 239, 'decl_bad_multi_array': 241,
    'decl_bad_duplicate_def': 878, 'decl_bad_static_extern_conflict': 878,
    'decl_bad_extern_static_conflict': 878, 'decl_bad_incompatible_extern': 878,
    'decl_bad_proto_int_short': 876, 'decl_bad_proto_char_uchar': 876,
    'decl_bad_proto_short_int': 876, 'decl_bad_proto_ptr_void': 876,
    'decl_bad_proto_arg_count': 335, 'decl_bad_old_style': 336,
    'decl_bad_block_function': 291, 'decl_bad_undeclared_call': 362,
    'decl_bad_duplicate_param': 880, 'decl_bad_static_main': 693,
    'decl_bad_object_main': 693, 'decl_bad_literal_too_big': 375,
    'decl_bad_array_overflow': 752, 'decl_bad_nested_initializer': 375,
    'decl_bad_designated_initializer': 375, 'decl_bad_void_size': 224,
    'decl_bad_array_type_size': 574, 'decl_bad_array_address': 239,
    'decl_bad_void_pointer_math': 327, 'decl_bad_void_pointer_deref': 327,
    'decl_bad_int_pointer_cast': 331, 'decl_bad_index_commute': 241,
    'sem_bad_void_return_value': 693, 'sem_bad_void_used_value': 693,
    'sem_bad_void_expr_condition': 693, 'sem_bad_declaration_after_stmt': 654,
    'sem_bad_out_of_loop_break': 683, 'sem_bad_out_of_loop_continue': 683,
    'sem_bad_ternary': 126, 'sem_bad_function_arity': 335,
    'sem_bad_function_variadic': 343,
}
# Remaining uniformly named cases are mapped to the single governing clause.
for case in CASES:
    ident = case.ident
    if ident in CLAUSE_FOR_CASE:
        continue
    if ident.startswith('lex_ok_'):
        suffix = ident[7:]
        CLAUSE_FOR_CASE[ident] = (187 if suffix.startswith('float_') else
            161 if suffix.startswith('char_') or suffix == 'character' else
            143 if suffix == 'octal' else 138 if 'suffix' in suffix else 135)
    elif ident.startswith('lex_bad_'):
        suffix = ident[8:]
        CLAUSE_FOR_CASE[ident] = (169 if 'escape' in suffix else
            170 if 'char' in suffix else 189 if 'float_' in suffix else
            143 if 'octal' in suffix else 145 if 'range' in suffix else
            131 if 'identifier' in suffix else 144)
    elif ident.startswith('lex_regular_identifier_'):
        CLAUSE_FOR_CASE[ident] = 101
    elif ident.startswith('keyword_reject_'):
        CLAUSE_FOR_CASE[ident] = 111
    elif ident.startswith('implementation_reserved_'):
        CLAUSE_FOR_CASE[ident] = 116
    elif ident.startswith('operator_unsupported_'):
        CLAUSE_FOR_CASE[ident] = 126
    elif ident.startswith('pp_unsupported_'):
        CLAUSE_FOR_CASE[ident] = 739

# This is a conservative test-to-requirement relation, not a section-level
# assertion. An unlinked case still runs, but establishes no clause coverage.
CASES = [Case(c.ident, (CLAUSE_FOR_CASE[c.ident],) if c.ident in CLAUSE_FOR_CASE
              else (), c.kind, c.source, c.expected, c.extra, c.note)
         for c in CASES]



# Checked-in grouped source fixture, shared by native and bytecode runs.
GROUPED_SOURCE = Path(__file__).with_name('grouped-runtime.c')
add('grouped_runtime_core', [301, 543, 593, 672, 696],
    'run', GROUPED_SOURCE.read_bytes())


# Additional checked-in grouped integer runtime fixture.
add('grouped_integer_runtime', [484, 496], 'run',
    Path(__file__).with_name('grouped-integers.c').read_bytes())

add('batch_literal_runtime', [177, 178, 181], 'run',
    Path(__file__).with_name('batch-literals.c').read_bytes())

# Independent lexical and literal diagnostic assertions.
for name, clause, source in (
    ('wide_character', 171, "int main(void){return L'A';}"),
    ('unterminated_character', 172, "int main(void){return 'a;}"),
    ('unterminated_string', 179, 'int main(void){return "abc;}'),
    ('literal_assignment', 180, 'int main(void){"abc"[0]=1;return 0;}'),
    ('wide_string', 182, 'int main(void){char *s=L"abc";return 0;}'),
):
    rejected('batch_literal_bad_' + name, [clause], source)

# Checked-in negative fixtures: explicit compile-time rejection, never runtime.
for fixture_id, clause, filename in (
    ('negative_reserved', 111, 'negative-reserved.c'),
    ('negative_operator', 126, 'negative-operator.c'),
    ('negative_preprocessor', 739, 'negative-preprocessor.c'),
):
    rejected(fixture_id, [clause],
             Path(__file__).with_name(filename).read_bytes())

from spec_batch import populate as populate_spec_batch
populate_spec_batch(accepted, rejected, runexpr, runprogram)

from spec_batch2 import populate as populate_spec_batch2
populate_spec_batch2(accepted, rejected, runprogram)

from spec_batch3 import populate as populate_spec_batch3
populate_spec_batch3(accepted, rejected, runprogram)

from spec_batch4 import populate as populate_spec_batch4
populate_spec_batch4(accepted, rejected, runprogram)

from spec_batch5 import populate as populate_spec_batch5
populate_spec_batch5(accepted, rejected, runprogram, add)

from spec_batch6 import populate as populate_spec_batch6
populate_spec_batch6(accepted, rejected, runprogram)

from spec_batch7 import populate as populate_spec_batch7
populate_spec_batch7(runprogram)

from spec_batch8 import populate as populate_spec_batch8
populate_spec_batch8(add, accepted, rejected, runexpr, runprogram)

from spec_batch9 import populate as populate_spec_batch9
populate_spec_batch9(add)


from spec_batch10 import populate as populate_spec_batch10
populate_spec_batch10(rejected, runprogram)

from spec_batch11 import populate as populate_spec_batch11
populate_spec_batch11(add, accepted, rejected, runprogram)

from spec_batch12 import populate as populate_spec_batch12
populate_spec_batch12(add, accepted, rejected, runprogram)

def _rcc(src, out, mode, timeout=35):
    return subprocess.run([sys.executable,str(RCC),mode,'-o',str(out),str(src)],
        cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=timeout,
        env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})

def execute_cli(c, case_dir, src):
    operation = c.note
    original = src.read_bytes()
    target = case_dir / 'custom.ssx'
    if operation == 'default_ssx':
        args, output, signature = [str(src)], src.with_suffix('.ssx'), b'SSX1'
    elif operation == 'default_obj':
        args, output, signature = ['-c', str(src)], src.with_suffix('.sso'), b'SSO1'
    elif operation == 'default_asm':
        args, output, signature = ['-S', str(src)], src.with_suffix('.s'), None
    elif operation == 'custom_output':
        args, output, signature = ['-o', str(target), str(src)], target, b'SSX1'
    elif operation == 'source_guard':
        args, output, signature = ['-o', str(src), str(src)], None, None
    elif operation == 'alias_guard':
        alias = case_dir / 'input-alias.c'
        os.link(src, alias)
        args, output, signature = ['-o', str(alias), str(src)], None, None
    elif operation == 'extension_guard':
        other = case_dir / 'fixture.ssx'
        other.write_bytes(original)
        src.unlink()
        src, original = other, other.read_bytes()
        args, output, signature = [str(src)], None, None
    elif operation == 'no_inputs':
        args, output, signature = [], None, None
    elif operation == 'missing_output':
        args, output, signature = ['-o'], None, None
    elif operation == 'missing_numeric':
        args, output, signature = ['--max'], None, None
    elif operation == 'invalid_numeric':
        args, output, signature = ['--max', 'invalid', str(src)], None, None
    elif operation == 'negative_numeric':
        args, output, signature = ['--max', '-1', str(src)], None, None
    elif operation == 'conflicting_forms':
        args, output, signature = ['-S', '-c', str(src)], None, None
    elif operation == 'conflicting_backends':
        args, output, signature = ['--bytecode', '--native', str(src)], None, None
    elif operation == 'write_error':
        args, output, signature = ['-o', str(case_dir/'nonexistent'/'program.ssx'), str(src)], None, None
    elif operation == 'source_error':
        args, output, signature = [str(src)], None, None
    else:
        raise ValueError('unexpected CLI contract case')
    proc = subprocess.run([sys.executable, str(RCC), *args], cwd=case_dir,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          timeout=35,
                          env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})
    stderr = proc.stderr.decode('utf-8', 'replace')
    expected_status = (0 if output is not None else
                       1 if operation in ('source_error', 'write_error') else 2)
    correct = proc.returncode == expected_status and src.read_bytes() == original
    if output is not None:
        correct = correct and output.is_file()
        if output.is_file():
            contents = output.read_bytes()
            correct = correct and bool(contents)
            if signature is not None:
                correct = correct and contents.startswith(signature)
    if operation in ('source_error', 'write_error', 'source_guard',
                     'alias_guard', 'extension_guard', 'missing_output',
                     'missing_numeric', 'invalid_numeric', 'negative_numeric'):
        correct = correct and stderr.startswith('rcc:')
    if operation in ('source_error',):
        correct = correct and src.name in stderr
    correct = correct and 'Traceback' not in stderr
    return correct, ('status=%s, src-unchanged=%s, output=%s, stderr=%s' %
                     (proc.returncode, src.read_bytes() == original,
                      output.name if output else '(none)', stderr[:110]))


def execute(c, temp, backend):
    case_dir = temp / c.ident
    case_dir.mkdir()
    src = case_dir / 'fixture.c'
    src.write_bytes(c.source)
    for name, contents in c.extra.items():
        if not name.isascii() or '/' in name or '..' in name:
            raise ValueError('invalid test include path')
        (case_dir / name).write_text(contents,encoding='ascii')
    if c.kind == 'cli':
        return execute_cli(c, case_dir, src)
    if c.kind in ('accept','reject'):
        sys.path.insert(0,str(ROOT/'sdk'))
        from rcc.driver import compile_to_asm
        from rcc.lex import CError
        try:
            assembly, _, _ = compile_to_asm(str(src))
            if c.kind=='reject':
                return False, 'compiler accepted invalid source'
            return bool(assembly), f'assembly bytes={len(assembly.encode())}'
        except CError as error:
            return c.kind=='reject', f'{error.cls}: {str(error)[:150]}'
    if c.kind=='object':
        out = case_dir/'fixture.sso'
        p=_rcc(src,out,'-c')
        okay=p.returncode==0 and out.exists() and out.read_bytes()[:4]==b'SSO1'
        return okay, f'rc={p.returncode}; header={out.read_bytes()[:4]!r}' if out.exists() else p.stderr.decode()[:150]
    sys.path.insert(0,str(ROOT/'sdk'))
    from rcc import driver
    from rcc.lex import CError
    from ras import AsmError
    from rld import LinkError
    import rvm
    opts = {'bytecode':'all'} if backend=='bytecode' else {}
    try:
        data, _, _, _, need = driver.build(str(src), opts)
    except (CError,AsmError,LinkError) as exc:
        return False, 'compiler: '+str(exc)[:180]
    if data[:4]!=b'SSX1':
        return False, f'bad SSX1 signature {data[:4]!r}'
    if c.kind=='repeat':
        data2, _, _, _, _ = driver.build(str(src), opts)
        return data==data2, f'{backend} repeatable: {len(data)} bytes'
    vm=rvm.VM(data,fixed_ticks=1234)
    why=vm.run(max_frames=200)
    return why=='exit' and vm.status==c.expected, f'{backend}: {why}; status={vm.status}; SSX1 bytes={len(data)}; memory need={need}'


def main(argv=None):
    ap=argparse.ArgumentParser()
    ap.add_argument('--report', type=Path)
    ap.add_argument('--backend',choices=('native','bytecode','both'),default='both')
    ap.add_argument('--only',help='comma separated case IDs')
    ap.add_argument('--kinds',help='comma separated kinds: accept,reject,run,object,repeat,cli')
    args=ap.parse_args(argv)
    trace=json.loads(TRACE.read_text())
    if hashlib.sha256(SPEC.read_bytes()).hexdigest()!=trace['spec_sha256']:
        print('STOP: specification checksum mismatch',file=sys.stderr)
        return 2
    if len({c.ident for c in CASES})!=len(CASES):
        print('STOP: duplicate verifier case identifiers',file=sys.stderr)
        return 2
    names=set(args.only.split(',')) if args.only else None
    kinds=set(args.kinds.split(',')) if args.kinds else None
    statuses=[]
    with tempfile.TemporaryDirectory(prefix='zxux-c48-') as t:
        temp=Path(t)
        for c in CASES:
            if names and c.ident not in names:continue
            if kinds and c.kind not in kinds:continue
            if c.kind in ('run','repeat') and args.backend=='both':
                backends=('native','bytecode')
            else:
                backends=(args.backend if args.backend!='both' else 'native',)
            for backend in backends:
                # each backend gets separate scratch output
                btemp=temp/backend;btemp.mkdir(exist_ok=True)
                try:
                    ok, why=execute(c,btemp,backend)
                    state='PASS' if ok else 'FAIL'
                except Exception as exc:
                    state='ERROR';why='%s: %s' % (type(exc).__name__,exc)
                statuses.append(dict(id=c.ident,paragraphs=list(c.paragraphs),backend=backend,
                                     kind=c.kind,status=state,detail=why))
                print('%-5s %-46s %-8s %s'%(state,c.ident,backend,why[:170]))
    index={x['paragraph_index']:[] for x in trace['requirements']}
    invalid = [(c.ident, p) for c in CASES for p in c.paragraphs if p not in index]
    if invalid:
        print('STOP: invalid C48 paragraph mappings', file=sys.stderr)
        return 2
    for s in statuses:
        for p in s['paragraphs']:
            if p in index:index[p].append(s)
    coverage=[]
    for r in trace['requirements']:
        results=index[r['paragraph_index']]
        state=('UNTESTED' if not results else
               'FAIL' if any(s['status']!='PASS' for s in results) else 'EXERCISED')
        coverage.append({'paragraph_index':r['paragraph_index'],'section':r['section'],
                         'classification':r['classification'],'status':state,
                         'tests':sorted(set(s['id'] for s in results))})
    summary={v:sum(s['status']==v for s in statuses) for v in ('PASS','FAIL','ERROR')}
    summary['UNTESTED_PARAGRAPHS']=sum(c['status']=='UNTESTED' for c in coverage)
    summary['UNMAPPED_TEST_EXECUTIONS']=sum(not s['paragraphs'] for s in statuses)
    result={'spec_sha256':trace['spec_sha256'],'cases_declared':len(CASES),
            'backend':args.backend,'summary':summary,'cases':statuses,'clauses':coverage,
            'claim':'EXERCISED records only a linked assertion; it does not certify the entire paragraph. No complete language-conformance claim.'}
    if args.report:
        args.report.parent.mkdir(parents=True,exist_ok=True)
        args.report.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print('SUMMARY:',summary,'/',len(coverage),'traced paragraphs')
    return 0 if not summary['FAIL'] and not summary['ERROR'] else 1

if __name__=='__main__':
    raise SystemExit(main())
