# Build instructions

The following sections show the scripts that were used to build the release artifacts of version [v0.2.0](https://github.com/FZJ-INM1-BDA/voluba-mriwarp/releases/tag/v0.2.0). For this release, only the Windows executable and installer were built (on a Windows 10 Virtual Machine). Although voluba-mriwarp was intended for Windows, a [Linux executable](#linux) can be built. As the configuration was figured out after the latest release, it is not yet included in the artifacts. For upcoming releases, the executable should certainly be added. If ANTs or siibra get updated to a newer version, the scripts need to be adjusted (explained in the following sections). Furthermore, the build process should be moved to [GitHub Actions](https://docs.github.com/de/actions).

------------------

## Windows

The actual Windows release artifact is a Windows installer which is scripted via the [Nullsoft Scriptable Install System (NSIS)](https://nsis.sourceforge.io/Developer_Center). The installer copies the Windows executable and all its dependencies into `$LOCALAPPDATA\voluba-mriwarp` on the user's computer (see [NSIS installer script](#nsis-installer-script)). The Windows executable is built with [pyinstaller](https://pyinstaller.org/en/stable/) which creates a directory including all dependencies and the exe file itself. In general, pyinstaller can also create one single exe file, but this did not work for voluba-mriwarp. In the following sections, all scripts for building the executable and installer are listed as well as instructions on what to change in case of updates. Supplementary material (`import_siibra.py` and `mriwarp.nsi`) can be found in [Supplementary scripts](#supplementary-scripts).

### Prerequisites

To execute build process the following requirements need to be met:

- [Git](https://git-scm.com/download/win)  
- [Python 3.8](https://www.python.org/downloads/release/python-380/)  
- [NSIS](https://nsis.sourceforge.io/Download)

### Setup build environment

The following Powershell script gathers all dependencies required to build the release artifacts:

```powershell title="setup_environment.ps1"
# Execute where voluba-mriwarp should be built.
# Get the code.
git clone https://github.com/FZJ-INM1-BDA/voluba-mriwarp.git
cd voluba-mriwarp
# Setup python build environment
python -m venv venv
venv/Scripts/activate
pip install -r requirements.txt
pip install pyinstaller
pip install jinja2
pip install python-dotenv
# Download HD-BET model for skull stripping
cd data
mkdir hd-bet_params
cd hd-bet_params
curl https://zenodo.org/record/2540695/files/0.model?download=1 -o 0.model
cd ../..
# Change HD-BET path
# Explanation: 
# The storage location of the HD-BET model is defined in HD_BET/paths.py and 
# defaults to the user's home directory. In the case of voluba-mriwarp, 
# the model is shipped with the artifacts in the `data` directory. Therefore 
# the path needs to be changed to `data/hd-bet_params`.
cd venv/Lib/site-packages/HD_BET
(Get-Content paths.py) -replace "os.path.join\(os.path.expanduser\('~'\), 'hd-bet_params'\)" "'data/hd-bet_params'" | Set-Content paths.py
cd ../../../..
# Download ANTs executables
curl https://github.com/ANTsX/ANTs/releases/download/v2.4.4/ants-2.4.4-windows-2022-X64-VS2019.zip -o ants.zip
Expand-Archive .\ants.zip -DestinationPath .
# Build siibra importer
# Explanation:
# During installation all probability maps of MNI152 space are fetched once.
# Thus they are cached which leads to faster region assignments. Therefore
# an executable is build from import_siibra.py, which can be found in the 
# Supplementary Scripts section of this document.
pyinstaller --noconfirm --onefile --console --icon "./data/voluba-mriwarp.ico" --name "import_siibra" --add-data "./venv/Lib/site-packages/siibra;siibra/" "import_siibra.py"
```

### Create artifacts

The following Powershell script builds the release artifacts (Windows executable and installer):

```powershell title="create_artifacts.ps1"
# Execute in voluba-mriwarp git repository 
# Get the latest version of voluba-mriwarp
git checkout main
git pull
# Build voluba-mriwarp executable
venv/Scripts/activate
pyinstaller --noconfirm --onedir --windowed --icon "./data/voluba-mriwarp.ico" --name "voluba-mriwarp" --add-data "./data;data/" --add-data "./venv/Lib/site-packages/HD_BET;HD_BET/" --add-data "./venv/Lib/site-packages/siibra;siibra/" --add-data "./venv/Lib/site-packages/sklearn;sklearn/" --add-data "./venv/Lib/site-packages/tksvg;tksvg/" --add-data "./venv/Lib/site-packages/nilearn;nilearn/" --add-data "./ants-2.4.4/bin/antsApplyTransformsToPoints.exe;." --add-data "./ants-2.4.4/bin/antsRegistration.exe;." --add--data "./dist/import_siibra.exe;." "./start_app.py" 
cd dist
# Explanation:
# After installation, there will be `$LOCALAPPDATA\voluba-mriwarp` which
# contains the pyinstaller output as well as a link to the exe file inside
# and the uninstaller. Thus the pyinstaller output needs to be placed inside
# another `voluba-mriwarp` directory before executing the NSIS script.
mkdir voluba-mriwarp2
mv voluba-mriwarp voluba-mriwarp2
mv voluba-mriwarp2 voluba-mriwarp
cd ..
# Build voluba-mriwarp installer
& 'makensis.exe' mriwarp.nsi
```

### Potential changes

Whenever one or more of the following changes are done the whole build process needs to be rerun:

| Change | Line number | What to do | Comment |
|----------|-------------|----------------|---------|
| Update ANTs version | #L23 in [setup_environment.ps1](#setup-build-environment) | Update the download path to the according [ANTs release](https://github.com/ANTsX/ANTs/releases) Windows artifact. | The currently used version is [Eotapinoma](https://github.com/ANTsX/ANTs/releases/tag/v2.4.4), but a newer version is already available. |
| Update siibra version | #L3 et sqq. in [siibra importer](#siibra-importer) | Depending on the changes made in siibra itself getting and fetching probability maps of MNI152 space needs to be adjusted accordingly. |
| Add/Update/Change python dependencies | #L7 in [create_artifacts.ps1](#create-artifacts) | It may occur that pyinstaller will be missing (hidden) dependencies. See info below. | Under Windows Python dependency directories can be found in `venv/Lib/site-packages`. |

!!! info
    pyinstaller often is not able to figure out all dependencies by itself. To solve this, you can either specify missing modules via `--hidden-imports` or add the dependency directly from the virtual environment via `--add-data` (which worked best so far). Unfortunately, figuring out which dependencies are missing has to be done by trial and error. Good sources are the pyinstaller log, error messages popping up during execution of the produced exe file or the voluba-mriwarp log in `$TEMP/voluba-mriwarp.log`.

------------------

## Linux

The Linux release artifact is a tar.gz archive. The Linux executable is built with [pyinstaller](https://pyinstaller.org/en/stable/) which creates a directory including all dependencies and the exe file itself. In general, pyinstaller can also create one single exe file, but this did not work for voluba-mriwarp. In the following sections, all scripts for building the executable are listed as well as instructions on what to change in case of updates.

### Prerequisites

To execute the build scripts the following requirements need to be met:

- [Git](https://git-scm.com/download/win)  
- [Python 3.8](https://www.python.org/downloads/release/python-380/)  
- unzip

!!! warning
    The following scripts have been tested on an Ubuntu 20.04 LTS machine. When trying them out on a Virtual Machine or in GitHub actions there could be more prerequisites, which were already present on the testing machine but are not part of the default Ubuntu software.

### Setup build environment

The following bash script gathers all dependencies required to build the release artifacts:

```bash title="setup_environment.sh"
# Execute where voluba-mriwarp should be built
# Get the code
git clone https://github.com/FZJ-INM1-BDA/voluba-mriwarp.git
cd voluba-mriwarp
# Setup python build environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install pyinstaller
pip install jinja2
pip install python-dotenv
# Download HD-BET model
cd data
mkdir hd-bet_params
cd hd-bet_params
curl https://zenodo.org/record/2540695/files/0.model?download=1 -o 0.model
cd ../..
# Change HD-BET path
# Explanation: 
# The storage location of the HD-BET model is defined in HD_BET/paths.py and 
# defaults to the user's home directory. In the case of voluba-mriwarp, 
# the model is shipped with the artifacts in the `data` directory. Therefore 
# the path needs to be changed to `data/hd-bet_params`.
cd venv/lib/python3.8/site-packages/HD_BET
sed -i "s@os.path.join(os.path.expanduser('~'), 'hd-bet_params')@'data/hd-bet_params'@g" paths.py
cd ../../../../..
# Download ANTs executables 
wget -O ants.zip https://github.com/ANTsX/ANTs/releases/download/v2.4.4/ants-2.4.4-ubuntu-20.04-X64-gcc.zip
unzip ants.zip
```

### Create artifacts

The following bash script builds the release artifacts (Linux executable):

```bash title="create_artifacts.sh"
# Execute in voluba-mriwarp git repository 
# Get the latest version of voluba-mriwarp
git checkout main
git pull
# Build voluba-mriwarp executable
source venv/bin/activate
pyinstaller --noconfirm --onedir --windowed --icon "data/voluba-mriwarp.ico" --name "voluba-mriwarp" --add-data "data/:data/" --add-data "venv/lib/python3.8/site-packages/HD_BET:HD_BET/" --add-data "venv/lib/python3.8/site-packages/siibra:siibra/" --add-data "venv/lib/python3.8/site-packages/skimage/:skimage/" --add-data "venv/lib/python3.8/site-packages/PIL/:PIL/" --add-data "venv/lib/python3.8/site-packages/tksvg:tksvg/" --add-data "ants-2.4.4/bin/antsApplyTransformsToPoints:." --add-data "ants-2.4.4/bin/antsRegistration:." "start_app.py"
# Package everything into tar.gz
cd dist
tar cfvz voluba-mriwarp.tar.gz voluba-mriwarp
```

!!! info
    With this configuration the voluba-mriwarp artifacts can only be executed via command-line directly from the `voluba-mriwarp` directory (`./voluba-mriwarp`). Executing the application via double-click from the file explorer is **not** possible.

### Potential changes

Whenever one or more of the following changes are done the whole build process needs to be rerun:

| Change | Line number | What to do | Comment |
|----------|-------------|----------------|---------|
| Update ANTs version | #L28 in [setup_environment.sh](#setup-build-environment-1) | Update the download path to the according [ANTs release](https://github.com/ANTsX/ANTs/releases) Linux artifact. | The currently used version is [Eotapinoma](https://github.com/ANTsX/ANTs/releases/tag/v2.4.4), but a newer version is already available. |
| Add/Update/Change python dependencies | #L7 in [create_artifacts.sh](#create-artifacts-1) | It may occur that pyinstaller will be missing (hidden) dependencies. See info below. | Under Windows Python dependency directories can be found in `venv/lib/python3.8/site-packages`. |

!!! info
    pyinstaller often is not able to figure out all dependencies by itself. To solve this, you can either specify missing modules via `--hidden-imports` or add the dependency directly from the virtual environment via `--add-data` (which worked best so far). Unfortunately, figuring out which dependencies are missing has to be done by trial and error. Good sources are the pyinstaller log, error messages popping up during execution of the produced exe file or the voluba-mriwarp log in `$TEMP/voluba-mriwarp.log`.

------------------

## Supplementary scripts

The following scripts are needed for building a [Windows executable and installer](#windows).

### siibra importer

```python title="voluba_mriwarp/import_siibra.py"
import siibra

# Get all probability maps in MNI152 space.
mni152 = siibra.spaces['mni152']
pmaps = siibra.maps.dataframe
mni_pmaps = pmaps[(pmaps.maptype == 'STATISTICAL') & (pmaps.space == mni152.name)]

# Prefetch all maps to minimize the time for region assignment.
for index in mni_pmaps.index:
    try:
        _ = siibra.maps[index].sparse_index
    except:
        continue
```

### NSIS installer script

```nsis title="voluba-mriwarp/mriwarp.nsi"
!include "MUI.nsh"

RequestExecutionLevel user
Name "voluba-mriwarp"
!define INSTALLATIONNAME "voluba-mriwarp"
OutFile ".\dist\installer.exe"
InstallDir "$LOCALAPPDATA\${INSTALLATIONNAME}"

;----------------------------------------------------------------------------------------
; Icons
!define MUI_ICON ".\data\voluba-mriwarp.ico"
!define MUI_HEADERIMAGE
!define MUI_HEADERIMAGE_BITMAP ".\data\voluba-mriwarp.ico"
!define MUI_HEADERIMAGE_RIGHT

; Install Pages
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE ".\LICENSE"
!insertmacro MUI_PAGE_DIRECTORY
    # variable for the startmenu name selected by the user
    Var StartMenuFolder
!insertmacro MUI_PAGE_STARTMENU 0 "$StartMenuFolder"
!insertmacro MUI_PAGE_INSTFILES
    # modified settings for MUI_PAGE_FINISH
    # Desktop Shortcut
    !define MUI_FINISHPAGE_SHOWREADME
    !define MUI_FINISHPAGE_SHOWREADME_NOTCHECKED
    !define MUI_FINISHPAGE_SHOWREADME_TEXT "Create Desktop Shortcut"
    !define MUI_FINISHPAGE_SHOWREADME_FUNCTION CreateDesktopShortcut
    # Run App
    !define MUI_FINISHPAGE_RUN
    !define MUI_FINISHPAGE_RUN_NOTCHECKED
    !define MUI_FINISHPAGE_RUN_FUNCTION RunShortcut
!insertmacro MUI_PAGE_FINISH

; Uninstall Pages
!insertmacro MUI_UNPAGE_WELCOME
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

; Languages
!insertmacro MUI_LANGUAGE "English"

;----------------------------------------------------------------------------------------
; Sections
Section ""
    SetOutPath "$INSTDIR"
    File /nonfatal /a /r ".\dist\${INSTALLATIONNAME}\"
    WriteUninstaller "$INSTDIR\uninstall.exe"
    DetailPrint "Fetch siibra components: This may take a while ..."
    nsExec::Exec "$INSTDIR\${INSTALLATIONNAME}\import_siibra.exe"
    Pop $0
SectionEnd

Section "Shortcut"
    SetOutPath "$INSTDIR\${INSTALLATIONNAME}"
    CreateShortCut "$INSTDIR\${INSTALLATIONNAME}.lnk" "$INSTDIR\${INSTALLATIONNAME}\${INSTALLATIONNAME}.exe"
SectionEnd

Section -StartMenu
    !insertmacro MUI_STARTMENU_WRITE_BEGIN 0
    SetOutPath "$INSTDIR\${INSTALLATIONNAME}"
    CreateDirectory "$SMPROGRAMS\$StartMenuFolder"
    CreateShortCut "$SMPROGRAMS\$StartMenuFolder\Uninstall.lnk" "$INSTDIR\uninstall.exe"
    CreateShortCut "$SMPROGRAMS\$StartMenuFolder\${INSTALLATIONNAME}.lnk" "$INSTDIR\${INSTALLATIONNAME}\${INSTALLATIONNAME}.exe"
    !insertmacro MUI_STARTMENU_WRITE_END
SectionEnd

Section "Uninstall"
    Delete "$INSTDIR\uninstall.exe"
    Delete "$DESKTOP\${INSTALLATIONNAME}.lnk"
    Delete "$INSTDIR\${INSTALLATIONNAME}.lnk"
    RMDir /r "$INSTDIR\${INSTALLATIONNAME}"
    RMDir "$INSTDIR"
    !insertmacro MUI_STARTMENU_GETFOLDER 0 $R0
    Delete "$SMPROGRAMS\$R0\*.*"
    RMDir "$SMPROGRAMS\$R0"
SectionEnd

;----------------------------------------------------------------------------------------
; Functions
Function CreateDesktopShortcut
    SetOutPath "$INSTDIR\${INSTALLATIONNAME}"
    CreateShortCut "$DESKTOP\${INSTALLATIONNAME}.lnk" "$INSTDIR\${INSTALLATIONNAME}\${INSTALLATIONNAME}.exe"
FunctionEnd

Function RunShortcut
    ExecShell "" "$INSTDIR\${INSTALLATIONNAME}.lnk"
FunctionEnd
```
