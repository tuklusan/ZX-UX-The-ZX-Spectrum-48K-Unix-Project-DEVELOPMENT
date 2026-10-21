/* Bulls and Cows: gameplay and UDG clues from Robert Erskine's BASIC. */
#include <c48.h>

static unsigned char bull_shape[8] = {0,2,3,255,126,126,66,66};
static unsigned char cow_shape[8] = {0,0,3,255,126,126,66,66};
static int secret[4];
static int guess[4];
static int taken[4];
static int black, white, turn_row;
static char typed[64];
static unsigned int random_state;

static char up(char c) {
    if (c >= 'a' && c <= 'z') return (char)(c - 'a' + 'A');
    return c;
}

static void read_line(char *out, int capacity, int newline) {
    int n = 0, key;
    for (;;) {
        key = getchar();
        if (key == 10 || key == 13) {
            out[n] = 0;
            if (newline) putchar('\n');
            return;
        }
        if (key == 8 || key == 127) {
            if (n) {
                --n;
                putchar(8);
                putchar(' ');
                putchar(8);
            }
        } else if (key >= 32 && key <= 126 && n < capacity - 1) {
            out[n++] = up((char)key);
            putchar(out[n-1]);
        }
    }
}

static int number(char *str) {
    int value = 0, i = 0;
    if (!str[0]) return -1;
    while (str[i]) {
        if (str[i] < '0' || str[i] > '9' || value > 3200) return -1;
        value = value * 10 + str[i] - '0';
        i++;
    }
    return value;
}

static void intro(void) {
    border(7); paper(7); ink(0); cls();
    puts("THE OBJECT OF BULLS AND COWS IS TO GUESS A FOUR");
    puts("DIGIT NUMBER CHOSEN BY THE COMPUTER. AFTER EACH");
    puts("GUESS THE COMPUTER WILL GIVE YOU CLUES; EACH");
    puts("BULL INDICATES A CORRECT DIGIT IN THE CORRECT");
    puts("POSITION AND EACH COW INDICATES A CORRECT DIGIT");
    puts("IN THE WRONG POSITION.");
    print_at(21,8,"PRESS ANY KEY TO START");
    getchar();
}

static void randomize(void) {
    random_state = (unsigned int)(ticks() ^ 0xaaa5);
    if (!random_state) random_state = 0x8765;
}

static int die(void) {
    if (random_state & 1) random_state = (random_state >> 1) ^ 0xb400;
    else random_state = random_state >> 1;
    return (int)(random_state % 9) + 1;
}

static void choose(void) {
    int x;
    randomize();
    for (x = 0; x < 4; ++x) secret[x] = die();
}

static int valid_guess(void) {
    int i;
    if (strlen(typed) != 4) return 0;
    for (i = 0; i < 4; ++i) {
        if (typed[i] < '0' || typed[i] > '9') return -1;
        guess[i] = typed[i] - '0';
    }
    return 1;
}

static void grade(void) {
    int i, j;
    black = 0; white = 0;
    for (i = 0; i < 4; ++i) taken[i] = 0;
    for (i = 0; i < 4; ++i) {
        if (guess[i] == secret[i]) {
            black++;
            taken[i] = 1;
        }
    }
    /* As in the listing, an exact digit is not available to a cow. */
    for (i = 0; i < 4; ++i) {
        for (j = 0; j < 4; ++j) {
            if (guess[i] == secret[j] && !taken[j]) {
                white++;
                taken[j] = 1;
                break;
            }
        }
    }
}

static void clues(void) {
    int j;
    print_at(turn_row, 0, typed);
    for (j = 0; j < black; ++j) {
        /* UDG columns are 8 pixels, print_at headings use 4-pixel columns.
           Put black bulls on yellow cells so they remain visible on blue. */
        paper(6); ink(0); udg_draw(0, turn_row, 9+j); beep(.1,25);
    }
    for (j = 0; j < white; ++j) {
        paper(1); ink(7); udg_draw(1, turn_row, 18+j); beep(.1,25);
    }
    if (turn_row < 21) turn_row++;
    else {
        cursor_at(21,0);
        putchar('\n');
    }
    paper(1); ink(7);
}

static void result(void) {
    int i;
    cls();
    if (black == 4) {
        puts("YOU ARE CORRECT. THE NUMBER");
        puts("I CHOSE WAS ");
    } else {
        puts("THAT WAS NOT VERY GOOD. THE");
        puts("NUMBER I CHOSE WAS ");
    }
    for (i=0; i<4; ++i) putchar('0'+secret[i]);
    puts("");
    puts("");
    puts("AND YOU GUESSED");
    for (i=0; i<4; ++i) putchar('0'+guess[i]);
    putchar('\n');
    print_at(21,8,"PRESS ANY KEY TO RESTART");
    getchar();
}

static void game(void) {
    int tries, trial, valid;
    border(7); paper(7); ink(0); cls();
    puts("HOW MANY GUESSES DO YOU WANT?");
    do {
        read_line(typed, 64, 1);
        tries = number(typed);
        if (tries < 1) puts("ENTER A POSITIVE WHOLE NUMBER");
    } while (tries < 1);
    choose();
    cls();
    puts("I HAVE CHOSEN A NUMBER");
    sleep(100);
    border(0); paper(1); ink(7); cls();
    print_at(0,0,"GUESSES           BULLS            COWS");
    turn_row = 2;
    for (trial=0; trial < tries; ++trial) {
        for (;;) {
            print_at(22,0,"ENTER YOUR GUESS NOW (4 DIGITS)");
            cursor_at(23,0);
            read_line(typed,64,0);
            valid = valid_guess();
            if (valid == 1) break;
            if (valid == 0) print_at(22,0,"REINPUT CORRECTLY!!             ");
            else print_at(22,0,"NUMBERS ONLY!!                 ");
            flash(1); sleep(60); flash(0);
            print_at(22,0,"                                ");
            print_at(23,0,"                                ");
        }
        print_at(22,0,"                                ");
        print_at(23,0,"                                ");
        grade();
        clues();
        if (black == 4) break;
    }
    sleep(100);
    result();
}

int main(void) {
    udg_define(0,bull_shape);
    udg_define(1,cow_shape);
    intro();
    for (;;) game();
    return 0;
}
