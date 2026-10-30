PROGRAM FIVECASE;
VAR I, N: INTEGER;
BEGIN
  N := 0;
  FOR I := -4 TO 4 DO
    CASE I OF
      -4, 4: N := N + 5;
      -3, 3: N := N + 7;
      -2, 2: N := N + 9;
      -1, 1: N := N + 11;
      0: N := N + 13
    END;
  WRITELN('FIVE=', N);
  CASE N OF
    77: WRITELN('PASS');
    78: WRITELN('FAIL')
  END
END.
