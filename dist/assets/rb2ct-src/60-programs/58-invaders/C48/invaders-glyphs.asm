; Original Invaders BASIC DATA lines 1030-1090, unmodified sprite bytes.
; 128-140 follow code assignments below.  142-159 are blank.
        section data
c48_game_glyphs:
        db 60,140,115,51,63,111,193,192   ; 128 alien left
        db 60,49,206,204,252,246,131,3   ; 129 alien right
        db 27,31,26,62,255,255,85,42   ; 130 rocket left
        db 224,240,88,124,255,255,170,84   ; 131 rocket right
        db 0,0,7,31,248,127,0,0   ; 132 ship1
        db 0,63,240,191,0,255,127,0   ; 133 ship2
        db 126,255,0,195,255,129,255,60   ; 134 ship3
        db 0,252,15,253,0,255,254,0   ; 135 ship4
        db 0,0,224,248,31,254,0,0   ; 136 ship5
        db 255,126,255,126,255,126,255,0   ; 137 shield1
        db 255,0,255,0,255,0,255,0   ; 138 shield2
        db 255,126,255,126,255,126,255,0   ; 139 shield3
        db 0,82,24,124,62,24,74,0   ; 140 explosion
        db 0,16,16,16,16,16,16,0   ; 141 visible upward rocket
        ds 144
