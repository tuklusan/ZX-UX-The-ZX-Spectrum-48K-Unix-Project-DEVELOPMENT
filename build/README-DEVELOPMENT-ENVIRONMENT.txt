ZX-UX DEVELOPMENT ENVIRONMENT - FRESH DEBIAN 13 AMD64 MACHINE
=================================================================

Purpose
-------
This guide is build/README-DEVELOPMENT-ENVIRONMENT.txt, beside build.py.
The installer packages and helper scripts are in build/dependencies/.

Take a full Git checkout of this repository to a new Debian 13 (trixie)
64-bit PC or virtual machine, install the saved build dependencies, and run
the same clean-room rebuild command used by GitHub Actions.

Use Debian 13/amd64 (Intel or AMD x86-64), NOT Ubuntu, Debian testing, or
ARM64 with the packages in build/dependencies/. The Debian package archive
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
tracked dist/ directory, from USB/shared storage. On the ONLINE source
machine, run 'git lfs pull' before copying, so the working tree contains
real dependency packages instead of LFS pointer text. The path on your USB
depends on how it is mounted. Copy it into your home directory.

If connected to the internet, prepare Git LFS and clone the actual binary
installers (Git without LFS would leave small pointer files instead):

    sudo apt-get update
    sudo apt-get install -y git git-lfs
    git lfs install
    git clone https://github.com/tuklusan/ZX-UX-The-ZX-Spectrum-48K-Unix-Project-DEVELOPMENT.git
    cd ZX-UX-The-ZX-Spectrum-48K-Unix-Project-DEVELOPMENT
    git lfs pull

On an EXISTING online mirror, use 'git lfs install', 'git pull --ff-only',
then 'git lfs pull' to update and hydrate the new binary files.

If copying from a USB volume named ZXUSB, for example, enter:
(change ZXUSB to your actual USB volume name)

    cp -a "/media/$USER/ZXUSB/ZX-UX-The-ZX-Spectrum-48K-Unix-Project-DEVELOPMENT" "$HOME/"
    cd "$HOME/ZX-UX-The-ZX-Spectrum-48K-Unix-Project-DEVELOPMENT"

You can instead copy the directory with a file manager, but make sure .git
and the tracked dist/ files are copied. If your USB is mounted elsewhere,
use its actual path in the cp command.

All commands below assume you are at the REPOSITORY ROOT, NOT in build/
or build/dependencies/. If you opened a terminal in build/, run 'cd ..'
before following the commands. Check that you have the right directory:

    test -d .git && test -d dist && test -d build/dependencies
    test -f build/README-DEVELOPMENT-ENVIRONMENT.txt
    pwd

A GitHub source ZIP without the .git directory is NOT sufficient: the
clean-room script compares regenerated files against the Git tree.

4. CHECK THAT THE OFFLINE INSTALLER SET IS COMPLETE
---------------------------------------------------
The required installers are already in the repository. The dependency
bundle was collected and verified for Debian 13/amd64:

    build/dependencies/debian-13-amd64/apt/      (248 .deb packages)
    build/dependencies/debian-13-amd64/pip/      (Pillow 12.3.0 wheel)
    build/dependencies/sjasmplus/sjasmplus-1.24.0-linux-amd64
    build/dependencies/sjasmplus/sjasmplus-1.24.0-src.tar.xz

The binary installers are in Git LFS. Before copying the repository to
an offline PC, run 'git lfs pull' on the online mirror. Copy the actual
files, not the small Git LFS pointer files.

