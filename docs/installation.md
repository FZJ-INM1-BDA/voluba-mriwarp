# Installation

_voluba-mriwarp_ is designed as a [Windows](#fa-windows-windows-10-or-higher) application but can also be executed on [Linux](#linux).

## :fa-windows: &nbsp; Windows 10 or higher

### Install voluba-mriwarp

1. Download the installer [here](https://fz-juelich.sciebo.de/s/xbjgb8yx7Jw01Jq/download).
2. Run the installer.
3. Run _voluba-mriwarp_ directly from the installer. Depending on the installation settings you have chosen, you can also run _voluba-mriwarp_ from the installation directory, the start menu or the desktop shortcut.

### Uninstall voluba-mriwarp

Run `Uninstall` from the installation directory or the `voluba-mriwarp` folder in your start menu, depending on the installation settings that you chose. If you wish to delete the default output folder, delete `voluba-mriwarp` from your home directory. Note that this may remove warping results.

!!! hint
    The default installation directory is `C:\Users\your_username\AppData\Local\voluba-mriwarp`.

## :fa-linux: &nbsp; Linux

### Requirements

* Python 3.8 or higher
* [ANTs](https://github.com/ANTsX/ANTs/wiki/Compiling-ANTs-on-Linux-and-Mac-OS) <span style="color:red">**TODO** Specify exact ANTs version, if Linux EXE won't work</span>  

### Install voluba-mriwarp

1. Install all [requirements](#requirements).
2. Clone _voluba-mriwarp_ from GitHub:

        :::bash
        git clone https://github.com/FZJ-INM1-BDA/voluba-mriwarp.git

3. Install all Python requirements with pip:

        :::bash
        cd voluba-mriwarp
        pip install scikit-build
        pip install -r requirements.txt

4. Run _voluba-mriwarp_:

        :::bash
        python3 start_app.py

!!! warning
    If you run _voluba-mriwarp_ via Python on Windows, you need to change all `"/"` in `HD_BET.utils.maybe_mkdir_p` to `"\\"`.

### Uninstall voluba-mriwarp

Delete `voluba-mriwarp` from the installation directory. If you wish to delete the default output folder, delete `voluba-mriwarp` from your home directory. Note that this may remove warping results.
