/* C48 grouped runtime conformance: return zero on success. */
int ck_arith(void) {
    int a;
    a = 7;
    return a + 5 == 12 && a * 3 == 21 && a / 2 == 3 && a % 2 == 1;
}
int ck_array(void) {
    int a[3];
    a[0] = 4;
    a[1] = 5;
    a[2] = 6;
    return a[0] + a[1] + a[2] == 15;
}
int ck_loops(void) {
    int i, sum;
    sum = 0;
    for (i = 0; i < 5; i++) sum = sum + i;
    return sum == 10;
}
int ck_calls(int a, int b) { return a * 10 + b; }
int main(void) {
    if (!ck_arith()) return 1;
    if (!ck_array()) return 2;
    if (!ck_loops()) return 3;
    if (ck_calls(4, 2) != 42) return 4;
    return 0;
}
