ZX-UX DEVELOPMENT ENVIRONMENT - FRESH DEBIAN 13 AMD64 MACHINE
=================================================================

Purpose
-------
Take a full Git checkout of this repository to a new Debian 13 (trixie)
64-bit PC or virtual machine, install the saved build dependencies, and run
the same clean-room rebuild command used by GitHub Actions.

Use Debian 13/amd64 (Intel or AMD x86-64), NOT Ubuntu, Debian testing, or
ARM64 with the packages in this directory. The Debian package archive
contains Debian-specific binary packages. It is not a bootable OS image.

1. GET THE OPERATING SYSTEM
---------------------------
On a computer with internet access, open the official Debian download site:

    https://www.debian.org/distrib/

For Debian 13 (trixie), amd64:
  - For a network-assisted install, download the amd64 netinst ISO from:
    https://cdimage.debian.org/debian-cd/current/amd64/iso-cd/
  - For an offline OS install, download the amd64 DVD-1 ISO from:
    https://cdimage.debian.org/debian-cd/current/amd64/iso-dvd/

Choose the newest Debian 13.x amd64 image there; the point-release number
can change. The netinst ISO needs a network connection to fetch packages.
The DVD-1 ISO carries more packages and is more suitable without internet.

For a VM, attach the ISO as a virtual optical drive and boot it.
For a physical PC, write the ISO to a bootable USB drive or DVD using the
instructions at https://wiki.debian.org/DebianInstaller/CreateUSBMedia .
Writing an ISO over a USB drive erases that drive.

2. INSTALL DEBIAN AND LOG IN
---------------------------
Start "Graphical install" (or "Install"). Follow the on-screen instructions:
  - Choose your language, keyboard, time zone, machine name, and disk.
  - Create an ordinary user with a password.
  - Leave the root-password field empty during installation. Debian will
    install sudo and give the first user permission to administer the PC.
  - In "Software selection", keep "standard system utilities" selected.
    A desktop is optional; Fuse screenshots use Xvfb, not a visible desktop.
  - Finish installation, remove the ISO, reboot, and log in as that user.

In a terminal, run:

    cat /etc/os-release
    dpkg --print-architecture
    sudo -v

The first command must identify Debian 13 (trixie). The second must print
amd64. The third must succeed with your user's password.

For a VM, 2 or more virtual CPUs, 4 GB or more RAM, and 25 GB or more of
free disk space are sensible starting allocations, not tested minimums.

3. MOVE THE REPOSITORY TO THE NEW MACHINE
-----------------------------------------
Transfer the WHOLE Git checkout, including its hidden .git directory and
tracked dist/ directory, from USB/shared storage. The path on your USB
depends on how it is mounted. Copy it into your home directory.

If connected to the internet and Git is already available, instead run:

    git clone https://github.com/tuklusan/ZX-UX-The-ZX-Spectrum-48K-Unix-Project-DEVELOPMENT.git
    cd ZX-UX-The-ZX-Spectrum-48K-Unix-Project-DEVELOPMENT

If copied from another machine, open a terminal and cd to the copied
ZX-UX-The-ZX-Spectrum-48K-Unix-Project-DEVELOPMENT directory.

All remaining commands in this guide are issued from the REPOSITORY ROOT.
Check that you have the right directory:

    test -d .git && test -d dist && test -d build/dependencies
    pwd

A GitHub source ZIP without the .git directory is NOT sufficient: the
clean-room script compares regenerated files against the Git tree.

4. CHECK THAT THE OFFLINE INSTALLER SET IS COMPLETE
---------------------------------------------------
You should have these tracked directories and files:

    build/dependencies/debian-13-amd64/apt/      (*.deb - full APT closure)
    build/dependencies/debian-13-amd64/pip/      (*.whl - Pillow wheel)
    build/dependencies/sjasmplus/sjasmplus-1.24.0-linux-amd64
    build/dependencies/sjasmplus/sjasmplus-1.24.0-src.tar.xz

