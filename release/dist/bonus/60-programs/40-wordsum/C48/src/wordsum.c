/* WORDSUM, Michael Bews (1983): original 54 six-letter puzzle words. */
#include <c48.h>

static char words[] =
    "HEARTHYELLOWENGINERABBITCARPETCLEVERFEASTSSHADESPOTATORADIOSTHAMES"
    "CARROTTOMATOCHEESEBUTTERRUDDERHEATERPLINTHFARMERTROPHYCHERRYHAPPEN"
    "COFFEETEAPOTMOTHERSISTERHOUSESCABINSISLANDPIRATESILVERJEWELSBOUNTY"
    "TOWELSPLANESPLANTSHOCKEYTENNISCOSTLYLEMONSAPPLESORANGEVIOLETROBBER"
    "RATHERPOINTSPAINTSTANDEMLETTERLITTERLATTERFASTERMASTERMISTER"
    ;
static unsigned int rng;
static char word[7],top[14],middle[14],bottom[14];
static char top_old[14],middle_old[14],bottom_old[14];
static int value[6],seen[6];
static float result,subtract,remain;

static unsigned int rand16(void) {
    if(rng & 1)rng=(rng>>1)^0xb400;
    else rng=rng>>1;
    if(!rng)rng=0xb9a1;
    return rng;
}
static int next(int bound) { return (int)(rand16()%(unsigned int)bound); }
static void copy(char *dst,char *src) {int i=0;while(src[i]){dst[i]=src[i];i++;}dst[i]=0;}
static void to_decimal(float x,char *dst) {
    float place=1000000.0;
    int first=0,i=0,digit;
    if(x<0.0) { dst[i++]='-'; x=-x; }
    while(place>=1.0) {
        digit=(int)(x/place);
        if(digit>9)digit=9;
        if(digit || first || place==1.0) {dst[i++]=(char)('0'+digit);first=1;}
        x=x-((float)digit*place);
        place=place/10.0;
    }
    dst[i]=0;
}
static int already(int upto,int digit) {
    int i;for(i=0;i<upto;i++)if(value[i]==digit)return 1;
    return 0;
}
static void make_puzzle(void) {
    int choice,j,i,d,match,tl,sl,il;
    float t=0.0;
    choice=next(54);
    for(i=0;i<6;++i)word[i]=words[choice*6+i];
    word[6]=0;
    for(i=0;i<6;++i) {
        match=-1;
        for(j=0;j<i;++j)if(word[i]==word[j])match=j;
        if(match>=0)value[i]=value[match];
        else {
            do {d=next(10);} while((i==0 && d==0) || already(i,d));
            value[i]=d;
        }
        t=t*10.0+(float)value[i];
    }
    result=t;
    subtract=9.0*(float)(1000+next(9000));
    remain=result-subtract;
    to_decimal(result,bottom_old);
    to_decimal(subtract,middle_old);
    to_decimal(remain,top_old);
    copy(bottom,bottom_old);copy(middle,middle_old);copy(top,top_old);
    tl=(int)strlen(bottom);
    sl=(int)strlen(middle);
    il=(int)strlen(top);
    for(i=0;i<6;++i)seen[i]=0;
    /* BASIC lines 280-450: digits in the answer reveal their letters in
       each addend. The second pass modifies a scalar C, not the C array. */
    for(i=0;i<tl && i<6;++i)for(j=0;j<il;++j)
        if(top[j]==bottom_old[i]) {seen[i]=1;top[j]=word[i];}
    for(i=0;i<tl && i<6;++i)for(j=0;j<sl;++j)
        if(middle[j]==bottom_old[i]) middle[j]=word[i];
    for(i=0;i<tl && i<6;++i)if(!seen[i])bottom[i]=word[i];
}
static void band(void) {
    int row;
    paper(6);
    for(row=6;row<=13;++row)print_at(row,18,"                          ");
    paper(5);
}
static void spaced(int row,int len,char *s,int pitch) {
    int i,column;
    char glyph[2];
    column=44-4*len;glyph[1]=0;
    if(column<18)column=18;
    for(i=0;i<len;++i) {
        glyph[0]=s[i];
        print_at(row,column+4*i,glyph);
        beep(.1,(float)(pitch+i+1));
    }
}
static void write_at_left(int row,char *text) {
    int col;
    col=12-2*(int)strlen(text);
    if(col<0)col=0;
    print_at(row,col,text);
}
static void screen_bands(void) {
    /* Sinclair PRINT paints the top row PAPER 7. BASIC's lower two
       input rows retain the initial yellow PAPER 6 after its CLS. */
    paper(7);ink(7);
    print_at(0,0,"                                                                ");
    paper(6);ink(1);
    print_at(22,0,"                                                                ");
    print_at(23,0,"                                                                ");
    paper(5);ink(1);
}
static void display_puzzle(void) {
    int i;
    border(6);paper(5);ink(1);cls();
    screen_bands();
    band();
    ink(1);paper(6);
    spaced(7,(int)strlen(top),top,0);
    spaced(9,(int)strlen(middle),middle,6);
    print_at(10,18,"__________________________");
    spaced(12,(int)strlen(bottom),bottom,11);
    paper(5);ink(1);inverse(1);
    print_at(18,0,"                                                                ");
    print_at(18,0,"PRESS <SPACE> TO REVEAL THE WORD");
    inverse(0);
}
static void reveal(void) {
    int i;
    paper(5);ink(1);
    write_at_left(7,top_old);
    write_at_left(9,middle_old);
    print_at(10,0,"____________");
    write_at_left(12,bottom_old);
    paper(6);
    spaced(12,6,word,18);
    paper(5);
    flash(1);inverse(1);
    print_at(18,0,"                                                                ");
    print_at(18,0,"  PRESS <1> FOR ANOTHER WORDSUM ");
    flash(0);inverse(0);
}
int main(int argc,char **argv) {
    int i,key;
    rng=(unsigned int)(ticks()^0x871f);if(!rng)rng=0x1237;
    if(argc>1 && argv[1][0]) {
        unsigned int v=0;
        for(i=0;argv[1][i];++i) {
            if(argv[1][i]<'0'||argv[1][i]>'9') {v=0;break;}
            v=v*10+(unsigned int)(argv[1][i]-'0');
        }
        if(v)rng=v;
    }
    border(6);paper(6);ink(1);cls();
    print_at(11,24,"STANDBY");
    for(;;) {
        make_puzzle();
        beep(.1,10);
        display_puzzle();
        getchar();  /* BASIC's INKEY$ accepts any key, despite its prompt. */
        beep(.1,40);
        reveal();
        do {key=getchar();}while(key!='1');
    }
    return 0;
}
