/* Russian Roulette, after the 1983 BASIC listing by Michael Bews. */
#include <c48.h>

static int hole_x[6] = {146,146,126,106,106,126};
static int hole_y[6] = {147,123,111,123,147,159};
static int chamber = 1;
static int score = 0;
static int best = 0;
static int showing = 0;
static int spun = 0;

static void decimal(int v, char *dst)
{
    char backwards[8];
    int n = 0;
    int i;
    if (!v) backwards[n++] = '0';
    while (v > 0 && n < 7) {
        backwards[n++] = (char)('0' + v % 10);
        v = v / 10;
    }
    for (i = 0; i < n; ++i) dst[i] = backwards[n - i - 1];
    dst[n] = 0;
}

static void value_at(int row, int col, int number)
{
    char text[8];
    print_at(row, col, "       ");
    decimal(number, text);
    print_at(row, col, text);
}

static void scores(void)
{
    inverse(0);
    ink(7);
    paper(0);
    print_at(0, 36, "THIS SCORE:");
    print_at(1, 30, "HIGHEST SCORE:");
    value_at(0, 57, score);
    value_at(1, 57, best);
    inverse(0);
}

static void clear_result(void)
{
    ink(7);
    paper(0);
    flash(0);
    print_at(6, 30, "    ");
    print_at(7, 30, "    ");
    print_at(12, 39, "                       ");
    print_at(14, 39, "                       ");
}

static void picture(void)
{
    int i, x, y;
    border(0);
    ink(7);
    paper(0);
    cls();
    paper(2);
    print_at(0, 0, "RUSSIAN ROULETTE");
    paper(0);
    circle(126, 135, 32);
    for (i = 0; i < 6; ++i) circle(hole_x[i], hole_y[i], 6);
    circle(126, 135, 14);
    circle(126, 135, 13);
    circle(126, 135, 12);
    /* BASIC's two adjacent solid UDG characters, in five text rows. */
    for (y = 64; y < 104; ++y)
        for (x = 120; x < 136; ++x)
            plot(x, y);
    paper(1);
    ink(7);
    print_at(16, 0, "THIS IS A REVOLVER, POINTING AT YOU. IT HAS ONE BULLET.");
    print_at(17, 0, "PRESS 'A' TO SPIN THE CYLINDER FOR AS LONG AS YOU WISH");
    print_at(18, 0, "AND FIRE WITH 'B'. SCORE 100 EACH TIME THE GUN FAILS");
    print_at(19, 0, "TO KILL YOU, THEN TRY AGAIN");
    paper(0);
    scores();
}

static void marker(void)
{
    /* The BASIC PLOT OVER 1 changes one pixel inside the active hole. */
    over(1);
    plot(hole_x[chamber - 1], hole_y[chamber - 1]);
    over(0);
}

static void rotate(void)
{
    if (spun) marker();
    if (!spun) chamber = 1;
    else chamber = (chamber % 6) + 1;
    spun = 1;
    marker();
}

static void fire(void)
{
    clear_result();
    beep(.002, 30);
    ink(7);
    paper(0);
    if (chamber == 1) {
        paper(7);
        ink(2);
        flash(1);
        print_at(6, 30, "    ");
        print_at(7, 30, "    ");
        paper(0);
        ink(7);
        flash(0);
        print_at(12, 39, "YOU'RE DEAD!");
        print_at(14, 39, "BULLET IN 1");
        if (score > best) best = score;
        score = 0;
        scores();
        beep(.1, 1);
        beep(.1, 1);
        beep(.1, 0);
        beep(.1, 1);
        showing = 2;
    } else {
        print_at(12, 39, "YOU SURVIVED");
        print_at(14, 39, "BULLET IN ");
        value_at(14, 59, chamber);
        score = score + 100;
        scores();
        beep(.1, 8);
        beep(.1, 5);
        beep(.1, 1);
        showing = 1;
    }
}

int main(void)
{
    int a = 0;
    int b = 0;
    picture();
    while (1) {
        int now_a;
        int now_b;
        now_a = kbd_down('a');
        now_b = kbd_down('b');
        if (now_a && !now_b) {
            if (showing) {
                clear_result();
                showing = 0;
            }
            rotate();
            beep(.002, 30);
            sleep(3);
        } else if (now_b && !b) {
            fire();
        }
        if (showing == 2 && !now_b && b) {
            if (spun) marker();
            chamber = 1;
            spun = 0;
        }
        a = now_a;
        b = now_b;
        sleep(1);
    }
    return 0;
}