From the REPOSITORY ROOT, check that the installers exist:

    ls build/dependencies/debian-13-amd64/apt/*.deb
    ls build/dependencies/debian-13-amd64/pip/*.whl
    ls -l build/dependencies/sjasmplus/

Check that ALL the .deb packages are real Debian archives and the
Pillow wheel is a ZIP file, not a Git LFS pointer:

    for pkg in build/dependencies/debian-13-amd64/apt/*.deb; do
        dpkg-deb --info "$pkg" >/dev/null || { echo "BAD: $pkg"; break; }
    done
    for wheel in build/dependencies/debian-13-amd64/pip/*.whl; do
        test "$(head -c 2 "$wheel")" = PK || { echo "BAD: $wheel"; break; }
    done

If a file is invalid, run 'git lfs pull' on a CONNECTED mirror and
copy the hydrated files again.

The five extra .deb files directly in
build/dependencies/debian-13-amd64/ are historical individual packages.
They are NOT the complete APT dependency set. The offline installer uses
the 248 packages in the apt/ subdirectory.

OFFLINE VERIFICATION: GitHub Actions run 41268220921 passed. In a fresh
Debian 13 container with networking disabled, the tracked APT packages
and Pillow installed successfully, Git LFS and the Fuse/Xvfb prerequisites
were checked, SJASMPlus was installed, and the ZX-UX core build completed:

    python3 -B build/build.py /usr/local/bin/sjasmplus

This confirms the OFFLINE DEPENDENCY INSTALLATION AND CORE BUILD, not a
full Debian VM installation from ISO or all Fuse screenshot portfolio
stages. The entire clean-room pipeline is run in step 7.

5. INSTALL THE DEPENDENCIES FROM THE MIRROR, IN ORDER
-----------------------------------------------------
The short route is the provided offline installer:

    bash build/dependencies/install-debian13-offline.sh

It performs the three parts below. For manual setup, use these EXACT
commands instead of the installer (not as well as it).

Part A - Debian packages: compilers, build tools, Python/venv, Git,
         curl, Xvfb, X11 utilities/libraries, Fuse and its libraries.

    sudo apt-get -y --allow-downgrades \
      -o Dir::Etc::sourcelist=/dev/null \
      -o Dir::Etc::sourceparts=- \
      install "$PWD"/build/dependencies/debian-13-amd64/apt/*.deb

Do not run dpkg -i separately on random .deb files. APT resolves their
install order and dependencies. The APT source-list options prevent network
repository downloads; a missing dependency is a real gap in the saved set.
Avoid --no-download here: APT needs to process the local .deb paths.

The APT bundle also installs git-lfs. Initialize it for the local mirror:

    git lfs install

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

The installed executable must be /usr/local/bin/sjasmplus, and its
version output must say 1.24.0. The ZX-UX build calls this full path
directly. No shell alias is needed.

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
    /usr/local/bin/sjasmplus --version
    test -x /usr/bin/fuse-sdl
    command -v Xvfb
    test -f /usr/share/fuse/fuse.font
    /tmp/zxux-py/bin/python -c 'from PIL import Image, ImageGrab, ImageChops; assert hasattr(Image.new("L",(1,1)), "get_flattened_data"); print("Pillow ready")'
    git rev-parse --show-toplevel
    git lfs version
    git ls-tree -r HEAD dist | sed -n '1,3p'

These should all succeed. If any step fails, repair it before running
the clean-room command. In particular, if a dependency is absent the
build script may try to download/install packages from the internet.
That cannot work offline. The ROM and original ZX-UX boot tape are
provided by the Git checkout; do not replace them with other revisions.

The Pillow virtual environment is under /tmp. After a reboot or a
clean-up that removes /tmp/zxux-py, repeat Part B in step 5.

7. RUN THE EXACT GITHUB CLEAN-ROOM BUILD COMMAND
------------------------------------------------
Read this warning first: the script intentionally DELETES the existing
dist/ directory, recreates it, runs all RVM and Fuse screenshot stages,
and compares every regenerated path against the tracked Git baseline.
Do not put personal files inside dist/.

From the root of the Git checkout, run EXACTLY what the workflow runs:

    bash build/tools/cleanroom-build-using-github-action-runner.sh

When every tool in step 6 is installed, the script reuses it instead
of downloading packages. On a fresh GitHub Ubuntu runner without the
tools, the same script installs them first. This is the same SCRIPT and
build sequence as the workflow, but the host OS and tool binaries differ
from GitHub's Ubuntu 24.04 environment; screenshot byte-for-byte
identity is therefore not promised.

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
reports Missing=0. The script returns a non-zero exit code on failure.
Rebuilt files should cover every tracked dist/ path.
"Changed" counts are diagnostic: screenshot pixels can differ between
emulator environments. Each stage has its own log in cleanroom-logs/.
The entire build works on a local machine without GitHub Actions;
the workflow merely runs the same script and uploads those logs.

If the apt/ or pip/ files are missing, the local copy is incomplete.
Run 'git lfs pull' on a connected mirror and transfer the actual files
before attempting the offline installation.
