"""Source-byte exceptions for comments; C48 Rev 0.11 paragraph 39-50."""


def populate(accepted, rejected, runprogram):
    body = b'int main(void){return 0;}\n'
    # The copyright symbol is two UTF-8 bytes; the lexer does not decode it.
    allowed = [
        ('copyright_block', b'/* \xc2\xa9 */\n' + body),
        ('copyright_line', b'// Copyright \xc2\xa9\n' + body),
        ('unicode_bytes', b'/* \xf0\x9f\x8c\x88 \xe2\x98\x83 */\n' + body),
        ('high_byte', b'/* \xff\x80\x7f */\n' + body),
        ('nul_and_control', b'/* \x00\x01\x1b\x1f */\n' + body),
        ('cr_inside_comment', b'/* \r */\n' + body),
        ('bom_inside_comment', b'/* \xef\xbb\xbf */\n' + body),
        ('line_comment_bytes', b'// \xff\x00\xc2\xa9\n' + body),
        ('trailing_line_comment', body[:-1] + b'// \xc2\xa9\x00'),
        ('mixed_with_directive', b'#define VALUE 7 /* \xc2\xa9 */\nint main(void){return VALUE!=7;}\n'),
        ('multiline_block', b'/* start \xff\n\x00 end */\n' + body),
    ]
    for name, src in allowed:
        accepted('spec16_accept_' + name, [39, 42, 44, 49, 50], src)
    runprogram('spec16_runtime_comments_are_ignored', [44, 49],
               b'/* \xc2\xa9 \x00 */\nint main(void){return 0;}\n')

    disallowed = [
        ('copyright_as_token', b'int main(void){return \xc2\xa9;}\n'),
        ('copyright_in_string', b'int main(void){char *p="\xc2\xa9";return 0;}\n'),
        ('copyright_in_character', b'int main(void){return \'\xc2\xa9\';}\n'),
        ('utf8_bom_before_comment', b'\xef\xbb\xbf/* \xc2\xa9 */\n' + body),
        ('high_byte_identifier', b'int name\xff;\n' + body),
        ('nul_outside_comment', b'\x00' + body),
        ('cr_outside_comment', b'int main(void){\rreturn 0;}\n'),
        ('ascii_control_outside_comment', b'\x01' + body),
    ]
    for name, src in disallowed:
        rejected('spec16_reject_' + name, [42, 44, 49, 50], src)
