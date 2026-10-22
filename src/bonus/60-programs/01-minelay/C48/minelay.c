/* MINELAY, historical program 01: C48 translation of 01-minelay.bas.
 * Q up, Z down, I left, P right. 1 hard, 2 easy.
 * Frozen ZX-UX C48 SDK and c48lib full-width renderer.
 */
#include <c48.h>
#include "../../c48lib/c48lib.h"

static unsigned char board[768];
static unsigned char attr[768];
static unsigned int seed=31147;
static int x,y,last_x,last_y,mx2,my2,old_mx,old_my;
static int score,highscore,lives,has_axe,hard,gameover;

static int rnd(int n)
{
    seed=seed^(seed<<7);
    seed=seed^(seed>>9);
    seed=seed^(seed<<8);
    if(n<2)return 0;
    return (seed&32767)%n;
}
static void at_cell(int r,int c,int glyph,int fg,int bright_on)
{
    int i;
    if(r<0||r>23||c<0||c>31)return;
    ink(fg);bright(bright_on);
    c48_cell(r,c,glyph);
    i=r*32+c;
    board[i]=glyph;
    attr[i]=fg+(bright_on*64);
}
static int get_attr(int r,int c)
{
    if(r<0||r>23||c<0||c>31)return 7;
    return attr[r*32+c];
}
static void blank(int r,int c) { at_cell(r,c,32,7,0); }
static void line(int r,int c,char *s,int fg)
{
    while(*s&&c<32){at_cell(r,c,*s,fg,0);c++;s++;}
}
static void digits(int row,int col,int n)
{
    char b[8];int k=0,i;
    if(n<0){at_cell(row,col,'-',7,0);col++;n=-n;}
    do{b[k]='0'+n%10;k++;n=n/10;}while(n>0&&k<7);
    for(i=k-1;i>=0;i--)at_cell(row,col++,b[i],7,0);
}
static void full_clear(void)
{
    int i;
    paper(0);ink(7);bright(0);border(0);cls();
    for(i=0;i<768;i++){board[i]=32;attr[i]=7;}
}
static void fresh_key(void)
{
    while(c48_any_key())sleep(1);
    while(!c48_any_key())sleep(1);
    while(c48_any_key())sleep(1);
}
static unsigned char tty[6];
static void game_keyboard(void)
{
    if(gtty(0,tty)>=0){tty[4]=32;stty(0,tty);}
}
static void status_line(void)
{
    int c;
    line(0,0,"Score       ",7);digits(0,6,score);
    for(c=13;c<32;c++)blank(0,c);
    for(c=0;c<lives&&c<6;c++)at_cell(0,13+c,129,7,0);
    line(0,19,"Hi-score",7);digits(0,28,highscore);
}
static void intro(void)
{
    full_clear();
    line(1,8,"M I N E L A Y",7);
    line(4,0,"Move about the maze picking up",7);
    line(5,0,"golden eggs, avoiding the mines",7);
    line(6,0,"and also the mine-layer.",7);
    line(8,0,"If you pick up an axe you can",6);
    line(9,0,"destroy maze walls, mines and",6);
    line(10,0,"the mine-layer.",6);
    line(12,0,"You begin with 3 lives; an",7);
    line(13,0,"extra life every 500 points.",7);
    line(16,0,"Q.....UP      Z.....DOWN",6);
    line(17,0,"I.....LEFT    P.....RIGHT",5);
    line(20,0,"Press any key to start...",7);
    fresh_key();
}
static void menu(void)
{
    int i;
    full_clear();
    if(gameover){
        line(5,8,"G A M E  O V E R",7);
        line(8,7,"You scored",5);digits(8,18,score);
        if(score>highscore)highscore=score;
        line(10,2,"The high-score is",7);digits(10,22,highscore);
    }
    line(13,1,"Press 1 for a hard game",6);
    line(15,1,"or 2 for an easier game",6);
    while(c48_any_key())sleep(1);
    while(1){
        if(kbd_down('1')){hard=1;break;}
        if(kbd_down('2')){hard=0;break;}
        sleep(1);
    }
    while(c48_any_key())sleep(1);
    for(i=0;i<4;i++)beep(0.004,i);
}
static void respawn_mine(void)
{
    my2=(10+rnd(11))*2;
    mx2=(12+rnd(18))*2;
    old_my=my2/2;old_mx=mx2/2;
}
static void make_maze(void)
{
    int i,k,r,s,e,c,passes;
    full_clear();
    for(i=1;i<=21;i++)at_cell(i,0,128,7,0);
    /* Original BASIC lines 7000/7010 also repeatedly draw these cells. */
    at_cell(4,30,128,7,0);
    at_cell(1,4,128,7,0);at_cell(21,4,128,7,0);
    passes=7;if(hard)passes=14;
    for(k=0;k<passes;k++) {
        s=rnd(28);e=s+rnd(10);if(e>29)e=29;
        r=rnd(9)*2+1;
        for(i=s;i<=e;i++)at_cell(r,i,128,7,0);
        s=rnd(18)+2;e=s+rnd(10);if(e>20)e=20;
        c=rnd(14)*2+2;
        for(i=s;i<=e;i++)at_cell(i,c,128,7,0);
    }
    /* BASIC lines 7410 and 7520 retry when SCREEN$ is empty for a UDG.
     * Do not replace pre-existing walls, eggs, mines or axes. */
    for(k=0;k<20;k++){
        do {r=rnd(18)+2;c=rnd(28)+1;}
        while(board[r*32+c]>=128);
        at_cell(r,c,132,6,1);
    }
    for(k=0;k<10;k++){
        do {r=rnd(18)+2;c=rnd(28)+1;}
        while(board[r*32+c]>=128);
        at_cell(r,c,133,5,0);
    }
    for(k=0;k<5;k++)at_cell(rnd(18)+2,rnd(28)+1,134,4,1);
    x=1;y=2;last_x=x;last_y=y;
    respawn_mine();score=0;lives=3;has_axe=0;gameover=0;
    status_line();
}
static void lose_life(void)
{
    int i;
    if(has_axe){has_axe=0;beep(0.05,15);respawn_mine();return;}
    for(i=7;i>=0;i--){at_cell(y,x,129,i,0);beep(0.01,i);}
    lives--;
    if(lives<=0){gameover=1;return;}
    blank(y,x);x=1;y=2;last_x=x;last_y=y;
    respawn_mine();status_line();
}
static void player_step(void)
{
    int nx,ny,a;
    nx=x;ny=y;
    if(kbd_down('p'))nx++;
    if(kbd_down('i'))nx--;
    if(kbd_down('z'))ny++;
    if(kbd_down('q'))ny--;
    if(nx<0||nx>30||ny<1||ny>21){nx=x;ny=y;}
    blank(last_y,last_x);
    a=get_attr(ny,nx);
    if(a==7 && board[ny*32+nx]!=32){
        if(has_axe && ny!=1 && ny!=21 && nx!=0 && nx!=30){
            blank(ny,nx);has_axe=0;beep(0.01,20);
        }else {nx=x;ny=y;}
    }
    if(a==70){score=score+10;beep(0.01,20);if(score%500==0)lives++;}
    if(a==68){has_axe=1;beep(0.03,10);}
    if(a==5){x=nx;y=ny;lose_life();if(gameover)return;}
    else{x=nx;y=ny;}
    if(has_axe)at_cell(y,x,130,6,0);else at_cell(y,x,129,6,0);
    last_x=x;last_y=y;
    status_line();
}
static void mine_step(void)
{
    int my,mx;
    my=my2/2;mx=mx2/2;
    blank(my,mx);
    /* BASIC's 0.5 movement increments: two internal units per cell. */
    if(my2<y*2)my2++;else if(my2>y*2)my2--;
    if(mx2<x*2)mx2++;else if(mx2>x*2)mx2--;
    my=my2/2;mx=mx2/2;
    if(my==y&&mx==x){lose_life();return;}
    /* BASIC 700/705/720: deposit the previous mine BEFORE drawing the
     * pursuer. A half-cell step can keep the same visible character cell;
     * drawing the deposited mine last would hide the active pursuer. */
    if(hard){if(rnd(100)>70)at_cell(old_my,old_mx,133,5,0);}
    else {if(rnd(100)>85)at_cell(old_my,old_mx,133,5,0);}
    at_cell(my,mx,131,5,1);
    old_my=my;old_mx=mx;
    if(rnd(5)==0){
        int r,c;
        r=rnd(18)+2;c=rnd(28)+1;
        at_cell(r,c,132,6,1);
        if(rnd(10)==0)at_cell(rnd(18)+2,rnd(28)+1,134,4,1);
    }
}
int main(void)
{
    game_keyboard();seed=seed^(unsigned int)ticks();highscore=0;gameover=0;
    intro();
    while(1){
        menu();make_maze();
        while(!gameover){player_step();if(!gameover)mine_step();sleep(2);}
    }
    return 0;
}
