import os
import threading
import tkinter as tk
import webbrowser
from tkinter import filedialog, simpledialog, ttk

from voluba_mriwarp.config import mriwarp_home


class ExportDialog(simpledialog.Dialog):
    """Custom dialog for PDF export of region assignments"""

    def __init__(self, parent, title, logic):
        """Initialize the dialog.

        :param parent: tkinter parent window (application window)
        :param str title: dialog title
        :param voluba_mriwarp.Logic logic: logic for region assignment
        """
        self.__logic = logic
        self.progress = tk.IntVar()

        super().__init__(parent, title=title)

    def body(self, master):
        """Create the dialog body.

        This method is automatically called by the __init__ method.

        :param master: tkinter parent widget
        """
        # widget for explanation
        label = tk.Label(
            master,
            text=f'Export assignments and features for {self.__logic.get_parcellation()}.',
            bg='white', anchor='w', padx=10, pady=10)
        label.pack(anchor='w', fill='x')

        frame = tk.Frame(master, padx=10, pady=5)
        frame.pack()

        # widgets for export location
        location_frame = tk.Frame(frame)
        location_frame.grid(column=0, row=0, pady=5, sticky='w')
        label = tk.Label(location_frame, text='PDF location: ', anchor='w')
        label.pack(side='left')
        self.__path_var = tk.StringVar()
        path = tk.Entry(location_frame, textvariable=self.__path_var, width=39)
        pdf_path = os.path.join(self.__logic.get_out_path(), self.__logic.get_name() + '.pdf')
        path.insert(0, pdf_path)
        path.pack(side='left', padx=10)
        button = tk.Button(location_frame, text='...',
                           command=self.__select_export_location, padx=2.5)
        button.pack(side='left')

        # widgets for assignment filtering
        filter_frame = tk.Frame(frame)
        filter_frame.grid(column=0, row=1, sticky='w')
        label = tk.Label(
            filter_frame, text='Export regions assigned with:',
            anchor='w')
        label.pack(anchor='w')
        keys = ['correlation', 'intersection over union', 'map value',
                'map weighted mean', 'map containedness',
                'input weighted mean', 'input containedness']
        self.__column = tk.StringVar()
        dropdown = ttk.OptionMenu(filter_frame, self.__column, keys[0], *keys)
        dropdown.pack(side='left')
        self.__sign = tk.StringVar()
        signs = ['>', '>=', '=', '<=', '<']
        dropdown = ttk.OptionMenu(filter_frame, self.__sign, signs[0], *signs)
        dropdown.pack(side='left')
        self.__value = tk.DoubleVar()
        self.__value.set(0.3)
        vcmd = (self.register(self.__validate_float), '%P')
        entry = tk.Entry(filter_frame, textvariable=self.__value,
                         validate='key', validatecommand=vcmd)
        entry.pack(side='left')

        # widgets for feature selection
        feature_frame = tk.Frame(frame)
        feature_frame.grid(column=0, row=2, sticky='w')
        label = tk.Label(feature_frame, text='Include features: ', anchor='w')
        label.pack(anchor='w')
        self.__features = {}
        for feature in self.__logic.get_features():
            var = tk.IntVar()
            self.__features[feature] = var
            check_button = tk.Checkbutton(
                feature_frame, text=feature, variable=var,
                command=lambda
                feat=feature: self.__change_extended_feature_visibility(feat))
            check_button.pack(anchor='w')

        # widgets for receptor selection
        self.__receptor_frame = tk.Frame(frame)
        self.__receptor_frame.grid(column=0, row=3, sticky='w')
        label = tk.Label(
            self.__receptor_frame, text='Receptors: ', justify='left',
            anchor='w')
        label.grid(column=0, row=0, sticky='w')
        self.__receptors = {}
        j = 0
        for i, receptor in enumerate(self.__logic.get_receptors()):
            j += (i % 4 == 0)
            var = tk.IntVar()
            self.__receptors[receptor] = var
            check_button = tk.Checkbutton(
                self.__receptor_frame, text=receptor, variable=var,
                justify='left', command=self.__tick_receptor, anchor='w')
            check_button.grid(column=i % 4, row=j, sticky='w')
        self.__tick_receptor()
        self.__change_extended_feature_visibility('ReceptorDensityProfile')

        # widgets for cohort selection
        self.__cohort_frame = tk.Frame(frame)
        self.__cohort_frame.grid(column=0, row=4, sticky='w')
        label = tk.Label(self.__cohort_frame, text='Cohorts: ',
                         justify='left', anchor='w')
        label.grid(column=0, row=0, sticky='w')
        self.__cohorts = {}
        for i, cohort in enumerate(['1000BRAINS', 'HCP']):
            var = tk.IntVar()
            self.__cohorts[cohort] = var
            check_button = tk.Checkbutton(
                self.__cohort_frame, text=cohort, variable=var,
                command=self.__tick_cohort)
            check_button.grid(column=i, row=1)
        self.__tick_cohort()
        self.__change_extended_feature_visibility('StreamlineCounts')

    def buttonbox(self):
        """Add the button box.

        This method is automatically called by the __init__ method.        
        """
        box = tk.Frame(self)
        box.pack()

        button = tk.Button(
            box, text='Export', command=self.export, default='active',
            width=10)
        button.pack(side='left', padx=5, pady=5)
        button = tk.Button(box, text='Cancel', command=self.cancel, width=10)
        button.pack(side='left', padx=5, pady=5)

        self.bind('<Return>', self.ok)
        self.bind('<Escape>', self.cancel)

    def __tick_receptor(self):
        """Make sure at least one receptor is ticked in the selection."""
        if sum([var.get() for var in self.__receptors.values()]) == 0:
            self.__receptors[list(self.__receptors.keys())[0]].set(1)

    def __tick_cohort(self):
        """Make sure at least one cohort is ticked in the selection."""
        if sum([var.get() for var in self.__cohorts.values()]) == 0:
            self.__cohorts['1000BRAINS'].set(1)

    def __change_extended_feature_visibility(self, feature):
        """Show/Hide extended settings depending on the current feature 
        selection.

        :param str feature: name of the selected feature
        """
        connectivity = ['StreamlineCounts',
                        'StreamlineLengths', 'FunctionalConnectivity']
        # Show receptor selection when ReceptorDensity is selected.
        if feature == 'ReceptorDensityProfile':
            if self.__features[feature].get() == 0:
                self.__receptor_frame.grid_remove()
            else:
                self.__receptor_frame.grid()
            self.update()
        # Show cohort selection when a connectivity feature is selected.
        elif feature in connectivity:
            if sum([self.__features[conn].get() for conn in connectivity]) == 0:
                self.__cohort_frame.grid_remove()
            else:
                self.__cohort_frame.grid()
            self.update()

    def __validate_float(self, value):
        """Validate if the entered filter is a numerical value.

        :param float value: value to check
        :return: True if the given value is numerical or else False.
        :rtype: bool
        """
        try:
            float(value)
            return True
        except:
            return False

    def __select_export_location(self):
        """Select an export location."""
        # Open the latest given valid folder in the filedialog.
        filename = filedialog.asksaveasfilename(
            title='Select export location',
            initialdir=os.path.dirname(self.__path_var.get()),
            initialfile=os.path.basename(self.__path_var.get()),
            defaultextension='.pdf', filetypes=[('PDF', '*.pdf')],
            confirmoverwrite=True)

        # Canceling the filedialog returns an empty string.
        if filename:
            filename = os.path.normpath(filename)
            self.__path_var.set(filename)

    def export(self, event=None):
        """Start the export to PDF of all assignments and linked features that
        are selected.
        """
        for widget in self.winfo_children():
            widget.destroy()

        # Show progress.
        label = tk.Label(self, text='Exporting to PDF ...')
        label.pack(anchor='w', padx=5, pady=5)
        progress_bar = ttk.Progressbar(
            self, orient='horizontal', variable=self.progress, length=200)
        progress_bar.pack(anchor='w', padx=5, pady=5)
        button = tk.Button(self, text='Cancel', command=self.cancel, width=10)
        button.pack(padx=5, pady=5)
        self.update()

        # Start export in a thread.
        features = [feature for feature in self.__features
                    if self.__features[feature].get() == 1]
        receptors = [receptor for receptor in self.__receptors
                     if self.__receptors[receptor].get() == 1]
        cohorts = [cohort for cohort in self.__cohorts
                   if self.__cohorts[cohort].get() == 1]
        filter = [
            self.__column.get(),
            self.__sign.get(),
            float(self.__value.get())]

        thread = threading.Thread(
            target=self.__logic.export_assignments,
            args=(self.__path_var.get(), filter, features, 
                  receptors, cohorts, self.progress),
            daemon=True)
        thread.start()

        while thread.is_alive():
            self.update()

        self.after(3000, self.cancel)

    def cancel(self, event=None):
        """Stop the export and close the dialog."""
        self.progress.set(-1)

        # Put the focus back to the parent window.
        if self.parent is not None:
            self.parent.focus_set()
        self.destroy()