Check the downloaded installers:

    ls build/dependencies/debian-13-amd64/apt/*.deb
    ls build/dependencies/debian-13-amd64/pip/*.whl
    ls -l build/dependencies/sjasmplus/

IMPORTANT: The five initial .deb files saved directly under
build/dependencies/debian-13-amd64/ are NOT the complete APT closure.
Do not attempt an offline setup until the apt/*.deb AND pip/*.whl
subdirectories have been populated and pushed to the mirrored checkout.

If they are missing, collect the packages on an ONLINE Debian 13/amd64
system with:

    bash build/dependencies/fetch-host-packages.sh

Then include the resulting apt/ and pip/ files in the repo mirror before
moving it to the offline machine. Do not use an Ubuntu package collection
for this Debian machine. A package bundle collected later may contain
versions newer than those on the Debian ISO.

5. INSTALL THE DEPENDENCIES FROM THE MIRROR, IN ORDER
-----------------------------------------------------
The short route is the provided offline installer:

    bash build/dependencies/install-debian13-offline.sh

It performs the three parts below. For manual setup, use these EXACT
commands instead of the installer (not as well as it).

Part A - Debian packages: compilers, build tools, Python/venv, Git,
         curl, Xvfb, X11 utilities/libraries, Fuse and its libraries.

    sudo apt-get -y --no-download --allow-downgrades \
      -o Dir::Etc::sourcelist=/dev/null \
      -o Dir::Etc::sourceparts=- \
      install "$PWD"/build/dependencies/debian-13-amd64/apt/*.deb

Do not run dpkg -i separately on random .deb files. APT resolves their
install order and dependencies. The options above prevent repository
downloads; a missing dependency is a real gap in the saved package set.

Part B - Pillow for Python image capture (offline, inside the same
         virtual environment path the GitHub build uses).

    python3 -m venv /tmp/zxux-py
    /tmp/zxux-py/bin/python -m pip install --no-index \
      --find-links "$PWD/build/dependencies/debian-13-amd64/pip" \
      'Pillow>=12.1,<13'

Part C - Install SJASMPlus 1.24.0 into the executable search path.

    sudo install -m 755 \
      build/dependencies/sjasmplus/sjasmplus-1.24.0-linux-amd64 \
      /usr/local/bin/sjasmplus
    hash -r
    command -v sjasmplus
    /usr/local/bin/sjasmplus --version

The command-v result should point to /usr/local/bin/sjasmplus, or another
intentionally installed version. The ZX-UX build calls
/usr/local/bin/sjasmplus by its full path. No shell alias is needed.

Optional: If you need to compile SJASMPlus from its source tarball instead,
use the build prerequisites installed above:

    mkdir -p /tmp/zxux-sjasmplus-build
    tar -xJf build/dependencies/sjasmplus/sjasmplus-1.24.0-src.tar.xz \
      -C /tmp/zxux-sjasmplus-build
    make -C /tmp/zxux-sjasmplus-build/sjasmplus-1.24.0 -j2
    sudo install -m 755 \
      /tmp/zxux-sjasmplus-build/sjasmplus-1.24.0/sjasmplus \
      /usr/local/bin/sjasmplus

6. CHECK THE TOOLS BEFORE DELETING ANY OUTPUT
---------------------------------------------
Run:

    test -x /usr/local/bin/sjasmplus
    test -x /usr/bin/fuse-sdl
    command -v Xvfb
    test -f /usr/share/fuse/fuse.font
    /tmp/zxux-py/bin/python -c 'from PIL import Image, ImageGrab, ImageChops; assert hasattr(Image.new("L",(1,1)), "get_flattened_data"); print("Pillow ready")'
    git rev-parse --show-toplevel

These should all succeed. The ROM and original ZX-UX boot tape are
provided by the Git checkout; do not replace them with other revisions.

7. RUN THE EXACT GITHUB CLEAN-ROOM BUILD COMMAND
------------------------------------------------
Read this warning first: the script intentionally DELETES the existing
dist/ directory, recreates it, runs all RVM and Fuse screenshot stages,
and compares every regenerated path against the tracked Git baseline.
Do not put personal files inside dist/.

From the root of the Git checkout, run EXACTLY what the workflow runs:

    bash build/tools/cleanroom-build-using-github-action-runner.sh

When the tools in step 6 are installed, the script reuses them instead of
re-downloading packages or requiring internet. On a fresh GitHub Ubuntu
runner without these tools, the same script installs them first.

The stages are, in order: build, c48-rvm, rbc-rvm, compilers-rvm,
c48-fuse, rbc-fuse, compilers-fuse, and gallery. Fuse uses two jobs and
independent Xvfb displays. The command can take substantial time.

8. READ THE RESULT
------------------
From the repository root:

    cat cleanroom-logs/exit-codes.tsv
    cat cleanroom-logs/audit-summary.txt
    find cleanroom-logs/fuse-processes -type f -name '*.fuse.log'

The run succeeds only when every required stage exits 0 and the audit
reports Missing=0. Rebuilt files should cover every tracked dist/ path.
"Changed" counts are diagnostic: screenshot pixels can differ between
emulator environments. Each stage has its own log in cleanroom-logs/.
The entire build works on a local machine without GitHub Actions;
the workflow merely runs the same script and uploads those logs.

If the apt/ or pip/ folders are missing, do not claim an offline build
was verified. Obtain the complete dependency bundle first.
