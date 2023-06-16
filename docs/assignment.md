# Probabilistic region assignment

_voluba-mriwarp_ allows you to make a probabilistic assignment of coordinates in the input space to brain regions of the [EBRAINS Human Brain Atlas](https://www.ebrains.eu/tools/human-brain-atlas). Probabilistic assignment means that at the given location values of different probability maps of the selected parcellation are retrieved. With the resulting list of regions, you get information about the most probable region assigned to your selected point.

To perform probabilistic region assignment in _voluba-mriwarp_ follow these steps:

![image](images/assignment_steps.png)

![icon](images/1.png) **Select the input MRI scan to inspect.**  
The <mark>Input NIfTI</mark> has to be in NIfTI format (.nii or .nii.gz) and has to contain the whole brain of the subject. You can either manually type in the path to the file or you can choose the input MRI scan in the file explorer by clicking <mark>...</mark>.

![icon](images/2.png) **Choose the output folder containing the warping results.**  
Probabilistic region assignment can only be performed if a transformation from the input to MNI152 space exists. On default, _voluba-mriwarp_ will search the matching transformation matrix `filename_transformationInverseComposite.h5` in the given <mark>Output folder</mark>. Please change the location to the folder where the warping results for the given <mark>Input NIfTI</mark> were written to or enter a specific transformation file in the [Advanced settings](#advanced-settings). If there are no results to this MRI scan yet, you need to [warp the input](../warping) first.

!!! hint
    The default output directory is `C:\Users\your_username\voluba-mriwarp`.

![icon](images/3.png) **Switch to the <mark>Region assignment</mark> menu section.**

![icon](images/4.png) **Adjust the general settings, if needed.**  
The [General settings](#general-settings) allow you to adjust the details of the probabilistic assignment like parcellation or point uncertainty.

![icon](images/5.png) **Select a point in subject's space to assign a region to it**.  
Double-click a point in the input scan in the [viewer](#viewer) or manually type one in the first row of the <mark>Selected points</mark> table. _voluba-mriwarp_ will then assign regions to this point and display the results in the side panel on the left. For more information about the selected points, see the section on [Point selection](#point-selection).

![icon](images/6.png) **View more details about a specific region in siibra-explorer.**  
Double click a row in the assignment table to get more information about the brain region in [siibra-explorer](https://atlases.ebrains.eu/viewer/human). Explore brain connectivity and multimodal data features like transmitter receptor densities, cell distributions, and physiological recordings linked to this area.

## General settings

### Input already in MNI152
Set this to `yes` if the <mark>input NIfTI</mark> already shows the subject's brain warped to MNI152 space. Thus, the image is already aligned to MNI152 space and _voluba-mriwarp_ doesn't need to apply a transformation anymore.

### Parcellation
You can choose between different parcellations that are available for ICBM MNI152 nonlinear asymmetric space in the EBRAINS Multilevel Human Atlas. A parcellation subdivides the brain into regions following organizational principles like cytoarchitecture (Julich-Brain), fibre architecture (fibre bundles) or function (functional modes).

### Point uncertainty
The specification of a location in the input MRI is usually not exact, but rather has several millimeters of uncertainty. If you specify an uncertainty for points, you will not only get the values of the probability maps. Instead, a 3D gaussian blob is correlated with the probability maps producing different measures that are presented to you in the resulting table of an assignment: a correlation coefficient, the intersection over union (IoU), weighted average of the map values over the blob, a containedness score of the blob wrt. the region (input containedness), and a containness score of the region wrt. the blob (map containedness). Per default, the resulting table is sorted by correlation coefficient. <span style="color:red">**TODO** Verify and adapt list of measures</span>  

## Advanced settings

In the advanced settings you can specify a particular transformation file is used by _voluba-mriwarp_. It can be a file produced by _voluba-mriwarp_ using the [Advanced settings for warping](../warping/#advanced-settings) or a file from another application. Keep in mind, that the file format needs to be ANTs compatible (`.mat` for linear or `.hdf5/.h5` for nonlinear transformations).

## Point selection

All coordinates shown in _voluba-mriwarp_ are given in the subject's physical RAS space. To select a location, you can either double click the according position in the viewer or manually type in the coordinates in the first row of the `Selected points` table.

![screenshot](images/points.png)

To save a point to the list of selected points, press :fa-save:. You can assign a label to each point
To delete a point from the list, click :fa-trash:.
If you want to see the assignment for a point again, click :fa-eye: in the row of the according location.

Double click or manually type in coordinates
Specify a label
Save a point
Review a point and its assignment
Delete a point


Explain what is shown (maybe link to siibra-python doc?)