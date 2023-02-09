# About siibra-mriwarp

> **Note: _siibra-mriwarp_ is still in development. You may still encounter bugs when using it.**

_siibra-mriwarp_ is an application that warps a whole brain MRI scan of an individual subject to [ICBM MNI152 2009c nonlinear asymmetric space](https://www.bic.mni.mcgill.ca/ServicesAtlases/ICBM152NLin2009). Furthermore, it allows probabilistic region assignment of a selected point to brain regions of [Julich Brain Atlas](https://julich-brain-atlas.de/).

Warping brain data to a standardized space like MNI152 enables anchoring to atlas volumes like [BigBrain](https://julich-brain-atlas.de/atlas/bigbrain). However, reasonable registration requires various steps that need a lot of optimization effort. _siibra_mriwarp_ aims to simplify the workflow of warping a patient's MRI scan to MNI152 space. With this application, you avoid installing multiple tools and tweaking many parameters for a proper registration result. Instead, _siibra-mriwarp_ is an easy-to-install and easy-to-use tool combining all necessary steps into one pipeline. 

You can immediately utilize the warping results in _siibra-mriwarp_ to assign brain regions to a point in the patient's space. Select a location in the displayed brain of a subject to perform a probabilistic assignment using Julich-Brain Cytoarchitectonic Maps 2.9. Hence, you can estimate the probability of a brain region occurring at the selected point. To explore even more information about a cytoarchitectonic area, you can access [_siibra-explorer_](https://atlases.ebrains.eu/viewer/human) through the application.

!!! info
    _siibra-mriwarp_ is a local application. Therefore, your data won't be stored on an online server but remains on your computer, which allows processing of **confidential data**.

![image](images/teaser.png)
