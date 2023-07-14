# voluba-mriwarp

> **Note: _voluba-mriwarp_ is still in development. You may still encounter bugs when using it.**

voluba (**Volu**metric **B**rain **A**nchoring) offers tools to connect volumetric imaging data to multilevel atlases and in this way makes it accessible for analysis with the siibra toolsuite.

_voluba-mriwarp_ is a desktop application that integrates whole-brain T1-weighted MRI scans into the anatomical context of the [EBRAINS Human Brain Atlas](https://www.ebrains.eu/tools/human-brain-atlas). It incorporates all required components like skull stripping, registration to [MNI ICBM 152 2009c Nonlinear Asymmetric space](https://www.bic.mni.mcgill.ca/ServicesAtlases/ICBM152NLin2009), and detailed analysis with the siibra toolsuite. The corresponding functionalities are provided via open-source tools like [HD-BET](https://github.com/MIC-DKFZ/HD-BET)[^1], [ANTs](http://stnava.github.io/ANTs/) and [siibra-python](https://github.com/FZJ-INM1-BDA/siibra-python). _voluba-mriwarp_ is primarily designed for Windows 10 but can also be executed on Linux.

> We designed _voluba-mriwarp_ as a desktop application. Therefore, **the input MRI dataset will not be uploaded to any online services**. It remains only on your local computer.

Warping brain data to a standardized space like MNI152 enables anchoring of whole-brain MRI scans to atlas volumes and therefore facilitates analysis in a detailed anatomical context. However, reasonable registration requires various steps that need optimization effort. _voluba-mriwarp_ aims to simplify this workflow. With this application, you avoid installing multiple tools and tweaking parameters for a proper registration result. Instead, _voluba-mriwarp_ is an easy-to-install and easy-to-use tool combining all necessary steps into one pipeline. 

_voluba-mriwarp_ applies a set of predefined parameters to remove the skull and warp the input brain scan to MNI152 space. You can utilize the warping results in _voluba-mriwarp_ to interactively analyze points by making a probabilistic assignment of coordinates in the input space to brain regions of the [EBRAINS Human Brain Atlas](https://www.ebrains.eu/tools/human-brain-atlas). To get an overview of more information about a brain region, you can access [siibra-explorer](https://atlases.ebrains.eu/viewer/human) through the application. For further analysis, _voluba-mriwarp_ offers to export the anatomical assignments together with linked multimodal data features like receptor densities, cell distributions or brain connectivity.

![image](docs/images/teaser.png)

## Getting Started

_voluba-mriwarp_ is designed as a Windows application but can also be executed on Linux.

### Windows 10 or higher

#### Install voluba-mriwarp

1. Download the installer [here](https://github.com/FZJ-INM1-BDA/voluba-mriwarp/releases/download/v0.2.0/installer.exe).
2. Run the installer.
3. Run _voluba-mriwarp_ directly from the installer. Depending on the installation settings you have chosen, you can also run _voluba-mriwarp_ from the installation directory, the start menu or the desktop shortcut.

#### Uninstall voluba-mriwarp

Run `Uninstall` from the installation directory or the `voluba-mriwarp` folder in your start menu, depending on the installation settings that you chose. If you wish to delete the default output folder, delete `voluba-mriwarp` from your home directory. Note that this may remove warping results.

Hint: The default installation directory is `C:\Users\your_username\AppData\Local\voluba-mriwarp`.

### Linux

#### Requirements

* Python 3.8 or higher
* [ANTs Eotapinoma](https://github.com/ANTsX/ANTs/releases/tag/v2.4.4)

#### Install voluba-mriwarp

1. Install all requirements.
2. Clone _voluba-mriwarp_ from GitHub:

        git clone https://github.com/FZJ-INM1-BDA/voluba-mriwarp.git

3. Install all Python requirements with pip:

        cd voluba-mriwarp
        pip install scikit-build
        pip install -r requirements.txt

5. Run _voluba-mriwarp_:

        python3 start_app.py
        
> **Warning: If you run _voluba-mriwarp_ via Python on Windows, you need to change all `"/"` in `HD_BET.utils.maybe_mkdir_p` to `"\\"`.**

#### Uninstall voluba-mriwarp

Delete `voluba-mriwarp` from the installation directory. If you wish to delete the default output folder, delete `voluba-mriwarp` from your home directory. Note that this may remove warping results.

## Usage and Help

Visit [voluba-mriwarp.readthedocs.io](https://voluba-mriwarp.readthedocs.io) or contact [support@ebrains.eu](mailto:support@ebrains.eu?subject=[voluba-mriwarp]).

## Authors

[Big Data Analytics Group](https://fz-juelich.de/en/inm/inm-1/research/big-data-analytics), Institute of Neuroscience and Medicine (INM-1), Forschungszentrum Jülich GmbH

## License

This project is licensed under the Apache License 2.0 - see the LICENSE file for details

## References

* [HD-BET](https://github.com/MIC-DKFZ/HD-BET)[^1] (skull removal)
* [ANTs](http://stnava.github.io/ANTs/) (warping)
* [siibra-python](https://github.com/FZJ-INM1-BDA/siibra-python) (analysis in atlas context)

[^1]: Isensee F, Schell M, Tursunova I, Brugnara G, Bonekamp D, Neuberger U, Wick A, Schlemmer HP, Heiland S, Wick W, Bendszus M, Maier-Hein KH, Kickingereder P. Automated brain extraction of multi-sequence MRI using artificial neural networks. Hum Brain Mapp. 2019; 1–13. [https://doi.org/10.1002/hbm.24750](https://doi.org/10.1002/hbm.24750)

## Acknowledgments

This software code is funded from the European Union’s Horizon 2020 Framework Programme for Research and Innovation under the Specific Grant Agreement No. 945539 (Human Brain Project SGA3).
