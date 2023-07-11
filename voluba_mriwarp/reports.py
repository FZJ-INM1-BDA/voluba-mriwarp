import logging
import os
from datetime import datetime
from tempfile import mkdtemp

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
import siibra
from fpdf import FPDF
from nilearn import plotting

from voluba_mriwarp.config import mriwarp_name


class AssignmentReport:
    """Report of probabilistic region assignments and linked features"""

    def __init__(
            self, progress, parcellation='julich 3.0', space='mni152',
            maptype='statistical', filter=['correlation', '>', 0.3]):
        """Initialize the report.

        :param tkinter.IntVar progress: variable to update the current progress in 
        a GUI
        :param str parcellation: parcellation of the maps used for assignment
        :param str space: space of the maps used for assignment
        :param str maptype: type of the maps used for assignment
        :param list filter: filter of the form [column, sign, value] to apply 
        to the assignments
        """
        self.filter = filter
        self.dpi = 300
        self.progress = progress

        self.pmaps = siibra.get_map(
            parcellation=parcellation, space=space, maptype=maptype)

        tmp_dir = mkdtemp()
        self.__plot_dir = os.path.join(tmp_dir, 'plots')

    def __set_progress(self, num_points):
        """Increase the progress depending on the number of processed points.

        :param int num_points: number of points that are processed
        """
        # "hack" to kill the calling thread
        if self.progress.get() == -1:
            exit(0)
        # There are four steps iterating over the points:
        # assign, plot pmaps, plot features, create report
        self.progress.set(self.progress.get() + 100/(num_points*4))

    def assign(self, points, sort_by='correlation'):
        """Run an anatomical assignment for the given points.

        :param list points: list of points to assign to regions
        :param str sort_by: column to sort the assignment by
        :return list: list of filtered assignments for each point
        """
        assignments = []
        for point in points:
            self.__set_progress(len(points))
            initial_assignment = self.pmaps.assign(point)
            initial_assignment.sort_values(
                by=sort_by, ascending=False, inplace=True)
            # Apply a user-defined filter to the assignments.
            assignment = self._filter_assignments(initial_assignment)
            assignments.append(assignment)

        return assignments

    def _filter_assignments(self, initial_assignments):
        """Filter the assignments by a user-defined filter.

        :param pandas.DataFrame initial_assignments: unfiltered assignments 
        :return: filtered assignments
        :rtype: pandas.DataFrame
        """
        mapping = {
            '<': lambda column, value: column < value,
            '>': lambda column, value: column > value,
            '=': lambda column, value: column == value
        }
        column, sign, value = self.filter
        initial_assignments = initial_assignments.drop(
            ['centroid', 'volume', 'fragment'], axis=1)
        results = []
        for _, row in initial_assignments.iterrows():
            if row[column] and mapping[sign](row[column], value):
                results.append(row)

        return pd.DataFrame(results)

    def create_report(
            self, assignments, subject_points, mni_points, labels, image,
            features, receptors, cohorts, output_file):
        """Create a PDF report of assigned regions and linked features.

        :param list assignments: region assignments for multiple points
        :param list subject_points: points in subject's physical space
        :param list mni_points: points in MNI152 space
        :param list labels: labels for each point
        :param nibabel.Nifti1Image image: input image
        :param list features: linked features to export for each region
        :param list receptors: receptors to plot a ReceptorDensityProfile for
        :param list cohorts: cohorts to plot connectivity plots for
        :param str output_file: PDF file to export report to
        """
        # In the following code the progress may be "fake" set to enable
        # checking for termination
        self.__set_progress(0.25)
        logging.getLogger(mriwarp_name).info(
            f'Creating pdf report: {output_file}')

        # Plot intermediate plots to a temporary directory.
        self.__set_progress(0.25)
        if not os.path.isdir(self.__plot_dir):
            os.makedirs(self.__plot_dir)

        # Activate matplotlib png renderer.
        self.__set_progress(0.25)
        backend = matplotlib.get_backend()
        matplotlib.use('Agg')

        # Plot the input image.
        self.__set_progress(0.25)
        input_plot = self._plot_input(image)

        # Plot the probability maps.
        pmap_plots = {}
        for i, assignment in enumerate(assignments):
            self.__set_progress(len(assignments))
            if assignment.empty:
                continue
            label = labels[i]
            point = mni_points[i]
            for region in assignment.region:
                pmap_plots[f'{region}_{label}'] = self._plot_pmap(
                    region, point, label)

        # Plot linked features.
        feature_plots = {}
        for i, assignment in enumerate(assignments):
            self.__set_progress(len(assignments))
            if assignment.empty:
                continue
            for region in assignment.region.unique():
                if region in feature_plots.keys():
                    continue
                feature_plots[region] = {}
                for feature in features:
                    feature_plots[region][feature] = self.__plot_features(
                        region, feature, receptors, cohorts)

        # Build the PDF report.
        self._build_pdf(
            assignments, input_plot, pmap_plots, feature_plots, labels,
            subject_points, mni_points, image, output_file)
        matplotlib.use(backend)

    def _plot_input(self, image):
        """Plot the input image to a file.

        :param nibabel.Nifti1Image image: input image
        :return: filename the input image is plotted to
        :rtype: string
        """
        filename = os.path.join(self.__plot_dir, 'input.png')
        plt.ion()
        fig, ax = plt.subplots(1, 1, figsize=(6, 3), dpi=self.dpi)
        plotting.plot_img(image, axes=ax, cmap='gray',
                          draw_cross=False, annotate=False)
        plt.ioff()
        fig.savefig(filename, dpi=self.dpi)
        return filename

    def _plot_pmap(self, region, point, label):
        """Plot the pmap of a region to a file.

        :param siibra.Region region: region assigned to the given point
        :param siibra.Point point: point
        :param str label: label of the point
        :return: filename the pmap is plotted to
        :rtype: string
        """
        filename = os.path.join(
            self.__plot_dir, f'{region.key}_{label}_pmap.png')
        fig, ax = plt.subplots(1, 1, figsize=(6, 3), dpi=self.dpi)
        plt.ion()
        pmap = region.fetch_regional_map(self.pmaps.space, self.pmaps.maptype)
        plot = plotting.plot_glass_brain(
            pmap, axes=ax, colorbar=False, alpha=0.3, cmap='viridis')
        plot.add_markers([point.coordinate], marker_size=15)
        plt.ioff()
        fig.savefig(filename, dpi=self.dpi)
        return filename

    def __plot_features(self, region, feature, selected_receptors, cohorts):
        """Plot the linked feature of a region to a file.

        :param siibra.Region region: region assigned to the given point
        :param siibra.Feature feature: feature linked to the assigned region
        :param list selected_receptors: receptors to plot a 
        ReceptorDensityProfile for
        :param list cohorts: cohorts to plot connectivity plots for
        :return: filenames the feature data is plotted to
        :rtype: list
        """
        receptors = [
            f'{receptor} '
            f'({siibra.vocabularies.RECEPTOR_SYMBOLS[receptor]["receptor"]["name"]})'
            for receptor in selected_receptors]

        # CellDensityProfile yields one aggregated feature.
        if feature == 'CellDensityProfile':
            filename = os.path.join(
                self.__plot_dir, f'{region.key}_{feature}.png')
            features = siibra.features.get(region, feature)
            if features:
                plt.ion()
                features[0].plot()
                plt.tight_layout(pad=0.2)
                plt.ioff()
                plt.savefig(filename, dpi=self.dpi)
                return [filename]
            else:
                return []
        # ReceptorDensityFingerprint may yield multiple features.
        elif feature == 'ReceptorDensityFingerprint':
            filenames = []
            features = siibra.features.get(region, feature)
            for i, feat in enumerate(features):
                filename = os.path.join(
                    self.__plot_dir, f'{region.key}_{feature}_{i+1}.png')
                plt.ion()
                feat.polar_plot()
                plt.tight_layout(pad=0.2)
                plt.ioff()
                plt.savefig(filename, dpi=self.dpi)
                filenames.append(filename)
            return filenames
        # ReceptorDensityProfile yields one feature for each receptor.
        elif feature == 'ReceptorDensityProfile':
            filenames = []
            features = siibra.features.get(region, feature)
            for feat in features:
                if feat.receptor in receptors:
                    filename = os.path.join(
                        self.__plot_dir,
                        f'{region.key}_{feature}_{feat.receptor}.png')
                    plt.ion()
                    feat.plot()
                    plt.tight_layout(pad=0.2)
                    plt.ioff()
                    plt.savefig(filename, dpi=self.dpi)
                    filenames.append(filename)
            return filenames
        # Connectivity features yield one feature for each cohort.
        else:
            filenames = []
            features = siibra.features.get(region.parcellation, feature)
            for feat in features:
                if feat.cohort in cohorts:
                    filename = os.path.join(
                        self.__plot_dir,
                        f'{region.key}_{feature}_{feat.cohort}.png')
                    if not filename in filenames:
                        plt.ion()
                        feat.get_profile(region, max_rows=30).plot()
                        plt.tight_layout(pad=0.2)
                        plt.ioff()
                        plt.savefig(filename, dpi=self.dpi)
                        filenames.append(filename)
            return filenames

    # TODO switch subject and mni points
    def _build_pdf(
            self, assignments, input_plot, pmap_plots, feature_plots, labels,
            subject_points, mni_points, image, output_file):
        """Actually create a PDF report of assigned regions and linked features.

        :param list assignments: region assignments for multiple points
        :param str input_plot: filename of the input image plot
        :param dict pmap_plots: filenames of the pmap plots
        :param dict feature_plots: filenames of the feature plots
        :param list labels: labels for each point
        :param list subject_points: points in subject's physical space
        :param list mni_points: points in MNI152 space
        :param nibabel.Nifti1Image image: input image
        :param str output_file: PDF file to export report to
        """
        logging.getLogger(mriwarp_name).info(
            f'Building PDF report {output_file} for {len(assignments)} points.')

        pdf = FPDF()
        text_height = 4

        # title page
        pdf.add_page()
        left = pdf.get_x()
        top = pdf.get_y()

        pdf.set_font('Helvetica', 'BU', 20)
        pdf.set_xy(left, top)
        pdf.cell(40, 10, f'{mriwarp_name} Anatomical Assignment')

        pdf.set_font('Helvetica', '', 10)
        pdf.set_xy(left, top + 14)
        pdf.multi_cell(
            0, text_height, '\n'.join(
                [f'Input scan: {os.path.basename(image.get_filename())}',
                 f'Parcellation: {self.pmaps.parcellation.name}', ' ',
                 f'For each point, regions with {self.filter[0]} '
                 f'{self.filter[1]} {self.filter[2]} are assigned.',
                 ' ', f'siibra version {siibra.__version__}',
                 f'Computed on {datetime.now().strftime("%c")}']),)

        pdf.set_xy(left, top + 60)
        pdf.image(input_plot, w=180)

        # new page for each point
        pdf.set_xy(left, top + 60 + 75)
        for idx, assignment in enumerate(assignments):
            # heading
            self.__set_progress(len(assignments))
            pdf.add_page()
            pdf.set_font('Helvetica', 'BU', 12)
            pdf.cell(40, text_height, f'Assignments for {labels[idx]}')

            # point in subject and mni space
            pdf.set_font('Helvetica', '', 10)
            pdf.set_xy(left, 14 + text_height)
            pdf.multi_cell(
                0, text_height,
                f'Point in subject space: \t{subject_points[idx]} [mm]'
                f'\nPoint in {siibra.spaces["mni152"].name}: '
                f'{mni_points[idx].coordinate} [mm]')

            # no regions assigned
            if assignment.empty:
                pdf.set_xy(left, 2 * (14 + text_height))
                pdf.multi_cell(
                    0, text_height,
                    f'No regions assigned with {self.filter[0]} '
                    f'{self.filter[1]} {self.filter[2]}.')
                continue

            for _, row in assignment.iterrows():
                # assignment
                pdf.set_font('Helvetica', 'B', 10)
                pdf.set_xy(left, pdf.get_y() + text_height + 10)
                pdf.cell(
                    40, text_height,
                    f'Point {labels[idx]} assigned to {row.region}')

                # assignment values
                pdf.set_font('Helvetica', '', 5)
                pdf.set_xy(left, pdf.get_y() + 5)
                with pdf.table() as table:
                    header = table.row()
                    values = table.row()
                    for col in assignment.columns[2:]:
                        header.cell(col)
                        if row[col]:
                            values.cell(f'{row[col]:.6f}')
                        else:
                            values.cell('')

                # pmap plot
                pdf.set_xy(left, pdf.get_y() + 5)
                pdf.image(pmap_plots[f'{row.region}_{labels[idx]}'], h=40)

                for feature in feature_plots[row.region].keys():
                    # heading with feature type
                    pdf.set_font('Helvetica', 'B', 10)
                    pdf.set_xy(left, pdf.get_y() + 10)
                    pdf.cell(40, text_height, feature)

                    # feature plot
                    pdf.set_x(left)
                    y = pdf.get_y()
                    if feature_plots[row.region][feature]:
                        for k, filename in enumerate(
                                feature_plots[row.region][feature]):
                            pdf.set_xy(pdf.get_x() + k %
                                       2 * pdf.epw * 0.5, y + 10)
                            pdf.image(filename, w=pdf.epw * 0.4)
                    # feature not available for region
                    else:
                        pdf.set_font('Helvetica', '', 10)
                        pdf.set_xy(left, pdf.get_y() + 10)
                        pdf.multi_cell(
                            0, text_height,
                            f'There is no {feature} information available '
                            f'for {row.region}.')

        logging.getLogger(mriwarp_name).info(f'Report written to {output_file}')
        pdf.output(output_file)
