/* BIORHYTHMS (1983) - port of the supplied Sinclair BASIC listing. */
#include <c48.h>

static int years[6];
static int months[11]={31,59,90,120,151,181,212,243,273,304,334};
static char number[8];
static char *labels[6]={"BIRTH YEAR:","BIRTH MONTH:","BIRTH DAY:",
                        "YEAR REQUIRED:","MONTH REQUIRED:","DAY REQUIRED:"};
static int form_rows[6]={4,6,8,11,13,15};

static void decimal(int n,char *s){
    int i=0,j,k,neg=0;
    char t[8];
    if(n<0){neg=1;n=-n;}
    do{t[i++]=(char)('0'+n%10);n=n/10;}while(n&&i<6);
    j=0;if(neg)s[j++]='-';
    for(k=i-1;k>=0;k--)s[j++]=t[k];
    s[j]=0;
}
static void form(void){
    int i;
    border(1);paper(1);ink(5);cls();
    print_at(0,20,"B I O R H Y T H M S");
    for(i=0;i<6;i++){
        paper(0);ink(5);
        print_at(form_rows[i],0,"                                    ");
        print_at(form_rows[i],6,labels[i]);
    }
    paper(1);ink(5);print_at(21,6,"Enter details now (numeric)");
}
static int read_number(int row,int col){
    int k,value=0,digits=0;
    char s[8];
    paper(0);ink(7);
    for(;;){
        k=getchar();
        if(k=='\r'||k=='\n'){
            if(digits)break;
        }else if(k>='0'&&k<='9'&&digits<4){
            value=value*10+(k-'0');
            s[0]=(char)k;s[1]=0;
            print_at(row,col+digits,s);
            digits++;
        }else if((k==8||k==12||k==127)&&digits){
            digits--;value=value/10;
            print_at(row,col+digits," ");
        }
    }
    decimal(value,number);
    print_at(row,col,"        ");
    print_at(row,col,number);
    return value;
}
static float quotient(float v,int div){
    /* Sinclair's INT rounds down, including negative values. */
    float q;
    int t;
    q=v/(float)div;
    t=(int)q;
    if((float)t>q)t--;
    return (float)t;
}
static void graph(int y,int m,int d,int y1,int m1,int d1){
    float total,total2,days,p,e,ii,scale=9.869565217;
    float start,angle,cy;
    int x,t,period;
    char ds[8];
    total=(float)(y-1)*365.25;
    total2=(float)(y1-1)*365.25;
    if(m>1 && m<=12)total=total+(float)months[m-2];
    if(m-1>1 && y%4==0)total=total+1.0;
    if(m1-1>1 && y1%4==0)total2=total2+1.0;
    total=total+(float)d;
    total2=total2+(float)d1;
    days=total2-total;
    p=days-quotient(days,23)*23.0;
    e=days-quotient(days,28)*28.0;
    ii=days-quotient(days,33)*33.0;
    border(1);paper(7);ink(2);cls();
    paper(0);ink(5);print_at(0,0,"DIVISIONS=DAYS");
    sleep(100);
    paper(7);ink(2);
    for(x=1;x<=25;x++){
        t=(int)((float)x*scale+0.5);
        draw(t,16,t,183);
    }
    paper(0);ink(5);print_at(0,36,"                    ");
    decimal(d1,ds);print_at(0,36,ds);
    print_at(0,44,"/");decimal(m1,ds);print_at(0,46,ds);
    print_at(0,52,"/");decimal(y1,ds);print_at(0,54,ds);
    print_at(0,64-2,"+");
    paper(7);ink(2);
    for(period=0;period<3;period++){
        paper(0);ink(5);
        if(period==0)print_at(0,0,"Physical cycle      ");
        else if(period==1)print_at(0,0,"Emotional cycle     ");
        else print_at(0,0,"Intellectual cycle  ");
        paper(7);ink(2);
        if(period==0) start=p*scale;
        else if(period==1) start=e*scale;
        else start=ii*scale;
        for(x=0;x<256;x++){
            if(period==0)angle=(start+(float)x)/(11.5*3.14159265);
            else if(period==1)angle=(start+(float)x)/(14.0*3.14159265);
            else angle=(start+(float)x)/(16.5*3.14159265);
            cy=83.5+83.5*sin(angle);
            t=(int)(cy+0.5);
            if(t<0)t=0;if(t>167)t=167;
            plot(x,t+16);
        }
    }
    paper(0);ink(5);print_at(0,0,"Biorhythm for      ");
    sleep(100);
    paper(7);ink(2);print_at(20,6,"Press a key to restart");
}
int main(void){
    int i;
    for(;;){
        form();
        years[0]=read_number(4,40);
        years[1]=read_number(6,40);
        years[2]=read_number(8,40);
        years[3]=read_number(11,40);
        years[4]=read_number(13,40);
        years[5]=read_number(15,40);
        if(years[3]>0&&years[0]>0){
            /* BASIC line 335 tests the day and month, not the year. */
            if(years[4]==years[1]&&years[5]==years[2]){
                beep(.2,0);beep(.2,0);beep(.4,2);beep(.4,0);beep(.4,5);beep(.4,4);
                sleep(10);
                beep(.2,0);beep(.2,0);beep(.4,2);beep(.4,0);beep(.4,7);beep(.4,5);
                sleep(10);
                beep(.2,0);beep(.2,0);beep(.4,12);beep(.4,9);beep(.4,5);beep(.4,4);beep(.4,2);
                sleep(10);
                beep(.2,0);beep(.2,10);beep(.4,9);beep(.4,5);beep(.4,7);beep(.4,5);
            }
            graph(years[0],years[1],years[2],years[3],years[4],years[5]);
        }
        getchar();
    }
    return 0;
}
