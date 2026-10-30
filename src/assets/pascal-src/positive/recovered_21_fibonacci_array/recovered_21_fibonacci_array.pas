{ SPDX-License-Identifier: BSD-3-Clause
  Adapted from modern-pascal/modern-pascal-course
  030_fibonacci_optimized/fibonacci_optimized.dpr.
  Restricts array to 0..23 and stops at F(23), the last Fibonacci
  value <= 32767: original code used wider integers and computed F(40).
  Removes Delphi platform directives and terminal pause.
  Shortened long names after authentic HiSoft v1 compilation rejected them.
}
PROGRAM RUN21;
VAR ARR: ARRAY [0..20] OF INTEGER;
    K: INTEGER;
BEGIN
  ARR[0] := 0;
  ARR[1] := 1;
  FOR K := 2 TO 20 DO
  BEGIN
    ARR[K] := ARR[K-1] + ARR[K-2];
    WRITELN('Series(', K, ') = ', ARR[K])
  END
END.
