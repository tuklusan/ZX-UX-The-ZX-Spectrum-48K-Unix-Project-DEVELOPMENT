"""Direct C48 Rev 0.11 lexical, identifier, and token assertions.

Each clause link records only the tested behavior, not its whole section.
"""


def populate(accepted, rejected, runprogram):
    valid = [
        (39, 'ascii_source', 'int main(void){return 0;}\n'),
        (40, 'canonical_lf', 'int a;\nint main(void){return 0;}\n'),
        (54, 'lf_terminates_line', '#define V 2\nint main(void){return V-2;}\n'),
        (63, 'tab_and_lf_whitespace', 'int\tmain(void)\n{\nreturn 0;\n}\n'),
        (66, 'whitespace_separates_tokens', 'int main(void){int x;x=0;return x;}'),
        (67, 'redundant_whitespace', 'int   main ( void ) { return   0  ; }'),
        (74, 'end_of_file_line_comment', 'int main(void){return 0;} // last comment'),
        (75, 'multiline_block_comment', 'int /* one\n two */ main(void){return 0;}'),
        (79, 'comment_as_whitespace', 'int/**/main(void){return 0;}'),
        (99, 'supported_control_keywords', 'static int f(void){int n;n=1;while(n){if(n)break;else continue;}return 0;}int main(void){return f();}'),
    ]
    for index, name, source in valid:
        accepted('spec3_accept_' + name, [index], source)

    bad = [
        (48, 'byte_order_mark', b'\xef\xbb\xbfint main(void){return 0;}'),
        (51, 'universal_character_name', 'int \\u0061;int main(void){return 0;}'),
        (65, 'vertical_tab_whitespace', 'int\x0bmain(void){return 0;}'),
        (76, 'nested_block_comment', 'int/* first /* nested */ second */main(void){return 0;}'),
        (102, 'unsupported_unsigned_float', 'unsigned float f;int main(void){return 0;}'),
        (104, 'unsupported_signed_specifier', 'signed int x;int main(void){return 0;}'),
        (107, 'unsupported_reserved_word', 'int auto;int main(void){return 0;}'),
        (109, 'later_reserved_word', 'int _Atomic;int main(void){return 0;}'),
        (112, 'reserved_not_identifier', 'int const;int main(void){return 0;}'),
        (129, 'compound_token_not_split', 'int main(void){int n;n=0;n+=1;return 0;}'),
        (132, 'bad_lexical_byte', 'int main(void){return @;}'),
    ]
    for index, name, source in bad:
        rejected('spec3_reject_' + name, [index], source)

    runtime = [
        (50, 'ascii_escape', 'int main(void){char v;v=\'\\x7f\';return v!=127;}'),
        (78, 'string_comment_introducers', 'int main(void){char *p;p="/*";return p[0]!=\'/\'||p[1]!=\'*\';}'),
        (89, 'distinct_short_spellings', 'int abcdefghijklmnX, abcdefghijklmnY;int main(void){abcdefghijklmnX=1;abcdefghijklmnY=2;return abcdefghijklmnX+abcdefghijklmnY!=3;}'),
        (90, 'symbol_identity', 'int abcdefghijklmnX, abcdefghijklmnY;int main(void){abcdefghijklmnX=1;abcdefghijklmnY=2;return abcdefghijklmnX+abcdefghijklmnY!=3;}'),
        (91, 'prefix_distinction', 'int abcdefghijklmnX, abcdefghijklmnY;int main(void){abcdefghijklmnX=1;abcdefghijklmnY=2;return abcdefghijklmnX==abcdefghijklmnY;}'),
        (92, 'identifier_case', 'int Abc,abc;int main(void){Abc=1;abc=2;return Abc+abc!=3;}'),
        (103, 'plain_signed_int_short', 'int main(void){int x;short y;x=-1;y=-1;return x>=0||y>=0;}'),
        (130, 'comment_prevents_token_fusion', 'int main(void){return (2 +/**/+ 3)!=5;}'),
    ]
    for index, name, source in runtime:
        runprogram('spec3_runtime_' + name, [index], source)