class customTreeView(ttk.Treeview):
    """Custom TreeView that allows sorting wrt columns and opening of 
    row-specific urls via double click
    """

    def heading(self, column, sort_by=None, **kwargs):
        """Query or modify the heading options for the specified column.

        :param column: column to apply sorting to
        :param str sort_by: value type to sort
        :return: If kwargs is not given, returns a dict of the heading option
        values. If option is specified then the value for that option is 
        returned. Otherwise, sets the options to the corresponding values.
        :rtype: dict, value or None
        """
        # Sorting function is passed via 'command' argument.
        if sort_by and not hasattr(kwargs, 'command'):
            sort_function = getattr(self, f'_sort_by_{sort_by}', None)
            if sort_function:
                kwargs['command'] = lambda: sort_function(column, False)
        return super().heading(column, **kwargs)

    def _sort(self, column, reverse, data_type, callback):
        """Sort the rows according to the specified column.

        :param str column: column to sort by
        :param bool reverse: if sorting should be reverted
        :param type data_type: data type to sort
        :param func callback: function to use for sorting
        """
        # Get values for each row in selected column.
        values = [(self.set(row, column), row) for row in self.get_children('')]
        # Sort values wrt data type and reverse flag.
        values.sort(key=lambda values_entry: data_type(
            values_entry[0]), reverse=reverse)
        # Move the rows according to sorting.
        for index, (_, row) in enumerate(values):
            self.move(row, '', index)

        # Reverse the sorting when the column is clicked again.
        self.heading(column, command=lambda: callback(column, not reverse))

    def _sort_by_float(self, column, reverse):
        """Sort the float entries of the specified column.

        :param str column: column to sort by
        :param bool reverse: if sorting should be reverted
        """
        self._sort(column, reverse, float, self._sort_by_float)

    def _sort_by_str(self, column, reverse):
        """Sort the string entries of the specified column.

        :param str column: column to sort by
        :param bool reverse: if sorting should be reverted
        """
        self._sort(column, reverse, str, self._sort_by_str)

    def open_url(self, event, urls):
        """Open the corresponding region of the selected row in 
        siibra-explorer.

        :param dict urls: dictionary of regions and their corresponding 
        siibra-explorer url
        """
        selected_row = self.selection()
        row_values = self.item(selected_row, 'values')
        if row_values:
            # The first row value is the region.
            webbrowser.open(urls[row_values[0]])
