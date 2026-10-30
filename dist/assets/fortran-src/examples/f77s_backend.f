C     BACKSPACE across ENDFILE marker and preceding INTEGER records.
      PROGRAM BEF
      INTEGER A,B,C
      A=17
      B=-42
      WRITE(7) A
      WRITE(7) B
      ENDFILE 7
      BACKSPACE 7
      BACKSPACE 7
      READ(7) C
      WRITE(6,10) C
   10 FORMAT(I5)
      END
