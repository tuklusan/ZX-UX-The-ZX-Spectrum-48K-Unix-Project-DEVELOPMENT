PROGRAM MATRIX2;
VAR J,S:INTEGER;
BEGIN
  S:=1;
  FOR J:=-3 TO 2 DO
    CASE J OF
      -3,2: S:=S+13;
      -1,1: S:=S+2;
      0: S:=S+7
    END;
  WRITELN('SCORE=',S);
  CASE S OF
    30: WRITELN('YES');
    99: WRITELN('NO')
  END
END.
