import logging
import platform
import threading
import time
import tkinter as tk
import tkinter.ttk as ttk
import webbrowser
from tkinter import filedialog, messagebox

from PIL import Image
from PIL.ImageTk import PhotoImage
from tkfontawesome import icon_to_image

from siibra_mriwarp.canvas import View
from siibra_mriwarp.config import *
from siibra_mriwarp.exceptions import *
from siibra_mriwarp.logic import Logic


class App(tk.Tk):
    """GUI window"""

    def __init__(self):
        """Initialize the window."""
        super().__init__(className=mriwarp_name)

        self.title(mriwarp_name)
        self.iconphoto(True, PhotoImage(Image.open(siibra_icon)))
        # When the window is closed on_closing is called.
        self.protocol('WM_DELETE_WINDOW', self.on_closing)

        self.__create_logic()
        self.__create_preload_window()
        self.__create_main_window()

        self.mainloop()

    def __create_logic(self):
        """Create the instances for the logical backend."""
        self.logic = Logic()
        self.logic.set_in_path(mni_template)
        if not os.path.exists(mriwarp_home):
            os.mkdir(mriwarp_home)
        self.logic.set_out_path(mriwarp_home)
        self.__annotation = [-1, -1, -1]

    def __create_preload_window(self):
        """Create the widgets for preloading siibra components."""
        self.configure(bg=siibra_bg)
        self.resizable(False, False)

        # siibra logo
        logo = Image.open(mriwarp_logo_inv)
        logo = PhotoImage(logo)
        tk.Label(self, image=logo, bg=siibra_bg).pack()

        # some information
        tk.Label(self, text='For details see siibra-mriwarp.readthedocs.io', bg=siibra_bg,
                 fg='white', font=font_12).pack(padx=10, pady=5)
        tk.Label(self, text="Loading siibra components. This may take a few minutes.",
                 bg=siibra_bg, fg=siibra_fg).pack(padx=10, pady=5)

        # Preload probability maps to speed up region assignment.
        thread = threading.Thread(target=self.logic.preload, daemon=True)
        thread.start()

        while thread.is_alive():
            self.update()

        for widget in self.winfo_children():
            widget.destroy()

    def __create_main_window(self):
        """Create the widgets for the main window."""
        self.resizable(True, True)
        self.configure(bg=warp_bg)

        # Maximize the window.
        if platform.system() == 'Linux':
            self.update()
            self.attributes('-zoomed', True)
            self.update()
        else:
            self.state('zoomed')

        self.__load_icons()
        self.__create_sidepanel()
        self.__create_viewpanel()
        self.__create_viewer()

    def __load_icons(self):
        """Load fontawesome icons and convert them into a TkImage."""
        self.__success_icon = icon_to_image(
            'check', fill='green', scale_to_width=15)
        self.__error_icon = icon_to_image(
            'times', fill='red', scale_to_width=15)
        self.__info_icon = icon_to_image(
            'info-circle', fill='white', scale_to_width=15)
        self.__link_icon = icon_to_image(
            'external-link-alt', fill=siibra_fg, scale_to_width=15)
        self.__help_icon = icon_to_image(
            'question-circle', fill=siibra_fg, scale_to_width=20)

    def __create_viewpanel(self):
        """Create the frame for the NIfTI viewer."""
        # Update the window to get the real size of it
        self.update()
        self.__view_panel = tk.Frame(self, bg=warp_bg, height=self.winfo_height(),
                                     width=self.winfo_width() - sidepanel_width)
        self.__view_panel.pack(side='right')
        self.__view_panel.pack_propagate(False)

    def __create_sidepanel(self):
        """Create the frame and widgets for data selection, warping and region assignment."""
        self.update()
        side_panel = tk.Frame(
            self, bg=siibra_bg, height=self.winfo_height(), width=sidepanel_width)
        side_panel.pack(side='left', pady=10)
        side_panel.pack_propagate(False)

        # frame for data selection and warping
        self.__warping_frame = tk.Frame(
            side_panel, bg=siibra_highlight_bg, pady=10)
        self.__warping_frame.pack(anchor='w', fill='x', side='top')

        # widgets for choosing the input NIfTI
        input_file = tk.StringVar()
        input_file.trace('w', lambda name, index, mode,
                         sv=input_file: self.__track_input(sv))
        label = tk.Label(self.__warping_frame, bg=siibra_highlight_bg,
                         fg='white', text='Input NIfTI: ')
        if platform.system() == "Linux":
            self.__open_file_path = tk.Entry(
                self.__warping_frame, bd=0, textvariable=input_file, width=39)
        else:
            self.__open_file_path = tk.Entry(
                self.__warping_frame, bd=0, textvariable=input_file, width=57)
        open_file_button = tk.Button(
            self.__warping_frame, bd=0, command=self.__select_file, text='...', padx=2.5)
        label.grid(column=0, row=0, padx=5, pady=5, sticky='w')
        self.__open_file_path.grid(column=1, row=0, pady=5)
        open_file_button.grid(column=2, row=0, padx=5, pady=5, sticky='e')

        # dropdown for MNI152 input
        tk.Label(self.__warping_frame, bg=siibra_highlight_bg, fg='white', justify='left',
                 text='Input already\nin MNI152:').grid(column=0, row=1, sticky='w', padx=5)
        self.__check = tk.StringVar()
        ttk.OptionMenu(self.__warping_frame, self.__check, "", "no", "yes",
                       command=self.__set_mni).grid(column=1, row=1, sticky='ew')

        # widgets for choosing the output folder
        output_folder = tk.StringVar()
        output_folder.trace('w', lambda name, index, mode,
                            sv=output_folder: self.__track_output(sv))
        label = tk.Label(self.__warping_frame, bg=siibra_highlight_bg,
                         fg='white', text='Output folder: ')
        if platform.system() == "Linux":
            self.__open_folder_path = tk.Entry(
                self.__warping_frame, bd=0, textvariable=output_folder, width=39)
        else:
            self.__open_folder_path = tk.Entry(
                self.__warping_frame, bd=0, textvariable=output_folder, width=57)
        self.__open_folder_path.insert(0, mriwarp_home)
        open_folder_button = tk.Button(
            self.__warping_frame, bd=0, command=self.__select_folder, text='...', padx=2.5)
        label.grid(column=0, row=2, padx=5, pady=5, sticky='w')
        self.__open_folder_path.grid(column=1, row=2, pady=5)
        open_folder_button.grid(column=2, row=2, padx=5, pady=5, sticky='e')

        # widgets for warping to MNI152
        self.__warp_button = tk.Button(self.__warping_frame, bd=0, command=self.__prepare_warping,
                                       text='Warp input to MNI152 space')
        self.__warp_button.grid(column=1, row=3, pady=5)
        self.__check_mark = None

        # frame for region assignment
        self.__region_frame = tk.Frame(side_panel, bg=siibra_bg)
        self.__region_frame.pack(anchor='w', fill='x',
                                 side='top', pady=(20, 10))

        # logos
        hbp_img = Image.open(hbp_ebrains_color)
        hbp_img = PhotoImage(hbp_img.resize(
            size=(hbp_img.size[0] // 25, hbp_img.size[1] // 25)))
        img_hbp = tk.Label(side_panel, bg=siibra_bg, image=hbp_img)
        img_hbp.image = hbp_img
        img_hbp.pack(anchor='s', side='left')

        # help icon
        tk.Button(side_panel, bg=siibra_bg, bd=0, highlightthickness=0, image=self.__help_icon, command=lambda: webbrowser.open(
            'https://siibra-mriwarp.readthedocs.io')).pack(anchor='s', side='right', pady=25, padx=(0, 25))

    def __set_mni(self, value):
        if value == "yes":
            self.__warp_button.grid_remove()
            if self.__check_mark:
                self.__check_mark.grid_remove()
        else:
            self.__warp_button.grid()
            if self.__check_mark:
                self.__check_mark.grid()
        # Retry the region assignment for the currently selected point if type changes.
        if self.__annotation != [-1, -1, -1]:
            self.set_annotation()

    def __create_viewer(self):
        """Create the viewer for the input NIfTI."""
        image = self.logic.get_numpy_source()
        # Initially the middle coronal slice is displayed.
        coronal_slice = round(image.shape[1] / 2) + 1

        # View needs to be initialized before slider as slider.set updates the viewer.
        self.__coronal_view = View(self.__view_panel, data=image[:, coronal_slice, :], slice=coronal_slice,
                                   side='bottom', padx=10, pady=10)

        # widget for changing the displayed slice
        self.__coronal_slider = tk.Scale(self.__view_panel, bg=warp_bg, fg='white',
                                         command=lambda value: self.__update_coronal(value), from_=1,
                                         highlightthickness=0, length=sidepanel_width - 100, orient=tk.HORIZONTAL,
                                         showvalue=True, sliderrelief=tk.FLAT, to=image.shape[1], )
        self.__coronal_slider.set(coronal_slice)
        self.__coronal_slider.pack(side='top', padx=10, pady=10)

        # Remove previous region assignments.
        for widget in self.__region_frame.winfo_children():
            widget.destroy()

        # widget for info on how to select regions
        label = tk.Label(self.__region_frame, anchor='w', bg=siibra_bg, borderwidth=10, compound='left', fg='white',
                         font=font_12, image=self.__info_icon, text=' Double click to select a region.')
        label.image = self.__info_icon
        label.pack(anchor='n', expand=True, fill='x', side='left')

        self.update()
        # Move the input NIfTI to the center of the viewer.
        self.__coronal_view.move_to_center()
        self.__annotation = [-1, -1, -1]

    def __track_input(self, variable):
        """Observe the Entry widget for the path to the input NIfTI.

        :param tkinter.StringVar variable: variable that holds the content of an Entry widget (path to input NIfTI)
        """
        path = variable.get()
        # Show the NIfTI when the given path is valid.
        if self.logic.check_in_path(path):
            self.logic.set_in_path(path)
            if self.__check_mark:
                self.__check_mark.grid_remove()
                self.__check_mark = None

            self.__coronal_view.canvas.destroy()
            self.__coronal_view.destroy()
            self.__coronal_slider.destroy()

            self.__create_viewer()
            self.__check.set("no")
            self.__set_mni("no")

    def __track_output(self, variable):
        """Observe the Entry widget for the path to the output folder.

        :param tkinter.StringVar variable: variable that holds the content of an Entry widget (path to output folder)
        """
        path = variable.get()
        if self.logic.check_out_path(path):
            self.logic.set_out_path(path)
            # Retry the region assignment for the currently selected point if the output folder changes.
            if self.__annotation != [-1, -1, -1]:
                self.set_annotation()

    def __select_file(self):
        """Select an input NIfTI."""
        # Open the latest given valid folder in the filedialog.
        folder = '/'
        if self.__open_file_path.get():
            folder = os.path.dirname(self.__open_file_path.get())

        filename = filedialog.askopenfilename(filetypes=[('NIfTI', '*.nii *.nii.gz')], initialdir=folder,
                                              title='Select input NIfTI')

        # Canceling the filedialog returns an empty string.
        if filename:
            self.__open_file_path.delete(0, tk.END)
            filename = os.path.normpath(filename)
        self.__open_file_path.insert(0, filename)

    def __select_folder(self):
        """Select an output folder."""
        # Open the latest given valid folder in the filedialog.
        foldername = filedialog.askdirectory(
            initialdir=self.__open_folder_path.get(), title='Select output folder')

        # Canceling the filedialog returns an empty string.
        if foldername:
            self.__open_folder_path.delete(0, tk.END)
            foldername = os.path.normpath(foldername)
        self.__open_folder_path.insert(0, foldername)

    def __prepare_warping(self):
        """Prepare the logic and widgets and start warping the input NIfTI to MNI152."""
        try:
            self.logic.set_in_path(self.__open_file_path.get())
            self.logic.set_out_path(self.__open_folder_path.get())
        except Exception as e:
            logging.getLogger(mriwarp_name).error(
                f'Error during in/out path definition: {str(e)}')
            messagebox.showerror('Error', str(e))
            return

        self.logic.save_paths()

        # During warping the button is disabled to prevent multiple starts.
        self.__warp_button.grid_remove()
        if self.__check_mark:
            self.__check_mark.grid_remove()

        self.__progress_bar = ttk.Progressbar(self.__warping_frame, length=450, mode='indeterminate',
                                              orient='horizontal')
        self.__progress_bar.grid(column=0, row=3, columnspan=3, padx=5, pady=5)
        self.__progress_bar.start()

        threading.Thread(target=self.__run_warping, daemon=True).start()

    def __run_warping(self):
        """Warp the input NIfTI to MNI152 space with initial skull stripping."""
        logger = logging.getLogger(mriwarp_name)
        logger.info('Performing skull stripping')
        try:
            self.logic.strip_skull()
        except Exception as e:
            self.__show_error('skull stripping', e)
            return
        logger.info('Performing registration')
        try:
            self.logic.register()
        except Exception as e:
            self.__show_error('registration', e)
            return
        self.__progress_bar.stop()
        self.__progress_bar.destroy()
        logger.info('Finished')
        self.__warp_button.grid()
        # Show a green check mark when the warping was successful.
        self.__check_mark = tk.Label(
            self.__warping_frame, bg=siibra_highlight_bg, image=self.__success_icon)
        self.__check_mark.grid(column=2, row=3, pady=5)
        # Retry the region assignment for the currently selected point when warping finishes.
        if self.__annotation != [-1, -1, -1]:
            self.set_annotation()

    def __show_error(self, stage, error):
        """Stop the warping and show the error that occurred.

        :param str stage: stage of the warping (skull stripping or registration)
        :param Error error: error that occurred
        """
        self.__progress_bar.stop()
        self.__progress_bar.destroy()
        self.__warp_button.grid()
        # Show a red cross when the warping was NOT successful.
        self.__check_mark = tk.Label(
            self.__warping_frame, bg=siibra_highlight_bg, image=self.__error_icon)
        self.__check_mark.grid(column=2, row=3, pady=5)
        logging.getLogger(mriwarp_name).error(
            f'Error during {stage}: {str(error)}')
        messagebox.showerror('Error',
                             f'The following error occurred during {stage}:\n\n{str(error)}\n\n'
                             f'If you need help, please contact support@ebrains.eu.')

    def __update_coronal(self, value):
        """Update the shown slice in the viewer.

        :param int value: slice of the input NIfTI to display
        """
        self.__coronal_view.update_data(self.logic.get_numpy_source()[
                                        :, int(value) - 1, :], int(value) - 1)

    def set_annotation(self):
        """Set the annotation and start the region assignment."""
        type = 'template' if self.logic.get_in_path(
        ) == mni_template else 'aligned' if self.__check.get() == 'yes' else 'unaligned'
        self.logic.set_img_type(type)
        self.__annotation = self.__coronal_view.get_annotation()
        # The origin in the viewer is upper left but the image origin is lower left.
        self.__annotation = [self.__annotation[0], self.__annotation[1],
                             self.logic.get_numpy_source().shape[0] - self.__annotation[2]]

        # Remove previous region assignments.
        for widget in self.__region_frame.winfo_children():
            widget.destroy()

        if self.logic.get_transform_path() or type != 'unaligned':
            threading.Thread(target=self.__create_assignment,
                             daemon=True).start()
        else:  # No transformation matrix can be found.
            source_coords_ras = self.logic.vox2phys(self.__annotation)

            self.__create_annotation(source_coords_ras[0])

            # widget for info on missing transformation matrix
            tk.Label(self.__region_frame, anchor='w', bg=siibra_highlight_bg, compound='left', fg=siibra_fg,
                     image=self.__info_icon, justify='left', padx=10, pady=5,
                     text=f'Could not find warping results in {self.logic.get_out_path()}.\n'
                          f'To assign regions to a selected point, please warp the input NIfTI to '
                          f'MNI152 space or provide the location of the transformation matrix as output folder.',
                     wraplength=sidepanel_width - 20).pack(anchor='n', fill='x', side='top')

    def __create_annotation(self, coords):
        """Create widgets to display the selected annotation.

        :param list coords: annotation in physical space
        """
        # Round the coordinates to two decimals.
        for i in range(len(coords)):
            coords[i] = round(coords[i], 2)

        # widget for the annotated point in physical space
        tk.Label(self.__region_frame, anchor='w', bg='gold', borderwidth=10, fg=siibra_highlight_bg,
                 font=font_12_b, justify='left', text=f'Point {tuple(coords)} [mm]',
                 wraplength=sidepanel_width - 20).pack(anchor='n', fill='x', side='top')

        # widget for the current filename
        tk.Label(self.__region_frame, anchor='w', bg=siibra_highlight_bg, fg=siibra_fg, justify='left', padx=10, pady=5,
                 text=f'in: {os.path.basename(self.logic.get_in_path())}').pack(anchor='n', fill='x', side='top')

    def __animate(self):
        """Show three animated dots to indicate running region assignment."""
        dots = tk.StringVar()
        dots.set('.')
        loading = tk.Label(self.__region_frame, bg=siibra_bg, fg='white', font=font_18_b,
                           textvariable=dots)
        loading.pack(anchor='center', side='top')

        while self.__calculating:
            time.sleep(1)
            if len(dots.get()) == 3:
                dots.set('')
            dots.set(dots.get() + '.')

        loading.destroy()

    def __create_assignment(self):
        """Create widgets displaying the regions assigned to the selected annotation."""
        # Indicate that the assignment is running
        self.__calculating = True
        threading.Thread(target=self.__animate, daemon=True).start()

        try:
            source, target, probabilities = self.logic.get_regions(
                self.__annotation)
        except SubprocessFailedError as e:
            logging.getLogger(mriwarp_name).error(
                f'Error during region calculation: {str(e)}')
            messagebox.showerror('Error', f'The following error occurred during region calculation:\n\n{str(e)}\n\n'
                                          f'If you need help, please contact support@ebrains.eu.')
            # No region can be found when an error occurs
            tk.Label(self.__region_frame, anchor='w', bg='red', borderwidth=10, fg='black',
                     font=font_10_b, text='No region found').pack(anchor='n', fill='x', side='top')

            self.__calculating = False
            return
        except PointNotFoundError:
            logging.getLogger(mriwarp_name).error(
                f'{self.__annotation} outside MNI152 space.')
            # The point is outside the brain.
            tk.Label(self.__region_frame, anchor='w', bg='red', borderwidth=10, fg='black',
                     font=font_10_b, text='Point outside MNI152 space').pack(anchor='n', fill='x',
                                                                             side='top')
            self.__calculating = False
            return

        self.__calculating = False

        self.__create_annotation(source)

        # widget for the corresponding point in MNI152 space
        tk.Label(self.__region_frame, anchor='w', bg=siibra_highlight_bg, fg=siibra_fg, justify='left', padx=10,
                 text=f'identified with: {tuple(target)} [mm] in MNI152 2009c nonl asym').pack(anchor='n', fill='x',
                                                                                               side='top')

        # widget for the parcellation
        tk.Label(self.__region_frame, anchor='w', bg=siibra_highlight_bg, fg=siibra_fg, justify='left', padx=10, pady=5,
                 text=f'assign to: Julich-Brain 2.9').pack(anchor='n', fill='x', side='top', pady=(0, 20))

        # widgets for assigned regions
        if probabilities:
            if len(probabilities) == 1 and probabilities[0][1] == 1:
                tk.Label(self.__region_frame, anchor='w', bg=siibra_bg, fg=siibra_fg, font=('', 8, ''), justify='left',
                         padx=5, text='brain region').pack(anchor='n', fill='x', side='top')

                (region, probabilitiy, url) = probabilities[0]
                frame = tk.Frame(self.__region_frame, bg=siibra_highlight_bg)
                tk.Label(frame, anchor='w', bg=siibra_highlight_bg, fg=siibra_fg, font=font_10_b, padx=5,
                         pady=5, text=region, wraplength=sidepanel_width - 20).pack(anchor='n', side='left')
                # link to region in siibra-explorer
                button = tk.Button(frame, bg=siibra_highlight_bg, bd=0, highlightthickness=0, command=lambda: webbrowser.open(url),
                                   image=self.__link_icon)
                button.image = self.__link_icon
                button.pack(anchor='center', side='right', padx=5)
                frame.pack(anchor='n', fill='x', side='top', pady=2.5)
                return

            tk.Label(self.__region_frame, anchor='w', bg=siibra_bg, fg=siibra_fg, font=('', 8, ''), justify='left',
                     padx=5, text='value of probability map - brain region').pack(anchor='n', fill='x', side='top')

            for (region, probabilitiy, url) in probabilities:
                frame = tk.Frame(self.__region_frame, bg=siibra_highlight_bg)
                tk.Label(frame, anchor='w', bg=siibra_highlight_bg, fg=siibra_fg, font=font_10_b, padx=5,
                         pady=5, text=f'{probabilitiy * 100:.2f}% - {region}', wraplength=sidepanel_width - 20).pack(
                    anchor='n', side='left')
                # link to region in siibra-explorer
                button = tk.Button(frame, bg=siibra_highlight_bg, bd=0, highlightthickness=0, command=lambda url=url: webbrowser.open(url),
                                   image=self.__link_icon)
                button.image = self.__link_icon
                button.pack(anchor='center', side='right', padx=5)
                frame.pack(anchor='n', fill='x', side='top', pady=2.5)
        else:
            frame = tk.Frame(self.__region_frame, bg=siibra_highlight_bg)
            tk.Label(frame, anchor='w', bg=siibra_highlight_bg, fg=siibra_fg, font=font_10_b, padx=5,
                     pady=5, text=f'No region found', wraplength=sidepanel_width - 20).pack(anchor='n', side='left')
            frame.pack(anchor='n', fill='x', side='top', pady=2.5)

    def on_closing(self):
        """Destroy the main window after asking for quit."""
        if messagebox.askokcancel('Quit', 'Do you really want to quit?', parent=self):
            self.destroy()
