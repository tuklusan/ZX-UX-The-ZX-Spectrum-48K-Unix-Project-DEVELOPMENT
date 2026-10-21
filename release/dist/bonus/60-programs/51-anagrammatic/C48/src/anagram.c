/* Anagrammatic: permutation order and all-length output from H. Nywalw's BASIC. */
#include <c48.h>

#define MAX_LETTERS 255
static char letters[MAX_LETTERS + 1];
static char known[512];
static char line[66];
static int chosen[MAX_LETTERS + 1];
static int nextidx[MAX_LETTERS + 1];
static int used[MAX_LETTERS];
static char permutation[MAX_LETTERS + 1];

static void error(void)
{
    ink(2);
    bright(1);
    flash(1);
    puts("E R R O R! PLEASE REDO.......");
    flash(0);
    bright(0);
    ink(0);
}

static char uppercase(char c)
{
    if (c >= 'a' && c <= 'z') return (char)(c - 'a' + 'A');
    return c;
}

/* A BASIC INPUT line, with visible editing despite raw ZX-UX keyboard mode. */
static void input_line(char *out, int capacity)
{
    int n, key;
    n = 0;
    for (;;) {
        key = getchar();
        if (key < 0) continue;
        if (key == 10 || key == 13) {
            out[n] = 0;
            putchar('\n');
            return;
        }
        if (key == 8 || key == 127) {
            if (n > 0) {
                n = n - 1;
                putchar(8);
                putchar(' ');
                putchar(8);
            }
            continue;
        }
        if (key >= 32 && key <= 126 && n < capacity - 1) {
            out[n] = uppercase((char)key);
            n = n + 1;
            putchar(out[n - 1]);
        }
    }
}

static int number(char *s)
{
    int i, result;
    i = 0;
    result = 0;
    if (s[0] == 0) return -1;
    while (s[i]) {
        if (s[i] < '0' || s[i] > '9' || result > 255) return -1;
        result = result * 10 + (s[i] - '0');
        i = i + 1;
    }
    return result;
}

static void print_arrange(int length)
{
    int a, i;
    a = 0;
    i = 0;
    while (known[i]) {
        if (known[i] == '-') {
            if (a < length) putchar(permutation[a]);
            else putchar(' ');
            a = a + 1;
        } else putchar(known[i]);
        i = i + 1;
    }
    putchar('\n');
    sleep(3); /* BASIC prints while the hardware scrolls; allow visible motion. */
}

static void enumerate(int size, int length)
{
    int depth, candidate, i;
    i = 0;
    while (i < MAX_LETTERS) {
        used[i] = 0;
        i = i + 1;
    }
    depth = 0;
    nextidx[0] = 0;
    while (depth >= 0) {
        if (depth == length) {
            print_arrange(length);
            depth = depth - 1;
            if (depth >= 0) used[chosen[depth]] = 0;
            continue;
        }
        candidate = nextidx[depth];
        while (candidate < size && used[candidate]) candidate = candidate + 1;
        if (candidate == size) {
            depth = depth - 1;
            if (depth >= 0) used[chosen[depth]] = 0;
            continue;
        }
        chosen[depth] = candidate;
        nextidx[depth] = candidate + 1;
        used[candidate] = 1;
        permutation[depth] = letters[candidate];
        depth = depth + 1;
        nextidx[depth] = 0;
    }
}

static void run_once(void)
{
    int length, kcount, first, i, key, yes;
    border(5);
    paper(5);
    ink(0);
    cls();
    bright(1);
    inverse(1);
    puts("          ANAGRAMMATIC");
    inverse(0);
    bright(0);
    puts("");
    puts("IF YOU ARE A CROSSWORD ADDICT, THEN YOU WILL KNOW");
    puts("THE PROBLEMS OF TRYING TO REARRANGE LETTERS.");
    puts("");
    puts("FOLLOW THE INSTRUCTIONS AND THEN SIT BACK AND WATCH");
    puts("THE SCREEN AS EVERY POSSIBLE COMBINATION RUNS UP");
    puts("BEFORE YOUR VERY EYES. THE AIM IS NOT TO LOOK AT");
    puts("EVERY WORD GROUP, BUT SIMPLY TO GLANCE AT THE");
    puts("SCREEN OCCASIONALLY AND YOU MAY WELL GET SOME");
    puts("INSPIRATION.");
    puts("");
    puts("ALTERNATIVELY, PUT IN A PRINTER SUBROUTINE");
    puts("FOR HARD COPY.");
    puts("PRESS ANY KEY TO START.");
    key = getchar();
    border(4);
    paper(4);
    ink(0);
    cls();
    puts("     ANAGRAMMATIC");
    puts("");
    puts("TYPE ONLY THOSE LETTERS WHICH ARE TO BE");
    puts("REARRANGED. DO NOT INPUT ANY LETTERS WHOSE");
    puts("POSITION IS KNOWN.");
    for (;;) {
        input_line(letters, MAX_LETTERS + 1);
        length = strlen(letters);
        if (length > 0 && length <= MAX_LETTERS) break;
        error();
    }
    puts("");
    puts("ARE ANY LETTERS/SPACES KNOWN?");
    puts("PRESS Y (YES) OR N (NO)");
    yes = 0;
    for (;;) {
        key = uppercase((char)getchar());
        if (key == 'Y' || key == 'N') {
            putchar(key);
            putchar('\n');
            yes = key == 'Y';
            break;
        }
    }
    if (yes) {
        puts("TYPE IN THE KNOWN ORDER AS PER EXAMPLE.");
        puts("E.G. '---D-F- -EE'");
        for (;;) {
            input_line(known, 512);
            kcount = 0;
            i = 0;
            while (known[i]) {
                if (known[i] == '-') kcount = kcount + 1;
                i = i + 1;
            }
            if (kcount == length) break;
            error();
        }
        first = length;
    } else {
        i = 0;
        while (i < length) {
            known[i] = '-';
            i = i + 1;
        }
        known[length] = 0;
        for (;;) {
            puts("NUMBER OF LETTERS TO BEGIN");
            input_line(line, 66);
            first = number(line);
            if (first >= 1 && first <= length) break;
            error();
        }
    }
    /* BASIC PRINT AT 21,0 then POKE 23692,-1: begin at the bottom.
       Subsequent rows must scroll the actual framebuffer, not recycle text. */
    puts("-------------------------------");
    cursor_at(21, 0);
    putchar(' ');
    putchar('\n');
    i = first;
    while (i <= length) {
        enumerate(length, i);
        i = i + 1;
    }
    puts("");
    puts("THAT'S ALL THE POSSIBLE ANAGRAMS WRITTEN.");
    puts("TYPE RUN FOR ANOTHER GO.");
}

int main(void)
{
    int key;
    for (;;) {
        run_once();
        /* BASIC STOP leaves its last screen intact; do not erase it by
           returning to the ZX-UX shell before the user has seen it. */
        for (;;) {
            key = uppercase((char)getchar());
            if (key == 'R' || key == 'Q') break;
        }
        if (key == 'Q') return 0;
    }
}
