import json
import logging
import os
import platform
import subprocess
import tempfile

import nibabel as nib
import numpy as np
import pandas as pd
import siibra
import siibra_explorer_toolsuite
from HD_BET.run import run_hd_bet
from HD_BET.utils import maybe_download_parameters

from voluba_mriwarp.config import *
from voluba_mriwarp.exceptions import *


class Logic:
    """Logic for warping and region assignment"""

    def __init__(self):
        """Initialize the logic."""
        self.__tmp_dir = tempfile.TemporaryDirectory()
        self.__in_path = ''
        self.__out_path = ''
        self.__transform_path = ''
        self.__name = ''
        self.__nifti_image = None
        self.__numpy_image = None
        self.__image_type = ''
        self.__warping_parameters = None
        self.__error = ''
        self.__saved_points = []

    def preload(self):
        """Preload HD_BET parameters, siibra and its components to speed up 
        region assignment.
        """
        # Create result directory.
        if not os.path.exists(mriwarp_home):
            os.mkdir(mriwarp_home)

        # Copy warping parameters.
        if not os.path.exists(parameter_home):
            parameter_source = os.path.normpath('./data/parameters')
            if platform.system() == 'Linux':
                os.system(f'cp -r {parameter_source} {mriwarp_home}')
            else:
                os.system(f'xcopy {parameter_source} {parameter_home} /i')
        
        # Download HD-BET parameters.
        maybe_download_parameters(0)

        # Initialize input and output.
        self.set_in_path(mni_template)
        self.set_out_path(mriwarp_home)

        # Get all parcellations available for MNI152 space.
        mni152 = siibra.spaces.MNI_152_ICBM_2009C_NONLINEAR_ASYMMETRIC
        
        pmaps = siibra.maps.dataframe
        mni_pmaps = pmaps[(pmaps.maptype == 'STATISTICAL')
                          & (pmaps.space == mni152.name)]
        self.__mni152_parcellations = [parcellation
                                       for parcellation in
                                       mni_pmaps.parcellation]
        # Remove duplicate Julich-Brain 3.0.
        self.__mni152_parcellations = list(dict.fromkeys(self.__mni152_parcellations))
        
        self.set_parcellation('julich 3.0')

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

    def get_in_path(self):
        """Return the path to the input NIfTI."""
        return self.__in_path

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

    def get_out_path(self):
        """Return the path to the output folder."""
        return self.__out_path

    def __set_name(self):
        """Set the name of the file without the file extension."""
        if self.__in_path.endswith('.nii.gz'):
            self.__name = self.__in_path.split('.nii.gz')[0].split(os.sep)[-1]
        else:
            self.__name = self.__in_path.split('.nii')[0].split(os.sep)[-1]

    def get_name(self):
        """Return the name of the file without the file extension."""
        return self.__name

    def load_source(self):
        """Load the NIfTI file and convert it to a numpy array."""
        # Reorient NIfTI to standard orientation.
        self.__nifti_image = nib.funcs.as_closest_canonical(
            nib.load(self.__in_path))
        # Rotate the image to display the correct orientation.
        self.__numpy_image = np.rot90(
            self.__nifti_image.get_fdata(), axes=(0, 2))
        # Normalize values for PIL.
        self.__numpy_image *= 255.0/self.__numpy_image.max()

    def get_nifti_source(self):
        """Return the input NIfTI as Nifti1Image"""
        return self.__nifti_image

    def get_numpy_source(self):
        """Return the input NIfTI as numpy.ndarray"""
        return self.__numpy_image

    def set_transform_path(self, transform_path):
        """Set the path to the transform matrix.

        :param str transform_path: path to the transform matrix
        """
        if self.check_transform_path(transform_path):
            self.__transform_path = transform_path
        else:
            self.__transform_path = ''

    def get_transform_path(self):
        """Return the path to the transform matrix."""
        return self.__transform_path

    def set_parameters_path(self, parameter_path):
        """Set the path to the parameter JSON.

        :param str parameter_path: path to the parameter JSON
        :raise ValueError: if path or JSON is not valid
        """
        if self.check_parameters_path(parameter_path):
            parameters = json.load(open(parameter_path, 'r'))
            if self.check_json(parameters):
                self.__warping_parameters = parameters
        else:
            raise ValueError(self.__error)

    def set_img_type(self, type):
        """Set the image type.

        :param str type: type of the image (template, aligned or unaligned)
        :raise ValueError: if path is not valid
        """
        if type not in ['template', 'aligned', 'unaligned']:
            raise ValueError(
                'Image type must be "template", "aligned" or "unaligned"')
        else:
            self.__image_type = type

    def get_img_type(self):
        """Return the image type."""
        return self.__image_type

    def set_parcellation(self, parcellation):
        """Set the parcellation that is used for region assignment.

        :param str parcellation: name of the parcellation to use
        """
        self.__parcellation = siibra.parcellations[parcellation]

    def get_parcellation(self):
        """Return the current parcellation that is used for region assignment."""
        return self.__parcellation

    def get_parcellations(self):
        """Return all available parcellations for MNI ICBM 152 2009c nonlinear 
        asymmetric space.
        """
        return self.__mni152_parcellations

    def set_uncertainty(self, uncertainty):
        """Set the uncertainty of a point in the input space.

        :param float uncertainty: uncertainty in mm of a point in input space
        """
        self.__uncertainty = uncertainty

    def get_num_points(self):
        """Return the number of saved points."""
        return len(self.__saved_points)

    def get_features(self):
        """Return features that are available for the current parcellation."""
        # TODO implement filtering reg. parcellation
        self.__modalities = ['CellDensityProfile',
                             'FunctionalConnectivity',
                             'StreamlineCounts',
                             'StreamlineLengths',
                             'ReceptorDensityFingerprint',
                             'ReceptorDensityProfile']

        return self.__modalities

    def get_receptors(self):
        """Return all receptors that are available in siibra."""
        return siibra.vocabularies.RECEPTOR_SYMBOLS.keys()

    def check_in_path(self, in_path):
        """Check if the input path is valid.

        :param str in_path: path to the input NIfTI
        :return: True if valid, False otherwise.
        :rtype: bool
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
        :return: True if valid, False otherwise.
        :rtype: bool
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

    def check_transform_path(self, transform_path):
        """Check if the transformation file path is valid.

        :param str transform_path: path to the transformation file
        :return: True if valid, False otherwise.
        :rtype: bool
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

    def check_parameters_path(self, parameter_path):
        """Check if the JSON path is valid.

        :param str parameter_path: path to the parameter JSON
        :return: True if valid, False otherwise.
        :rtype: bool
        """
        self.__error = ''

        if not parameter_path:
            self.__error += f'Please enter a parameter location.\n'
        elif not os.path.exists(parameter_path):
            self.__error += f'{parameter_path} could not be found.\n'
        elif not os.path.isfile(parameter_path) or not parameter_path.endswith('.json'):
            self.__error += f'{parameter_path} is not a JSON file.\n'

        if self.__error:
            return False
        else:
            return True

    def check_json(self, parameters):
        """Check if the JSON is valid.

        :param str parameters: parameters from the JSON
        :return: True if valid, False otherwise.
        :rtype: bool
        """
        for value in parameters.values():
            if not type(value) == dict:
                return False
            if not 'stages' in value.keys():
                return False
        return True

    def save_paths(self):
        """Save the current input and output path for calculation as the user 
        may inspect a different volume during calculation.
        """
        self.__in_path_calc = self.__in_path
        self.__out_path_calc = self.__out_path
        self.__name_calc = self.__name
        self.__reorient_path_calc = os.path.join(
            self.__tmp_dir.name, f'{self.__name}_reorient.nii.gz')
        nib.save(self.__nifti_image, self.__reorient_path_calc)

    def strip_skull(self):
        """Strip the skull of the input brain using HD-BET.

        :raise mriwarp.SubprocessFailedError: if execution of HD-BET failed
        """
        input = os.path.normpath(self.__reorient_path_calc)
        output = os.path.normpath(os.path.join(
            self.__out_path_calc, f'{self.__name_calc}_stripped.nii.gz'))

        try:
            run_hd_bet(
                [input],
                [output],
                mode='fast', device='cpu', postprocess=True, do_tta=False,
                keep_mask=True, overwrite=True)
        except Exception as e:
            raise SubprocessFailedError(str(e))

    def warp(self):
        """Register the stripped input brain to MNI152 space using ANTs.

        :raise mriwarp.SubprocessFailedError: if execution of antsRegistration 
        failed
        """
        fixed = mni_template
        moving = os.path.normpath(self.__reorient_path_calc)
        mask = os.path.normpath(os.path.join(
            self.__out_path_calc, f'{self.__name_calc}_stripped_mask.nii.gz'))
        transform = os.path.normpath(os.path.join(
            self.__out_path_calc, f'{self.__name_calc}_transformation'))
        volume = os.path.normpath(os.path.join(
            self.__out_path_calc, f'{self.__name_calc}_registered.nii.gz'))

        commands = []
        for command in self.__warping_parameters.keys():
            cmd = 'antsRegistration '
            for parameter in self.__warping_parameters[command].keys():
                if parameter == 'stages':
                    # transformation stage parameters
                    for stage in self.__warping_parameters[command][parameter]:
                        for stage_param in stage.keys():
                            cmd += f'--{stage_param} {stage[stage_param]} '
                else:
                    # general parameters
                    cmd += f'--{parameter} {self.__warping_parameters[command][parameter]} '

            # replace placeholders with actual files
            cmd = cmd.replace('FIXED', fixed)
            cmd = cmd.replace('MOVING', moving)
            cmd = cmd.replace('MASK', mask)
            cmd = cmd.replace('TRANSFORM', transform)
            cmd = cmd.replace('VOLUME', volume)
            cmd = cmd.replace('OUTPATH', self.__out_path_calc)
            cmd = cmd.replace('NAME', self.__name_calc)

            commands.append(cmd.rstrip())

        # subprocess.run needs different structure of commands depending on OS.
        if platform.system() == 'Linux':
            for i in range(len(commands)):
                commands[i] = [commands[i]]
        else:
            for i in range(len(commands)):
                commands[i] = commands[i].split(' ')

        try:
            for command in commands:
                logging.getLogger(mriwarp_name).info(f'Executing: {command}')
                result = subprocess.run(
                    command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    check=True, shell=True)
                logging.getLogger(mriwarp_name).info(
                    result.stdout.decode('utf-8'))
        except subprocess.CalledProcessError as e:
            logging.getLogger(mriwarp_name).error(
                e.output.decode('utf-8').split('ERROR: ')[0].rstrip())
            raise SubprocessFailedError(e.output.decode(
                'utf-8').split('ERROR: ')[-1].rstrip())

        if self.__in_path == self.__in_path_calc and self.__out_path == self.__out_path_calc:
            self.__transform_path = transform+'InverseComposite.h5'

    def __warp_phys2mni(self, point):
        """Warp point from subject's physical to MNI152 space using the 
        transform matrix.

        :param tuple point: point in subject's physical space (RAS)
        :return: warped point in MNI152 space (RAS)
        :rtype: list
        :raise mriwarp.SubprocessFailedError: if execution of 
        antsApplyTransformsToPoints failed
        """
        # Warp from RAS to LBS because ANTs uses LBS.
        source_points_lbs = (np.array([point])
                             * (-1, -1, 1)).tolist()
        source_points = pd.DataFrame(source_points_lbs, columns=['x', 'y', 'z'])
        source_points.to_csv(
            f'{os.path.join(self.__tmp_dir.name, "source_pts.csv")}',
            index=False)

        if platform.system() == 'Linux':
            command = [
                f'antsApplyTransformsToPoints --dimensionality 3 '
                f'--input {os.path.join(self.__tmp_dir.name, "source_pts.csv")} '
                f'--output {os.path.join(self.__tmp_dir.name, "target_pts.csv")} '
                f'--transform {self.__transform_path}']
        else:
            command = [
                'antsApplyTransformsToPoints', '--dimensionality', '3',
                '--input', f'{os.path.join(self.__tmp_dir.name, "source_pts.csv")}',
                '--output', f'{os.path.join(self.__tmp_dir.name, "target_pts.csv")}',
                '--transform', f'{self.__transform_path}']

        # In ANTs points are transformed from moving to fixed using the inverse transformation.
        try:
            result = subprocess.run(
                command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                check=True, shell=True)
            logging.getLogger(mriwarp_name).info(result.stdout.decode('utf-8'))
        except subprocess.CalledProcessError as e:
            logging.getLogger(mriwarp_name).error(
                e.output.decode('utf-8').split('ERROR: ')[0].rstrip())
            raise SubprocessFailedError(e.output.decode('utf-8').rstrip())

        target_points = pd.read_csv(
            f'{os.path.join(self.__tmp_dir.name, "target_pts.csv")}')
        target_points_lbs = target_points.to_numpy()

        # Warp from LBS to RAS because nibabel and numpy use RAS.
        return (target_points_lbs * (-1, -1, 1)).tolist()[0]

    def warp_vox2phys(self, point):
        """Warp point from subject's voxel to physical space using the affine.

        :param tuple point: point in voxel space
        :return: warped point in physical space
        :rtype: list
        """
        vox2phys = self.__nifti_image.affine
        return nib.affines.apply_affine(vox2phys, point)

    def warp_phys2vox(self, point):
        """Warp point from subject's physical to voxel space using the 
        inverted affine.

        :param tuple point: point in physical space
        :return: warped point in voxel space
        :rtype: list
        """
        vox2phys = self.__nifti_image.affine
        phys2vox = np.linalg.inv(vox2phys)
        return nib.affines.apply_affine(phys2vox, point)

    def assign_regions2point(self, point, uncertainty_mm):
        """Assign subject voxel point to regions in the Julich Brain Atlas.

        :param tuple point: point in subject's voxel space
        :param float uncertainty_mm: uncertainty of a point in input's physical
        space
        :return: source point in RAS, target point in RAS, assignments and 
        urls to siibra-explorer
        :rtype: list, list, list, dict
        :raise PointNotFoundError: if the given point is outside the brain
        """
        multilevel_human = siibra.atlases.MULTILEVEL_HUMAN_ATLAS
        mni152 = siibra.spaces.MNI_152_ICBM_2009C_NONLINEAR_ASYMMETRIC

        sort_value = 'correlation' if uncertainty_mm else 'map value'

        # Transform from subject's voxel to subject's physical space.
        source_point_ras = self.warp_vox2phys(point)

        if self.__image_type == 'unaligned':
            target_point_ras = self.__warp_phys2mni(source_point_ras)
        else:
            target_point_ras = source_point_ras

        pmap = siibra.get_map(self.__parcellation, mni152,
                              maptype='statistical')
        target = siibra.Point(
            target_point_ras, space=mni152, sigma_mm=uncertainty_mm)

        try:
            assignments = pmap.assign(target)
        except IndexError:
            raise PointNotFoundError('Point doesn\'t match MNI152 space.')
        results = assignments.sort_values(by=sort_value, ascending=False)
        # Remove all columns that are irrelevant or None.
        results = results.drop(
            ['input structure', 'centroid', 'volume', 'fragment'], axis=1)
        results = results.dropna(axis=1)
        urls = {}
        for region in results['region']:
            urls[region.name] = siibra_explorer_toolsuite.run(
                multilevel_human, mni152, self.__parcellation, region)

        return source_point_ras, target_point_ras, results, urls

    def save_point(self, point, label):
        """Save a selected point.

        :param tuple point: point to save
        :param tkinter.StringVar() label: variable holding the label of the point
        """
        self.__saved_points.append(point)
        self.__labels.append(label)

    def delete_point(self, point):
        """Delete a saved point.

        :param tuple point: point to delete
        :return: index of the point in the list of saved points
        :rtype: int
        """
        for i, saved_point in enumerate(self.__saved_points):
            if saved_point is point:
                self.__saved_points.pop(i)
                self.__labels.pop(i)
                return i

    def delete_points(self):
        """Delete all saved points."""
        self.__saved_points = []
        self.__labels = []

    def export_assignments(
            self, output_file, filter, features, receptors, cohorts,
            progress_indicator):
        """Export all assignments together with linked features to a PDF report.

        :param str output_file: PDF file to export report to
        :param list filter: filter of the form [column, sign, value] to apply 
        to the assignments before export
        :param list features: linked features to export for each region
        :param list receptors: receptors to plot a ReceptorDensityProfile for
        :param list cohorts: cohorts to plot connectivity plots for
        :param tkinter.IntVar progress_indicator: variable indicating the export
        progress
        """
        from voluba_mriwarp.reports import AssignmentReport

        report = AssignmentReport(
            parcellation=self.__parcellation, filter=filter,
            progress=progress_indicator)

        # Transfer points to siibra.Point objects.
        if self.__image_type == 'unaligned':
            mni_points = [
                siibra.Point(
                    self.__warp_phys2mni(point),
                    space='mni152', sigma_mm=self.__uncertainty)
                for point in self.__saved_points]
        else:
            mni_points = [
                siibra.Point(
                    point, space='mni152', sigma_mm=self.__uncertainty)
                for point in self.__saved_points]
        labels = [label.get() for label in self.__labels]

        # Filter the region assignments.
        assignments = report.assign(mni_points)

        # Create the PDF report.
        report.create_report(assignments=assignments,
                             subject_points=self.__saved_points,
                             mni_points=mni_points, labels=labels,
                             image=self.__nifti_image, features=features,
                             receptors=receptors, cohorts=cohorts,
                             output_file=output_file)
