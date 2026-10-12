"""C48 Rev 0.11 host-compiler command and output contract cases."""


def populate(add):
    source = 'int main(void){return 0;}\n'
    for name, paragraph, operation in (
        ('default_executable', [762, 1082, 1083, 1088, 1090], 'default_ssx'),
        ('default_object', [764, 1082, 1083, 1090], 'default_obj'),
        ('default_assembly', [1082, 1083, 1090], 'default_asm'),
        ('custom_output', [1083], 'custom_output'),
        ('source_output_guard', [1085], 'source_guard'),
        ('source_alias_guard', [1085], 'alias_guard'),
        ('source_default_collision', [1085], 'extension_guard'),
        ('no_inputs', [774, 1087], 'no_inputs'),
        ('missing_output_value', [774, 1087], 'missing_output'),
        ('missing_numeric_value', [1087], 'missing_numeric'),
        ('invalid_numeric_value', [1087], 'invalid_numeric'),
        ('negative_numeric_value', [1087], 'negative_numeric'),
        ('conflicting_output_modes', [1082], 'conflicting_forms'),
        ('conflicting_backends', [1082], 'conflicting_backends'),
        ('write_error', [782, 1087], 'write_error'),
    ):
        add('spec9_' + name, paragraph, 'cli', source, note=operation)
    add('spec9_invalid_source', [773, 775, 778, 780, 1087], 'cli',
        'int main(void){return missing_symbol;}\n', note='source_error')
    add('spec9_include_error', [777], 'cli',
        '#include "not-a-valid-local-header.h"\nint main(void){return 0;}\n',
        note='source_error')
