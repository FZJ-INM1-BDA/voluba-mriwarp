import os
from datetime import datetime

import matplotlib
import matplotlib.pyplot as plt
import nibabel as nib
import pandas as pd
import siibra
from fpdf import FPDF
from nilearn import plotting
from tqdm import tqdm


class AssignmentReport:

    def __init__(
        self,
        progress,
        parcellation="julich 2.9",
        space="mni152",
        maptype="statistical",
        filter=['correlation', '>', 0.3],
        resolution_dpi=300,
        force_overwrite=False,
    ):
        self.filter = filter
        self.dpi = resolution_dpi
        self.overwrite = force_overwrite
        self.progress = progress

        self.pmaps = siibra.get_map(
            parcellation=parcellation, space=space, maptype=maptype)

    def __update_step(self, num_coords):
        if self.progress.get() == -1:
            exit(0)
        # there are 4 steps iterating over coordinates (assign, plot pmaps, plot features, create report)
        self.progress.set(self.progress.get() + 100/(num_coords*4))

    def analyze(self, coordinates, sort_by="correlation"):
        """ Run the anatomical assignment for the given coordinates.

        """
        # get assignments
        assignments = []
        for coordinate in coordinates:
            self.__update_step(len(coordinates))
            initial_assignment = self.pmaps.assign(coordinate)
            initial_assignment.sort_values(
                by=sort_by, ascending=False, inplace=True)
            assignment = self._select_assignments(initial_assignment)
            assignments.append(assignment)

        return assignments

    def create_report(self, assignments, coordinates, subject_coordinates, labels, image, reportfile, features, selected_receptors, cohorts):

        if labels is None:
            labels = [i+1 for i in range(len(coordinates))]
        assert (len(labels) == len(coordinates))

        self.__update_step(0.25)
        from tempfile import mkdtemp
        tmpdir = mkdtemp()
        siibra.logger.info(
            f"Creating pdf report: {reportfile}")

        # output directory for intermediate plots
        self.__update_step(0.25)
        plotdir = os.path.join(tmpdir, "plots")
        if not os.path.isdir(plotdir):
            os.makedirs(plotdir)

        # pdf report
        self.__update_step(0.25)
        if os.path.isfile(reportfile) and not self.overwrite:
            siibra.logger.warn(
                f"File {reportfile} exists - skipping analysis.")
            return reportfile

        backend = matplotlib.get_backend()
        matplotlib.use("Agg")

        # create plot of the input image
        self.__update_step(0.25)
        if image:
            input_plot = self._plot_input(
                image, os.path.join(plotdir, 'input.png'))
        else:
            input_plot = None

        # plot relevant probability maps
        pmap_plots = {}
        for i, assignment in enumerate(assignments):
            self.__update_step(len(assignments))
            if assignment.empty:
                continue
            label = labels[i]
            coordinate = coordinates[i]
            for regionname in tqdm(
                assignment.region.unique(),
                desc=f"Plotting probability maps for {label}...",
                unit="maps",
            ):
                pmap_plots[regionname] = self._plot_pmap(
                    regionname, plotdir, coordinate)

        # plot relevant features
        feature_plots = {}
        for i, assignment in enumerate(assignments):
            self.__update_step(len(assignments))
            if assignment.empty:
                continue
            for region in assignment.region.unique():
                if region in feature_plots.keys():
                    continue
                feature_plots[region] = {}
                for feature in features:
                    feature_plots[region][feature] = self.__plot_features(
                        region, feature, selected_receptors, cohorts, plotdir=plotdir)

        # build the actual pdf report
        self._build_pdf(
            assignments,
            input_plot,
            pmap_plots,
            feature_plots,
            reportfile,
            labels,
            coordinates,
            subject_coordinates,
            image
        )

        matplotlib.use(backend)
        return reportfile

    def __plot_features(self, region, feature, selected_receptors, cohorts, plotdir):

        receptors = [receptor + ' (' + siibra.vocabularies.RECEPTOR_SYMBOLS[receptor]
                     ['receptor']['name'] + ')' for receptor in selected_receptors]

        if feature == 'CellDensityProfile':
            filename = os.path.join(plotdir, f"{region.key}_{feature}.png")
            features = siibra.features.get(region, feature)
            if (not os.path.isfile(filename) or self.overwrite) and features:
                plt.ion()
                features[0].plot()
                plt.tight_layout(pad=0.2)
                plt.ioff()
                plt.savefig(filename, dpi=self.dpi)
                return [filename]
            else:
                return []
        elif feature == 'ReceptorDensityFingerprint':
            filenames = []

            features = siibra.features.get(region, feature)
            for i, feat in enumerate(features):
                filename = os.path.join(
                    plotdir, f"{region.key}_{feature}_{i+1}.png")
                if not os.path.isfile(filename) or self.overwrite:
                    plt.ion()
                    feat.polar_plot()
                    plt.tight_layout(pad=0.2)
                    plt.ioff()
                    plt.savefig(filename, dpi=self.dpi)
                    filenames.append(filename)

            return filenames

        elif feature == 'ReceptorDensityProfile':
            filenames = []

            features = siibra.features.get(region, feature)
            for feat in features:
                if feat.receptor in receptors:
                    filename = os.path.join(
                        plotdir, f"{region.key}_{feature}_{feat.receptor}.png")
                    if not os.path.isfile(filename) or self.overwrite:
                        plt.ion()
                        feat.plot()
                        plt.tight_layout(pad=0.2)
                        plt.ioff()
                        plt.savefig(filename, dpi=self.dpi)
                        filenames.append(filename)

            return filenames
        else:  # connectivity
            filenames = []

            features = siibra.features.get(region.parcellation, feature)
            for feat in features:
                if feat.cohort in cohorts:
                    filename = os.path.join(
                        plotdir, f"{region.key}_{feature}_{feat.cohort}.png")
                    if (not os.path.isfile(filename) or self.overwrite) and not filename in filenames:
                        plt.ion()
                        feat.get_profile(region, max_rows=30).plot()
                        plt.tight_layout(pad=0.2)
                        plt.ioff()
                        plt.savefig(filename, dpi=self.dpi)
                        filenames.append(filename)

            return filenames

    def _select_assignments(self, initial_assignments):
        mapping = {
            '<': lambda column, value: column < value,
            '>': lambda column, value: column > value,
            '=': lambda column, value: column == value
        }
        column, sign, value = self.filter
        initial_assignments = initial_assignments.drop(
            ['centroid', 'volume', 'fragment'], axis=1)
        results = []
        for component_id in range(initial_assignments['input structure'].max()+1):
            for _, (_, row) in enumerate(initial_assignments[lambda df: df['input structure'] == component_id].iterrows()):
                if row[column] and mapping[sign](row[column], value):
                    results.append(row)

        return pd.DataFrame(results)

    def _plot_input(self, img, filename):
        """plot  image to file"""
        if isinstance(img, str):
            img = nib.load(img)
        if not os.path.isfile(filename) or self.overwrite:
            plt.ion()
            fig, ax = plt.subplots(1, 1, figsize=(6, 3), dpi=self.dpi)
            plotting.plot_img(img, axes=ax, cmap='gray',
                              draw_cross=False, annotate=False)
            plt.ioff()
            fig.savefig(filename, dpi=self.dpi)
        return filename

    def _plot_pmap(self, region, plotdir, coordinate):
        filename = os.path.join(plotdir, f"{region.key}_pmap.png")
        if not os.path.isfile(filename) or self.overwrite:
            fig, ax = plt.subplots(1, 1, figsize=(6, 3), dpi=self.dpi)
            plt.ion()
            plotting.plot_glass_brain(
                region.fetch_regional_map(
                    self.pmaps.space, self.pmaps.maptype),
                axes=ax, colorbar=False, alpha=0.3, cmap="viridis"
            ).add_markers([coordinate.coordinate], marker_size=15)
            plt.ioff()
            fig.savefig(filename, dpi=self.dpi)
        return filename

    def _build_pdf(
        self,
        assignments,
        input_plot,
        pmap_plots,
        feature_plots,
        outfile,
        labels,
        coords,
        subj_coords,
        image
    ):

        pdf = FPDF()
        plot_height = 40
        text_height = 4

        # title page
        pdf.add_page()
        left = pdf.get_x()
        top = pdf.get_y()

        pdf.set_font("Helvetica", "BU", 20)
        pdf.set_xy(left, top)
        pdf.cell(40, 10, "voluba-mriwarp Anatomical Assignment")

        pdf.set_font("Helvetica", "", 10)
        pdf.set_xy(left, top + 14)
        pdf.multi_cell(
            0,
            text_height,
            "\n".join(
                [
                    f'Input scan: {os.path.basename(image.get_filename())}',
                    f"Parcellation: {self.pmaps.parcellation.name}",
                    " ",
                    f"For each point, regions with {self.filter[0]} {self.filter[1]} {self.filter[2]} are assigned.",
                    " ",
                    f"siibra version {siibra.__version__}",
                    f'Computed on {datetime.now().strftime("%c")}'
                ]
            ),
        )

        pdf.set_xy(left, top + 60)
        if input_plot:
            pdf.image(input_plot, w=180)

        pdf.set_xy(left, top + 60 + 75)

        siibra.logger.info(
            f"Building pdf report {outfile} for {len(assignments)} coordinates.")

        # one page per analyzed component
        for idx, assignment in enumerate(assignments):
            self.__update_step(len(assignments))
            pdf.add_page()
            pdf.set_font("Helvetica", "BU", 12)
            pdf.cell(40, text_height,
                     f"Assignments for {labels[idx]}")

            pdf.set_font("Helvetica", "", 10)
            pdf.set_xy(left, 14 + text_height)
            pdf.multi_cell(0, text_height,
                           f"Coordinate in subject space: \t{subj_coords[idx]} [mm]\nCoordinate in {siibra.spaces['mni152'].name}: {coords[idx].coordinate} [mm]")

            if assignment.empty:
                pdf.set_xy(left, 2 * (14 + text_height))
                pdf.multi_cell(0, text_height,
                               f"No regions assigned with {self.filter[0]} {self.filter[1]} {self.filter[2]}.")
                continue

            components = assignment['input structure'].unique()
            selection = pd.concat([assignment[lambda d: d['input structure'] == component]
                                  for component in components])

            for i, (_, row) in tqdm(
                enumerate(selection.iterrows()),
                total=len(selection),
                desc=f"- Page #{idx}",
                unit="assignments",
            ):

                pdf.set_font("Helvetica", "B", 10)
                pdf.set_xy(left, pdf.get_y() + text_height + 10)
                pdf.cell(40, text_height,
                         f"Coordinate {labels[idx]} assigned to {row.region}")

                pdf.set_font("Helvetica", "", 5)
                pdf.set_xy(left, pdf.get_y() + 5)
                with pdf.table() as table:
                    header = table.row()
                    values = table.row()
                    for col in selection.columns[2:]:
                        header.cell(col)
                        if row[col]:
                            values.cell(f'{row[col]:.6f}')
                        else:
                            values.cell('')

                pdf.set_xy(left, pdf.get_y() + 5)
                pdf.image(pmap_plots[row.region], h=plot_height)

                for feature in feature_plots[row.region].keys():
                    pdf.set_font("Helvetica", "B", 10)
                    pdf.set_xy(left, pdf.get_y() + 10)
                    pdf.cell(40, text_height, feature)

                    pdf.set_x(left)
                    y = pdf.get_y()
                    if feature_plots[row.region][feature]:
                        for k, filename in enumerate(feature_plots[row.region][feature]):
                            pdf.set_xy(pdf.get_x() + k %
                                       2 * pdf.epw * 0.5, y + 10)
                            pdf.image(filename, w=pdf.epw * 0.4)
                    else:
                        pdf.set_font("Helvetica", "", 10)
                        pdf.set_xy(left, pdf.get_y() + 10)
                        pdf.multi_cell(
                            0, text_height, f'There is no {feature} information available for {row.region}.')

        siibra.logger.info(f"Report written to {outfile}")
        pdf.output(outfile)
