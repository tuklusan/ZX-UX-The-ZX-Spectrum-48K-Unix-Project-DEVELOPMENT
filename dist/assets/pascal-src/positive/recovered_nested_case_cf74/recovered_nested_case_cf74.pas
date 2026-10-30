PROGRAM NESTEDCASE;
VAR C: CHAR; N: INTEGER;
BEGIN
  C := 'Z';
  N := 0;
  CASE C OF
    'X': N := 1;
    'Z': BEGIN
      CASE 32767 OF
        -32767: N := 2;
         32767: N := 3
      END
    END
  END;
  WRITELN('NEST=', N)
END.
