import os
import platform
import subprocess
import tempfile

import nibabel as nib
import numpy as np
import pandas as pd
from HD_BET.run import run_hd_bet

from siibra_mriwarp.exceptions import *


class Logic:
    """Logic for warping and region assignment"""

    def __init__(self):
        """Initialize the logic."""
        self.__in_path = ''
        self.__out_path = ''
        self.__transform_path = ''
        self.__name = ''
        self.__nifti_source = None
        self.__numpy_source = None
        self.__img_type = ''
        self.__error = ''

    def check_in_path(self, in_path):
        """Check if the input path is valid.

        :param str in_path: path to the input NIfTI
        :return bool: True if valid, False otherwise.
        """
        self.__error = ''

        if not in_path:
            self.__error += f'Please enter an input location.\n'
        elif not os.path.exists(in_path):
            self.__error += f'{in_path} could not be found.\n'
        elif not os.path.isfile(in_path) or not (in_path.endswith('.nii') or in_path.endswith('.nii.gz')):
            self.__error += f'{in_path} is not a NIfTI file.\n'

        if self.__error:
            return False
        else:
            return True

    def check_out_path(self, out_path):
        """Check if the output path is valid.

        :param str out_path: path to the output folder
        :return bool: True if valid, False otherwise.
        """
        self.__error = ''

        if not out_path:
            self.__error += f'Please enter an output location.\n'
        elif not os.path.exists(out_path):
            self.__error += f'{out_path} could not be found.\n'
        elif not os.path.isdir(out_path):
            self.__error += f'{out_path} is not a folder.\n'

        if self.__error:
            return False
        else:
            return True

    def set_in_path(self, in_path):
        """Set the path to the input NIfTI.

        :param str in_path: path to the input NIfTI
        :raise ValueError: if path is not valid
        """
        if self.check_in_path(in_path):
            self.__in_path = in_path
            self.__set_name()
            self.__set_transform_path()
            self.load_source()
        else:
            raise ValueError(self.__error)

    def __set_transform_path(self):
        """Set the path to the transform matrix."""
        transform_path = f'{os.path.normpath(os.path.join(self.__out_path, self.__name))}' \
                         f'_transformationInverseComposite.h5'
        if os.path.exists(transform_path):
            self.__transform_path = transform_path
        else:
            self.__transform_path = ''

    def set_out_path(self, out_path):
        """Set the path to the output folder.

        :param str out_path: path to the output folder
        :raise ValueError: if path is not valid
        """
        if self.check_out_path(out_path):
            self.__out_path = out_path
            self.__set_transform_path()
        else:
            raise ValueError(self.__error)

    def __set_name(self):
        """Set the name of the file without the file extension."""
        if self.__in_path.endswith('.nii.gz'):
            self.__name = self.__in_path.split('.nii.gz')[0].split(os.sep)[-1]
        else:
            self.__name = self.__in_path.split('.nii')[0].split(os.sep)[-1]

    def load_source(self):
        """Load the NIfTI file and convert it to a numpy array."""
        # Reorient NIfTI to standard orientation
        self.__nifti_source = nib.funcs.as_closest_canonical(
            nib.load(self.__in_path))
        # Rotate the image to display the correct orientation.
        self.__numpy_source = np.rot90(
            self.__nifti_source.get_fdata(), axes=(0, 2))
        # Normalize values for PIL
        self.__numpy_source *= 255.0/self.__numpy_source.max()

    def preload(self):
        """Preload siibra and its components to speed up region assignment."""
        import siibra

        siibra.parcellations['julich 2.9'].get_map(
            'mni152', maptype='continuous')

    def get_in_path(self):
        """Return the path to the input NIfTI."""
        return self.__in_path

    def get_out_path(self):
        """Return the path to the output folder."""
        return self.__out_path

    def get_transform_path(self):
        """Return the path to the transform matrix."""
        return self.__transform_path

    def get_nifti_source(self):
        """Return the input NIfTI as Nifti1Image"""
        return self.__nifti_source

    def get_numpy_source(self):
        """Return the input NIfTI as numpy.ndarray"""
        return self.__numpy_source

    def set_img_type(self, type):
        """Set the image type.

        :param str type: type of the image (template, aligned or unaligned)
        :raise ValueError: if path is not vali
        """
        if type not in ['template', 'aligned', 'unaligned']:
            raise ValueError(
                'Image type musst be "template", "aligned" or "unaligned"')
        else:
            self.__img_type = type

    def save_paths(self):
        """Save the current input and output path for calculation as the user may inspect a different volume during calculation."""
        self.__in_path_calc = self.__in_path
        self.__out_path_calc = self.__out_path
        self.__name_calc = self.__name
        self.__tmp = tempfile.TemporaryDirectory()
        self.__reorient_path_calc = os.path.join(
            self.__tmp.name, f'{self.__name}_reorient.nii.gz')
        nib.save(self.__nifti_source, self.__reorient_path_calc)

    def strip_skull(self):
        """Strip the skull of the input brain using HD-BET.

        :raise siibra_mriwarp.SubprocessFailedError: if execution of HD-BET failed
        """
        input = os.path.normpath(self.__reorient_path_calc)
        output = os.path.normpath(os.path.join(
            self.__out_path_calc, f'{self.__name_calc}_stripped.nii.gz'))

        try:
            run_hd_bet([input], [output], mode='fast', device='cpu', postprocess=True, do_tta=False, keep_mask=True,
                       overwrite=True)
        except Exception as e:
            raise SubprocessFailedError(str(e))

    def register(self):
        """Register the stripped input brain to MNI152 space using ANTs

        :raise siibra_mriwarp.SubprocessFailedError: if execution of antsRegistration failed
        """
        fixed = 'data/MNI152_stripped.nii.gz'
        moving = os.path.normpath(self.__reorient_path_calc)
        mask = os.path.normpath(os.path.join(
            self.__out_path_calc, f'{self.__name_calc}_stripped_mask.nii.gz'))
        transform = os.path.normpath(os.path.join(
            self.__out_path_calc, f'{self.__name_calc}_transformation'))
        volume = os.path.normpath(os.path.join(
            self.__out_path_calc, f'{self.__name_calc}_registered.nii.gz'))

        if platform.system() == 'Linux':
            command = [f'antsRegistration --verbose 1 --dimensionality 3 --use-histogram-matching 0 --winsorize-image-intensities [0.005,0.995] --masks [NULL,{mask}] --float --interpolation Linear --output [{transform},{volume}] --write-composite-transform 1 --collapse-output-transforms 1 --transform Rigid[0.1] --metric MI[{fixed},{moving},1,32,Regular,0.25] --convergence [1000x500x250x0,1e-6,10] --smoothing-sigmas 4x3x2x1vox --shrink-factors 12x8x4x2 --transform Affine[0.1] --metric MI[{fixed},{moving},1,32,Regular,0.25] --convergence [1000x500x250x0,1e-6,10] --smoothing-sigmas 4x3x2x1vox --shrink-factors 12x8x4x2 --transform SyN[0.1,3,0] --metric MI[{fixed},{moving},1,32] --convergence [100x100x70x50x0,1e-6,10] --smoothing-sigmas 5x3x2x1x0vox --shrink-factors 10x6x4x2x1']
        else:
            command = ['antsRegistration', '--verbose', '1', '--dimensionality', '3', '--use-histogram-matching', '0',
                       '--winsorize-image-intensities', '[0.005,0.995]', '--masks', f'[NULL,{mask}]', '--float', '--interpolation', 'Linear', '--output',
                       f'[{transform},{volume}]', '--write-composite-transform', '1', '--collapse-output-transforms', '1',
                       '--transform', 'Rigid[0.1]', '--metric', f'MI[{fixed},{moving},1,32,Regular,0.25]',
                       '--convergence', '[1000x500x250x0,1e-6,10]', '--smoothing-sigmas', '4x3x2x1vox', '--shrink-factors',
                       '12x8x4x2', '--use-estimate-learning-rate-once', '--transform', 'Affine[0.1]', '--metric',
                       f'MI[{fixed},{moving},1,32,Regular,0.25]', '--convergence', '[1000x500x250x0,1e-6,10]',
                       '--smoothing-sigmas', '4x3x2x1vox', '--shrink-factors', '12x8x4x2',
                       '--use-estimate-learning-rate-once', '--transform', 'SyN[0.1,3,0]', '--metric',
                       f'MI[{fixed},{moving},1,32]', '--convergence', '[100x100x70x50x0,1e-6,10]', '--smoothing-sigmas',
                       '5x3x2x1x0vox', '--shrink-factors', '10x6x4x2x1', '--use-estimate-learning-rate-once']

        try:
            subprocess.run(command, stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE, check=True, shell=True)
        except subprocess.CalledProcessError as e:
            raise SubprocessFailedError(e.output)

        if self.__in_path == self.__in_path_calc and self.__out_path == self.__out_path_calc:
            self.__transform_path = transform+'InverseComposite.h5'

    def __phys2mni(self, source_coords_ras):
        """Warp coordinates from patient's physical to MNI152 space using the transform matrix.

        :param list source_coords_ras: coordinates in patient's physical space (RAS)
        :return list: warped coordinates in MNI152 space (RAS)
        :raise siibra_mriwarp.SubprocessFailedError: if execution of antsApplyTransformsToPoints failed
        """
        tmp_dir = tempfile.TemporaryDirectory()

        # Warp from RAS to LBS because ANTs uses LBS.
        source_coords_lbs = (np.array(source_coords_ras)
                             * (-1, -1, 1)).tolist()
        source_pts = pd.DataFrame(source_coords_lbs, columns=['x', 'y', 'z'])
        source_pts.to_csv(
            f'{os.path.join(tmp_dir.name, "source_pts.csv")}', index=False)

        if platform.system() == 'Linux':
            command = [
                f'antsApplyTransformsToPoints --dimensionality 3 --input {os.path.join(tmp_dir.name, "source_pts.csv")} --output {os.path.join(tmp_dir.name, "target_pts.csv")} --transform {self.__transform_path}']
        else:
            command = ['antsApplyTransformsToPoints', '--dimensionality', '3', '--input',
                       f'{os.path.join(tmp_dir.name, "source_pts.csv")}', '--output',
                       f'{os.path.join(tmp_dir.name, "target_pts.csv")}', '--transform',
                       f'{self.__transform_path}']

        # In ANTs points are transformed from moving to fixed using the inverse transformation.
        try:
            subprocess.run(command, stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE, check=True, shell=True)
        except subprocess.CalledProcessError as e:
            print(str(e.output))
            raise SubprocessFailedError(e.output)

        target_pts = pd.read_csv(
            f'{os.path.join(tmp_dir.name, "target_pts.csv")}')
        target_coords_lbs = target_pts.to_numpy()

        # Warp from LBS to RAS because nibabel and numpy use RAS.
        return (target_coords_lbs * (-1, -1, 1)).tolist()

    def vox2phys(self, coords):
        """Warp coordinates from patient's voxel to physical space.

        :param list source_coords_ras: coordinates in RAS space
        :return list: warped coordinates in RAS space
        """
        vox2phys = self.__nifti_source.affine
        return [nib.affines.apply_affine(vox2phys, coords)]

    def get_regions(self, coords):
        """Assign patient voxel coordinates to regions in the Julich Brain Atlas.

        :param list coords: coordinates in patient's voxel space
        :return list, list, list: source coordinates in RAS, target coordinates in RAS and the assigned regions
        with their probabilities and url to siibra-explorer
        :raise PointNotFoundError: if the given point is outside the brain
        """
        # Import siibra related modules here to make use of preloading/caching.
        import siibra
        import siibra_explorer_toolsuite

        multilevel_human = siibra.atlases.MULTILEVEL_HUMAN_ATLAS
        mni152 = multilevel_human.spaces.MNI152_2009C_NONL_ASYM
        julichbrain = multilevel_human.parcellations.JULICH_BRAIN_CYTOARCHITECTONIC_MAPS_2_9

        # Transform from patient's voxel to patient's physical space.
        source_coords_ras = self.vox2phys(coords)

        if self.__img_type == 'unaligned':
            pmaps = julichbrain.get_map(mni152, maptype='continuous')
            target_coords_ras = self.__phys2mni(source_coords_ras)
            target = siibra.Point(target_coords_ras[0], space=mni152)
            try:
                assignments = pmaps.assign(target)
            except IndexError:
                raise PointNotFoundError('Point doesn\'t match MNI152 space.')
            results = assignments.sort_values('MaxValue', ascending=False)

            if results.empty:
                probabilities = None
            else:
                probabilities = []
                for i in range(len(results)):
                    region = julichbrain.decode_region(results.iloc[i].Region)
                    probability = results.iloc[i].MaxValue
                    url = siibra_explorer_toolsuite.run(
                        multilevel_human, mni152, julichbrain, region)
                    probabilities.append([region, probability, url])
        elif self.__img_type == 'aligned':
            pmaps = julichbrain.get_map(mni152, maptype='continuous')
            target_coords_ras = source_coords_ras
            target = siibra.Point(target_coords_ras[0], space=mni152)
            try:
                assignments = pmaps.assign(target)
            except IndexError:
                raise PointNotFoundError('Point doesn\'t match MNI152 space.')
            results = assignments.sort_values('MaxValue', ascending=False)

            if results.empty:
                probabilities = None
            else:
                probabilities = []
                for i in range(len(results)):
                    region = julichbrain.decode_region(results.iloc[i].Region)
                    probability = results.iloc[i].MaxValue
                    url = siibra_explorer_toolsuite.run(
                        multilevel_human, mni152, julichbrain, region)
                    probabilities.append([region, probability, url])
        else:
            mpmaps = julichbrain.get_map(mni152, maptype='labelled')
            target_coords_ras = source_coords_ras
            target = siibra.Point(target_coords_ras[0], space=mni152)
            try:
                assignments = mpmaps.assign_coordinates(target)
            except IndexError:
                raise PointNotFoundError('Point doesn\'t match MNI152 space.')

            try:
                region = julichbrain.decode_region(assignments[0][0][0])
            except IndexError:
                probabilities = None
            else:
                probabilities = []
                probability = 1
                url = siibra_explorer_toolsuite.run(
                    multilevel_human, mni152, julichbrain, region)
                probabilities.append([region, probability, url])

        return source_coords_ras[0], target_coords_ras[0], probabilities
