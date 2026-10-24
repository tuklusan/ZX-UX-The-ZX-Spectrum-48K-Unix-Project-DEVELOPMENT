# 03-tug-of-war: RBC Round 2

Independent original BAS and tokenized TZX results using the same RBC revision.

- BAS: failed (exit 1); %RBC HIS_UNSUPPORTED Line: 2232 Statement: 2 HiSoft cannot compile this statement or construct. Not supported DIM again, with different sizes | -RBC 2232 IF tb=.002 THEN DIM b$(2,2): LET b$(1)="{94}{95}": LET b$(2)="{96}{97}" |                           ^
- TZX: failed (exit 1); %RBC HIS_UNSUPPORTED Line: 2232 Statement: 2 HiSoft cannot compile this statement or construct. Not supported DIM again, with different sizes | -RBC 2232 IF {74}{62}{3D}{2E}{30}{30}{32}{0E}{78}{03}{12}{6E}{97}THEN DIM {62}{24}({32}{0E}{00}{00}{02}{00}{00}{2C}{32}{0E}{00}{00}{02}{00}{00}):LET {62}{24}({31}{0E}{00}{00}{01}{00}{00}){3D}"{94}{95}":LET {62}{24}({32}{0E}{00}{00}{02}{00}{00}){3D}"{96}{97}" |                                                                       ^
- Comparison: unavailable; at least one path failed or fidelity could not be proved

