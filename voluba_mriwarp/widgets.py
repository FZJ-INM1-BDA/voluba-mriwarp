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
        tk.Label(master, text=f'Export assignments and features for {self.__logic.get_parcellation()}.', bg='white', anchor='w', padx=10, pady=10).pack(
            anchor='w', fill='x')

        frame = tk.Frame(master, padx=10, pady=5)
        frame.pack()

        # widgets for export location
        location_frame = tk.Frame(frame)
        location_frame.grid(column=0, row=0, pady=5, sticky='w')
        tk.Label(location_frame, text='Location: ',
                 anchor='w').pack(side='left')
        self.__path_var = tk.StringVar()
        path = tk.Entry(location_frame, textvariable=self.__path_var, width=39)
        pdf_path = os.path.join(mriwarp_home, self.__logic.get_name() + '.pdf')
        path.insert(0, pdf_path)
        path.pack(side='left', padx=10)
        tk.Button(location_frame, text='...',
                  command=self.__select_export_location, padx=2.5).pack(side='left')

        # widgets for assignment filtering
        filter_frame = tk.Frame(frame)
        filter_frame.grid(column=0, row=1, sticky='w')
        tk.Label(filter_frame, text='Export features for regions assigned with:',
                 anchor='w').pack(anchor='w')
        keys = ['correlation', 'intersection over union', 'map value', 'map weighted mean',
                'map containedness', 'input weighted mean', 'input containedness']
        self.__col = tk.StringVar()
        ttk.OptionMenu(filter_frame, self.__col,
                       keys[0], *keys).pack(side='left')
        self.__sign = tk.StringVar()
        signs = [">", ">=", "=", "<=", "<"]
        ttk.OptionMenu(filter_frame, self.__sign,
                       signs[0], *signs).pack(side='left')
        self.__num = tk.DoubleVar()
        self.__num.set(0.3)
        vcmd = (self.register(self.__validate_float), '%P')
        tk.Entry(filter_frame, textvariable=self.__num,
                 validate='key', validatecommand=vcmd).pack(side='left')

        # widgets for feature selection
        feature_frame = tk.Frame(frame)
        feature_frame.grid(column=0, row=2, sticky='w')
        tk.Label(feature_frame, text='Features: ', anchor='w').pack(anchor='w')
        self.__features = {}
        for feature in self.__logic.get_features():
            var = tk.IntVar()
            self.__features[feature] = var
            tk.Checkbutton(feature_frame, text=feature, variable=var,
                           command=lambda feat=feature: self.__change_extended_feature_visibility(feat)).pack(anchor='w')

        # widgets for receptor selection
        self.__receptor_frame = tk.Frame(frame)
        self.__receptor_frame.grid(column=0, row=3, sticky='w')
        tk.Label(self.__receptor_frame, text='Receptors: ',
                 justify='left', anchor='w').grid(row=0, column=0, sticky='w')
        self.__receptors = {}
        j = 0
        for i, receptor in enumerate(self.__logic.get_receptors()):
            j += (i % 4 == 0)
            var = tk.IntVar()
            self.__receptors[receptor] = var
            tk.Checkbutton(self.__receptor_frame, text=receptor, variable=var, justify='left',
                           command=self.__tick_receptor, anchor='w').grid(row=j, column=i % 4, sticky='w')
        self.__tick_receptor()
        self.__change_extended_feature_visibility('ReceptorDensityProfile')

        # widgets for cohort selection
        self.__cohort_frame = tk.Frame(frame)
        self.__cohort_frame.grid(column=0, row=4, sticky='w')
        tk.Label(self.__cohort_frame, text='Cohorts: ', justify='left',
                 anchor='w').grid(column=0, row=0, sticky='w')
        self.__cohorts = {}
        for i, cohort in enumerate(['1000BRAINS', 'HCP']):
            var = tk.IntVar()
            self.__cohorts[cohort] = var
            tk.Checkbutton(self.__cohort_frame, text=cohort, variable=var,
                           command=self.__tick_cohort).grid(column=i, row=1)
        self.__tick_cohort()
        self.__change_extended_feature_visibility('StreamlineCounts')

    def buttonbox(self):
        """Add the button box.

        This method is automatically called by the __init__ method.        
        """
        box = tk.Frame(self)

        w = tk.Button(box, text='Export', command=self.export,
                      default='active', width=10)
        w.pack(side='left', padx=5, pady=5)
        w = tk.Button(box, text='Cancel', command=self.cancel, width=10)
        w.pack(side='left', padx=5, pady=5)

        self.bind('<Return>', self.ok)
        self.bind('<Escape>', self.cancel)

        box.pack()

    def __tick_receptor(self):
        """Make sure at least one receptor is ticked in the selection."""
        if sum([var.get() for var in self.__receptors.values()]) == 0:
            self.__receptors[list(self.__receptors.keys())[0]].set(1)

    def __tick_cohort(self):
        """Make sure at least one cohort is ticked in the selection."""
        if sum([var.get() for var in self.__cohorts.values()]) == 0:
            self.__cohorts['1000BRAINS'].set(1)

    def __change_extended_feature_visibility(self, feature):
        """Show/Hide extended settings depending on the current feature selection."""
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
        filename = filedialog.asksaveasfilename(title='Select export location', initialdir=os.path.dirname(self.__path_var.get(
        )), initialfile=os.path.basename(self.__path_var.get()), defaultextension='.pdf', filetypes=[('PDF', '*.pdf')], confirmoverwrite=True)

        # Canceling the filedialog returns an empty string.
        if filename:
            filename = os.path.normpath(filename)
            self.__path_var.set(filename)

    def export(self, event=None):
        """Start the export to PDF of all assignments and linked features that are selected."""

        for widget in self.winfo_children():
            widget.destroy()

        tk.Label(self, text='Exporting to PDF ...').pack(
            anchor='w', padx=5, pady=5)
        ttk.Progressbar(self, orient='horizontal', variable=self.progress,
                        length=200).pack(anchor='w', padx=5, pady=5)
        tk.Button(self, text="Cancel", command=self.cancel,
                  width=10).pack(padx=5, pady=5)
        self.update()

        features = [
            feature for feature in self.__features if self.__features[feature].get() == 1]
        receptors = [
            receptor for receptor in self.__receptors if self.__receptors[receptor].get() == 1]
        cohorts = [
            cohort for cohort in self.__cohorts if self.__cohorts[cohort].get() == 1]
        filter = [self.__col.get(), self.__sign.get(), float(self.__num.get())]

        thread = threading.Thread(target=self.__logic.export_assignments, args=(
            filter, features, receptors, cohorts, self.__path_var.get(), self.progress), daemon=True)
        thread.start()

        while thread.is_alive():
            self.update()

        self.after(3000, self.cancel)

    def cancel(self, event=None):
        """Stop the export and close the dialog."""
        self.progress.set(-1)

        # put focus back to the parent window
        if self.parent is not None:
            self.parent.focus_set()
        self.destroy()


