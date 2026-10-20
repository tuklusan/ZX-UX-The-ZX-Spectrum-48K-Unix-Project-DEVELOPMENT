/* Copyright (c) 2026 SANYALnet Labs.
 * SANYALnet Labs Non-Commercial License applies; see root LICENSE.
 */
/* ANAGRAMMATIC, adapted from the supplied Sinclair BASIC listing.
 * Original credits in BASIC/51-anagrammatic.bas. The C48 edition enumerates
 * each ordered selection; repeated letters retain separate source positions.
 * Input is capped at eight letters to fit a responsive 48K session.
 */
#include <c48.h>

char letters[9];
char pattern[25];
char picked[9];
char line[33];
int chosen[9];
int letter_count;
int pattern_count;
int output_row;
int total;

int upper(int c)
{
    if (c >= 'a' && c <= 'z') return c - 32;
    return c;
}

void clear_line(int row)
{
    print_at(row, 0, "                                                                ");
}

void write_line(int row, char *text)
{
    clear_line(row);
    print_at(row, 0, text);
}

void prompt_line(int row, char *question, char *out, int limit)
{
    int c, n;
    write_line(row, question);
    n = 0;
    while (1) {
        c = getchar();
        if (c == 10 || c == 13) break;
        if (c == 8 || c == 127) {
            if (n > 0) --n;
        } else if (c >= 32 && c <= 126 && n < limit) {
            out[n++] = (char)upper(c);
        }
        out[n] = 0;
        clear_line(row+1);
        print_at(row+1, 2, out);
        if (limit == 1 && n == 1) break;
    }
    out[n] = 0;
}

void show_result(int length)
{
    int i, j, n;
    n = 0;
    if (pattern_count) {
        j = 0;
        for (i=0; i<pattern_count && n<31; ++i) {
            if (pattern[i] == '-') line[n++] = picked[j++];
            else line[n++] = pattern[i];
        }
    } else {
        for (i=0; i<length; ++i) line[n++] = picked[i];
    }
    line[n] = 0;
    if (output_row > 21) output_row = 16;
    write_line(output_row++, line);
    ++total;
}

void arrange(int depth, int length)
{
    int i;
    if (depth == length) {
        show_result(length);
        return;
    }
    for (i=0; i<letter_count; ++i) {
        if (!chosen[i]) {
            chosen[i]=1;
            picked[depth]=letters[i];
            arrange(depth+1, length);
            chosen[i]=0;
        }
    }
}

int number(char *s)
{
    int v, i;
    v=0;
    for (i=0; s[i]; ++i) {
        if (s[i]<'0' || s[i]>'9') return 0;
        v = v*10 + s[i]-'0';
    }
    return v;
}

int main(void)
{
    int c, i, w, dashes;
    char answer[12];
    border(5); paper(5); ink(0); cls();
    write_line(0, "                  ANAGRAMMATIC");
    write_line(2, "IF YOU ARE A CROSSWORD ADDICT, YOU KNOW THE PROBLEM");
    write_line(3, "OF TRYING TO REARRANGE LETTERS.");
    write_line(5, "ENTER JUST THE LETTERS WHICH ARE TO BE REARRANGED.");
    write_line(7, "EVERY POSSIBLE ORDER WILL APPEAR ON THE SCREEN.");
    write_line(9, "GLANCE AT THE COMBINATIONS FOR INSPIRATION.");
    write_line(12, "PRESS ANY KEY TO START");
    getchar();
    while (1) {
        border(4); paper(4); ink(0); cls();
        write_line(1, "                   ANAGRAMMATIC");
        prompt_line(3, "TYPE THE LETTERS TO REARRANGE (1-8):", letters, 8);
        letter_count = strlen(letters);
        if (!letter_count) continue;
        prompt_line(6, "ARE ANY LETTERS OR SPACES KNOWN? (Y/N)", answer, 1);
        pattern_count = 0;
        w=letter_count;
        if (answer[0] == 'Y') {
            while (1) {
                prompt_line(9, "KNOWN ORDER; USE - FOR UNKNOWN LETTERS:", pattern, 24);
                pattern_count = strlen(pattern);
                dashes = 0;
                for (i=0; i<pattern_count; ++i)
                    if (pattern[i]=='-') ++dashes;
                if (dashes == letter_count) break;
                write_line(12, "ERROR: DASH COUNT MUST MATCH THE LETTER COUNT");
            }
        } else {
            while (1) {
                prompt_line(9, "NUMBER OF LETTERS TO BEGIN:", answer, 2);
                w = number(answer);
                if (w >= 1 && w <= letter_count) break;
                write_line(12, "ERROR: ENTER A NUMBER WITHIN THE LETTER COUNT");
            }
        }
        cls();
        write_line(0, "ANAGRAMMATIC - POSSIBLE ARRANGEMENTS");
        write_line(2, "OUTPUT FOLLOWS BELOW");
        output_row = 16;
        total = 0;
        for (i=w; i<=letter_count; ++i) arrange(0, i);
        write_line(22, "ALL POSSIBLE ARRANGEMENTS FINISHED");
        write_line(23, "PRESS ANY KEY FOR ANOTHER GO");
        c = getchar();
        if (c == 'q' || c == 'Q') return 0;
    }
}
