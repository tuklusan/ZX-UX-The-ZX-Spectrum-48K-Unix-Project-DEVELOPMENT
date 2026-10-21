# C48 v1 host compiler decision

The project owner confirms that `sdk/rcc` is the host C48 compiler for
ZX-UX v1. It is independent of the ZX-UX kernel and produces the current
SSX1 or SSO1 output using the current compiler tools.

The 34 host-implementation paragraphs in the original 220-row audit
receive the disposition `host_rcc_architecture_accepted`. The project
does not require a second Windows C48 compiler for ZX-UX v1.

The paragraph review records an architectural decision. Compiler test
results, target integration, and operating-system checks have separate

The scoped host-compiler gate reads the checked paragraph inventory and
the owner's decision. The mandatory full release coverage check remains
in place and continues to report unverified obligations.
