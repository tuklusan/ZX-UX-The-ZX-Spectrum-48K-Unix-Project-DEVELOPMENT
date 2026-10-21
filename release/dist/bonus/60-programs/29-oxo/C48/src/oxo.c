/* NOUGHTS + CROSSES (Michael Bews, 1982). C48 port of program 29. */
#include <c48.h>

/* The original DATA values, in the original UDG order. */
static unsigned char o_shape[8] = {24,126,102,195,195,102,126,24};
static unsigned char x_shape[8] = {129,195,102,60,24,60,102,195};
static int shades[4] = {4,2,5,3};
static int marks[10];      /* 1..9; +1 machine (O), -1 human (X). */
static int moves, me_wins, you_wins, draws;
static unsigned int rng;

static unsigned int rnd(void) {
    if (rng & 1) rng=(rng>>1)^0xb400;
    else rng=rng>>1;
    if (!rng) rng=0xb8e1;
    return rng;
}

static void num(int v, char *dst) {
    char rev[8]; int i=0,j;
    if (!v) rev[i++]='0';
    while (v>0 && i<7) { rev[i++]=(char)('0'+v%10);v=v/10; }
    for (j=0;j<i;++j) dst[j]=rev[i-j-1];
    dst[i]=0;
}

/* One BASIC character is two font64 cells. The 19-cell board starts at 6. */
static void segment(int row, int column, int shade) {
    paper(shade);print_at(row,column*2,"  ");paper(1);
}
static void divider(int row) {
    paper(6);print_at(row,12,"                                      ");paper(1);
}
static void grid(void) {
    int section,r,shade,i;
    divider(3);
    for (section=0;section<3;++section) {
        for (r=0;r<4;++r) {
            shade=shades[r];
            for (i=0;i<4;++i)segment(4+5*section+r,6+6*i,shade);
        }
        divider(8+5*section);
    }
}

static void board(void) {
    int row,col,n,i;
    ink(7);
    for (row=0;row<3;++row) for (col=0;col<3;++col) {
        n=1+row*3+col;
        i=19+12*col; /* original PRINT AT column (9+6*col), doubled + 1 */
        print_at(5+5*row,i,"  ");
        if (marks[n] == 1) udg_draw(2,5+5*row,(i-1)/2);
        else if (marks[n] == -1) udg_draw(0,5+5*row,(i-1)/2);
        else {
            char digit[2];digit[0]=(char)('0'+n);digit[1]=0;
            print_at(5+5*row,i,digit);
        }
    }
}

static void heading(void) {
    paper(1);border(1);ink(7);cls();
    print_at(0,17,"NOUGHTS & CROSSES");
    print_at(1,2,"I am");
    print_at(1,49,"You are");
    udg_draw(2,3,2);
    udg_draw(0,3,28);
    grid();
    board();
}

static int vacant(int n) { return n>=1 && n<=9 && marks[n]==0; }

/* BASIC lines 100--144: win first, block second, then take corner. */
static int in_line(int a,int b,int c,int sum) {
    if (marks[a]+marks[b]+marks[c] != sum) return 0;
    if (vacant(c)) return c;
    if (vacant(b)) return b;
    if (vacant(a)) return a;
    return 0;
}
static int can_complete(int sum) {
    int x,n;
    for (x=0;x<3;++x) {
        n=in_line(3*x+1,3*x+2,3*x+3,sum); if(n)return n;
        n=in_line(x+1,x+4,x+7,sum); if(n)return n;
        if (x==0) {n=in_line(5,7,3,sum);if(n)return n;}
        if (x==1) {n=in_line(5,9,1,sum);if(n)return n;}
    }
    return 0;
}
static int machine_move(void) {
    int i,n;
    if (moves) {
        n=can_complete(2); if(n)return n;
        n=can_complete(-2); if(n)return n;
    }
    for (i=0;i<40;++i) {
        n=1+2*(int)(rnd()%5);
        if(n!=5 && vacant(n))return n;
    }
    for(i=1;i<=9;++i)if(vacant(i))return i;
    return 0;
}
static int check_win(void) {
    int x,n;
    for(x=0;x<3;++x) {
        n=marks[3*x+1]+marks[3*x+2]+marks[3*x+3];
        if (n==3 || n==-3)return 1;
        n=marks[x+1]+marks[x+4]+marks[x+7];
        if (n==3 || n==-3)return 1;
        if(x<2) {
            n=marks[5]+marks[5+2*(x+1)]+marks[5-2*(x+1)];
            if (n==3 || n==-3)return 1;
        }
    }
    return 0;
}
static void scores(void) {
    char a[8],b[8],c[8];
    num(you_wins,a);num(me_wins,b);num(draws,c);
    ink(7);
    print_at(20,0,"Score: You ");print_at(20,11,a);
    print_at(20,18,"Me ");print_at(20,21,b);
    print_at(20,27,"Draw ");print_at(20,32,c);
    print_at(21,6,"Press any key for new game");
}
static void result(int state,int mover) {
    int i;
    print_at(19,26,"                ");
    if(state==2) {print_at(19,26,"DRAW!");draws++;}
    else if(mover<0) {print_at(19,26,"YOU WIN");you_wins++;}
    else {print_at(19,26,"I WIN");me_wins++;}
    flash(1);
    for(i=0;i<5;++i)beep(.06,(float)(i*3-7));
    flash(0);
    scores();
    getchar();
}
static void set_turn(int side) {
    print_at(2,16,"                           ");
    if(side<0)print_at(2,16,"You to go FIRST");
    else print_at(2,16,"Me to go FIRST");
}

int main(int argc, char **argv) {
    int n,side,key,state,i;
    udg_define(0,x_shape);udg_define(2,o_shape);
    rng=(unsigned int)(ticks()^0xd729);if(!rng)rng=0x735d;
    /* Optional replay seed; normal ZX-UX launch still uses the live clock. */
    if(argc>1 && argv[1][0]) {
        unsigned int value=0;
        for(i=0;argv[1][i];++i) {
            if(argv[1][i]<'0'||argv[1][i]>'9') {value=0;break;}
            value=value*10+(unsigned int)(argv[1][i]-'0');
        }
        if(value)rng=value;
    }
    for (;;) {
        for(i=1;i<=9;++i)marks[i]=0;
        moves=0;
        if (rnd()&1) side=1; else side=-1;
        heading();set_turn(side);
        for(;;) {
            if(side==1) {
                n=machine_move();if(!n)break;
            } else {
                do {key=getchar();} while(key<'1'||key>'9');
                n=key-'0';
                print_at(10,52,"         ");
                print_at(10,52,"You ");
                {char s[2];s[0]=(char)key;s[1]=0;print_at(10,56,s);}
                if(!vacant(n)) {
                    print_at(11,52,"AGAIN!");
                    for(i=0;i<5;++i)beep(.06,20);
                    continue;
                }
                print_at(11,52,"       ");
            }
            marks[n]=side;
            moves++;
            beep(.1,(float)(moves*4));
            side=-side;
            if(side<0)print_at(10,60,"  ");
            board();
            state=check_win();
            if(state) {result(1,-side);break;}
            if(moves==9) {result(2,0);break;}
        }
    }
    return 0;
}
