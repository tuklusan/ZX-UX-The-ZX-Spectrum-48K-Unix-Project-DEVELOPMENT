/* C48 integer arithmetic and shifts: zero means every check passed. */
int main(void) {
    unsigned char a;
    unsigned short b;
    int x;
    a = 255;
    b = 65535u;
    x = 7;
    if (x + 5 != 12) return 1;
    if (x * 3 != 21) return 2;
    if (x / 2 != 3) return 3;
    if (x % 2 != 1) return 4;
    if (a != 255) return 5;
    if (b != 65535u) return 6;
    if ((x << 2) != 28) return 7;
    if ((x >> 1) != 3) return 8;
    return 0;
}
