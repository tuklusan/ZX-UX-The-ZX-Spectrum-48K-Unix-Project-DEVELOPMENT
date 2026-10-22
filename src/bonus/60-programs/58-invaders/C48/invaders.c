/* Invaders (1983 Michael Bews): C48 port of original BASIC lines 10..1090.
 * The 32x24 renderer is common c48lib, with original program sprite data.
 * 5/8 and shifted left/right move, 7/up fires (60 rockets initially).
 */
#include <c48.h>
#include "../../c48lib/c48lib.h"

static unsigned char cells[768];
static unsigned char hit[50];
static int top_row, line_row, cycles, direction, fleet_x;
static int position, score, highest, total, rockets;
static int over_game;
static unsigned int seed=22831;

static int random_n(int n)
{
    seed=seed^(seed<<7);
    seed=seed^(seed>>9);
    seed=seed^(seed<<8);
    if(n<=1)return 0;
    return (seed&32767)%n;
}
static void ch(int row,int col,int v)
{
    if(row<0 || row>=24 || col<0 || col>=32)return;
    c48_cell(row,col,v);
    cells[row*32+col]=v;
}
static int at(int row,int col)
{
    if(row<0 || row>=24 || col<0 || col>=32)return 32;
    return cells[row*32+col];
}
static void line(int row,int col,char *s)
{
    while(*s && col<32) {ch(row,col,*s);s++;col++;}
}
static void clear_n(int row,int col,int n)
{
    int x;
    for(x=0;x<n;x++)ch(row,col+x,32);
}
static void val(int row,int col,int n)
{
    char b[9];int k=0,i;
    if(n<0) {ch(row,col,'-');col++;n=-n;}
    do {b[k]=(char)('0'+n%10);k++;n=n/10;}while(n>0 && k<8);
    for(i=k-1;i>=0;i--)ch(row,col++,b[i]);
}
static void wipe(void)
{
    int i;cls();for(i=0;i<768;i++)cells[i]=32;
}
static void draw_ship(int row,int col)
{
    ch(row,col,132);ch(row,col+1,133);ch(row,col+2,134);
    ch(row,col+3,135);ch(row,col+4,136);
}
static void launcher(void)
{
    ch(20,position,' ');ch(20,position+1,130);
    ch(20,position+2,131);ch(20,position+3,' ');
}
static void score_line(void)
{
    ink(0);line(21,0,"SCORE:");clear_n(21,6,7);val(21,6,score);
    line(21,15,"ROCKET RESERVE:");clear_n(21,30,2);val(21,30,rockets);
}
static void full_field(void)
{
    int r,c,x;
    paper(5);ink(1);border(5);wipe();
    for(r=0;r<7;r++)for(x=0;x<7;x++) {
        c=2+x*4;
        ch(r,c,128);ch(r,c+1,129);
    }
    ink(3);
    for(x=0;x<6;x++) {
        ch(19,x*5,137);ch(19,x*5+1,138);ch(19,x*5+2,139);
        ch(19,x*5+3,' ');ch(19,x*5+4,' ');
    }
    ch(19,30,139);ch(19,31,138);
    ink(0);launcher();score_line();
}
static void intro(void)
{
    border(1);paper(1);ink(7);wipe();
    line(0,1,"I N V A D E R S  @1982 M.BEWS");
    /* Keep the title readable with the alternate VGA font. */
    line(1,0,"USE YOUR ROCKET LAUNCHER  ");ch(1,26,130);ch(1,27,131);
    line(2,0,"TO WIPE OUT THE INVADERS  ");ch(2,26,128);ch(2,27,129);
    line(3,0,"AND TO DAMAGE THE COMMAND SHIP");
    line(4,0,"WHICH ARRIVES LATER");draw_ship(4,22);
    line(6,0,"YOU CAN NOT FIRE WHILE YOU ARE");
    line(7,0,"BEHIND A LASER SHIELD");
    ch(7,24,137);ch(7,25,138);ch(7,26,139);
    line(9,0,"USE LEFT AND RIGHT CURSOR ARROWS");
    line(10,0,"TO MOVE YOUR LAUNCHER (WITH CAPS");
    line(11,0,"SHIFT TO MOVE FASTER).  USE THE");
    line(12,0,"'UP' ARROW TO FIRE ROCKETS.");
    line(13,4,"YOU HAVE ONLY 61 ROCKETS.");
    line(15,0,"* * * * * * * * * * * * * * * *");
    line(16,0,"SCORE 20 FOR EACH KNOCKED OUT");
    line(17,0,"INVADER AND 200 FOR EACH");
    line(18,0,"DIRECT HIT ON THE COMMAND SHIP.");
    line(19,0,"LOSE 10 POINTS FOR EACH MISS!");
    line(21,0,"IF INVADERS GET CLOSE TO YOU");
    line(22,0,"THEY BECOME INDESTRUCTIBLE!");
    flash(1);line(23,2,"<PRESS ANY KEY TO START GAME>");flash(0);
    getchar();
}
static void new_game(void)
{
    int i;
    top_row=0;line_row=0;cycles=0;direction=1;fleet_x=0;
    score=0;rockets=60;position=0;over_game=0;
    for(i=0;i<50;i++)hit[i]=0;
    full_field();
}
static int all_gone(void)
{
    int i;for(i=1;i<50;i++)if(!hit[i])return 0;
    return 1;
}
static void end_game(int won)
{
    int i;
    ink(7);flash(0);
    if(won) {
        paper(1);line(5,0,"YOU HAVE WIPED OUT THE INVADERS");
        line(7,0,"SCORED ");val(7,7,score);line(7,15," AND USED ");val(7,25,60-rockets);
        flash(1);line(9,1,"C O N G R A T U L A T I O N S");flash(0);
    } else {
        paper(2);line(5,0,"YOUR PLANET HAS BEEN TAKEN OVER");
        line(7,0,"YOU SCORED ");val(7,11,score);
        line(8,0,"USING ");val(8,6,60-rockets);line(8,10," ROCKETS");
    }
    if(score>highest)highest=score;
    total=total+score;
    paper(6);ink(2);
    line(11,12,"LAST SCORE");val(11,26,score);
    line(12,12,"HIGHEST SCORE");val(12,26,highest);
    line(13,12,"TOTAL SCORE");val(13,26,total);
    flash(1);line(15,2,"PRESS ANY KEY FOR NEXT GAME");flash(0);
    getchar();
    paper(6);ink(2);wipe();line(11,12,"STANDBY");
    for(i=5;i>0;i--) {val(17,15,i);sleep(10);}
    over_game=1;
}
static void march(void)
{
    int x,r,c,empties=0,all=0,index;
    for(x=1;x<=7;x++)if(hit[7*line_row+x])empties++;
    if(empties==7) {
        for(x=1;x<=49;x++)if(hit[x])all++;
        if(all==49) {end_game(1);return;}
    } else {
        if(top_row+line_row>21) {end_game(0);return;}
        r=top_row+line_row;
        c=0;
        if(direction<0){ch(r,c++,' ');ch(r,c++,' ');}
        ink(1);
        for(x=1;x<=7;x++) {
            index=7*line_row+x;
            if(hit[index])clear_n(r,c,4);
            else {ch(r,c,128);ch(r,c+1,129);ch(r,c+2,' ');ch(r,c+3,' ');}
            c=c+4;
        }
    }
    line_row++;
    if(line_row>6) {
        line_row=0;direction=-direction;cycles++;
        if(cycles==5) {
            cycles=0;clear_n(top_row,0,32);top_row++;
        }
    }
    if(line_row==0 && top_row>0) {
        clear_n(0,0,32);
        ink(2);draw_ship(0,random_n(27));
    }
}
static void rocket(void)
{
    int xs,r,x,ix,shotcol;
    shotcol=position+1;
    xs=((position-1+10)*2)%10;
    if(xs!=2 && xs!=4)return; /* shield gap, BASIC line 330 */
    if(rockets<1){flash(1);line(21,15,"  TAKE COVER!! 0 ");flash(0);return;}
    beep(0.12,35);rockets--;score_line();
    ink(0);ch(19,shotcol,97);
    for(r=18;r>=0;r--)if(at(r,shotcol)!=32)break;
    if(r<0){
        ch(19,shotcol,' ');ch(0,shotcol,97);
        flash(1);line(21,10,"MISS!");flash(0);
        beep(0.2,-15);score=score-10;
        clear_n(21,6,7);val(21,6,score);
        ch(0,shotcol,' ');return;
    }
    for(x=1;x<=3;x++){
        ch(r,shotcol,140);beep(0.02,30-3*x);
        sleep(1);ch(r,shotcol,' ');
    }
    clear_n(r,position,3);ch(19,shotcol,' ');
    if(r==0)score=score+200;
    else score=score+20;
    clear_n(21,6,7);val(21,6,score);
    if(r>=top_row && r<=top_row+6){
        ix=7*(r-top_row)+1+(position+1)/4;
        if(ix>=1 && ix<=49)hit[ix]=1;
    }
}
static void controls(void)
{
    int old,move;
    old=position;move=0;
    if(kbd_down('5'))move=-1;
    if(kbd_down('8'))move=1;
    if(kbd_down('7') || kbd_down(11)) {rocket();return;}
    if(kbd_down(8))move=-5;
    if(kbd_down(9))move=5;
    if(move<0 && position>0){position=position+move;if(position<0)position=0;}
    if(move>0 && position<27){position=position+move;if(position>27)position=27;}
    if(position!=old){ink(0);clear_n(20,old,4);launcher();beep(0.08,-40);}
}
int main(void)
{
    seed=seed^ticks();highest=0;total=0;
    intro();
    while(1) {
        new_game();
        while(!over_game) {march();if(!over_game)controls();sleep(2);}
    }
    return 0;
}
