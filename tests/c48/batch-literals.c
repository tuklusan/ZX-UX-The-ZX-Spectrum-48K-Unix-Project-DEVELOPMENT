/* Independent runtime assertions for C48 byte string rules. */
int main(void) {
    char *a;
    char *b;
    a = "ab" "cd";
    b = "abcd";
    if (sizeof("abc") != 4) return 1;
    if (sizeof("ab" "cd") != 5) return 2;
    if (a[0] != 'a' || a[3] != 'd' || a[4] != 0) return 3;
    if (a == b) return 4;
    return 0;
}
