# Step-by-step example

In this tutorial, you will warp an example MRI scan to ICBM MNI152 2009c nonlinear asymmetric space and assign a region to a point in the patient's space. For this example, we use a NIfTI file from the publicly available [NFBS Skull-Stripped Repository](http://preprocessed-connectomes-project.org/NFB_skullstripped/). We choose the T1-weighted MRI scan `sub-A00028185_ses-NFB3_T1w.nii.gz` of patient `A00028185`.

1. Download the NFBS skull-stripped images from [here](http://preprocessed-connectomes-project.org/NFB_skullstripped/).
2. Unpack the .tar.gz archive. We recommend using [7zip](https://www.7-zip.org).
3. Choose `C:/Users/your_username/Downloads/NFBS_Dataset/A00028185/sub-A00028185_ses-NFB3_T1w.nii.gz` as <mark>Input NIfTI</mark>. You can either copy and paste this path or you can choose this file from the file explorer by clicking <mark>...</mark>.
4. Leave the <mark>Output folder</mark> at the default location `C:\Users\your_username\siibra-mriwarp`.
5. Click <mark>Warp input to MNI152 space</mark> to warp patient `A00028185`'s brain to ICBM MNI152 2009c nonlinear asymmetric space. The progress bar indicates that the calculation is still running. When the registration is finished, a green checkmark will appear next to the button.
6. Double-click a location in the patient's space to assign brain regions to it. We select a point in Hippocampus. In the side panel on the left every listed region is indeed part of the Hippocampus.
7. Click <mark>:fa-external-link:</mark> to get more details about a specific region in siibra-explorer. We choose the most probable brain region for this point, which is DG (Hippocampus) left.

<h1>Video tutorial</h1>

<video style="height: 20.5vw" controls="">
    <source src="../gifs/mriwarp_demo.mp4" type="video/mp4">
</video>
<br>
