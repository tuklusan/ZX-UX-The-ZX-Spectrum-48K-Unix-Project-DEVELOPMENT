C     BZ changes blanks in integer input to zeros; BN ignores them.
      PROGRAM BNBZ
      INTEGER A,B
      READ(5,10) A,B
   10 FORMAT(BZ,I5,BN,I5)
      WRITE(6,20) A,B
   20 FORMAT(2I5)
      END
