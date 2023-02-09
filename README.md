# siibra-mriwarp

> **Note: _siibra-mriwarp_ is still in development. You may still encounter bugs when using it.**

_siibra-mriwarp_ is an application that warps a whole brain MRI scan of an individual subject to [ICBM MNI152 2009c nonlinear asymmetric space](https://www.bic.mni.mcgill.ca/ServicesAtlases/ICBM152NLin2009). Furthermore, it allows probabilistic region assignment of a selected point to brain regions of [Julich Brain Atlas](https://julich-brain-atlas.de/).

Warping brain data to a standardized space like MNI152 enables anchoring to atlas volumes like [BigBrain](https://julich-brain-atlas.de/atlas/bigbrain). However, reasonable registration requires various steps that need a lot of optimization effort. _siibra_mriwarp_ aims to simplify the workflow of warping a patient's MRI scan to MNI152 space. With this application, you avoid installing multiple tools and tweaking many parameters for a proper registration result. Instead, _siibra-mriwarp_ is an easy-to-install and easy-to-use tool combining all necessary steps into one pipeline. 

You can immediately utilize the warping results in _siibra-mriwarp_ to assign brain regions to a point in the patient's space. Select a location in the displayed brain of a subject to perform a probabilistic assignment using Julich-Brain Cytoarchitectonic Maps 2.9. Hence, you can estimate the probability of a brain region occurring at the selected point. To explore even more information about a cytoarchitectonic area, you can access [_siibra-explorer_](https://atlases.ebrains.eu/viewer/human) through the application.

_siibra-mriwarp_ is a local application. Therefore, your data won't be stored on an online server but remains on your computer, which allows processing of **confidential data**.

![image](docs/images/teaser.png)

## Getting Started

_siibra-mriwarp_ is designed as a Windows application but can also be executed on Linux.

### Windows 10 or higher

#### Install siibra-mriwarp

1. Download the installer [here](https://fz-juelich.sciebo.de/s/N9taLOGoE5MiSz8/download).
2. Run the installer.
3. Run _siibra-mriwarp_ directly from the installer. Depending on the installation settings you have chosen, you can also run _siibra-mriwarp_ from the installation directory, the start menu or the desktop shortcut.

#### Uninstall siibra-mriwarp

Run `Uninstall` from the installation directory or the `siibra-mriwarp` folder in your start menu, depending on the installation settings that you chose. If you wish to delete the default output folder, delete `siibra-mriwarp` from your home directory. Note that this may remove warping results.

Hint: The default installation directory is `C:\Users\your_username\AppData\Local\siibra-mriwarp`.

### Linux

#### Requirements

* Python 3.8 or higher
* [ANTs](https://github.com/ANTsX/ANTs/wiki/Compiling-ANTs-on-Linux-and-Mac-OS)

#### Install siibra-mriwarp

1. Install all requirements.
2. Clone _siibra-mriwarp_ from GitHub:

        git clone https://github.com/FZJ-INM1-BDA/siibra-mriwarp.git

3. Install all Python requirements with pip:

        cd siibra-mriwarp
        pip install scikit-build
        pip install -r requirements.txt

5. Run _siibra-mriwarp_:

        python3 start_app.py
        
> **Warning: If you run _siibra-mriwarp_ via Python on Windows, you need to change all `"/"` in `HD_BET.utils.maybe_mkdir_p` to `"\\"`.**

#### Uninstall siibra-mriwarp

Delete `siibra-mriwarp` from the installation directory. If you wish to delete the default output folder, delete `siibra-mriwarp` from your home directory. Note that this may remove warping results.

## Usage and Help

Visit [siibra-mriwarp.readthedocs.io](https://siibra-mriwarp.readthedocs.io) or contact [support@ebrains.eu](mailto:support@ebrains.eu?subject=[siibra-mriwarp]).

## Authors

[Big Data Analytics Group](https://fz-juelich.de/en/inm/inm-1/research/big-data-analytics), Institute of Neuroscience and Medicine (INM-1), Forschungszentrum Jülich GmbH

## License

This project is licensed under the [NAME HERE] License - see the LICENSE.md file for details

## References

* [HD-BET](https://github.com/MIC-DKFZ/HD-BET)[^1] (skull removal)
* [ANTs](http://stnava.github.io/ANTs/) (warping)
* [siibra-python](https://github.com/FZJ-INM1-BDA/siibra-python) (region assignment)

[^1]: Isensee F, Schell M, Tursunova I, Brugnara G, Bonekamp D, Neuberger U, Wick A, Schlemmer HP, Heiland S, Wick W, Bendszus M, Maier-Hein KH, Kickingereder P. Automated brain extraction of multi-sequence MRI using artificial neural networks. Hum Brain Mapp. 2019; 1–13. [https://doi.org/10.1002/hbm.24750](https://doi.org/10.1002/hbm.24750)

## Acknowledgments

This software code is funded from the European Union’s Horizon 2020 Framework Programme for Research and Innovation under the Specific Grant Agreement No. 945539 (Human Brain Project SGA3).

![image](./data/hbp_ebrains_color_dark.png)
