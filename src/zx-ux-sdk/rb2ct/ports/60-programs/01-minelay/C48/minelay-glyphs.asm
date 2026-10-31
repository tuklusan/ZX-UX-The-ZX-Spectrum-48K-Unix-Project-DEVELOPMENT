; Seven original MineLay UDGs from BASIC lines 9010-9040, codes 128..134.
        section data
c48_game_glyphs:
        db 24,36,66,153,153,66,36,24   ; wall 128 (BASIC 144)
        db 28,28,73,62,8,28,20,54      ; player 129 (BASIC 145)
        db 220,220,73,126,72,92,20,54  ; player with axe 130 (BASIC 146)
        db 195,36,24,36,126,90,129,0   ; enemy 131 (BASIC 147)
        db 0,0,0,12,62,126,62,12        ; gold 132 (BASIC 148)
        db 0,0,8,73,42,28,62,127       ; laid mine 133 (BASIC 149)
        db 4,14,6,12,24,48,96,0         ; axe 134 (BASIC 150)
        ds 200
