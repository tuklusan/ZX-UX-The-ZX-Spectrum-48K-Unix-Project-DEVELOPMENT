/* GALAXIANS, program 25 in the historical Spectrum BASIC collection.
 * Experimental C48 translation: uses frozen C48 SDK and shared renderer
 * (generated from shared c48lib and program glyphs).
 * Based on BASIC listing 25-galaxians.bas, lines 10..9500.
 * Z=left, X=right, M=fire.  Menu starts on any key.
 */
#include <c48.h>

#include "../../c48lib/c48lib.h"
static unsigned int rnd_state=917;
static int ship[6];
static int bomb[2];
static int posx;
static int score;
static int highscore;
static int fleetx;
static int fleetdir;
static int bombrow;
static int bombcol;
static int diverrow;
static int divercol;
static int gameover;

static int random_n(int n)
{
    rnd_state=rnd_state ^ (rnd_state << 7);
    rnd_state=rnd_state ^ (rnd_state >> 9);
    rnd_state=rnd_state ^ (rnd_state << 8);
    if (n<=1) return 0;
    return (rnd_state & 32767)%n;
}
static void tile(int row,int col,int ch)
{
    if (row>=0 && row<24 && col>=0 && col<32)
        c48_cell(row,col,ch);
}
static void txt(int row,int col,char *s)
{
    int c;
    c=col;
    while (*s && c<32) {
        tile(row,c,(unsigned char)*s);
        ++s;
        ++c;
    }
}
static void spaces(int row,int col,int n)
{
    int k;
    for (k=0;k<n;k++) tile(row,col+k,' ');
}
static void number(int row,int col,int n)
{
    char buf[7];
    int i;
    int z;
    if (n<0) n=0;
    i=0;
    do { buf[i]='0'+n%10; n=n/10; i++; } while(n>0 && i<6);
    z=0;
    while (i>0) { i--; tile(row,col+z,buf[i]); z++; }
}
static void intro(void)
{
    ink(7); paper(0); border(0); cls();
    txt(0,6,"G A L A X I A N S");
    over(1); txt(0,6,"-----------------"); over(0);
    txt(2,0,"Fleet after fleet, the invaders");
    txt(3,0,"form and wait to attack. Some of");
    txt(4,0,"them dive down to Earth firing");
    txt(5,0,"lasers as they do.");
    txt(7,0,"The invaders in the formation");
    txt(8,0,"drop dangerous bombs to try and");
    txt(9,0,"destroy your laser base. Diving");
    txt(10,0,"invaders are worth more points.");
    txt(12,0,"As soon as 1 fleet of invaders");
    txt(13,0,"have been destroyed their mother-");
    txt(14,0,"ship will arrange a new battle-");
    txt(15,0,"line.");
    txt(17,0,"z = left  x = right  m = fire");
    inverse(1);txt(19,0,"PRESS ANY KEY TO START");inverse(0);
    getchar();
    cls();
}
static void fleet_reset(void)
{
    int i;
    for(i=0;i<6;i++)ship[i]=1;
    fleetx=0;fleetdir=1;
}
static void draw_fleet(int phase)
{
    int i;
    ink(5);
    for(i=0;i<6;i++) {
        if(ship[i]) {
            if(phase) {
                tile(2,fleetx+1+i*3,130);tile(2,fleetx+2+i*3,131);
            } else {
                tile(2,fleetx+1+i*3,128);tile(2,fleetx+2+i*3,129);
            }
        }
    }
    ink(7);
}
static void clear_fleet(void)
{
    spaces(2,fleetx,19);
}
static int defeated(void)
{
    int i;
    for(i=0;i<6;i++)if(ship[i])return 0;
    return 1;
}
static void celebrate(void)
{
    int f,i;
    for(f=0;f<16;f++) {
        /* Clear the previous mothership position before drawing the next. */
        if(f>0)spaces(7,f,3);
        ink(7);tile(7,f+1,136);tile(7,f+2,137);tile(7,f+3,138);
        if(f%3==0) {
            for(i=6;i>=2;i=i-2) {
                ink(5);over(1);tile(i,f+1,128);tile(i,f+2,129);
                beep(0.01,i);
                tile(i,f+1,128);tile(i,f+2,129);over(0);
            }
            tile(2,f+1,128);tile(2,f+2,129);
        }
    }
    spaces(7,1,19); /* no trail left from the first pass */
    for(f=14;f<=26;f=f+2) {
        beep(0.01,-4);
        spaces(7,f,5);tile(7,f+2,136);tile(7,f+3,137);tile(7,f+4,138);
    }
    spaces(7,14,18);
    fleet_reset();
    ink(7);
}
static void print_score(void)
{
    ink(7);txt(0,0,"SCORE:      ");number(0,6,score);
    txt(0,17,"HIGH-SCORE:     ");number(0,28,highscore);
}
static void explosion(int row,int col)
{
    int k;
    ink(6);
    for(k=0;k<3;k++)tile(row,col+k,135);
    for(k=0;k<=15;k=k+5)beep(0.01,k);
    spaces(row,col,3);
    ink(7);
}
static void fire_laser(void)
{
    int sx;
    int i;
    int shipcol;
    int victim;
    sx=posx*8+23;
    /* The BASIC game's plot/draw missile from lines 1000-1140. */
    ink(7);plot(sx,8);draw(sx,8,sx,138);
    beep(0.02,10);
    over(1);plot(sx,8);draw(sx,8,sx,138);over(0);
    /* Check the BASIC cells occupied by the formation and falling pair. */
    if(bombrow>=3 && bombrow<21) {
        victim=-1;
        if(bomb[0] && posx+2>=bombcol+1 && posx+2<=bombcol+2)victim=0;
        if(bomb[1] && posx+2>=bombcol+4 && posx+2<=bombcol+5)victim=1;
        if(victim>=0) {
            bomb[victim]=0;
            score=score+20;
            spaces(bombrow,bombcol+victim*3,3);
            explosion(bombrow,posx+1);
            print_score();
            return;
        }
    }
    shipcol=posx+2;
    for(i=0;i<6;i++) {
        if(ship[i] && (shipcol==fleetx+1+i*3 || shipcol==fleetx+2+i*3)) {
            ship[i]=0;
            score=score+10;
            spaces(2,fleetx+1+i*3,2);
            explosion(2,posx+1);
            print_score();
            if(defeated())celebrate();
            return;
        }
    }
}
static void game_over_msg(void)
{
    int i;
    for(i=1;i<=15;i++) {
        ink(1+random_n(6));
        tile(21,posx+2,135);tile(21,posx+3,135);
        beep(0.05,-random_n(30));
    }
    spaces(21,posx+2,2);
    if(score>highscore)highscore=score;
    ink(7);flash(1);
    txt(10,8,"G A M E  O V E R");
    txt(18,2,"PRESS ANY KEY TO PLAY AGAIN");
    flash(0);
    getchar();
    ink(7);cls();
    gameover=1;
}
static void enemy_fire(void)
{
    int col;
    int y0;
    /* Either of the two descending BASIC sprite bomb locations. */
    if(bomb[0]) col=bombcol+2;
    else if(bomb[1])col=bombcol+4;
    else return;
    y0=(21-bombrow)*8-1;
    ink(3);
    if(y0>=0 && y0<=191) {
        plot(col*8,y0);
        draw(col*8,y0,col*8,9);
        beep(0.001,38);beep(0.001,40);beep(0.001,42);
        over(1);plot(col*8,y0);draw(col*8,y0,col*8,9);over(0);
    }
    ink(7);
    if(col==posx+2 || col==posx+3) game_over_msg();
}
static void round_init(void)
{
    int i;
    posx=15;score=0;
    bombrow=3;
    bombcol=random_n(18);
    diverrow=3;
    divercol=random_n(18);
    bomb[0]=1;bomb[1]=1;
    fleet_reset();
    gameover=0;
    ink(7);cls();
    print_score();
}
static void play(void)
{
    int oldx;
    int i;
    int phase;
    int previous;
    int t;
    round_init();
    oldx=posx;
    phase=0;
    while(!gameover) {
        draw_fleet(phase);
        for(i=0;i<3;i++) {
            if(phase)beep(0.001,40);else beep(0.001,30);
        }
        phase=1-phase;
        if(kbd_down('x') && posx<25)posx=posx+2;
        if(kbd_down('z') && posx>1)posx=posx-2;
        spaces(21,oldx,7);
        ink(7);txt(21,posx,"  ");
        tile(21,posx+2,141);tile(21,posx+3,134);
        txt(21,posx+4,"  ");
        oldx=posx;
        if(kbd_down('m'))fire_laser();
        if(gameover)break;
        clear_fleet();
        fleetx=fleetx+fleetdir;
        if(fleetx==0 || fleetx==13)fleetdir=-fleetdir;
        spaces(bombrow,bombcol,7);
        bombrow=bombrow+1;
        bombcol=bombcol+random_n(4)-random_n(4);
        if(bombcol>25 || bombcol<0)bombcol=12;
        if(bombrow==21) {
            bombrow=3;bomb[0]=1;bomb[1]=1;
        }
        ink(4);
        if(bomb[0]) {tile(bombrow,bombcol+1,132);tile(bombrow,bombcol+2,133);}
        if(bomb[1]) {tile(bombrow,bombcol+4,132);tile(bombrow,bombcol+5,133);}
        ink(7);
        spaces(diverrow,divercol,2);
        diverrow=diverrow+3;
        if(diverrow==21) {
            diverrow=3;
            spaces(21,divercol,2);
            previous=divercol;
            divercol=random_n(17)+1;
            if(previous==posx+1 || previous==posx+2 || previous==posx+3) {
                game_over_msg();
                break;
            }
        }
        tile(diverrow,divercol,139);tile(diverrow,divercol+1,140);
        if(random_n(5)==0 && (bomb[0] || bomb[1]))enemy_fire();
        if(gameover)break;
        t=(int)ticks();rnd_state=rnd_state ^ t;
    }
}
int main(void)
{
    border(0);paper(0);ink(7);cls();
    rnd_state=rnd_state ^ ticks();
    intro();
    highscore=0;
    while(1)play();
    return 0;
}
