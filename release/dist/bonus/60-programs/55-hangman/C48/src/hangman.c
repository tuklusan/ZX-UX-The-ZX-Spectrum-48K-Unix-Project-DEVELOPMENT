/* HANGMAN: word banks, repeated guesses and graphic stages from Paul Stanley's BASIC. */
#include <c48.h>

static char words110[] = "PIGEONDONKEYBUDGIEMAGGOTJAGUARSPIDERBEETLEWEEVILEARWIGSHRIMPSALMONPLAICEMINNOWBADGERCATTLEKITTENLOCUSTMAGPIERABBITTURKEYTURTLECANARYGERBILMONKEYCURLEW";
static char words125[] = "SNAILROACHHIPPOLLAMACHIMPCAMELHORSETIGERHOUNDSNAKEROBINHERONRAVENSTORKTROUTWHALEHYENAPANDASKUNKTAPIRZEBRAMOUSESHREWEAGLESWIFTPERCHPRAWNOTTERGOOSEKOALASHEEP";
static char words160[] = "ALBANIAAUSTRIABELGIUMDENMARKFINLANDGERMANYHUNGARYICELANDIRELANDRUMANIABAHRAINLEBANONALGERIALIBERIANIGERIASENEGALTUNISIABERMUDAJAMAICABOLIVIAURUGUAY";
static char words175[] = "TURKEYUGANDASWEDENPOLANDNORWAYMEXICOKUWAITISRAELGREECEZAMBIAFRANCECYPRUSCANADABRAZILTAIWANPANAMAMALAWIJORDANAZORESANGOLA";
static char words200[] = "PURCELLROSSINIBELLINIBERLIOZBORODINPUCCINIDEBUSSYSTRRAUSSBRITTENHODBEINMILLAISDAUMIERCEZANNEGAUGUINMATISSEPICASSO";
static char words260[] = "BARIUMCARBONCERIUMCOBALTCOPPERCURIUMERBIUMHELIUMINDIUMIODINENICKELOSMIUMOXYGENRADIUMSILVERSODIUM";
static char words275[] = "ARSENICBISMUTHBROMINECADMIUMCAESIUMCALCIUMFERMIUMGALLIUMHAFNIUMHOLMIUMIRIDIUMKRYPTONLITHIUMMERCURYRHENIUMRHODIUMSILICONCONSULPHURTERBIUMTHORIUMTHULIUMYTTRIUM";
static char words300[] = "JAMESDAVIDEDGARHENRYCAROLHELENBRIANSALLYSARAHSUSANPETERSIMONMANDYKEVINSCOTTNIGELMILESROBINVENUSROMEOCECILDYLANPERCYLEIGHEMILYPABLOFRANKCLIVEDIANANICKYTRACYBARRYGEOFFTERRY";
static char words360[] = "CARRYCATCHMARRYLAUGHTWISTBRINGFETCHWRITECLIMBWORRYGLIDEAWASHSHOOTDODGEPUNCHSMACKSCALETHROWLOATHDRIVEPRESSTASTESPEAKHURRYSCORETRAILFORCEPROVETRACEPAINT";
static char words375[] = "COLOURTHRILLUNLOCKAFFECTABDUCTFOLLOWATTACKDEFENDDIFFERSELECTOUTPUTDEFINECHANCEMODIFYREMAINACCEPTSPRINGASSUREVANISHFINISHTRAVEL";

static char answer[9];
static char visible[9];
static int length, solved, missed, wrong_col, wrong_row;
static unsigned int rng;

static unsigned int roll(void) {
    if (rng & 1) rng = (rng >> 1) ^ 0xb400;
    else rng = rng >> 1;
    if (!rng) rng = 0x7583;
    return rng;
}

static int next(int range) { return roll() % range; }

static void choose_word(int category) {
    char *blob = words110;
    int count = 25;
    int size = 6;
    int i, start;
    if (category == 1) {
        if (next(2)) { blob = words125; count = 31; size = 5; }
    } else if (category == 2) {
        if (next(2)) { blob = words175; count = 20; size = 6; }
        else { blob = words160; count = 21; size = 7; }
    } else if (category == 3) { blob = words200; count = 16; size = 7; }
    else if (category == 4) {
        if (next(2)) { blob = words275; count = 22; size = 7; }
        else { blob = words260; count = 16; size = 6; }
    } else if (category == 5) { blob = words300; count = 34; size = 5; }
    else if (category == 6) {
        if (next(2)) { blob = words375; count = 21; size = 6; }
        else { blob = words360; count = 30; size = 5; }
    }
    start = next(count) * size;
    for (i = 0; i < size; ++i) {
        answer[i] = blob[start + i];
        visible[i] = '_';
    }
    length = size;
    answer[size] = 0;
    visible[size] = 0;
}

static void block(int r, int c, int color) {
    int old;
    paper(color);
    print_at(r, c*2, "  ");
    paper(7);
}

/* Sinclair BASIC PLOT uses the 176-pixel drawing viewport. */
static void pplot(int x, int y) { plot(x,y+16); }
static void pdraw(int x1, int y1, int x2, int y2) {
    draw(x1,y1+16,x2,y2+16);
}
static void pcircle(int x,int y,int r) { circle(x,y+16,r); }

