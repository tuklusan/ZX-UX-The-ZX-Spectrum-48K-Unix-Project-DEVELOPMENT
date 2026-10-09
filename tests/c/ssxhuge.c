/* runix suite: a program that cannot fit at all */
#include <c48.h>

char huge[20000];

int main(void)
{
    huge[0] = 1;
    return huge[0];
}
