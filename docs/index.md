# About voluba-mriwarp

> **Note: _voluba-mriwarp_ is still in development. You may still encounter bugs when using it.**

voluba (**Volu**metric **B**rain **A**nchoring) offers tools to connect volumetric imaging data to multilevel atlases and in this way makes it accessible for analysis with the siibra toolsuite.

_voluba-mriwarp_ is a desktop application that integrates whole-brain T1-weighted MRI scans into the anatomical context of the [EBRAINS Human Brain Atlas](https://www.ebrains.eu/tools/human-brain-atlas). It incorporates all required components like skull stripping, registration to [MNI ICBM 152 2009c Nonlinear Asymmetric space](https://www.bic.mni.mcgill.ca/ServicesAtlases/ICBM152NLin2009), and detailed analysis with the siibra toolsuite. The corresponding functionalities are provided via open-source tools like [HD-BET](https://github.com/MIC-DKFZ/HD-BET)[^1], [ANTs](http://stnava.github.io/ANTs/) and [siibra-python](https://github.com/FZJ-INM1-BDA/siibra-python). _voluba-mriwarp_ is primarily designed for Windows 10 but can also be executed on Linux.

<div class="admonition info">
<p class="admonition-title">Your data remains on your computer</p>
<p>We designed <em>voluba-mriwarp</em> as a desktop application. Therefore, the input MRI dataset will not be uploaded to any online services. It remains only on your local computer.</p>
</div>

Warping brain data to a standardized space like MNI152 enables anchoring of whole-brain MRI scans to atlas volumes and therefore facilitates analysis in a detailed anatomical context. However, reasonable registration requires various steps that need optimization effort. _voluba-mriwarp_ aims to simplify this workflow. With this application, you avoid installing multiple tools and tweaking parameters for a proper registration result. Instead, _voluba-mriwarp_ is an easy-to-install and easy-to-use tool combining all necessary steps into one pipeline. 

_voluba-mriwarp_ applies a set of predefined parameters to remove the skull and warp the input brain scan to MNI152 space. You can utilize the warping results in _voluba-mriwarp_ to interactively analyze points by making a probabilistic assignment of coordinates in the input space to brain regions of the [EBRAINS Human Brain Atlas](https://www.ebrains.eu/tools/human-brain-atlas). To get an overview of more information about a brain region, you can access [siibra-explorer](https://atlases.ebrains.eu/viewer/human) through the application. For further analysis, _voluba-mriwarp_ offers to export the anatomical assignments together with linked multimodal data features like receptor densities, cell distributions or brain connectivity.

![image_centered](images/teaser2.png)

[^1]: Isensee F, Schell M, Tursunova I, Brugnara G, Bonekamp D, Neuberger U, Wick A, Schlemmer HP, Heiland S, Wick W, Bendszus M, Maier-Hein KH, Kickingereder P. Automated brain extraction of multi-sequence MRI using artificial neural networks. Hum Brain Mapp. 2019; 1–13. [https://doi.org/10.1002/hbm.24750](https://doi.org/10.1002/hbm.24750)