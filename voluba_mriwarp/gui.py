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

from voluba_mriwarp.config import *
from voluba_mriwarp.exceptions import *
from voluba_mriwarp.logic import Logic
from voluba_mriwarp.viewer import Viewer
from voluba_mriwarp.widgets import *


class App(tk.Tk):
    """GUI window"""

    def __init__(self):
        """Initialize the window."""
        super().__init__(className=mriwarp_name)

        self.title(mriwarp_name)
        self.iconphoto(True, PhotoImage(Image.open(mriwarp_icon)))
        # When the window is closed on_closing is called.
        self.protocol('WM_DELETE_WINDOW', self.close)

        self.__create_logic()
        self.__create_preload_window()
        self.__create_main_window()

        self.mainloop()

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
        self.__brain_icon = icon_to_image(
            'brain', fill=siibra_bg, scale_to_width=15)

    def __create_logic(self):
        """Create the instances for the logical backend."""
        self.logic = Logic()
        self.logic.set_in_path(mni_template)
        self.logic.set_out_path(mriwarp_home)
        self.__annotation = (-1, -1, -1)

    def __create_preload_window(self):
        """Create the widgets for preloading siibra components."""
        self.configure(bg=siibra_bg)
        self.resizable(False, False)

        # siibra logo
        logo = Image.open(mriwarp_logo_inv)
        logo = PhotoImage(logo)
        label = tk.Label(self, image=logo, bg=siibra_bg)
        label.pack()

        # some information
        label = tk.Label(
            self, text='For details see voluba-mriwarp.readthedocs.io',
            font=font_12, bg=siibra_bg, fg='white')
        label.pack(padx=10, pady=5)
        label = tk.Label(
            self,
            text='Loading siibra components. This may take a few minutes.',
            bg=siibra_bg, fg=siibra_fg)
        label.pack(padx=10, pady=5)

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
        self.configure(bg=viewer_bg)

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

    def __create_viewpanel(self):
        """Create the frame for the NIfTI viewer."""
        # Update the window to get the real size of it.
        self.update()
        self.__view_panel = tk.Frame(
            self, bg=viewer_bg, height=self.winfo_height(),
            width=self.winfo_width() - sidepanel_width)
        self.__view_panel.pack(side='right')
        self.__view_panel.pack_propagate(False)

    def __create_sidepanel(self):
        """Create the frame and widgets for data selection, warping and region 
        assignment.
        """
        # Update the window to get the real size of it.
        self.update()
        self.__sidepanel = tk.Frame(
            self, bg=siibra_highlight_bg, height=self.winfo_height(),
            width=sidepanel_width)
        self.__sidepanel.pack(side='left', fill='both', expand=True, pady=10)
        self.__sidepanel.pack_propagate(False)

        # little hack to make following widgets expand to full width
        frame = tk.Frame(self.__sidepanel, bg=viewer_bg, width=sidepanel_width)
        frame.grid(column=0, row=0, sticky='we')
        frame.grid_propagate(False)

        # frame for data selection
        self.__data_frame = tk.Frame(self.__sidepanel, bg=siibra_highlight_bg)
        self.__data_frame.grid(column=0, row=0, sticky='we')
        self.__create_data_widgets()

        # menu chips for warping and region assignment
        self.__step = tk.IntVar()
        self.__menu = tk.Frame(self.__sidepanel, bg=viewer_bg)
        self.__menu.grid(column=0, row=1, sticky='we')
        radio_button = tk.Radiobutton(
            self.__menu, text='Warping', font=font_10_b, bg=siibra_bg,
            fg='white', variable=self.__step, value=0,
            command=self.__show_warping_frame, indicatoron=0,
            selectcolor=siibra_highlight_bg, bd=0, width=20)
        radio_button.grid(column=0, row=0, pady=(20, 0))
        radio_button = tk.Radiobutton(
            self.__menu, text=' Region assignment', font=font_10_b,
            bg=siibra_bg, fg='white', variable=self.__step, value=1,
            command=self.__show_assignment_frame, indicatoron=0,
            selectcolor=siibra_highlight_bg, bd=0, width=20)
        radio_button.grid(column=1, row=0, pady=(20, 0))

        # frame for warping
        self.__warping_frame = tk.Frame(
            self.__sidepanel, bg=siibra_highlight_bg)
        self.__warping_frame.grid(column=0, row=2, sticky='we')
        self.__create_warping_widgets()

        # frame for region assignment
        self.__assignment_frame = tk.Frame(
            self.__sidepanel, bg=siibra_highlight_bg)
        self.__assignment_frame.grid(column=0, row=2, sticky='nswe')
        self.__create_assignment_widgets()

        self.__show_warping_frame()

    def __create_data_widgets(self):
        """Create widgets for data selection."""
        # widgets for choosing the input NIfTI
        input_file = tk.StringVar()
        input_file.trace('w', lambda name, index, mode,
                         sv=input_file: self.__track_input(sv))
        label = tk.Label(
            self.__data_frame, text='Input NIfTI: ', bg=siibra_highlight_bg,
            fg='white', anchor='w', width=15)
        label.grid(column=0, row=0, sticky='w', padx=(15, 10), pady=(20, 15))
        if platform.system() == 'Linux':
            self.__open_file_path = tk.Entry(
                self.__data_frame, textvariable=input_file, bd=0, width=39)
        else:
            self.__open_file_path = tk.Entry(
                self.__data_frame, textvariable=input_file, bd=0,  width=57)
        self.__open_file_path.grid(column=1, row=0, pady=(20, 15))
        button = tk.Button(
            self.__data_frame, text='...', command=self.__select_input, bd=0,
            padx=2.5)
        button.grid(column=2, row=0, sticky='e', padx=(10, 15), pady=(20, 15))

        # widgets for choosing the output folder
        output_folder = tk.StringVar()
        output_folder.trace('w', lambda name, index, mode,
                            sv=output_folder: self.__track_output(sv))
        label = tk.Label(
            self.__data_frame, text='Output folder: ', bg=siibra_highlight_bg,
            fg='white', anchor='w', width=15)
        label.grid(column=0, row=1, sticky='w', padx=(15, 10), pady=(0, 20))
        if platform.system() == 'Linux':
            self.__open_folder_path = tk.Entry(
                self.__data_frame, textvariable=output_folder, bd=0, width=39)
        else:
            self.__open_folder_path = tk.Entry(
                self.__data_frame, textvariable=output_folder, bd=0, width=57)
        self.__open_folder_path.insert(0, mriwarp_home)
        self.__open_folder_path.grid(column=1, row=1, pady=(0, 20))
        button = tk.Button(
            self.__data_frame, text='...', command=self.__select_output, bd=0,
            padx=2.5)
        button.grid(column=2, row=1, sticky='e', padx=(10, 15), pady=(0, 20))

    def __create_warping_widgets(self):
        """Create widgets for warping."""
        # widgets for advanced registration
        advanced_frame = tk.Frame(
            self.__warping_frame, bg=siibra_highlight_bg,
            highlightbackground=siibra_bg, highlightthickness=2)
        advanced_frame.pack(fill='x', padx=15, pady=(20, 0))
        # button to expand parameter file selection
        self.__parameter_button = tk.Button(
            advanced_frame, text=' Advanced settings ', bg=siibra_highlight_bg,
            fg='white', image=self.__caret_right, compound='left',
            command=self.__change_advanced_parameter_visibility, anchor='w',
            bd=0, padx=2.5)
        self.__parameter_button.grid(column=0, row=0, sticky='w')
        # widgets for parameter file selection
        self.__parameter_frame = tk.Frame(
            advanced_frame, bg=siibra_highlight_bg)
        self.__parameter_frame.grid(column=0, row=1, padx=10, pady=5)
        json_file = tk.StringVar()
        label = tk.Label(
            self.__parameter_frame, text='Parameters: ', justify='left',
            bg=siibra_highlight_bg, fg='white', anchor='w', width=15)
        label.grid(column=0, row=1, sticky='w')
        if platform.system() == 'Linux':
            self.__open_json_path = tk.Entry(
                self.__parameter_frame, textvariable=json_file, bd=0, width=35)
        else:
            self.__open_json_path = tk.Entry(
                self.__parameter_frame, textvariable=json_file, bd=0, width=53)
        self.__open_json_path.insert(
            0, os.path.join(parameter_home, 'default.json'))
        self.__open_json_path.grid(column=1, row=1, padx=10)
        button = tk.Button(self.__parameter_frame, text='...',
                           command=self.__select_parameters, bd=0, padx=2.5)
        button.grid(column=2, row=1, sticky='e')
        self.__parameter_frame.grid_remove()
        self.__json_showing = False

        # widgets for warping to MNI152
        self.__warp_button = tk.Button(
            self.__warping_frame, text='Warp input to MNI152 space',
            command=self.__prepare_warping, bd=0)
        self.__warp_button.pack(fill='x', padx=15, pady=(15, 20))
        self.__check_mark = None

        # separator
        separator = tk.Frame(self.__warping_frame, bg=siibra_bg, height=10)
        separator.pack(fill='x')

        # frame for progressbar and status text
        self.__status_frame = tk.Frame(
            self.__warping_frame, bg=siibra_highlight_bg)
        self.__status_frame.pack(fill='x')

    def __create_assignment_widgets(self):
        """Create widgets for region assignment."""
        # widgets for MNI152 input
        mni_frame = tk.Frame(self.__assignment_frame, bg=siibra_highlight_bg)
        mni_frame.pack(fill='x', padx=15, pady=(20, 0))
        label = tk.Label(
            mni_frame, text='Input already in\nMNI152 space:', justify='left',
            bg=siibra_highlight_bg, fg='white', anchor='w', width=15)
        label.grid(column=0, row=0, sticky='w')
        style = ttk.Style(self)
        style.configure('TRadiobutton', background=siibra_highlight_bg,
                        foreground='white')
        self.__mni = tk.BooleanVar(value=0)
        radio_button = ttk.Radiobutton(
            mni_frame, text='no', variable=self.__mni, value=0,
            command=self.__set_already_mni)
        radio_button.grid(column=1, row=0, sticky='w', padx=10)
        radio_button = ttk.Radiobutton(
            mni_frame, text='yes', variable=self.__mni, value=1,
            command=self.__set_already_mni)
        radio_button.grid(column=2, row=0, sticky='w')

        # widgets for the parcellation selection
        parcellation_frame = tk.Frame(
            self.__assignment_frame, bg=siibra_highlight_bg)
        parcellation_frame.pack(fill='x', padx=15, pady=15)
        label = tk.Label(
            parcellation_frame, text='Parcellation:', justify='left',
            bg=siibra_highlight_bg, fg='white', anchor='w', width=15)
        label.grid(column=0, row=0, sticky='w')
        parcellation = tk.StringVar()
        parcellation_options = ttk.OptionMenu(
            parcellation_frame, parcellation, self.logic.get_parcellation(),
            *self.logic.get_parcellations(),
            command=self.__change_parcellation)
        parcellation_options.configure(width=40)
        parcellation_options.grid(column=1, row=0, sticky='we', padx=10)

        # widgets for point uncertainty
        uncertainty_frame = tk.Frame(
            self.__assignment_frame, bg=siibra_highlight_bg)
        uncertainty_frame.pack(fill='x', padx=15)
        label = tk.Label(
            uncertainty_frame, text='Point uncertainty:', justify='left',
            bg=siibra_highlight_bg, fg='white', anchor='w', width=15)
        label.grid(column=0, row=0, sticky='w')
        vcmd = (self.register(self.__validate_float), '%P')
        self.__uncertainty = tk.Spinbox(
            uncertainty_frame, from_=0, to=100, increment=0.1, format='%.2f',
            validate='key', validatecommand=vcmd, width=5)
        self.__uncertainty.grid(column=1, row=0, sticky='w', padx=10)
        label = tk.Label(
            uncertainty_frame, text='mm', justify='left',
            bg=siibra_highlight_bg, fg='white', anchor='w')
        label.grid(column=2, row=0, sticky='w')

        # widgets for advanced registration
        advanced_frame = tk.Frame(
            self.__assignment_frame, bg=siibra_highlight_bg,
            highlightbackground=siibra_bg, highlightthickness=2)
        advanced_frame.pack(fill='x', padx=15, pady=(15, 20))
        # button to expand parameter file selection
        self.__transform_button = tk.Button(
            advanced_frame, text=' Advanced settings ', bg=siibra_highlight_bg,
            fg='white', image=self.__caret_right, compound='left',
            command=self.__change_advanced_transform_visibility, bd=0,
            anchor='w', padx=2.5)
        self.__transform_button.grid(column=0, row=0, sticky='w')
        # widgets for parameter file selection
        self.__transform_frame = tk.Frame(
            advanced_frame, bg=siibra_highlight_bg)
        self.__transform_frame.grid(column=0, row=1, padx=10, pady=5)
        transform_file = tk.StringVar()
        transform_file.trace('w', lambda name, index, mode,
                             sv=transform_file: self.__track_transform(sv))
        label = tk.Label(
            self.__transform_frame, text='Transformation file: ',
            justify='left', bg=siibra_highlight_bg, fg='white', anchor='w',
            width=15)
        label.grid(column=0, row=1, sticky='w')
        if platform.system() == 'Linux':
            self.__open_transform_path = tk.Entry(
                self.__transform_frame, textvariable=transform_file,
                bd=0, width=35)
        else:
            self.__open_transform_path = tk.Entry(
                self.__transform_frame, textvariable=transform_file,
                bd=0, width=53)
        self.__open_transform_path.grid(column=1, row=1, padx=10)
        button = tk.Button(self.__transform_frame, text='...',
                           command=self.__select_transform, bd=0, padx=2.5)
        button.grid(column=2, row=1, sticky='e')
        self.__transform_frame.grid_remove()
        self.__transform_showing = False

        # separator
        separator = tk.Frame(self.__assignment_frame, bg=siibra_bg, height=10)
        separator.pack(fill='x')

        frame = tk.Frame(self.__assignment_frame, bg=siibra_highlight_bg)
        frame.pack(fill='x', padx=10, pady=(20, 10))
        label = tk.Label(
            frame, text='Points', font=font_10, justify='left',
            bg=siibra_highlight_bg, fg='white', anchor='w')
        label.pack(side='left')

        self.__export_button = tk.Button(
            frame, image=self.__export_icon, justify='right', relief='flat',
            bg=siibra_highlight_bg, fg='white',
            command=self.__export_assignments, anchor='e',
            state='disabled')
        self.__export_button.pack(side='left', padx=10)

        self.update()
        remaining_height = (
            self.winfo_height() - self.__data_frame.winfo_height()
            - self.__assignment_frame.winfo_height())//4

        # scrollable frame for points
        point_scroll_frame = tk.Frame(
            self.__assignment_frame, bg=siibra_highlight_bg)
        point_scroll_frame.pack(fill='x')
        point_canvas = tk.Canvas(
            point_scroll_frame, bg=siibra_highlight_bg,
            highlightbackground=siibra_highlight_bg,
            selectbackground=siibra_highlight_bg, height=remaining_height)
        point_scrollbar = tk.Scrollbar(
            point_scroll_frame, orient='vertical', command=point_canvas.yview)
        self.__point_frame = tk.Frame(
            point_canvas, bg=siibra_highlight_bg, padx=10, pady=10)

        self.__point_frame.bind(
            '<Configure>', lambda e: point_canvas.configure(
                scrollregion=point_canvas.bbox('all')))
        point_canvas.create_window(
            (0, 0), window=self.__point_frame, anchor='nw')
        point_canvas.configure(yscrollcommand=point_scrollbar.set)
        point_canvas.pack(side='left', fill='both', expand=True)
        point_scrollbar.pack(side='right', fill='y')

        # table header
        columns = ['Label', 'R', 'A', 'S', 'Assign regions']
        for i, column_text in enumerate(columns):
            entry = tk.Entry(
                self.__point_frame,
                textvariable=tk.StringVar(value=column_text),
                state='readonly', width=13)
            entry.grid(column=i, row=1)
        self.__point_widgets = []
        # add point (manually or by clicking)
        label = tk.StringVar()
        # Not using DoubleVar here because it does rounding.
        self.__R, self.__A, self.__S = tk.StringVar(), tk.StringVar(), tk.StringVar()
        vcmd = (self.register(self.__validate_float), '%P')
        widgets = [
            tk.Entry(self.__point_frame, textvariable=label, width=10),
            tk.Entry(
                self.__point_frame, textvariable=self.__R, validate='key',
                validatecommand=vcmd, width=10),
            tk.Entry(
                self.__point_frame, textvariable=self.__A, validate='key',
                validatecommand=vcmd, width=10),
            tk.Entry(
                self.__point_frame, textvariable=self.__S, validate='key',
                validatecommand=vcmd, width=10),
            tk.Button(
                self.__point_frame, image=self.__brain_icon, relief='groove',
                command=lambda: self.__redo_assignment(
                    (float(self.__R.get()),
                     float(self.__A.get()),
                     float(self.__S.get())))),
            tk.Button(
                self.__point_frame, image=self.__save_icon,
                command=lambda: self.__save_point(
                    (float(self.__R.get()),
                     float(self.__A.get()),
                     float(self.__S.get())),
                    label))]
        for i, widget in enumerate(widgets):
            widget.grid(column=i, row=2, sticky='nswe',
                        padx=5*(i == len(widgets)-1))

        # separator
        separator = tk.Frame(self.__assignment_frame, bg=siibra_bg, height=10)
        separator.pack(fill='x')

        # frame for results of region assignment
        self.__region_frame = tk.Frame(
            self.__assignment_frame, bg=siibra_highlight_bg)
        self.__region_frame.pack(fill='both', expand=True)

    def __create_viewer(self):
        """Create the viewer for the input NIfTI."""
        image = self.logic.get_numpy_source()
        # Initially the middle coronal slice is displayed.
        coronal_slice = round(image.shape[1] / 2) + 1

        # View needs to be initialized before slider as slider.set updates the
        # viewer.
        self.__coronal_viewer = Viewer(
            self.__view_panel, image=image[:, coronal_slice, :],
            side='bottom', padx=10, pady=10)

        # help icon
        button = tk.Button(
            self.__view_panel, image=self.__help_icon, bg=viewer_bg,
            command=lambda: webbrowser.open(
                'https://voluba-mriwarp.readthedocs.io'),
            highlightthickness=0, bd=0)
        button.pack(anchor='e', side='right', padx=20, pady=(20, 0))

        # widget for changing the displayed slice
        self.__coronal_slider = tk.Scale(
            self.__view_panel, from_=1, to=image.shape[1],
            bg=viewer_bg, showvalue=True, fg='white', sliderrelief='flat',
            orient='horizontal', command=lambda value: self.__update_viewer(
                value),
            highlightthickness=0, length=sidepanel_width - 100)
        self.__coronal_slider.set(coronal_slice)
        self.__coronal_slider.pack(padx=10, pady=10)

        # Remove previous region assignments.
        for widget in self.__region_frame.winfo_children():
            widget.destroy()

        # Remove previously saved points.
        self.__R.set('')
        self.__A.set('')
        self.__S.set('')
        self.logic.delete_points()
        for row in self.__point_widgets:
            for widget in row:
                widget.destroy()
        self.__point_widgets = []
        self.__export_button.configure(state='disabled')

        self.update()
        # Move the input NIfTI to the center of the viewer.
        self.__coronal_viewer.move_image_to_center()
        self.__annotation = (-1, -1, -1)

    def __update_viewer(self, value):
        """Update the shown slice in the viewer.

        :param int value: slice of the input NIfTI to display
        """
        self.__coronal_viewer.update_image(self.logic.get_numpy_source()[
            :, int(value) - 1, :], int(value) - 1)

    def __validate_float(self, value):
        """Validate if the entered value is a numerical value.

        :param value: value to check
        """
        try:
            float(value)
            return True
        except:
            # Empty strings and negative sign need to be accepted to enable
            # overwrite.
            if value in ['', '-']:
                return True
            return False

    def __show_warping_frame(self):
        """Bring the warping frame to the foreground."""
        self.__assignment_frame.grid_remove()
        self.__warping_frame.grid()

    def __show_assignment_frame(self):
        """Bring the assignment frame to the foreground."""
        self.__warping_frame.grid_remove()
        self.__assignment_frame.grid()

    def __change_advanced_parameter_visibility(self):
        """Show/Hide selection for parameter JSON."""
        if self.__json_showing:
            self.__parameter_button.config(image=self.__caret_right)
            self.__parameter_frame.grid_remove()
            self.__json_showing = False
        else:
            self.__parameter_button.config(image=self.__caret_down)
            self.__parameter_frame.grid()
            self.__json_showing = True

    def __change_advanced_transform_visibility(self):
        """Show/Hide selection for transformation file."""
        if self.__transform_showing:
            self.__transform_button.config(image=self.__caret_right)
            self.__transform_frame.grid_remove()
            self.__transform_showing = False
        else:
            self.__transform_button.config(image=self.__caret_down)
            self.__transform_frame.grid()
            self.__transform_showing = True

    def __track_input(self, variable):
        """Observe the Entry widget for the path to the input NIfTI.

        :param tkinter.StringVar variable: variable that holds the content of 
        an Entry widget (path to input NIfTI)
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
            self.__set_already_mni()

    def __track_output(self, variable):
        """Observe the Entry widget for the path to the output folder.

        :param tkinter.StringVar variable: variable that holds the content of 
        an Entry widget (path to output folder)
        """
        path = variable.get()
        if self.logic.check_out_path(path):
            self.logic.set_out_path(path)

    def __track_transform(self, variable):
        """Observe the Entry widget for the path to the transformation file.

        :param tkinter.StringVar variable: variable that holds the content of 
        an Entry widget (path to transformation file)
        """
        path = variable.get()
        # If the custom transform is removed again, use the output folder.
        if path == '':
            self.logic.set_out_path(self.logic.get_out_path())
            path = self.logic.get_transform_path()

    def __select_input(self):
        """Select an input NIfTI."""
        # Open the latest given valid folder in the filedialog.
        folder = '/'
        if self.__open_file_path.get():
            folder = os.path.dirname(self.__open_file_path.get())

        filename = filedialog.askopenfilename(
            filetypes=[('NIfTI', '*.nii *.nii.gz')],
            initialdir=folder, title='Select input NIfTI')

        # Canceling the filedialog returns an empty string.
        if filename:
            self.__open_file_path.delete(0, 'end')
            filename = os.path.normpath(filename)
        self.__open_file_path.insert(0, filename)

    def __select_output(self):
        """Select an output folder."""
        # Open the latest given valid folder in the filedialog.
        foldername = filedialog.askdirectory(
            initialdir=self.__open_folder_path.get(),
            title='Select output folder')

        # Canceling the filedialog returns an empty string.
        if foldername:
            self.__open_folder_path.delete(0, 'end')
            foldername = os.path.normpath(foldername)
        self.__open_folder_path.insert(0, foldername)

    def __select_parameters(self):
        """Select a parameter JSON."""
        # Open the latest given valid folder in the filedialog.
        folder = os.path.join(mriwarp_home, 'parameters')
        if self.__open_json_path.get():
            folder = os.path.dirname(self.__open_json_path.get())

        filename = filedialog.askopenfilename(
            filetypes=[('JSON', '*.json')],
            initialdir=folder, title='Select parameter JSON')

        # Canceling the filedialog returns an empty string.
        if filename:
            self.__open_json_path.delete(0, 'end')
            filename = os.path.normpath(filename)
        self.__open_json_path.insert(0, filename)

    def __select_transform(self):
        """Select a transformation file."""
        # Open the latest given valid folder in the filedialog.
        folder = mriwarp_home
        if self.__open_transform_path.get():
            folder = os.path.dirname(self.__open_transform_path.get())

        filename = filedialog.askopenfilename(
            filetypes=[('*.h5, *.mat', '*.h5 *.mat')],
            initialdir=folder, title='Select transformation file')

        # Canceling the filedialog returns an empty string.
        if filename:
            self.__open_transform_path.delete(0, 'end')
            filename = os.path.normpath(filename)
        self.__open_transform_path.insert(0, filename)

    def __set_already_mni(self):
        """Retry the region assignment for the currently selected point if the 
        image type changes.
        """
        if self.__mni.get() == 1:
            self.__transform_showing = True
            self.__change_advanced_transform_visibility()
            self.__transform_button.configure(state='disabled')
        else:
            self.__transform_button.configure(state='normal')

    def __change_parcellation(self, parcellation):
        """Change the current parcellation that is used for region assignment.

        :param str parcellation: parcellation for region assignment
        """
        self.logic.set_parcellation(parcellation)

    def __prepare_warping(self):
        """Prepare the logic and widgets and start warping the input NIfTI to 
        MNI152.
        """
        try:
            self.logic.set_in_path(self.__open_file_path.get())
            self.logic.set_out_path(self.__open_folder_path.get())
            self.logic.set_parameters_path(self.__open_json_path.get())
        except Exception as e:
            logging.getLogger(mriwarp_name).error(
                f'Error during path definition: {str(e)}')
            messagebox.showerror('Error', str(e))
            return

        self.logic.save_paths()

        # During warping the button is disabled to prevent multiple starts.
        self.__warp_button.configure(state='disabled')

        # Remove status of previous warping.
        for widget in self.__status_frame.winfo_children():
            widget.destroy()

        # widgets for current warping status
        label = tk.Label(
            self.__status_frame,
            text=f'File: {os.path.basename(self.logic.get_in_path())}',
            bg=siibra_highlight_bg, fg='white', anchor='w')
        label.pack(anchor='w', padx=10, pady=(20, 10))
        self.__progress_bar = ttk.Progressbar(
            self.__status_frame, orient='horizontal', mode='indeterminate')
        self.__progress_bar.pack(fill='x', padx=10)
        self.__progress_bar.start()

        # Start warping.
        threading.Thread(target=self.__run_warping, daemon=True).start()

    def __run_warping(self):
        """Warp the input NIfTI to MNI152 space with initial skull stripping."""
        logger = logging.getLogger(mriwarp_name)
        logger.info(f'Warping {os.path.basename(self.logic.get_in_path())}')

        # Skull stripping
        logger.info('Performing skull stripping')
        label = tk.Label(
            self.__status_frame, text='Skull stripping ... ',
            bg=siibra_highlight_bg, fg='white', anchor='w')
        label.pack(anchor='w', padx=10, pady=5)
        try:
            self.logic.strip_skull()
        except Exception as e:
            label.configure(image=self.__error_icon, compound='right')
            self.__show_error('skull stripping', e)
            return
        label.configure(image=self.__success_icon, compound='right')

        # Registration
        logger.info('Performing registration')
        label = tk.Label(
            self.__status_frame, text='Registration to MNI152 ... ',
            bg=siibra_highlight_bg, fg='white', anchor='w')
        label.pack(anchor='w', padx=10, pady=5)
        try:
            self.logic.warp()
        except Exception as e:
            label.configure(image=self.__error_icon, compound='right')
            self.__show_error('registration', e)
            return
        label.configure(image=self.__success_icon, compound='right')
        self.__progress_bar.stop()

        # Finished
        logger.info('Finished')
        label = tk.Label(self.__status_frame, text='Finished!',
                         bg=siibra_highlight_bg, fg='white', anchor='w',)
        label.pack(anchor='w', padx=10, pady=(5, 20))
        self.__warp_button.configure(state='normal')

    def __save_point(self, point, label):
        """Save a point and add its corresponding widgets.

        :param tuple point: point to save
        :param tkinter.StringVar label: label for the point 
        """
        new_label = tk.StringVar()
        self.logic.save_point(point, new_label)
        idx = self.logic.get_num_points()
        new_label.set(label.get() if label.get().rstrip() else idx)

        widgets = [
            tk.Entry(
                self.__point_frame, textvariable=new_label, width=10),
            tk.Entry(
                self.__point_frame, textvariable=tk.StringVar(
                    value=point[0]),
                state='readonly', width=10),
            tk.Entry(
                self.__point_frame, textvariable=tk.StringVar(
                    value=point[1]),
                state='readonly', width=10),
            tk.Entry(
                self.__point_frame, textvariable=tk.StringVar(
                    value=point[2]),
                state='readonly', width=10),
            tk.Button(
                self.__point_frame, image=self.__brain_icon, relief='groove',
                command=lambda: self.__redo_assignment(point)),
            tk.Button(
                self.__point_frame, image=self.__trash_icon,
                command=lambda: self.__remove_point(point))]
        for i, widget in enumerate(widgets):
            widget.grid(column=i, row=idx+3, sticky='nswe',
                        padx=5*(i == len(widgets)-1))
        self.__point_widgets.append(widgets)

        self.__export_button.configure(state='normal')

    def __remove_point(self, point):
        """Remove a saved point and its corresponding widgets.

        :param tuple point: point to delete
        """
        idx = self.logic.delete_point(point)
        widgets = self.__point_widgets.pop(idx)
        for widget in widgets:
            widget.destroy()

        if self.logic.get_num_points() == 0:
            self.__export_button.configure(state='disabled')

    def assign_regions2point(self, point):
        """Set the annotation and start the region assignment."""
        # If the user specifies a new transformation file, it is used instead
        # of the default file.
        transform_path = self.__open_transform_path.get()
        if transform_path:
            self.logic.set_transform_path(transform_path)

        type = 'template' if self.logic.get_in_path(
        ) == mni_template else 'aligned' if self.__mni.get() == 1 else 'unaligned'
        self.logic.set_img_type(type)
        self.__annotation = point
        # The origin in the viewer is upper left but the image origin is lower
        # left.
        self.__annotation = (
            self.__annotation[0],
            self.__annotation[1],
            self.logic.get_numpy_source().shape[0] - self.__annotation[2])

        # set manual points to annotation
        source_point_ras = self.logic.warp_vox2phys(self.__annotation)
        self.__R.set(source_point_ras[0])
        self.__A.set(source_point_ras[1])
        self.__S.set(source_point_ras[2])

        # Remove previous region assignments.
        for widget in self.__region_frame.winfo_children():
            widget.destroy()

        if self.logic.get_transform_path() or type != 'unaligned':
            threading.Thread(target=self.__create_assignment,
                             daemon=True).start()
        else:  # No transformation matrix can be found.
            self.__create_point_info(source_point_ras)

            path = self.__open_transform_path.get().rstrip()
            if path == '':
                path = self.logic.get_out_path()
            # widget for info on missing transformation matrix
            label = tk.Label(
                self.__region_frame,
                text=f'Could not find a transformation in {path}.\n'
                f'To assign regions to a selected point, please warp the input '
                f'NIfTI to MNI152 space or provide the location of the '
                f'transformation matrix in Advanced settings.\n'
                f'If you need help, visit voluba-mriwarp.readthedocs.io.',
                justify='left', image=self.__info_icon, compound='left',
                bg=siibra_bg, fg=siibra_fg, anchor='w',
                wraplength=sidepanel_width - 80, padx=5)
            label.pack(fill='x', padx=5, pady=10)

    def __create_point_info(self, point):
        """Create widgets to display the selected annotation.

        :param tuple point: annotation in physical space
        """
        # Round the point to two decimals.
        for i in range(len(point)):
            point[i] = round(point[i], 2)

        # widget for the annotated point in physical space
        label = tk.Label(
            self.__region_frame, text=f'Point {tuple(point)} [mm]',
            font=font_12_b, justify='left', bg='gold', fg=siibra_bg,
            anchor='w', padx=10, pady=10)
        label.pack(fill='x', expand=True)

        # widget for the current filename
        label = tk.Label(
            self.__region_frame,
            text=f'in: {os.path.basename(self.logic.get_in_path())}',
            justify='left', bg=siibra_highlight_bg, fg=siibra_fg, anchor='w',
            padx=5, pady=5)
        label.pack(fill='x', padx=5, pady=(5, 0))

    def __create_assignment(self):
        """Create widgets displaying the regions assigned to the selected 
        annotation.
        """
        # Indicate that the assignment is running.
        self.__calculating = True
        threading.Thread(target=self.__show_wip, daemon=True).start()

        # Assign regions.
        uncertainty = self.__uncertainty.get()
        try:
            source, target, results, urls = self.logic.assign_regions2point(
                self.__annotation, float(uncertainty))
        except SubprocessFailedError as e:
            logging.getLogger(mriwarp_name).error(
                f'Error during region calculation: {str(e)}')
            messagebox.showerror(
                'Error',
                f'The following error occurred during region calculation:'
                f'\n\n{str(e)}\n\n'
                f'If you need help, please contact support@ebrains.eu.')
            # No region can be found when an error occurs.
            label = tk.Label(
                self.__region_frame, text='No region found', font=font_10_b,
                bg='red', fg='black', borderwidth=10, anchor='w')
            label.pack(fill='x')

            self.__calculating = False
            return
        except PointNotFoundError:
            logging.getLogger(mriwarp_name).error(
                f'Point {self.__annotation} [vox] is outside MNI152 space.')
            # The point is outside the brain.
            label = tk.Label(
                self.__region_frame,
                text=f'The selected point is outside MNI152 space.',
                font=font_10_b, bg='red', fg='black', borderwidth=10,
                anchor='w')
            label.pack(fill='x')
            self.__calculating = False
            return

        self.__calculating = False

        self.__create_point_info(source)

        # widget for the corresponding point in MNI152 space
        label = tk.Label(
            self.__region_frame,
            text=f'identified with: {tuple(target)} [mm] '
            f'in MNI152 2009c nonlinear asymmetric',
            justify='left', bg=siibra_highlight_bg, fg=siibra_fg, anchor='w',
            padx=5)
        label.pack(fill='x', padx=5)

        # widget for the parcellation
        label = tk.Label(self.__region_frame,
                         text=f'assigned to: {self.logic.get_parcellation()}',
                         justify='left', bg=siibra_highlight_bg, fg=siibra_fg,
                         anchor='w', padx=5, pady=5)
        label.pack(fill='x', padx=5)

        # widget for the point uncertainty
        label = tk.Label(self.__region_frame,
                         text=f'with point uncertainty: {uncertainty} mm',
                         justify='left', bg=siibra_highlight_bg, fg=siibra_fg,
                         anchor='w', padx=5, pady=5)
        label.pack(fill='x', padx=5)

        # widget for the transformation file
        if self.logic.get_img_type() != 'unaligned':
            transform = 'NIfTI affine'
        elif self.logic.get_transform_path() == self.__open_transform_path.get():
            transform = 'advanced transformation'
        else:
            transform = 'default transformation'
        label = tk.Label(
            self.__region_frame, text=f'using: {transform}', justify='left',
            bg=siibra_highlight_bg, fg=siibra_fg, anchor='w', padx=5)
        label.pack(fill='x', padx=5)

        # separator with optional text
        separator = tk.Frame(self.__region_frame, bg=siibra_bg, height=10)
        separator.pack(fill='x')

        self.update()
        remaining_height = self.winfo_height(
        )-self.__data_frame.winfo_height() - self.__assignment_frame.winfo_height()

        # widgets for assigned regions
        if not results.empty:
            region_frame = tk.Frame(
                self.__region_frame, bg=siibra_highlight_bg,
                height=remaining_height)
            region_frame.pack(fill='both', expand=True)
            region_frame.pack_propagate(False)

            style = ttk.Style()
            style.configure('Treeview.Heading', font=font_10_b)
            columns = results.columns.values.tolist()
            tree = customTreeView(
                region_frame, columns=columns, show='headings')
            tree.bind('<Double-1>', lambda event,
                      _urls=urls: tree.open_url(event, _urls))

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
                tree.insert('', 'end', values=values)
        else:
            # no region found
            label = tk.Label(
                self.__region_frame, text=f'No region found', font=font_10_b,
                bg=siibra_highlight_bg, fg=siibra_fg, anchor='w', padx=10,
                pady=10)
            label.pack(side='left')

    def __redo_assignment(self, point):
        """Set the annotation and redo the region assignment.

        This method is called when the user clicks the brain icon.

        :param tuple point: point to assign regions to
        """
        x, slice, y = self.logic.warp_phys2vox(point)
        # The origin in the viewer is upper left but the image origin is lower
        # left.
        y = self.logic.get_numpy_source().shape[0] - y
        self.__coronal_slider.set(round(slice)+1)  # The slider starts at 1.
        self.__coronal_viewer.draw_annotation(x, round(slice), y)
        self.assign_regions2point((x, slice, y))

    def __show_wip(self):
        """Show three animated dots to indicate running region assignment."""
        dots = tk.StringVar()
        dots.set('.')
        loading = tk.Label(
            self.__region_frame, textvariable=dots, font=font_18_b,
            bg=siibra_highlight_bg, fg='white')
        loading.pack(fill='x', padx=15, pady=20)

        while self.__calculating:
            time.sleep(1)
            if len(dots.get()) == 3:
                dots.set('')
            dots.set(dots.get() + '.')

        loading.destroy()

    def __export_assignments(self):
        """Export region assignments and linked features for all saved points."""
        type = 'template' if self.logic.get_in_path(
        ) == mni_template else 'aligned' if self.__mni.get() == 1 else 'unaligned'
        self.logic.set_img_type(type)
        self.logic.set_uncertainty(float(self.__uncertainty.get()))
        ExportDialog(self, title='Export', logic=self.logic)

    def __show_error(self, stage, error):
        """Stop the warping and show the error that occurred.

        :param str stage: stage of the warping (skull stripping or registration)
        :param Error error: error that occurred
        """
        self.__progress_bar.stop()
        self.__warp_button.configure(state='normal')
        logging.getLogger(mriwarp_name).error(
            f'Error during {stage}: {str(error)}')
        messagebox.showerror(
            'Error',
            f'The following error occurred during {stage}:\n\n{str(error)}\n\n'
            f'If you need help, please contact support@ebrains.eu.')

    def close(self):
        """Destroy the main window after asking for quit."""
        if messagebox.askokcancel(
                'Quit', 'Do you really want to quit?', parent=self):
            self.destroy()
