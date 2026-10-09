/* runix suite: two cassette programs share the screen and the processor
 * (mtleft draws in columns 0-31, mtright in 32-63) */
#include <c48.h>

char num[6];

void show(int row, int col, unsigned int v)
{
    int i;
    for (i = 4; i >= 0; i--) {
        num[i] = (char)('0' + v % 10u);
        v = v / 10u;
    }
    num[5] = 0;
    print_at(row, col, num);
}

int main(void)
{
    unsigned int i;
    print_at(2, 2, "left running");
    for (i = 0u; i < 700u; i++) {
        show(4, 2, i);
        sleep(4u);
    }
    print_at(6, 2, "left done");
    sleep(50u);
    return 0;
}
