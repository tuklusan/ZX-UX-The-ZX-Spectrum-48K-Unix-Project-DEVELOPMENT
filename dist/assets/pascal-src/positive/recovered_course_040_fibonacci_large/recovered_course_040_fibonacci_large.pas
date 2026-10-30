{ SPDX-License-Identifier: BSD-3-Clause
  Adapted from modern-pascal/modern-pascal-course
  040_fibonacci_large/fibonacci_large.dpr.
  Uses INTEGER instead of UInt64 and reduces 0..1000 to 0..23,
  output to F(23), the last representable positive 16-bit value.
  Removed SysUtils, Delphi assertions, platform directives and READLN.
  This changes the output range; it does not preserve 64-bit behavior.
}
PROGRAM FIBLARGE;
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
