# Installation

_siibra-mriwarp_ is designed as a [Windows](#fa-windows-windows-10-or-higher) application but can also be executed on [Linux](#linux).

## :fa-windows: &nbsp; Windows 10 or higher

### Install siibra-mriwarp

1. Download the installer [here](https://fz-juelich.sciebo.de/s/N9taLOGoE5MiSz8/download).
2. Run the installer.
3. Run _siibra-mriwarp_ directly from the installer. Depending on the installation settings you have chosen, you can also run _siibra-mriwarp_ from the installation directory, the start menu or the desktop shortcut.

### Uninstall siibra-mriwarp

Run `Uninstall` from the installation directory or the `siibra-mriwarp` folder in your start menu, depending on the installation settings that you chose. If you wish to delete the default output folder, delete `siibra-mriwarp` from your home directory. Note that this may remove warping results.

!!! hint
    The default installation directory is `C:\Users\your_username\AppData\Local\siibra-mriwarp`.

## :fa-linux: &nbsp; Linux

### Requirements

* Python 3.8 or higher
* [ANTs](https://github.com/ANTsX/ANTs/wiki/Compiling-ANTs-on-Linux-and-Mac-OS)

### Install siibra-mriwarp

1. Install all [requirements](#requirements).
2. Clone _siibra-mriwarp_ from GitHub:

        :::bash
        git clone https://github.com/FZJ-INM1-BDA/siibra-mriwarp.git

3. Install all Python requirements with pip:

        :::bash
        cd siibra-mriwarp
        pip install -r requirements.txt

4. Run _siibra-mriwarp_:

        :::bash
        python3 start_app.py

### Uninstall siibra-mriwarp

Delete `siibra-mriwarp` from the installation directory. If you wish to delete the default output folder, delete `siibra-mriwarp` from your home directory. Note that this may remove warping results.
