/* runix suite: an SSX1 program from tape gets its arguments, prints
 * through the console and ends with a status */
#include <c48.h>

int main(int argc, char **argv)
{
    int i;
    print_at(2, 0, "ssx args:");
    for (i = 0; i < argc; i++)
        print_at(i + 3, 2, argv[i]);
    return argc;
}
