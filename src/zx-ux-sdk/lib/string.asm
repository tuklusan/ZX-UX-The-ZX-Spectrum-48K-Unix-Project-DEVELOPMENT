; rcc runtime: <string> functions                           (ZX-UX SDK)
        section text
        global _strlen,_strcmp,_strcpy,_strncpy,_memcpy,_memmove,_memchr,_memset
; unsigned strlen(char *s)
_strlen:
        xor a
        ld b,a
        ld c,a
        ld d,h
        ld e,l
        cpir
        or a
        sbc hl,de
        dec hl
        ret
; int strcmp(char *a, char *b): -1, 0, 1
_strcmp:
        pop bc
        pop de                  ; a
        push bc
.l:     ld a,(de)
        cp (hl)
        j nz,.d
        or a
        j z,.eq
        inc de
        inc hl
        j .l
.eq:    ld hl,0
        ret
.d:     ld hl,1
        ret nc
        ld hl,-1
        ret
; char *strcpy(char *d, char *s)
_strcpy:
        pop bc
        pop de
        push bc
        push de
.l:     ld a,(hl)
        ld (de),a
        inc hl
        inc de
        or a
        j nz,.l
        pop hl
        ret
; char *strncpy(char *d, char *s, unsigned n)
_strncpy:
        ld b,h
        ld c,l                  ; BC = n
        pop hl
        pop de                  ; s
        ex (sp),hl              ; HL = d, ret on stack
        push hl
        ex de,hl                ; HL = s, DE = d
.l:     ld a,b
        or c
        j z,.x
        ld a,(hl)
        ld (de),a
        inc de
        dec bc
        or a
        j z,.z
        inc hl
        j .l
.z:     ld a,b                  ; pad with NULs
        or c
        j z,.x
        xor a
        ld (de),a
        inc de
        dec bc
        j .z
.x:     pop hl
        ret
; void *memcpy(void *d, void *s, unsigned n)   (memmove semantics)
_memcpy:
_memmove:
        ld b,h
        ld c,l
        pop hl
        pop de                  ; s
        ex (sp),hl              ; HL = d
        push hl
        ld a,b
        or c
        j z,.x
        ex de,hl                ; HL = s, DE = d
        push hl
        or a
        sbc hl,de
        pop hl
        j c,.back              ; s < d: copy from the end
        ldir
        j .x
.back:  add hl,bc
        dec hl
        ex de,hl
        add hl,bc
        dec hl
        ex de,hl
        lddr
.x:     pop hl
        ret
; void *memchr(void *p, int c, unsigned n)
_memchr:
        ld b,h
        ld c,l
        pop hl
        pop de                  ; c
        ex (sp),hl              ; HL = p
        ld a,b
        or c
        j z,.no
        ld a,e
        cpir
        j nz,.no
        dec hl
        ret
.no:    ld hl,0
        ret
; void *memset(void *p, int c, unsigned n)
_memset:
        ld b,h
        ld c,l
        pop hl
        pop de                  ; c
        ex (sp),hl              ; HL = p
        ld a,b
        or c
        ret z
        push hl
.l:     ld (hl),e
        inc hl
        dec bc
        ld a,b
        or c
        j nz,.l
        pop hl
        ret
