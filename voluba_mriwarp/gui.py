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

from voluba_mriwarp.canvas import View
from voluba_mriwarp.config import *
from voluba_mriwarp.exceptions import *
from voluba_mriwarp.logic import Logic


class App(tk.Tk):
    """GUI window"""

    def __init__(self):
        """Initialize the window."""
        super().__init__(className=mriwarp_name)

        self.title(mriwarp_name)
        self.iconphoto(True, PhotoImage(Image.open(mriwarp_icon)))
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
        if not os.path.exists(parameter_home):
            os.mkdir(parameter_home)
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
        tk.Label(self, text='For details see voluba-mriwarp.readthedocs.io',
                 bg=siibra_bg, fg='white', font=font_12).pack(padx=10, pady=5)
        tk.Label(self, text='Loading siibra components. This may take a few minutes.',
                 bg=siibra_bg, fg=siibra_fg).pack(padx=10, pady=5)

        # Preload probability maps to speed up region assignment.
        thread = threading.Thread(target=self.logic.preload, daemon=True)
        thread.start()

        # Threading is needed because the window cannot be closed otherwise.
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
        self.__caret_right = icon_to_image(
            'caret-right', fill='white', scale_to_width=7)
        self.__caret_down = icon_to_image(
            'caret-down', fill='white', scale_to_width=11)

    def __create_viewpanel(self):
        """Create the frame for the NIfTI viewer."""
        # Update the window to get the real size of it.
        self.update()
        self.__view_panel = tk.Frame(self, bg=warp_bg, height=self.winfo_height(
        ), width=self.winfo_width() - sidepanel_width)
        self.__view_panel.pack(side='right')
        self.__view_panel.pack_propagate(False)

    def __create_sidepanel(self):
        """Create the frame and widgets for data selection, warping and region assignment."""
        # Update the window to get the real size of it.
        self.update()
        side_panel = tk.Frame(self, bg=siibra_highlight_bg,
                              height=self.winfo_height(), width=sidepanel_width)
        side_panel.pack(side='left', pady=10, fill='y', expand=True)
        side_panel.pack_propagate(False)

        # frame for data selection and menu chips
        operation_frame = tk.Frame(side_panel, bg=warp_bg)
        operation_frame.grid(row=0, column=0, sticky='nsew')

        # frame for data selection
        self.__data_frame = tk.Frame(operation_frame, bg=siibra_highlight_bg)
        self.__data_frame.grid(row=0, column=0, sticky='we')
        self.__create_data_widgets()

        # menu chips for warping and region assignment
        self.__step = tk.IntVar()
        menu = tk.Frame(operation_frame, bg=warp_bg)
        tk.Radiobutton(menu, text='Warping', indicatoron=0, width=20, bg=siibra_bg, fg='white', selectcolor=siibra_highlight_bg,
                       bd=0, variable=self.__step, command=self.__show_warping_frame, value=0).grid(row=0, column=0, pady=(20, 0))
        tk.Radiobutton(menu, text=' Region assignment', indicatoron=0, width=20, bg=siibra_bg, fg='white', selectcolor=siibra_highlight_bg,
                       bd=0, variable=self.__step, command=self.__show_assignment_frame, value=1).grid(row=0, column=1, pady=(20, 0))
        menu.grid(row=1, column=0, sticky='we')

        # frame for warping
        self.__warping_frame = tk.Frame(
            operation_frame, bg=siibra_highlight_bg)
        self.__warping_frame.grid(row=2, column=0, sticky='nwe')
        self.__create_warping_widgets()

        # frame for region assignment
        self.__assignment_frame = tk.Frame(
            operation_frame, bg=siibra_highlight_bg)
        self.__assignment_frame.grid(row=2, column=0, sticky='nwe')
        self.__create_assignment_widgets()
        self.__show_warping_frame()

        # help icon
        side_panel.rowconfigure(1, weight=1)
        tk.Button(side_panel, bg=siibra_highlight_bg, bd=0, highlightthickness=0, image=self.__help_icon, command=lambda: webbrowser.open(
            'https://voluba-mriwarp.readthedocs.io'), anchor='se').grid(row=3, column=0, sticky='se', pady=25, padx=(0, 25))

    def __create_data_widgets(self):
        """Create widgets for data selection."""
        # widgets for choosing the input NIfTI
        input_file = tk.StringVar()
        input_file.trace('w', lambda name, index, mode,
                         sv=input_file: self.__track_input(sv))
        tk.Label(self.__data_frame, bg=siibra_highlight_bg, width=11, anchor='w', fg='white',
                 text='Input NIfTI: ').grid(column=0, row=0, sticky='w', padx=(15, 10), pady=(20, 10))
        if platform.system() == 'Linux':
            self.__open_file_path = tk.Entry(
                self.__data_frame, bd=0, textvariable=input_file, width=39)
        else:
            self.__open_file_path = tk.Entry(
                self.__data_frame, bd=0, textvariable=input_file, width=57)
        self.__open_file_path.grid(column=1, row=0, pady=(20, 10))
        tk.Button(self.__data_frame, bd=0, command=self.__select_file, text='...', padx=2.5).grid(
            column=2, row=0, sticky='e', padx=(10, 15), pady=(20, 10))

        # widgets for choosing the output folder
        output_folder = tk.StringVar()
        output_folder.trace('w', lambda name, index, mode,
                            sv=output_folder: self.__track_output(sv))
        tk.Label(self.__data_frame, bg=siibra_highlight_bg, width=11, anchor='w', fg='white',
                 text='Output folder: ').grid(column=0, row=1, sticky='w', padx=(15, 10), pady=(0, 20))
        if platform.system() == 'Linux':
            self.__open_folder_path = tk.Entry(
                self.__data_frame, bd=0, textvariable=output_folder, width=39)
        else:
            self.__open_folder_path = tk.Entry(
                self.__data_frame, bd=0, textvariable=output_folder, width=57)
        self.__open_folder_path.insert(0, mriwarp_home)
        self.__open_folder_path.grid(column=1, row=1, pady=(0, 20))
        tk.Button(self.__data_frame, bd=0, command=self.__select_folder, text='...', padx=2.5).grid(
            column=2, row=1, sticky='e', padx=(10, 15), pady=(0, 20))

    def __create_warping_widgets(self):
        """Create widgets for warping."""
        # widgets for advanced registration
        advanced_frame = tk.Frame(self.__warping_frame, bg=siibra_highlight_bg, highlightbackground=siibra_bg, highlightthickness=2)
        advanced_frame.pack(fill='x', padx=10, pady=(20, 0))
        # button to expand parameter file selection
        self.__json_btn = tk.Button(advanced_frame, bd=0, command=self.__change_advanced, text=' Advanced registration settings ',
                                    padx=2.5, bg=siibra_highlight_bg, fg='white', image=self.__caret_right, compound='left', anchor='w')
        self.__json_btn.grid(column=0, row=0, sticky='w')
        # widgets for parameter file selection
        self.__param_frame = tk.Frame(advanced_frame, bg=siibra_highlight_bg)
        self.__param_frame.grid(column=0, row=1)
        json_file = tk.StringVar()
        label = tk.Label(self.__param_frame, bg=siibra_highlight_bg,
                         fg='white', text='Parameters: ', width=11)
        label.grid(column=0, row=1, padx=(0, 10), pady=5, sticky='w')
        if platform.system() == 'Linux':
            self.__open_json_path = tk.Entry(
                self.__param_frame, bd=0, textvariable=json_file, width=38)
        else:
            self.__open_json_path = tk.Entry(
                self.__param_frame, bd=0, textvariable=json_file, width=56)
        self.__open_json_path.insert(
            0, os.path.join(parameter_home, 'default.json'))
        self.__open_json_path.grid(column=1, row=1, pady=5)
        button = tk.Button(
            self.__param_frame, bd=0, command=self.__select_json, text='...', padx=2.5)
        button.grid(column=2, row=1, padx=10, pady=5, sticky='e')
        self.__param_frame.grid_remove()
        self.__json_showing = False

        # widgets for warping to MNI152
        self.__warp_button = tk.Button(
            self.__warping_frame, bd=0, command=self.__prepare_warping, text='Warp input to MNI152 space', padx=2.5)
        self.__warp_button.pack(fill='x', padx=10, pady=(10, 20))
        self.__check_mark = None

        # separator
        tk.Frame(self.__warping_frame, bg=siibra_bg).pack(fill='x')

        # frame for progressbar and status text
        self.__status_frame = tk.Frame(
            self.__warping_frame, bg=siibra_highlight_bg)
        self.__status_frame.pack(fill='x')

    def __create_assignment_widgets(self):
        """Create widgets for region assignment."""
        option_frame = tk.Frame(self.__assignment_frame,
                                bg=siibra_highlight_bg)
        option_frame.pack(fill='x')

        # widgets for MNI152 input
        tk.Label(option_frame, bg=siibra_highlight_bg, fg='white', justify='left', anchor='w',
                 text='Input already\nin MNI152:', width=11).grid(column=0, row=0, sticky='w', padx=(15, 10), pady=(20, 0))
        button_frame = tk.Frame(option_frame, bg=siibra_highlight_bg)
        button_frame.grid(column=1, row=0, sticky='w', padx=10, pady=(20, 0))
        s = ttk.Style(self)
        s.configure("TRadiobutton", background=siibra_highlight_bg,
                    foreground='white')
        self.__mni = tk.BooleanVar(value=0)
        ttk.Radiobutton(button_frame, text='no', variable=self.__mni, value=0,
                        command=self.__set_mni).grid(column=0, row=0, sticky='w')
        ttk.Radiobutton(button_frame, text='yes', variable=self.__mni,
                        value=1, command=self.__set_mni).grid(column=1, row=0, sticky='w', padx=(10, 0))

        # widgets for the parcellation selection
        tk.Label(option_frame, bg=siibra_highlight_bg, fg='white', justify='left', anchor='w',
                 text='Parcellation:', width=11).grid(row=1, column=0, sticky='w', padx=(15, 10), pady=(10, 20))
        parcellation = tk.StringVar()
        p_options = ttk.OptionMenu(option_frame, parcellation, self.logic.get_parcellation(), *self.logic.get_parcellations(),
                                   command=self.__change_parcellation)
        p_options.configure(width=40)
        p_options.grid(row=1, column=1, sticky='we', pady=(10, 20))

        # separator
        tk.Frame(self.__assignment_frame, bg=siibra_bg).pack(
            fill='x', pady=(0, 20))

        # frame for results of region assignment
        self.__region_frame = tk.Frame(
            self.__assignment_frame, bg=siibra_highlight_bg)
        self.__region_frame.pack(fill='x')

    def __show_warping_frame(self):
        """Bring the warping frame to the foreground."""
        self.__assignment_frame.grid_remove()
        self.__warping_frame.grid()

    def __show_assignment_frame(self):
        """Bring the assignment frame to the foreground."""
        self.__warping_frame.grid_remove()
        self.__assignment_frame.grid()

    def __change_advanced(self):
        """Show/Hide selection for parameter JSON."""
        if self.__json_showing:
            self.__json_btn.config(image=self.__caret_right)
            self.__param_frame.grid_remove()
            self.__json_showing = False
        else:
            self.__json_btn.config(image=self.__caret_down)
            self.__param_frame.grid()
            self.__json_showing = True

    def __set_mni(self):
        """Retry the region assignment for the currently selected point if the image type changes."""
        if self.__annotation != [-1, -1, -1]:
            self.set_annotation()

    def __create_viewer(self):
        """Create the viewer for the input NIfTI."""
        image = self.logic.get_numpy_source()
        # Initially the middle coronal slice is displayed.
        coronal_slice = round(image.shape[1] / 2) + 1

        # View needs to be initialized before slider as slider.set updates the viewer.
        self.__coronal_view = View(
            self.__view_panel, data=image[:, coronal_slice, :], slice=coronal_slice, side='bottom', padx=10, pady=10)

        # widget for changing the displayed slice
        self.__coronal_slider = tk.Scale(self.__view_panel, bg=warp_bg, fg='white', command=lambda value: self.__update_coronal(
            value), from_=1, highlightthickness=0, length=sidepanel_width - 100, orient=tk.HORIZONTAL, showvalue=True, sliderrelief=tk.FLAT, to=image.shape[1], )
        self.__coronal_slider.set(coronal_slice)
        self.__coronal_slider.pack(padx=10, pady=10)

        # Remove previous region assignments.
        for widget in self.__region_frame.winfo_children():
            widget.destroy()

        # widget for info on how to select regions
        label = tk.Label(self.__region_frame, anchor='w', bg=siibra_highlight_bg, borderwidth=10, compound='left', fg='white',
                         font=font_10, image=self.__info_icon, text=' Double click a location in the viewer to assign a brain region.')
        label.image = self.__info_icon
        label.grid(row=0, column=0, sticky='w', padx=5)

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
            self.__mni.set(0)
            self.__set_mni()

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

    def __select_json(self):
        """Select a parameter JSON."""
        # Open the latest given valid folder in the filedialog.
        folder = '/'
        if self.__open_json_path.get():
            folder = os.path.dirname(self.__open_json_path.get())

        filename = filedialog.askopenfilename(filetypes=[('JSON', '*.json')], initialdir=folder,
                                              title='Select parameter JSON')

        # Canceling the filedialog returns an empty string.
        if filename:
            self.__open_json_path.delete(0, tk.END)
            filename = os.path.normpath(filename)
        self.__open_json_path.insert(0, filename)

    def __select_file(self):
        """Select an input NIfTI."""
        # Open the latest given valid folder in the filedialog.
        folder = '/'
        if self.__open_file_path.get():
            folder = os.path.dirname(self.__open_file_path.get())

        filename = filedialog.askopenfilename(filetypes=[(
            'NIfTI', '*.nii *.nii.gz')], initialdir=folder, title='Select input NIfTI')

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
            self.logic.set_json_path(self.__open_json_path.get())
        except Exception as e:
            logging.getLogger(mriwarp_name).error(
                f'Error during path definition: {str(e)}')
            messagebox.showerror('Error', str(e))
            return

        self.logic.save_paths()

        # During warping the button is disabled to prevent multiple starts.
        self.__warp_button.configure(state=tk.DISABLED)

        # Remove status of previous warping.
        for widget in self.__status_frame.winfo_children():
            widget.destroy()

        # widgets for current warping status
        tk.Label(self.__status_frame, bg=siibra_highlight_bg, anchor='w', fg='white',
                 text=f'File: {os.path.basename(self.logic.get_in_path())}').pack(padx=10, pady=(20, 10), anchor='w')
        self.__progress_bar = ttk.Progressbar(
            self.__status_frame, mode='indeterminate', orient='horizontal')
        self.__progress_bar.pack(padx=10, fill='x')
        self.__progress_bar.start()

        # Start warping.
        threading.Thread(target=self.__run_warping, daemon=True).start()

    def __run_warping(self):
        """Warp the input NIfTI to MNI152 space with initial skull stripping."""
        logger = logging.getLogger(mriwarp_name)
        logger.info(f'Warping {os.path.basename(self.logic.get_in_path())}')

        # Skull stripping
        logger.info('Performing skull stripping')
        skull = tk.Label(self.__status_frame, bg=siibra_highlight_bg,
                         anchor='w', fg='white', text='Skull stripping ... ')
        skull.pack(padx=10, pady=5, anchor='w')
        try:
            self.logic.strip_skull()
        except Exception as e:
            skull.configure(image=self.__error_icon, compound='right')
            self.__show_error('skull stripping', e)
            return
        skull.configure(image=self.__success_icon, compound='right')

        # Registration
        logger.info('Performing registration')
        reg = tk.Label(self.__status_frame, bg=siibra_highlight_bg,
                       anchor='w', fg='white', text='Registration to MNI152 ... ')
        reg.pack(padx=10, pady=5, anchor='w')
        try:
            self.logic.register()
        except Exception as e:
            reg.configure(image=self.__error_icon, compound='right')
            self.__show_error('registration', e)
            return
        reg.configure(image=self.__success_icon, compound='right')
        self.__progress_bar.stop()

        # Finished
        logger.info('Finished')
        tk.Label(self.__status_frame, bg=siibra_highlight_bg, anchor='w',
                 fg='white', text='Finished!').pack(padx=10, pady=(5, 20), anchor='w')
        self.__warp_button.configure(state=tk.NORMAL)

        # Retry the region assignment for the currently selected point when warping finishes.
        if self.__annotation != [-1, -1, -1]:
            self.set_annotation()

    def __show_error(self, stage, error):
        """Stop the warping and show the error that occurred.

        :param str stage: stage of the warping (skull stripping or registration)
        :param Error error: error that occurred
        """
        self.__progress_bar.stop()
        self.__warp_button.configure(state=tk.NORMAL)
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
        ) == mni_template else 'aligned' if self.__mni.get() == 1 else 'unaligned'
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
            tk.Label(self.__region_frame, anchor='w', bg=siibra_highlight_bg, compound='left', fg=siibra_fg, image=self.__info_icon, justify='left', padx=10, pady=5, text=f'Could not find warping results in {self.logic.get_out_path()}.\n'
                     f'To assign regions to a selected point, please warp the input NIfTI to '
                     f'MNI152 space or provide the location of the transformation matrix as output folder.', wraplength=sidepanel_width - 20).pack(anchor='n', fill='x')

    def __create_annotation(self, coords):
        """Create widgets to display the selected annotation.

        :param list coords: annotation in physical space
        """
        # Round the coordinates to two decimals.
        for i in range(len(coords)):
            coords[i] = round(coords[i], 2)

        # widget for the annotated point in physical space
        tk.Label(self.__region_frame, anchor='w', bg='gold', borderwidth=10, fg=siibra_highlight_bg, font=font_12_b,
                 justify='left', text=f'Point {tuple(coords)} [mm]', wraplength=sidepanel_width - 20).pack(anchor='n', fill='x')

        # widget for the current filename
        tk.Label(self.__region_frame, anchor='w', bg=siibra_highlight_bg, fg=siibra_fg, justify='left',
                 padx=10, pady=5, text=f'in: {os.path.basename(self.logic.get_in_path())}').pack(anchor='n', fill='x')

    def __animate(self):
        """Show three animated dots to indicate running region assignment."""
        dots = tk.StringVar()
        dots.set('.')
        loading = tk.Label(self.__region_frame, bg=siibra_highlight_bg,
                           fg='white', font=font_18_b, textvariable=dots)
        loading.pack(anchor='center')

        while self.__calculating:
            time.sleep(1)
            if len(dots.get()) == 3:
                dots.set('')
            dots.set(dots.get() + '.')

        loading.destroy()

    def __create_assignment(self):
        """Create widgets displaying the regions assigned to the selected annotation."""
        # Indicate that the assignment is running.
        self.__calculating = True
        threading.Thread(target=self.__animate, daemon=True).start()

        # Assign regions.
        try:
            source, target, probabilities = self.logic.get_regions(
                self.__annotation)
        except SubprocessFailedError as e:
            logging.getLogger(mriwarp_name).error(
                f'Error during region calculation: {str(e)}')
            messagebox.showerror('Error', f'The following error occurred during region calculation:\n\n{str(e)}\n\n'
                                          f'If you need help, please contact support@ebrains.eu.')
            # No region can be found when an error occurs.
            tk.Label(self.__region_frame, anchor='w', bg='red', borderwidth=10, fg='black',
                     font=font_10_b, text='No region found').pack(anchor='n', fill='x')

            self.__calculating = False
            return
        except PointNotFoundError:
            logging.getLogger(mriwarp_name).error(
                f'{self.__annotation} outside MNI152 space.')
            # The point is outside the brain.
            tk.Label(self.__region_frame, anchor='w', bg='red', borderwidth=10, fg='black',
                     font=font_10_b, text='Point outside MNI152 space').pack(anchor='n', fill='x', side='top')
            self.__calculating = False
            return

        self.__calculating = False

        self.__create_annotation(source)

        # widget for the corresponding point in MNI152 space
        tk.Label(self.__region_frame, anchor='w', bg=siibra_highlight_bg, fg=siibra_fg, justify='left', padx=10,
                 text=f'identified with: {tuple(target)} [mm] in MNI152 2009c nonl asym').pack(anchor='n', fill='x', side='top')

        # widget for the parcellation
        tk.Label(self.__region_frame, anchor='w', bg=siibra_highlight_bg, fg=siibra_fg, justify='left',
                 padx=10, pady=5, text=f'assign to: {self.logic.get_parcellation()}').pack(anchor='n', fill='x')

        # separator with optional text
        separator = tk.Label(self.__region_frame, anchor='w', bg=siibra_bg,
                             fg=siibra_fg, font=('', 8, ''), padx=5, pady=5, text='\n')
        separator.pack(anchor='n', fill='x')

        # widgets for assigned regions
        region_frame = tk.Frame(self.__region_frame, bg=siibra_bg)
        region_frame.pack(anchor='n', fill='x')
        if probabilities:
            # in MNI152
            if len(probabilities) == 1 and probabilities[0][1] == 1:
                separator.configure(text='\nbrain region')

                (region, probabilitiy, url) = probabilities[0]
                frame = tk.Frame(region_frame, bg=siibra_highlight_bg)
                tk.Label(frame, anchor='w', bg=siibra_highlight_bg, fg=siibra_fg, font=font_10_b, padx=5,
                         pady=5, text=region, wraplength=sidepanel_width - 20).pack(anchor='n', side='left')
                # link to region in siibra-explorer
                button = tk.Button(frame, bg=siibra_highlight_bg, bd=0, highlightthickness=0,
                                   command=lambda: webbrowser.open(url), image=self.__link_icon)
                button.image = self.__link_icon
                button.pack(anchor='center', side='right', padx=5)
                frame.pack(anchor='n', fill='x', pady=(0, 5))
                return
            # in input brain scan
            separator.configure(
                text='\nvalue of probability map - brain region')

            for (region, probabilitiy, url) in probabilities:
                frame = tk.Frame(region_frame, bg=siibra_highlight_bg)
                tk.Label(frame, anchor='w', bg=siibra_highlight_bg, fg=siibra_fg, font=font_10_b, padx=5, pady=5,
                         text=f'{probabilitiy * 100:.2f}% - {region}', wraplength=sidepanel_width - 20).pack(anchor='n', side='left')
                # link to region in siibra-explorer
                button = tk.Button(frame, bg=siibra_highlight_bg, bd=0, highlightthickness=0,
                                   command=lambda url=url: webbrowser.open(url), image=self.__link_icon)
                button.image = self.__link_icon
                button.pack(anchor='center', side='right', padx=5)
                frame.pack(anchor='n', fill='x', pady=(0, 5))
        else:
            # no region found
            frame = tk.Frame(region_frame, bg=siibra_highlight_bg)
            tk.Label(frame, anchor='w', bg=siibra_highlight_bg, fg=siibra_fg, font=font_10_b, padx=5,
                     pady=5, text=f'No region found', wraplength=sidepanel_width - 20).pack(anchor='n', side='left')
            frame.pack(anchor='n', fill='x', side='top', pady=(0, 5))

    def __change_parcellation(self, parcellation):
        """Change the current parcellation that is used for region assignment.

        :param str parcellation: parcellation for region assignment
        """
        self.logic.set_parcellation(parcellation)

        # Rerun region assignment if parcellation is changed.
        if self.__annotation != [-1, -1, -1]:
            for widget in self.__region_frame.winfo_children():
                widget.destroy()
            self.__create_assignment()

    def on_closing(self):
        """Destroy the main window after asking for quit."""
        if messagebox.askokcancel('Quit', 'Do you really want to quit?', parent=self):
            self.destroy()
