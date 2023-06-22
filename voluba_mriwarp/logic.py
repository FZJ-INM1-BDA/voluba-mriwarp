import logging
import os
import platform
import subprocess
import tempfile
import json

import nibabel as nib
import numpy as np
import pandas as pd
from HD_BET.run import run_hd_bet

from voluba_mriwarp.config import mriwarp_name, mni_template
from voluba_mriwarp.exceptions import *


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
        self.__parameters = None
        self.__error = ''
        self.__saved_points = []

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
            transform_path = f'{os.path.normpath(os.path.join(self.__out_path, self.__name))}' \
                         f'_transformationInverseComposite.h5'
            self.set_transform_path(transform_path)
            self.load_source()
        else:
            raise ValueError(self.__error)
        
    def set_json_path(self, json_path):
        """Set the path to the parameter JSON.
        
        :param str json_path: path to the parameter JSON
        :raise ValueError: if path or JSON is not valid
        """
        if self.check_json_path(json_path):
            parameters = json.load(open(json_path, 'r'))
            if self.check_json(parameters):
                self.__parameters = parameters
        else:
            raise ValueError(self.__error)

    def check_json_path(self, json_path):
        """Check if the JSON path is valid.

        :param str json_path: path to the parameter JSON
        :return bool: True if valid, False otherwise.
        """
        self.__error = ''

        if not json_path:
            self.__error += f'Please enter a parameter location.\n'
        elif not os.path.exists(json_path):
            self.__error += f'{json_path} could not be found.\n'
        elif not os.path.isfile(json_path) or not json_path.endswith('.json'):
            self.__error += f'{json_path} is not a JSON file.\n'

        if self.__error:
            return False
        else:
            return True

    def check_json(self, parameters):
        """Check if the JSON is valid.

        :param str parameters: parameters from the JSON
        :return bool: True if valid, False otherwise.
        """
        for value in parameters.values():
            if not type(value) == dict:
                return False
            if not 'stages' in value.keys():
                return False
        return True
    
    def check_transform_path(self, transform_path):
        """Check if the transformation file path is valid.

        :param str transform_path: path to the transformation file
        :return bool: True if valid, False otherwise.
        """
        self.__error = ''

        if not transform_path:
            self.__error += f'Please enter a transformation file.\n'
        if not os.path.exists(transform_path):
            self.__error += f'{transform_path} could not be found.\n'
        elif not os.path.isfile(transform_path) or not (transform_path.endswith('.h5') or transform_path.endswith('.mat')):
            self.__error += f'{transform_path} is not a h5 or mat file.\n'

        if self.__error:
            return False
        else:
            return True

    def set_transform_path(self, transform_path):
        """Set the path to the transform matrix.
        
        :param str transform_path: path to the transform matrix
        """
        if self.check_transform_path(transform_path):
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
            transform_path = f'{os.path.normpath(os.path.join(self.__out_path, self.__name))}' \
                         f'_transformationInverseComposite.h5'
            self.set_transform_path(transform_path)
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
        # Reorient NIfTI to standard orientation.
        self.__nifti_source = nib.funcs.as_closest_canonical(
            nib.load(self.__in_path))
        # Rotate the image to display the correct orientation.
        self.__numpy_source = np.rot90(
            self.__nifti_source.get_fdata(), axes=(0, 2))
        # Normalize values for PIL.
        self.__numpy_source *= 255.0/self.__numpy_source.max()

    def preload(self):
        """Preload HD_BET parameters, siibra and its components to speed up region assignment."""
        import siibra
        from HD_BET.utils import maybe_download_parameters

        maybe_download_parameters(0)

        multilevel_human = siibra.atlases.MULTILEVEL_HUMAN_ATLAS
        mni152 = siibra.spaces.MNI_152_ICBM_2009C_NONLINEAR_ASYMMETRIC

        self.__mni152_parcellations = []
        for parcellation in multilevel_human.parcellations:
            pmap = siibra.get_map(parcellation, mni152, maptype='statistical')
            if parcellation.supports_space(mni152) and pmap:
                    self.__mni152_parcellations.append(parcellation.shortname)

        self.set_parcellation('julich 2.9')

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
    
    def get_parcellations(self):
        """Return all available parcellations for MNI152 nonlinear asymmetric."""
        return self.__mni152_parcellations
    
    def set_parcellation(self, parcellation):
        """Set the parcellation that is used for region assignment.
        
        :param str parcellation: name of the parcellation to use
        """
        import siibra
        multilevel_human = siibra.atlases.MULTILEVEL_HUMAN_ATLAS
        self.__parcellation = multilevel_human.get_parcellation(parcellation)

    def get_parcellation(self):
        """Return the current parcellation that is used for region assignment."""
        return self.__parcellation.shortname

    def set_img_type(self, type):
        """Set the image type.

        :param str type: type of the image (template, aligned or unaligned)
        :raise ValueError: if path is not valid
        """
        if type not in ['template', 'aligned', 'unaligned']:
            raise ValueError(
                'Image type must be "template", "aligned" or "unaligned"')
        else:
            self.__img_type = type

    def get_img_type(self):
        """Return the image type."""
        return self.__img_type
    
    def save_point(self, point):
        """Save a selected point.
        
        :param tuple point: point to save
        """
        self.__saved_points.append(point)

    def delete_point(self, point):
        """Delete a saved point.
        
        :param tuple point: point to delete
        :return int: index of the point in the list of saved points
        """
        for i, p in enumerate(self.__saved_points):
            if p is point:
                self.__saved_points.pop(i)
                return i
    
    def get_num_points(self):
        """Get number of saved points"""
        return len(self.__saved_points)
    
    def delete_points(self):
        """Delete all saved points."""
        self.__saved_points = []

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

        :raise mriwarp.SubprocessFailedError: if execution of HD-BET failed
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

        :raise mriwarp.SubprocessFailedError: if execution of antsRegistration failed
        """
        fixed = mni_template
        moving = os.path.normpath(self.__reorient_path_calc)
        mask = os.path.normpath(os.path.join(
            self.__out_path_calc, f'{self.__name_calc}_stripped_mask.nii.gz'))
        
        transform = os.path.normpath(os.path.join(self.__out_path_calc, f'{self.__name_calc}_transformation'))
        volume = os.path.normpath(os.path.join(self.__out_path_calc, f'{self.__name_calc}_registered.nii.gz'))

        commands = []
        for command in self.__parameters.keys():
            cmd = 'antsRegistration '
            for param in self.__parameters[command].keys():
                if param == 'stages':
                    # transformation stage parameters
                    for stage in self.__parameters[command][param]:
                        for stage_param in stage.keys():
                            cmd += f'--{stage_param} {stage[stage_param]} '
                else:
                    # general parameters
                    cmd += f'--{param} {self.__parameters[command][param]} '

            # replace placeholders with actual files
            cmd = cmd.replace('FIXED', fixed)
            cmd = cmd.replace('MOVING', moving)
            cmd = cmd.replace('MASK', mask)
            cmd = cmd.replace('TRANSFORM', transform)
            cmd = cmd.replace('VOLUME', volume)
            cmd = cmd.replace('OUTPATH', self.__out_path_calc)
            cmd = cmd.replace('NAME', self.__name_calc)

            commands.append(cmd.rstrip())

        if platform.system() == 'Linux':
            for i in range(len(commands)):
                commands[i] = [commands[i]]    
        else:
            for i in range(len(commands)):
                commands[i] = commands[i].split(' ')

        try:
            for command in commands:
                logging.getLogger(mriwarp_name).info(f'Executing: {command}')
                result = subprocess.run(command, stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE, check=True, shell=True)
                logging.getLogger(mriwarp_name).info(result.stdout.decode('utf-8'))
        except subprocess.CalledProcessError as e:
            logging.getLogger(mriwarp_name).error(e.output.decode('utf-8').split('ERROR: ')[0].rstrip())
            raise SubprocessFailedError(e.output.decode('utf-8').split('ERROR: ')[-1].rstrip())

        if self.__in_path == self.__in_path_calc and self.__out_path == self.__out_path_calc:
            self.__transform_path = transform+'InverseComposite.h5'

    def __phys2mni(self, source_coords_ras):
        """Warp coordinates from subject's physical to MNI152 space using the transform matrix.

        :param list source_coords_ras: coordinates in subject's physical space (RAS)
        :return list: warped coordinates in MNI152 space (RAS)
        :raise mriwarp.SubprocessFailedError: if execution of antsApplyTransformsToPoints failed
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
            result = subprocess.run(command, stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE, check=True, shell=True)
            logging.getLogger(mriwarp_name).info(result.stdout.decode('utf-8'))
        except subprocess.CalledProcessError as e:
            logging.getLogger(mriwarp_name).error(e.output.decode('utf-8').split('ERROR: ')[0].rstrip())
            raise SubprocessFailedError(e.output.decode('utf-8').rstrip())

        target_pts = pd.read_csv(
            f'{os.path.join(tmp_dir.name, "target_pts.csv")}')
        target_coords_lbs = target_pts.to_numpy()

        # Warp from LBS to RAS because nibabel and numpy use RAS.
        return (target_coords_lbs * (-1, -1, 1)).tolist()

    def vox2phys(self, coords):
        """Warp coordinates from subject's voxel to physical space.

        :param list source_coords_ras: coordinates in voxel space
        :return list: warped coordinates in physical space
        """
        vox2phys = self.__nifti_source.affine
        return [nib.affines.apply_affine(vox2phys, coords)]
    
    def phys2vox(self, coords):
        """Warp coordinates from subject's physical to voxel space.

        :param list source_coords_ras: coordinates in physical space
        :return list: warped coordinates in voxel space
        """
        vox2phys = self.__nifti_source.affine
        phys2vox = np.linalg.inv(vox2phys)
        return [nib.affines.apply_affine(phys2vox, coords)]

    def get_regions(self, coords, uncertainty_mm):
        """Assign subject voxel coordinates to regions in the Julich Brain Atlas.

        :param list coords: coordinates in subject's voxel space
        :param float uncertainty_mm: uncertainty of a point in input's physical space
        :return list, list, list, dict: source coordinates in RAS, target coordinates in RAS, assignments and urls to siibra-explorer
        :raise PointNotFoundError: if the given point is outside the brain
        """
        # Import siibra related modules here to make use of preloading/caching.
        import siibra
        import siibra_explorer_toolsuite

        multilevel_human = siibra.atlases.MULTILEVEL_HUMAN_ATLAS
        mni152 = siibra.spaces.MNI_152_ICBM_2009C_NONLINEAR_ASYMMETRIC

        sort_value = 'input containedness' if uncertainty_mm else 'map value'

        # Transform from subject's voxel to subject's physical space.
        source_coords_ras = self.vox2phys(coords)

        if self.__img_type == 'unaligned':
            maptype = 'statistical'
            target_coords_ras = self.__phys2mni(source_coords_ras)
        elif self.__img_type == 'aligned':
            maptype='statistical'
            target_coords_ras = source_coords_ras
        else:
            maptype='labelled'
            target_coords_ras = source_coords_ras

        map = siibra.get_map(self.__parcellation, mni152, maptype=maptype)
        target = siibra.Point(target_coords_ras[0], space=mni152, sigma_mm=uncertainty_mm)

        try:
            assignments = map.assign(target)
        except IndexError:
            raise PointNotFoundError('Point doesn\'t match MNI152 space.')
        results = assignments.sort_values(by=sort_value, ascending=False)
        # Remove all columns that are irrelevant or None.
        results = results.drop(['input structure', 'centroid', 'volume', 'fragment'], axis=1)
        results = results.dropna(axis=1)
        urls = {}
        for region in results['region']:
            urls[region.name] = 'atlases.ebrains.eu/viewer' # siibra_explorer_toolsuite.run(multilevel_human, mni152, self.__parcellation, region)

        return source_coords_ras[0], target_coords_ras[0], results, urls