static void gallows(int stage) {
    int i;
    if (stage == 0) {
        for (i = 1; i <= 14; ++i) block(17,i,5);
    } else if (stage == 1) {
        for (i = 5; i <= 16; ++i) block(i,2,3);
    } else if (stage == 2) {
        /* The original third routine clears this row. */
        paper(7); print_at(4,4,"                ");
    } else if (stage >= 3 && stage <= 5) {
        ink(2);
        pcircle(73,118,9);
        pplot(70,120); pdraw(70,120,71,120); pdraw(71,120,71,121);
        pdraw(71,121,70,121);
        pplot(76,120); pdraw(76,120,77,120); pdraw(77,120,77,121);
        pdraw(77,121,76,121);
        pplot(73,118); pdraw(73,118,76,115); pdraw(76,115,74,115);
        pdraw(74,115,73,116); pplot(69,115); pdraw(69,115,79,115);
        ink(0);
    } else if (stage == 6) {
        for (i=72;i<=75;++i) pdraw(i,104,i,108);
        block(9,8,3);block(9,9,3);
        block(10,8,5);block(10,9,5);block(10,10,5);
        block(11,8,3);block(11,9,3);
    } else if (stage == 7) {
        pdraw(83,104,93,114); pdraw(93,114,94,114);
        pdraw(94,114,84,104);
        for (i=1;i<=3;++i) pcircle(97,116,i);
    } else if (stage == 8) {
        pdraw(64,104,54,114); pdraw(54,114,53,114);
        pdraw(53,114,63,104);
        for (i=1;i<=3;++i) pcircle(51,116,i);
    } else if (stage == 9) {
        ink(5);
        for (i=1;i<=4;++i) pdraw(67+i,79,47+i,49);
        ink(0);
        print_at(16,10,"    ");
    } else if (stage == 10) {
        ink(5);
        for (i=1;i<=4;++i) pdraw(79+i,79,99+i,49);
        ink(0);
        print_at(16,24,"    ");
    }
}

static void intro_demo(void) {
    int i,j;
    border(7);paper(7);ink(0);cls();
    for(i=0;i<=9;++i)gallows(i);
    gallows(10);
    for(i=0;i<3;++i) for(j=1;j<=11;++j) beep(.02,(float)j);
    sleep(250);
    cls();
}

static void category_menu(void) {
    paper(7); border(7); ink(0);cls();
    paper(3);ink(7);print_at(0,18,"H A N G M A N");
    paper(7);
    ink(1);print_at(2,0,"Which subject do you want?");
    ink(4);print_at(4,0,"1.....ANIMALS");
    ink(3);print_at(6,0,"2.....COUNTRIES OF THE WORLD");
    ink(4);print_at(8,0,"3.....COMPOSERS & ARTISTS");
    ink(3);print_at(10,0,"4.....CHEMICAL ELEMENTS");
    ink(4);print_at(12,0,"5.....CHRISTIAN NAMES");
    ink(3);print_at(14,0,"6.....GENERAL VERBS");
    ink(2);print_at(17,0,"Press the appropriate key.");
}

static void show_word(void) {
    int i;
    paper(7);ink(0);cls();
    paper(3);ink(7);print_at(0,30,"H A N G M A N");paper(7);
    ink(2);print_at(11,30,"Your guesses:");
    ink(4);
    for(i=0;i<length;++i) {
        char glyph[2];glyph[0]=visible[i];glyph[1]=0;
        print_at(3,30+4*i,glyph);
    }
    ink(0);print_at(7,30,"Guess a letter");
    missed=0;solved=0;wrong_col=30;wrong_row=13;
}

static void wrong(char key) {
    char letter[2];
    beep(.4,-15);beep(.4,-25);
    gallows(missed);
    missed++;
    ink(4);
    letter[0]=key;letter[1]=0;
    print_at(wrong_row,wrong_col,letter);
    wrong_col = wrong_col + 4;
    if(wrong_col>=66) { wrong_col=30;wrong_row = wrong_row + 2; }
    ink(0);
}

static void decimal(int v, char *dst) {
    char rev[8];
    int n=0, i;
    if (!v) rev[n++]='0';
    while (v>0 && n<7) {rev[n++]=(char)('0'+v%10);v=v/10;}
    for(i=0;i<n;++i)dst[i]=rev[n-i-1];
    dst[n]=0;
}

static void display_result(int success) {
    char count[8];
    ink(0);
    if (success) {
        print_at(20,0,"WELL DONE! YOU CORRECTLY GOT");
        print_at(21,0,answer);
        print_at(21,20,"IN");
        decimal(missed+solved,count);
        print_at(21,28,count);
        print_at(21,36,"GUESSES");
    } else {
        print_at(20,0,"BAD LUCK! YOU'VE BEEN HANGED.");
        print_at(21,0,"THE ANSWER WAS");
        /* BASIC prints its in-place masked word, not a fresh copy. */
        print_at(21,32,visible);
    }
    sleep(160);
}

static void play(int category) {
    int key, i, hits;
    char letter[2];
    choose_word(category);
    show_word();
    for (;;) {
        key = getchar();
        if (key < 'A' || key > 'Z') continue;
        hits = 0;
        letter[0]=(char)key;letter[1]=0;
        for (i=0;i<length;++i) {
            if (visible[i]=='_' && answer[i] == key) {
                visible[i]='*';
                ink(2);print_at(3,30+4*i,letter);
                beep(.3,30);
                solved++;
                hits++;
            }
        }
        if (!hits) {
            wrong((char)key);
            if (missed == 11) { display_result(0); return; }
        }
        if (solved == length) { display_result(1); return; }
    }
}

int main(void) {
    int key;
    rng=(unsigned int)(ticks() ^ 0x63b9);
    if (!rng) rng=0x9473;
    intro_demo();
    for (;;) {
        category_menu();
        do { key = getchar(); } while (key < '1' || key > '6');
        play(key-'0');
    }
    return 0;
}
