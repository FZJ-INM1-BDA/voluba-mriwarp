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
from voluba_mriwarp.widgets import *


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
        self.__export_icon = icon_to_image(
            'file-export', fill=siibra_fg, scale_to_width=18)
        self.__help_icon = icon_to_image(
            'question-circle', fill=siibra_fg, scale_to_width=20)
        self.__caret_right = icon_to_image(
            'caret-right', fill='white', scale_to_width=7)
        self.__caret_down = icon_to_image(
            'caret-down', fill='white', scale_to_width=11)
        self.__save_icon = icon_to_image(
            'save', fill=siibra_bg, scale_to_width=15)
        self.__trash_icon = icon_to_image(
            'trash', fill='darkred', scale_to_width=12)
        self.__eye_icon = icon_to_image(
            'eye', fill=siibra_bg, scale_to_width=15)

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
        self.__sidepanel = tk.Frame(self, bg=siibra_highlight_bg,
                                    height=self.winfo_height(), width=sidepanel_width)
        self.__sidepanel.pack(side='left', pady=10, fill='both', expand=True)
        self.__sidepanel.pack_propagate(False)

        # little hack to make following widgets expand to full width
        f = tk.Frame(self.__sidepanel, bg=warp_bg, width=sidepanel_width)
        f.grid(row=0, column=0, sticky='we')
        f.grid_propagate(False)

        # frame for data selection
        self.__data_frame = tk.Frame(self.__sidepanel, bg=siibra_highlight_bg)
        self.__data_frame.grid(row=0, column=0, sticky='we')
        self.__create_data_widgets()

        # menu chips for warping and region assignment
        self.__step = tk.IntVar()
        self.__menu = tk.Frame(self.__sidepanel, bg=warp_bg)
        self.__menu.grid(row=1, column=0, sticky='we')
        tk.Radiobutton(self.__menu, text='Warping', indicatoron=0, width=20, bg=siibra_bg, fg='white', selectcolor=siibra_highlight_bg,
                       bd=0, variable=self.__step, command=self.__show_warping_frame, value=0, font=font_10_b).grid(row=0, column=0, pady=(20, 0))
        tk.Radiobutton(self.__menu, text=' Region assignment', indicatoron=0, width=20, bg=siibra_bg, fg='white', selectcolor=siibra_highlight_bg,
                       bd=0, variable=self.__step, command=self.__show_assignment_frame, value=1, font=font_10_b).grid(row=0, column=1, pady=(20, 0))

        # frame for warping
        self.__warping_frame = tk.Frame(
            self.__sidepanel, bg=siibra_highlight_bg)
        self.__warping_frame.grid(row=2, column=0, sticky='we')
        self.__create_warping_widgets()

        # frame for region assignment
        self.__assignment_frame = tk.Frame(
            self.__sidepanel, bg=siibra_highlight_bg)
        self.__assignment_frame.grid(row=2, column=0, sticky='nswe')
        self.__create_assignment_widgets()

        self.__show_warping_frame()

    def __create_data_widgets(self):
        """Create widgets for data selection."""
        # widgets for choosing the input NIfTI
        input_file = tk.StringVar()
        input_file.trace('w', lambda name, index, mode,
                         sv=input_file: self.__track_input(sv))
        tk.Label(self.__data_frame, bg=siibra_highlight_bg, width=15, anchor='w', fg='white',
                 text='Input NIfTI: ').grid(column=0, row=0, sticky='w', padx=(15, 10), pady=(20, 15))
        if platform.system() == 'Linux':
            self.__open_file_path = tk.Entry(
                self.__data_frame, bd=0, textvariable=input_file, width=39)
        else:
            self.__open_file_path = tk.Entry(
                self.__data_frame, bd=0, textvariable=input_file, width=57)
        self.__open_file_path.grid(column=1, row=0, pady=(20, 15))
        tk.Button(self.__data_frame, bd=0, command=self.__select_file, text='...', padx=2.5).grid(
            column=2, row=0, sticky='e', padx=(10, 15), pady=(20, 15))

        # widgets for choosing the output folder
        output_folder = tk.StringVar()
        output_folder.trace('w', lambda name, index, mode,
                            sv=output_folder: self.__track_output(sv))
        tk.Label(self.__data_frame, bg=siibra_highlight_bg, width=15, anchor='w', fg='white',
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
        advanced_frame = tk.Frame(self.__warping_frame, bg=siibra_highlight_bg,
                                  highlightbackground=siibra_bg, highlightthickness=2)
        advanced_frame.pack(fill='x', padx=15, pady=(20, 0))
        # button to expand parameter file selection
        self.__json_btn = tk.Button(advanced_frame, bd=0, command=self.__change_advanced, text=' Advanced settings ',
                                    padx=2.5, bg=siibra_highlight_bg, fg='white', image=self.__caret_right, compound='left', anchor='w')
        self.__json_btn.grid(column=0, row=0, sticky='w')
        # widgets for parameter file selection
        self.__param_frame = tk.Frame(advanced_frame, bg=siibra_highlight_bg)
        self.__param_frame.grid(column=0, row=1, padx=10, pady=5)
        json_file = tk.StringVar()
        tk.Label(self.__param_frame, bg=siibra_highlight_bg, justify='left', anchor='w', fg='white',
                 text='Parameters: ', width=15).grid(column=0, row=1, sticky='w')
        if platform.system() == 'Linux':
            self.__open_json_path = tk.Entry(
                self.__param_frame, bd=0, textvariable=json_file, width=35)
        else:
            self.__open_json_path = tk.Entry(
                self.__param_frame, bd=0, textvariable=json_file, width=53)
        self.__open_json_path.insert(
            0, os.path.join(parameter_home, 'default.json'))
        self.__open_json_path.grid(column=1, row=1, padx=10)
        tk.Button(self.__param_frame, bd=0, command=self.__select_json, text='...',
                  padx=2.5).grid(column=2, row=1, sticky='e')
        self.__param_frame.grid_remove()
        self.__json_showing = False

        # widgets for warping to MNI152
        self.__warp_button = tk.Button(
            self.__warping_frame, bd=0, command=self.__prepare_warping, text='Warp input to MNI152 space')
        self.__warp_button.pack(fill='x', padx=15, pady=(15, 20))
        self.__check_mark = None

        # separator
        tk.Frame(self.__warping_frame, bg=siibra_bg, height=10).pack(fill='x')

        # frame for progressbar and status text
        self.__status_frame = tk.Frame(
            self.__warping_frame, bg=siibra_highlight_bg)
        self.__status_frame.pack(fill='x')

    def __create_assignment_widgets(self):
        """Create widgets for region assignment."""
        # widgets for MNI152 input
        mni_frame = tk.Frame(self.__assignment_frame, bg=siibra_highlight_bg)
        mni_frame.pack(fill='x', padx=15, pady=(20, 0))
        tk.Label(mni_frame, bg=siibra_highlight_bg, fg='white', justify='left', anchor='w',
                 text='Input already in\nMNI152 space:', width=15).grid(column=0, row=0, sticky='w')
        style = ttk.Style(self)
        style.configure('TRadiobutton', background=siibra_highlight_bg,
                        foreground='white')
        self.__mni = tk.BooleanVar(value=0)
        ttk.Radiobutton(mni_frame, text='no', variable=self.__mni, value=0,
                        command=self.__set_mni).grid(column=1, row=0, sticky='w', padx=10)
        ttk.Radiobutton(mni_frame, text='yes', variable=self.__mni,
                        value=1, command=self.__set_mni).grid(column=2, row=0, sticky='w')

        # widgets for the parcellation selection
        parcellation_frame = tk.Frame(
            self.__assignment_frame, bg=siibra_highlight_bg)
        parcellation_frame.pack(fill='x', padx=15, pady=15)
        tk.Label(parcellation_frame, bg=siibra_highlight_bg, fg='white', justify='left', anchor='w',
                 text='Parcellation:', width=15).grid(row=0, column=0, sticky='w')
        parcellation = tk.StringVar()
        p_options = ttk.OptionMenu(parcellation_frame, parcellation, self.logic.get_parcellation(), *self.logic.get_parcellations(),
                                   command=self.__change_parcellation)
        p_options.configure(width=40)
        p_options.grid(row=0, column=1, sticky='we', padx=10)

        # widgets for point uncertainty
        uncertainty_frame = tk.Frame(
            self.__assignment_frame, bg=siibra_highlight_bg)
        uncertainty_frame.pack(fill='x', padx=15)
        tk.Label(uncertainty_frame, bg=siibra_highlight_bg, fg='white', justify='left', anchor='w',
                 text='Point uncertainty:', width=15).grid(row=0, column=0, sticky='w')
        vcmd = (self.register(self.__validate_uncertainty), '%P')
        self.__uncertainty = tk.Spinbox(uncertainty_frame, from_=0, to=100, validate='key', validatecommand=vcmd,
                                        increment=0.1, format='%.2f', width=5)
        self.__uncertainty.grid(row=0, column=1, sticky='w', padx=10)
        tk.Label(uncertainty_frame, bg=siibra_highlight_bg, fg='white', justify='left', anchor='w',
                 text='mm').grid(row=0, column=2, sticky='w')

        # widgets for advanced registration
        advanced_frame = tk.Frame(self.__assignment_frame, bg=siibra_highlight_bg,
                                  highlightbackground=siibra_bg, highlightthickness=2)
        advanced_frame.pack(fill='x', padx=15, pady=(15, 20))
        # button to expand parameter file selection
        self.__transform_btn = tk.Button(advanced_frame, bd=0, command=self.__change_advanced_transform, text=' Advanced settings ',
                                         padx=2.5, bg=siibra_highlight_bg, fg='white', image=self.__caret_right, compound='left', anchor='w')
        self.__transform_btn.grid(column=0, row=0, sticky='w')
        # widgets for parameter file selection
        self.__transform_frame = tk.Frame(
            advanced_frame, bg=siibra_highlight_bg)
        self.__transform_frame.grid(column=0, row=1, padx=10, pady=5)
        transform_file = tk.StringVar()
        transform_file.trace('w', lambda name, index, mode,
                             sv=transform_file: self.__track_transform(sv))
        tk.Label(self.__transform_frame, bg=siibra_highlight_bg, fg='white', justify='left', anchor='w',
                 text='Transformation file: ', width=15).grid(column=0, row=1, sticky='w')
        if platform.system() == 'Linux':
            self.__open_transform_path = tk.Entry(
                self.__transform_frame, bd=0, textvariable=transform_file, width=35)
        else:
            self.__open_transform_path = tk.Entry(
                self.__transform_frame, bd=0, textvariable=transform_file, width=53)
        self.__open_transform_path.grid(column=1, row=1, padx=10)
        tk.Button(self.__transform_frame, bd=0, command=self.__select_transform,
                  text='...', padx=2.5).grid(column=2, row=1, sticky='e')
        self.__transform_frame.grid_remove()
        self.__transform_showing = False

        # separator
        tk.Frame(self.__assignment_frame, bg=siibra_bg,
                 height=10).pack(fill='x')

        frame = tk.Frame(self.__assignment_frame, bg=siibra_highlight_bg)
        frame.pack(pady=(20, 10), padx=10, fill='x')
        tk.Label(frame, bg=siibra_highlight_bg, fg='white', font=font_10,
                 justify='left', anchor='w', text='Coordinates').pack(side='left')
        
        self.__export_btn = tk.Button(frame, bg = siibra_highlight_bg, fg='white', image=self.__export_icon, relief='flat', justify='right', anchor='e', command=self.__export_assignments, state=tk.DISABLED)
        self.__export_btn.pack(padx=10, side='left')

        self.update()
        remaining_height = (self.winfo_height()-self.__data_frame.winfo_height() -
                            self.__assignment_frame.winfo_height())//4

        # scrollable frame for points
        point_scroll_frame = tk.Frame(
            self.__assignment_frame, bg=siibra_highlight_bg)
        point_scroll_frame.pack(fill='x')
        point_canvas = tk.Canvas(point_scroll_frame, bg=siibra_highlight_bg, height=remaining_height,
                                 highlightbackground=siibra_highlight_bg, selectbackground=siibra_highlight_bg)
        point_scrollbar = tk.Scrollbar(
            point_scroll_frame, orient='vertical', command=point_canvas.yview)
        self.__point_frame = tk.Frame(
            point_canvas, bg=siibra_highlight_bg, padx=10, pady=10)

        self.__point_frame.bind('<Configure>', lambda e: point_canvas.configure(
            scrollregion=point_canvas.bbox('all')))
        point_canvas.create_window(
            (0, 0), window=self.__point_frame, anchor='nw')
        point_canvas.configure(yscrollcommand=point_scrollbar.set)
        point_canvas.pack(side='left', fill='both', expand=True)
        point_scrollbar.pack(side='right', fill='y')

        # table header
        columns = ['Label', 'R', 'A', 'S', 'Show regions']
        for i, column_text in enumerate(columns):
            tk.Entry(self.__point_frame, textvariable=tk.StringVar(
                value=column_text), state='readonly', width=13).grid(row=1, column=i)
        self.__point_widgets = []
        # add point (manually or by clicking)
        label = tk.StringVar()
        self.__R, self.__A, self.__S = tk.DoubleVar(), tk.DoubleVar(), tk.DoubleVar()
        widgets = [
            tk.Entry(self.__point_frame, width=10, textvariable=label),
            tk.Entry(self.__point_frame, textvariable=self.__R, width=10),
            tk.Entry(self.__point_frame, textvariable=self.__A, width=10),
            tk.Entry(self.__point_frame, textvariable=self.__S, width=10),
            tk.Button(self.__point_frame, image=self.__eye_icon, relief='groove',
                      command=lambda: self.__reload_assignment((self.__R.get(), self.__A.get(), self.__S.get()))),
            tk.Button(self.__point_frame, image=self.__save_icon, command=lambda: self.__save_point(
                (self.__R.get(), self.__A.get(), self.__S.get()), label))
        ]
        for i, widget in enumerate(widgets):
            widget.grid(row=2, column=i, sticky='nswe',
                        padx=5*(i == len(widgets)-1))

        # separator
        tk.Frame(self.__assignment_frame, bg=siibra_bg,
                 height=10).pack(fill='x')

        # frame for results of region assignment
        self.__region_frame = tk.Frame(
            self.__assignment_frame, bg=siibra_highlight_bg)
        self.__region_frame.pack(fill='both', expand=True)

    def __validate_uncertainty(self, value):
        """Validate if the entered uncertainty is a numerical value."""
        try:
            float(value)
            return True
        except:
            return False

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

    def __change_advanced_transform(self):
        """Show/Hide selection for transformation file."""
        if self.__transform_showing:
            self.__transform_btn.config(image=self.__caret_right)
            self.__transform_frame.grid_remove()
            self.__transform_showing = False
        else:
            self.__transform_btn.config(image=self.__caret_down)
            self.__transform_frame.grid()
            self.__transform_showing = True

    def __set_mni(self):
        """Retry the region assignment for the currently selected point if the image type changes."""
        if self.__mni.get() == 1:
            self.__transform_showing = True
            self.__change_advanced_transform()
            self.__transform_btn.configure(state=tk.DISABLED)
        else:
            self.__transform_btn.configure(state=tk.NORMAL)

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

        # help icon
        tk.Button(self.__view_panel, bg=warp_bg, bd=0, highlightthickness=0, image=self.__help_icon, command=lambda: webbrowser.open(
            'https://voluba-mriwarp.readthedocs.io')).pack(anchor='e', side='right', padx=20, pady=(20, 0))

        # widget for changing the displayed slice
        self.__coronal_slider = tk.Scale(self.__view_panel, bg=warp_bg, fg='white', command=lambda value: self.__update_coronal(
            value), from_=1, highlightthickness=0, length=sidepanel_width - 100, orient=tk.HORIZONTAL, showvalue=True, sliderrelief=tk.FLAT, to=image.shape[1], )
        self.__coronal_slider.set(coronal_slice)
        self.__coronal_slider.pack(padx=10, pady=10)

        # Remove previous region assignments.
        for widget in self.__region_frame.winfo_children():
            widget.destroy()

        # Remove previously saved points.
        self.__R.set(0)
        self.__A.set(0)
        self.__S.set(0)
        self.logic.delete_points()
        for row in self.__point_widgets:
            for widget in row:
                widget.destroy()
        self.__point_widgets = []

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

            for widget in self.__view_panel.winfo_children():
                widget.destroy()

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

    def __track_transform(self, variable):
        """Observe the Entry widget for the path to the transformation file.

        :param tkinter.StringVar variable: variable that holds the content of an Entry widget (path to transformation file)
        """
        path = variable.get()
        if self.logic.check_transform_path(path):
            # Retry the region assignment for the currently selected point if the transformation file changes.
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

    def __select_transform(self):
        """Select a transformation file."""
        # Open the latest given valid folder in the filedialog.
        folder = '/'
        if self.__open_transform_path.get():
            folder = os.path.dirname(self.__open_transform_path.get())

        filename = filedialog.askopenfilename(filetypes=[('*.h5, *.mat', '*.h5 *.mat')], initialdir=folder,
                                              title='Select transformation file')

        # Canceling the filedialog returns an empty string.
        if filename:
            self.__open_transform_path.delete(0, tk.END)
            filename = os.path.normpath(filename)
        self.__open_transform_path.insert(0, filename)

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
        # If the user specifies a new transformation file, it is used instead of the default file.
        transform_path = self.__open_transform_path.get()
        if transform_path:
            self.logic.set_transform_path(transform_path)

        type = 'template' if self.logic.get_in_path(
        ) == mni_template else 'aligned' if self.__mni.get() == 1 else 'unaligned'
        self.logic.set_img_type(type)
        self.__annotation = self.__coronal_view.get_annotation()
        # The origin in the viewer is upper left but the image origin is lower left.
        self.__annotation = [self.__annotation[0], self.__annotation[1],
                             self.logic.get_numpy_source().shape[0] - self.__annotation[2]]

        # set manual points to coords
        source_coords_ras = self.logic.vox2phys(self.__annotation)[0]
        self.__R.set(source_coords_ras[0])
        self.__A.set(source_coords_ras[1])
        self.__S.set(source_coords_ras[2])

        # Remove previous region assignments.
        for widget in self.__region_frame.winfo_children():
            widget.destroy()

        if self.logic.get_transform_path() or type != 'unaligned':
            threading.Thread(target=self.__create_assignment,
                             daemon=True).start()
        else:  # No transformation matrix can be found.
            self.__create_annotation(source_coords_ras)

            path = self.__open_transform_path.get().rstrip()
            if path == '':
                path = self.logic.get_out_path()
            # widget for info on missing transformation matrix
            tk.Label(self.__region_frame, anchor='w', bg=siibra_bg, compound='left', fg=siibra_fg, image=self.__info_icon, justify='left', padx=5,
                     text=f'Could not find a transformation in {path}.\n'
                     f'To assign regions to a selected point, please warp the input NIfTI to MNI152 space or '
                     f'provide the location of the transformation matrix in Advanced settings.\n'
                     f'If you need help, visit voluba-mriwarp.readthedocs.io.',
                     wraplength=sidepanel_width - 80).pack(fill='x', padx=5, pady=10)

    def __create_annotation(self, coords):
        """Create widgets to display the selected annotation.

        :param list coords: annotation in physical space
        """
        # Round the coordinates to two decimals.
        for i in range(len(coords)):
            coords[i] = round(coords[i], 2)

        # widget for the annotated point in physical space
        tk.Label(self.__region_frame, anchor='w', bg='gold', fg=siibra_bg, font=font_12_b, padx=10, pady=10,
                 justify='left', text=f'Point {tuple(coords)} [mm]').pack(fill='x', expand=True)

        # widget for the current filename
        tk.Label(self.__region_frame, anchor='w', bg=siibra_highlight_bg, fg=siibra_fg, justify='left', padx=5, pady=5,
                 text=f'in: {os.path.basename(self.logic.get_in_path())}').pack(fill='x', padx=5, pady=(5, 0))

    def __remove_point(self, point):
        """Remove a saved point and its corresponding widgets.

        :param tuple point: point to delete
        """
        idx = self.logic.delete_point(point)
        widgets = self.__point_widgets.pop(idx)
        for widget in widgets:
            widget.destroy()

        # TODO check len==0 and disable button
        if self.logic.get_num_points() == 0:
            self.__export_btn.configure(state=tk.DISABLED)

    def __save_point(self, point, label):
        """Save a point and add its corresponding widgets.

        :param tuple point: point to save
        """
        self.logic.save_point(point, label)
        idx = self.logic.get_num_points()

        widgets = [
            tk.Entry(self.__point_frame, width=10, textvariable=tk.StringVar(
                value=label.get() if label.get().rstrip() else idx)),
            tk.Entry(self.__point_frame, textvariable=tk.StringVar(
                value=point[0]), width=10, state='readonly'),
            tk.Entry(self.__point_frame, textvariable=tk.StringVar(
                value=point[1]), width=10, state='readonly'),
            tk.Entry(self.__point_frame, textvariable=tk.StringVar(
                value=point[2]), width=10, state='readonly'),
            tk.Button(self.__point_frame, image=self.__eye_icon, relief='groove',
                      command=lambda: self.__reload_assignment(point)),
            tk.Button(self.__point_frame, image=self.__trash_icon,
                      command=lambda: self.__remove_point(point))
        ]
        for i, widget in enumerate(widgets):
            widget.grid(row=idx+3, column=i, sticky='nswe',
                        padx=5*(i == len(widgets)-1))
        self.__point_widgets.append(widgets)

        self.__export_btn.configure(state=tk.NORMAL)

    def __reload_assignment(self, point):
        x, slice, y = self.logic.phys2vox(point)[0]
        # The origin in the viewer is upper left but the image origin is lower left.
        y = self.logic.get_numpy_source().shape[0] - y
        self.__coronal_slider.set(slice+1)  # The slider starts at 1.

        # redraw annotation on canvas
        self.__coronal_view.draw_annotation(x, slice, y)

    def __animate(self):
        """Show three animated dots to indicate running region assignment."""
        dots = tk.StringVar()
        dots.set('.')
        loading = tk.Label(self.__region_frame, bg=siibra_highlight_bg,
                           fg='white', font=font_18_b, textvariable=dots)
        loading.pack(fill='x', padx=15, pady=20)

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
            source, target, results, urls = self.logic.get_regions(
                self.__annotation, float(self.__uncertainty.get()))
        except SubprocessFailedError as e:
            logging.getLogger(mriwarp_name).error(
                f'Error during region calculation: {str(e)}')
            messagebox.showerror('Error', f'The following error occurred during region calculation:\n\n{str(e)}\n\n'
                                          f'If you need help, please contact support@ebrains.eu.')
            # No region can be found when an error occurs.
            tk.Label(self.__region_frame, anchor='w', bg='red', borderwidth=10, fg='black',
                     font=font_10_b, text='No region found').pack(fill='x')

            self.__calculating = False
            return
        except PointNotFoundError:
            logging.getLogger(mriwarp_name).error(
                f'{self.__annotation} outside MNI152 space.')
            # The point is outside the brain.
            tk.Label(self.__region_frame, anchor='w', bg='red', borderwidth=10, fg='black',
                     font=font_10_b, text='Point outside MNI152 space').pack(fill='x')
            self.__calculating = False
            return

        self.__calculating = False

        self.__create_annotation(source)

        # widget for the corresponding point in MNI152 space
        tk.Label(self.__region_frame, anchor='w', bg=siibra_highlight_bg, fg=siibra_fg, justify='left', padx=5,
                 text=f'identified with: {tuple(target)} [mm] in MNI152 2009c nonlinear asymmetric').pack(fill='x', padx=5)

        # widget for the parcellation
        tk.Label(self.__region_frame, anchor='w', bg=siibra_highlight_bg, fg=siibra_fg, justify='left', padx=5, pady=5,
                 text=f'assign to: {self.logic.get_parcellation()}').pack(fill='x', padx=5)

        # widget for the transformation file
        if self.logic.get_img_type() != 'unaligned':
            transform = 'NIfTI affine'
        elif self.logic.get_transform_path() == self.__open_transform_path.get():
            transform = 'advanced transformation'
        else:
            transform = 'default transformation'
        tk.Label(self.__region_frame, anchor='w', bg=siibra_highlight_bg, fg=siibra_fg, justify='left', padx=5,
                 text=f'using: {transform}').pack(fill='x', padx=5)

        # separator with optional text
        tk.Frame(self.__region_frame, bg=siibra_bg, height=10).pack(fill='x')

        self.update()
        remaining_height = self.winfo_height()-self.__data_frame.winfo_height() - \
            self.__assignment_frame.winfo_height()

        # widgets for assigned regions
        if not results.empty:
            region_frame = tk.Frame(
                self.__region_frame, bg=siibra_highlight_bg, height=remaining_height)
            region_frame.pack(fill='both', expand=True)
            region_frame.pack_propagate(False)

            style = ttk.Style()
            style.configure('Treeview.Heading', font=font_10_b)
            columns = results.columns.values.tolist()
            tree = customTreeView(
                region_frame, columns=columns, show='headings')
            tree.bind('<Double-1>', lambda event,
                      _urls=urls: tree.onDoubleClick(event, _urls))

            y_scrollbar = tk.Scrollbar(
                region_frame, orient='vertical', command=tree.yview)
            y_scrollbar.pack(side='right', fill='y')
            x_scrollbar = tk.Scrollbar(
                region_frame, orient='horizontal', command=tree.xview)
            x_scrollbar.pack(side='bottom', fill='x')
            tree.configure(xscrollcommand=x_scrollbar.set,
                           yscrollcommand=y_scrollbar.set)
            tree.pack(fill='both')

            for column in columns:
                tree.heading(column, text=column,
                             sort_by='str' if column == 'region' else 'float')

            for _, row in results.iterrows():
                values = [f'{value:.6f}' if isinstance(
                    value, float) else value for value in row.values]
                tree.insert('', tk.END, values=values)
        else:
            # no region found
            tk.Label(self.__region_frame, anchor='w', bg=siibra_highlight_bg, fg=siibra_fg, font=font_10_b, padx=10,
                     pady=10, text=f'No region found').pack(side='left')

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

    def __export_assignments(self):
        self.logic.set_uncertainty(float(self.__uncertainty.get()))
        ExportDialog(self, title='Export', logic=self.logic)

class ExportDialog(tk.simpledialog.Dialog):
    
    def __init__(self, parent, title, logic):
        self.__logic = logic

        super().__init__(parent, title=title)
        
    def body(self, master):

        # Explanation
        frame = tk.Frame(master, bg='white', padx=10, pady=10)
        frame.pack(fill='x')
        tk.Label(frame, text=f'Export assignments and features for {self.__logic.get_parcellation()}.', anchor='w', bg='white').pack(anchor='w')

        # Export location
        frame = tk.Frame(master, padx=10, pady=5)
        frame.pack()
        location_frame = tk.Frame(frame)
        location_frame.grid(row=0, column=0, pady=5, sticky='w')
        tk.Label(location_frame, text='Location: ', anchor='w').pack(side='left')
        self.__path_var = tk.StringVar()
        path = tk.Entry(location_frame, textvariable=self.__path_var, width=39)
        path.insert(0, os.path.join(mriwarp_home, self.__logic.get_name()))
        path.pack(side='left', padx=10)
        tk.Button(location_frame, text='...', padx=2.5, command=self.__select_location).pack(side='left')

        # Filter
        filter_frame = tk.Frame(frame)
        filter_frame.grid(row=1, column=0, sticky='w')
        tk.Label(filter_frame, text='Export features for regions assigned with:', anchor='w').pack(anchor='w')
        keys = ['correlation', 'intersection over union', 'map value', 'map weighted mean', 'map containedness', 'input weighted mean', 'input containedness']
        self.__col = tk.StringVar()
        ttk.OptionMenu(filter_frame, self.__col, keys[0], *keys).pack(side='left')
        self.__sign = tk.StringVar()
        signs = [">", ">=", "=", "<=", "<"]
        ttk.OptionMenu(filter_frame, self.__sign, signs[0], *signs).pack(side='left')
        self.__num = tk.DoubleVar()
        self.__num.set(0.3)
        vcmd = (self.register(self.__validate_filter), '%P')
        tk.Entry(filter_frame, textvariable=self.__num, validate='key', validatecommand=vcmd).pack(side='left')

        # Export features
        feature_frame = tk.Frame(frame)
        feature_frame.grid(row=2, column=0, sticky='w')
        tk.Label(feature_frame, text='Features: ', anchor='w').pack(anchor='w')
        self.__export_modalities = {}
        for modality in self.__logic.get_modalities():
            var = tk.IntVar()
            self.__export_modalities[modality] = var
            tk.Checkbutton(feature_frame, text=modality, variable=var, command=lambda modality=modality: self.__visibility(modality)).pack(anchor='w')

        # Export receptors
        self.__receptor_frame = tk.Frame(frame)
        self.__receptor_frame.grid(row=3, column=0, sticky='w')
        tk.Label(self.__receptor_frame, text='Receptors: ', anchor='w', justify='left').grid(row=0, column=0, sticky='w')
        self.__receptors = {}
        j = 0
        for i, receptor in enumerate(self.__logic.get_receptors()):
            j += (i%4 == 0)
            var = tk.IntVar()
            self.__receptors[receptor] = var
            tk.Checkbutton(self.__receptor_frame, text=receptor, variable=var, anchor='w', justify='left').grid(row=j, column=i%4, sticky='w')
        self.__visibility('ReceptorDensityProfile')

        # Export cohorts
        self.__cohort_frame = tk.Frame(frame)
        self.__cohort_frame.grid(row=4, column=0, sticky='w')
        tk.Label(self.__cohort_frame, text='Cohorts: ', anchor='w', justify='left').grid(row=0, column=0, sticky='w')
        self.__cohorts = {}
        for i, cohort in enumerate(['1000BRAINS', 'HCP']):
            var = tk.IntVar()
            self.__cohorts[cohort] = var
            tk.Checkbutton(self.__cohort_frame, text=cohort, variable=var).grid(row=1, column=i)
        self.__visibility('StreamlineCounts')

    def __visibility(self, modality):
        if modality == 'ReceptorDensityProfile':
            if self.__export_modalities[modality].get() == 0:
                self.__receptor_frame.grid_remove()
            else:
                self.__receptor_frame.grid()
            self.update()
        elif modality in ['StreamlineCounts', 'StreamlineLengths', 'FunctionalConnectivity']:
            if self.__export_modalities[modality].get() == 0:
                self.__cohort_frame.grid_remove()
            else:
                self.__cohort_frame.grid()
            self.update()

    def __validate_filter(self, value):
        """Validate if the entered filter is a numerical value."""
        try:
            float(value)
            return True
        except:
            return False

    def __select_location(self):
        """Select an export location."""
        # Open the latest given valid folder in the filedialog.
        foldername = filedialog.askdirectory(
            initialdir=self.__path_var.get(), title='Select export location')

        # Canceling the filedialog returns an empty string.
        if foldername:
            foldername = os.path.normpath(foldername)
            self.__path_var.set(foldername)

    def buttonbox(self):
        box = tk.Frame(self)

        w = tk.Button(box, text="Export", width=10, command=self.export, default=tk.ACTIVE)
        w.pack(side=tk.LEFT, padx=5, pady=5)
        w = tk.Button(box, text="Cancel", width=10, command=self.cancel)
        w.pack(side=tk.LEFT, padx=5, pady=5)

        self.bind("<Return>", self.ok)
        self.bind("<Escape>", self.cancel)

        box.pack()

    def export(self, event=None):

        # TODO call this in a thread
        # TODO show progress
        modalities = [modality for modality in self.__export_modalities if self.__export_modalities[modality].get() == 1]
        receptors = [receptor for receptor in self.__receptors if self.__receptors[receptor].get() == 1]
        cohorts = [cohort for cohort in self.__cohorts if self.__cohorts[cohort].get() == 1]
        self.__logic.export_assignments([self.__col.get(), self.__sign.get(), float(self.__num.get())], modalities, receptors, cohorts, self.__path_var.get())

        self.withdraw()
        self.update_idletasks()
        self.cancel()

    def cancel(self, event=None):
        # put focus back to the parent window
        if self.parent is not None:
            self.parent.focus_set()
        self.destroy()