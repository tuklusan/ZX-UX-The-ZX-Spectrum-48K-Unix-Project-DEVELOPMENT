/*
 * Copyright (c) 2026 SANYALnet Labs.
 * SANYALnet Labs Non-Commercial License; see repository LICENSE.
 * This C48 target fixture exercises the existing process bootstrap rule.
 * The v1 process creates one private ENV1 byte in the C48 runtime BSS.
 * These deliberate internal writes are diagnostics, not portable ENV1 use.
 * Test actual v1-native process ownership, ARG1 separation and lifetime.
 */
#include <c48.h>
extern char _c48_env1;

int main(int argc, char **argv)
{
    char *env;
    int mode;
    env = &_c48_env1;
    if (argc != 2 || argv[0] == 0 || argv[1] == 0 || argv[2] != 0) {
        puts("C48-ENV1-FAIL-ARGC");
        return 1;
    }
    if (env == argv[0] || env == argv[1]) {
        puts("C48-ENV1-FAIL-ALIAS");
        return 1;
    }
    if (_c48_env1 != 0) {
        puts("C48-ENV1-FAIL-INIT");
        return 1;
    }
    mode = 0;
    if (strcmp(argv[1], "hold") == 0)
        mode = 1;
    else if (strcmp(argv[1], "check") == 0)
        mode = 2;
    else if (strcmp(argv[1], "e48") != 0) {
        puts("C48-ENV1-FAIL-ARGV");
        return 1;
    }
    if (mode == 1) {
        _c48_env1 = 90;
        puts("C48-ENV1-HOLD-START");
        sleep(1800u);
        if (_c48_env1 != 90) {
            puts("C48-ENV1-FAIL-HOLD");
            return 1;
        }
        puts("C48-ENV1-HOLD-OK");
    } else if (mode == 2) {
        _c48_env1 = 65;
        sleep(25u);
        if (_c48_env1 != 65) {
            puts("C48-ENV1-FAIL-CHECK");
            return 1;
        }
        puts("C48-ENV1-CHECK-OK");
    } else {
        _c48_env1 = 90;
        sleep(25u);
        if (_c48_env1 != 90) {
            puts("C48-ENV1-FAIL-LIFETIME");
            return 1;
        }
        puts("C48-ENV1-OK");
    }
    return 0;
}
