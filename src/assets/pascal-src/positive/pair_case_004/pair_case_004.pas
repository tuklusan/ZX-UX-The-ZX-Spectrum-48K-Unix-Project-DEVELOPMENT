PROGRAM PC004;
VAR J,S:INTEGER;
BEGIN
  S:=4;
  FOR J:=-3 TO 2 DO
    CASE J OF
      -3,2: S:=S+13;
      -1,1: S:=S+2;
      0: S:=S+7
    END;
  WRITELN('PAIR4=',S);
  CASE S OF
    30: WRITELN('YES');
    99: WRITELN('NO')
  END
END.


