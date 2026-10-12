"""Specification-led primary-expression and statement assertions for C48 Rev 0.11.

Each mapping names the actual specification paragraph, not just its section.
A test proves the stated observation only, not an entire prose chapter.
"""


def populate(add, accepted, rejected, runexpr, runprogram):
    # Section 39: every primary-expression form has independent runtime proof.
    runprogram('spec8_primary_identifier', [440, 441],
               'int main(void){int value;value=41;return value!=41;}')
    runexpr('spec8_primary_integer', [442], '0x2b', 43)
    runexpr('spec8_primary_float', [443], '1.25 == 1.25', 1)
    runexpr('spec8_primary_character', [444], "'A'", 65)
    runprogram('spec8_primary_string', [445],
               'int main(void){char *s;s="hi";return s[0]!=104||s[1]!=105||s[2]!=0;}')
    runexpr('spec8_primary_parenthesized', [446], '2*(3+4)', 14)

    # Unsupported constructs must be explicitly diagnosed (Sections 39, 76).
    rejected('spec8_reject_compound_literal', [448],
             'int main(void){int x;x=(int){3};return x;}')
    rejected('spec8_reject_generic_selection', [449],
             'int main(void){return _Generic(1,int:1,default:0);}')
    rejected('spec8_reject_statement_expression', [450],
             'int main(void){return ({int x;x=2;x;});}')
    rejected('spec8_reject_member_expression', [451],
             'int main(void){int x;return x.member;}')

    # Section 60 and control statements: actual body effects and control flow.
    runprogram('spec8_statement_inventory', [629],
               'int main(void){int n;n=0;while(n<2){n=n+1;}'
               'do{n=n+1;}while(n<3);for(n=0;n<4;n=n+1)'
               '{if(n==2)continue;if(n==3)break;}return n!=3;}')
    rejected('spec8_no_switch', [633, 682],
             'int main(void){int n;n=1;switch(n){case 1:return 0;default:return 1;}}')
    runprogram('spec8_expression_statement', [645],
               'int main(void){int n;n=3;n+4;return n!=3;}')
    runprogram('spec8_if_then', [649],
               'int main(void){int x;x=0;if(1){x=7;}return x!=7;}')
    runprogram('spec8_if_else', [651],
               'int main(void){int x;x=0;if(0)x=8;else x=9;return x!=9;}')
    runprogram('spec8_while', [657],
               'int main(void){int x;x=0;while(x<5)x=x+1;return x!=5;}')
    runprogram('spec8_do_while', [663],
               'int main(void){int x;x=0;do{x=x+2;}while(x<4);return x!=4;}')
    runprogram('spec8_for', [670],
               'int main(void){int i,s;s=0;for(i=0;i<4;i=i+1)s=s+i;return s!=6;}')
    rejected('spec8_break_outside_loop', [683],
             'int main(void){break;return 0;}')

    # Supported/unsupported punctuation should not vary between backends.
    accepted('spec8_decl_punctuation', [123],
             'int glob[2];int main(void){int x,y;x=1;y=2;glob[0]=x;glob[1]=y;return 0;}')
    rejected('spec8_member_punctuation', [128],
             'int main(void){int x;return x.z;}')

    # Host source text and scope are not historical tape-object formats.
    accepted('spec8_ascii_lf', [42, 47],
             'int item;\nint main(void){return item;}\n')
    accepted('spec8_comment_boundaries', [72],
             'int main(void){int n;/* block\n comment */n=1;return n-1;}')
    # A local include is host source text, not an old ZX-UX binary object.
    add('spec8_local_host_include', [725, 726], 'run',
        '#include "local.h"\nint main(void){return seed!=3;}\n',
        extra={'local.h': 'int seed=3;\n'})