class customTreeView(ttk.Treeview):
    """Custom TreeView that allows sorting wrt columns and opening of row-specific urls via double click."""

    def onDoubleClick(self, event, urls):
        """Open the corresponding region of the selected row in siibra-explorer."""
        item = self.selection()
        values = self.item(item, 'values')
        if values:
            webbrowser.open(urls[values[0]])

    def heading(self, column, sort_by=None, **kwargs):
        """Query or modify the heading options for the specified column.
        
        :param column: column to apply sorting to
        :param str sort_by: value type to sort
        :return: If kwargs is not given, returns a dict of the heading option values. 
        If option is specified then the value for that option is returned. 
        Otherwise, sets the options to the corresponding values.
        :rtype: dict, value or None
        """
        if sort_by and not hasattr(kwargs, 'command'):
            func = getattr(self, f"_sort_by_{sort_by}", None)
            if func:
                kwargs['command'] = lambda: func(column, False)
        return super().heading(column, **kwargs)

    def _sort(self, column, reverse, data_type, callback):
        """Sort the rows according to the specified column.

        :param str column: column to sort by
        :param bool reverse: if sorting should be reverted
        :param type data_type: data type to sort
        :param func callback: function to use for sorting
        """
        l = [(self.set(k, column), k) for k in self.get_children('')]
        l.sort(key=lambda t: data_type(t[0]), reverse=reverse)
        for index, (_, k) in enumerate(l):
            self.move(k, '', index)

        self.heading(column, command=lambda: callback(column, not reverse))

    def _sort_by_float(self, column, reverse):
        """Sort the float entries of the specified column.

        :param str column: column to sort by
        :param bool reverse: if sorting should be reverted
        :return func: function for sorting
        """
        self._sort(column, reverse, float, self._sort_by_float)

    def _sort_by_str(self, column, reverse):
        """Sort the string entries of the specified column.

        :param str column: column to sort by
        :param bool reverse: if sorting should be reverted
        :return func: function for sorting
        """
        self._sort(column, reverse, str, self._sort_by_str)
