/* runix suite: a program bigger than the free arena - the kernel lends it
 * the window while it runs */
#include <c48.h>

char big[11000];

int main(void)
{
    unsigned int i;
    unsigned int sum;
    memset(big, 3, 11000);
    sum = 0;
    for (i = 0; i < 11000; i = i + 1)
        sum = sum + big[i];
    if (sum == 33000)
        print_at(2, 2, "big ok");
    else
        print_at(2, 2, "big bad");
    getchar();
    return 0;
}
