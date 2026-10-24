# 16-snap: RBC Round 2

Independent original BAS and tokenized TZX results using the same RBC revision.

- BAS: failed (exit 1); %RBC RBC_USR_MACHINE_CODE Line: 70 Statement: 1 Executable USR machine-code calls are prohibited in ZX-UX BASIC programs. ZX-UX memory check stopped line 70: USR raw_machine_code_address. 2 blocked operation(s); use --memory-policy review only for isolated tests | -RBC   70 POKE USR CHR$ (143+M)+L,A(K,L*9+M) |                ^
- TZX: failed (exit 1); %RBC RBC_USR_MACHINE_CODE Line: 70 Statement: 1 Executable USR machine-code calls are prohibited in ZX-UX BASIC programs. ZX-UX memory check stopped line 70: USR raw_machine_code_address. 2 blocked operation(s); use --memory-policy review only for isolated tests | -RBC   70 POKE USR CHR$ (143+M)+L,A(K,L*9+M) |                ^
- Comparison: unavailable; at least one path failed or fidelity could not be proved

