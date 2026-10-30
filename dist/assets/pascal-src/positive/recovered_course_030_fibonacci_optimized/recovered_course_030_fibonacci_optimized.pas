{ SPDX-License-Identifier: BSD-3-Clause
  Adapted from modern-pascal/modern-pascal-course
  030_fibonacci_optimized/fibonacci_optimized.dpr.
  Restricts array to 0..23 and stops at F(23), the last Fibonacci
  value <= 32767: original code used wider integers and computed F(40).
  Removes Delphi platform directives and terminal pause.
  Shortened long names after authentic HiSoft v1 compilation rejected them.
}
PROGRAM FIBOPT;
VAR FIBO: ARRAY [0..23] OF INTEGER;
    I: INTEGER;
BEGIN
  FIBO[0] := 0;
  FIBO[1] := 1;
  FOR I := 2 TO 23 DO
  BEGIN
    FIBO[I] := FIBO[I-1] + FIBO[I-2];
    WRITELN('Fibonacci(', I, ') = ', FIBO[I])
  END
END.
