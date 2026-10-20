/* Copyright (c) 2026 SANYALnet Labs.
 * SANYALnet Labs Non-Commercial License applies; see root LICENSE.
 */
/* RUSSIAN ROULETTE, from the supplied 1983 Michael Bews BASIC program.
 * Six chambers, one live chamber, scoring and the original A/B controls.
 * The cylinder and six chambers use ZX-UX's native circle routine.
 */
#include <c48.h>

int chamber;
int score;
int high_score;

void number_at(int row, int col, int value)
{
    char buf[8];
    int i, n;
    n=value; i=6; buf[7]=0;
    do { buf[i--]=(char)('0'+(n%10)); n=n/10; } while (n>0 && i>=0);
    print_at(row, col, buf+i+1);
}

void cylinder(void)
{
    circle(126,119,32);
    circle(146,131,6);
    circle(146,107,6);
    circle(126,95,6);
    circle(106,107,6);
    circle(106,131,6);
    circle(126,143,6);
    circle(126,119,14);
    circle(126,119,13);
    circle(126,119,12);
    draw(126,143,126,47);
}

void show_score(void)
{
    print_at(0,36,"           ");
    print_at(1,36,"           ");
    number_at(0,36,score);
    number_at(1,36,high_score);
}

int main(void)
{
    int c;
    border(0); paper(0); ink(7);
    score=0; high_score=0; chamber=1;
    cls();
    print_at(0,0,"RUSSIAN ROULETTE");
    print_at(0,24,"THIS SCORE:");
    print_at(1,21,"HIGHEST SCORE:");
    cylinder();
    print_at(16,0,"THIS REVOLVER HAS ONE BULLET. IT POINTS AT YOU.");
    print_at(18,0,"PRESS A TO SPIN THE CYLINDER.");
    print_at(19,0,"PRESS B TO FIRE.");
    print_at(20,0,"SCORE 100 FOR EACH TIME YOU SURVIVE.");
    show_score();
    while (1) {
        c=getchar();
        if (c=='a' || c=='A') {
            chamber=chamber%6+1;
            print_at(12,40,"                        ");
            print_at(13,40,"                        ");
            print_at(12,40,"CYLINDER SPINS");
            beep(0.01f, 10.0f);
        } else if (c=='b' || c=='B') {
            print_at(12,40,"                        ");
            print_at(13,40,"                        ");
            if (chamber==1) {
                print_at(12,40,"YOU'RE DEAD!");
                print_at(13,40,"BULLET IN 1");
                if (score>high_score) high_score=score;
                score=0;
                beep(0.08f,-15.0f);
            } else {
                print_at(12,40,"YOU SURVIVED");
                print_at(13,40,"EMPTY CHAMBER");
                score=score+100;
                beep(0.03f,8.0f);
            }
            show_score();
        } else if (c=='q' || c=='Q') return 0;
    }
}
