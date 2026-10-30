PROGRAM FOURCASE;
VAR I, N: INTEGER;
BEGIN
  N := 0;
  FOR I := -3 TO 3 DO
    CASE I OF
      -3, 3: N := N + 9;
      -2, 2: N := N + 7;
      -1, 1: N := N + 5;
      0: N := N + 11
    END;
  WRITELN('FOUR=', N);
  CASE N OF
    53: WRITELN('PASS');
    54: WRITELN('FAIL')
  END
END.
