"""Rev 0.11 checks of named compiler test outcomes.

Each audit runs only after the compiler cases and checks that a named,
relevant corpus actually passed. Audits are not a substitute for an
independent compiler, target execution, or proof of an entire chapter.
"""


def populate(add, available):
    known = {c.ident: c for c in available}
    bundles = (
        ('physical_source', [964, 965],
         ['lex_final_no_lf','lex_crlf_host_convenience','lex_valid_comments',
          'lex_bad_splice','lex_bad_control','lex_bad_nonascii']),
        ('positive_lexical_examples', [831],
         ['lex_ok_decimal_zero','lex_ok_decimal_boundary','lex_ok_unsigned_implicit',
          'lex_ok_octal','lex_ok_hex','lex_ok_character','lex_ok_char_hex',
          'lex_ok_float_zero','lex_ok_float_exponent']),
        ('negative_lexical_examples', [836, 839],
         ['lex_bad_binary','lex_bad_digit_separator','lex_bad_two_char',
          'lex_bad_float_long','lex_bad_octal_escape','lex_bad_float_hex',
          'decl_bad_array_type_size','sem_bad_void_used_value']),
        ('complete_reserved_inventory', [838, 966],
         sorted([c.ident for c in available if c.ident.startswith('keyword_reject_') or
                 c.ident.startswith('pp_unsupported_') or
                 c.ident.startswith('implementation_reserved_')])),
        ('identifier_range', [1007],
         ['lex_15_identifier','lex_16_identifier','lex_case_sensitive',
          'lex_single_underscore','spec13_source_byte_identifier_limit']),
        ('literal_forms', [969, 1039],
         ['lex_ok_hex_upper','lex_ok_unsigned_suffix','lex_ok_char_zero',
          'lex_ok_float_fraction','lex_ok_float_exp_signed','lex_bad_long_suffix',
          'lex_bad_float_hex','spec7_rom_float_diverse_golden_inventory']),
        ('declaration_and_linkage_examples', [875, 971],
         ['decl_multiple_declarators','decl_static_globals','decl_extern_before',
          'decl_extern_repeat','decl_pointer_return','decl_pointer_double',
          'decl_array_inferred','decl_pointer_array','spec13_external_and_static_resolution']),
        ('initializer_examples', [883, 974],
         ['decl_array_trailing_comma','decl_array_partial','decl_global_address',
          'decl_global_string_pointer','decl_global_null_pointer',
          'runtime_global_zero','runtime_global_array_zero',
          'spec12_initialized_globals_ready_before_main']),
        ('preprocessor_macro_examples', [901],
         ['pp_integer','pp_floating','pp_char','pp_string','pp_expr','pp_backward',
          'pp_bad_forward','pp_bad_self','pp_bad_diff_redefinition','pp_nonexpand_literal']),
        ('preprocessor_include_examples', [903],
         ['pp_local_include','pp_include_inherit','pp_builtin_header',
          'pp_bad_unknown_header','pp_bad_include_trailer','pp_bad_header_clash',
          'spec8_local_host_include']),
        ('numeric_integer_semantics', [976],
         ['runtime_signed_div','runtime_signed_rem','runtime_unsigned_wrap',
          'runtime_char_left_shift','runtime_int_shift_mask','runtime_bitwise',
          'runtime_eval_left_to_right','runtime_pointer_int_stride',
          'spec13_numeric_float_storage']),
        ('pointer_domains', [972],
         ['runtime_pointer_int_stride','runtime_pointer_char_stride',
          'runtime_pointer_float_stride','runtime_pointer_distances',
          'runtime_null_equality','spec13_heap_valid_aligned_pointer',
          'spec13_no_implicit_alias_optimizing']),
        ('functions_and_calls', [973],
         ['runtime_pass_by_value','runtime_eval_args','decl_function_two_args',
          'decl_int_main','runtime_main_low_status','spec10_three_float_arguments_preserved']),
        ('operators_and_statements', [975, 978],
         ['spec13_operator_arithmetic_set','spec13_evaluation_precedence',
          'spec8_statement_inventory','spec8_if_then','spec8_if_else',
          'spec8_while','spec8_do_while','spec8_for',
          'runtime_eval_shortcircuit']),
        ('operator_and_token_examples', [833, 968],
         ['spec13_operator_arithmetic_set',
          'spec13_complete_comparison_and_update_tokens',
          'spec13_evaluation_precedence',
          'spec8_decl_punctuation',
          'spec13_reject_unsupported_compound_punctuation',
          'spec8_comment_boundaries']),
        ('arithmetic_boundary_examples', [842],
         ['runtime_char_narrowing','runtime_signed_wrap','runtime_unsigned_wrap',
          'runtime_signed_min','runtime_literal_negative_min',
          'runtime_neg_div','runtime_neg_rem','runtime_char_left_shift',
          'runtime_shift_char_variable','runtime_shift_int_variable',
          'spec13_no_host_promotion_shift']),
        ('complete_pointer_examples', [855],
         ['runtime_pointer_char_stride','runtime_pointer_int_stride',
          'runtime_pointer_float_stride','runtime_pointer_distances',
          'runtime_null_equality','runtime_pointer_subscript',
          'runtime_pointer_double_index','spec6_runtime_increment_and_decrement_pointer',
          'decl_bad_array_address','decl_bad_void_pointer_math',
          'spec13_heap_valid_aligned_pointer']),
        ('diagnostics_command', [1064, 1070],
         ['spec9_default_executable','spec9_source_output_guard',
          'spec9_invalid_source','spec9_missing_output_value',
          'spec9_write_error','decl_bad_duplicate_def',
          'lex_bad_unknown_escape']),
    )
    for ident, paragraphs, required in bundles:
        assert len(required) == len(set(required)), ident
        assert all(c in known for c in required), (ident, [c for c in required if c not in known])
        if ident == 'complete_reserved_inventory':
            assert sum(x.startswith('keyword_reject_') for x in required) >= 25
            assert sum(x.startswith('pp_unsupported_') for x in required) >= 8
        add('spec14_audit_' + ident, paragraphs, 'audit', '',
            extra={'required_cases':required})
