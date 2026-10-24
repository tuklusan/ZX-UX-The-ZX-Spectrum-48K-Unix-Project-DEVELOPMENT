# 27-picture-pairs: RBC Round 2

Independent original BAS and tokenized TZX results using the same RBC revision.

- BAS: failed (exit 1); %RBC RBC_USR_MACHINE_CODE Line: 70 Statement: 1 Executable USR machine-code calls are prohibited in ZX-UX BASIC programs. ZX-UX memory check stopped line 70: USR raw_machine_code_address. 1 blocked operation(s); use --memory-policy review only for isolated tests | -RBC   70 POKE USR CHR$ (143+M)+L,A(CODE G$(K)-64,L*9+M) |                ^
- TZX: failed (exit 1); %RBC RBC_USR_MACHINE_CODE Line: 70 Statement: 1 Executable USR machine-code calls are prohibited in ZX-UX BASIC programs. ZX-UX memory check stopped line 70: USR raw_machine_code_address. 1 blocked operation(s); use --memory-policy review only for isolated tests | -RBC 70 POKE USR CHR$ ({31}{34}{33}{0E}{00}{00}{8F}{00}{00}{2B}{4D}){2B}{4C}{2C}{41}(CODE {47}{24}({4B}){2D}{36}{34}{0E}{00}{00}{40}{00}{00}{2C}{4C}{2A}{39}{0E}{00}{00}{09}{00}{00}{2B}{4D}) |              ^
- Comparison: unavailable; at least one path failed or fidelity could not be proved

