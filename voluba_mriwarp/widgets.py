import webbrowser
from tkinter import ttk


class customTreeView(ttk.Treeview):

    def onDoubleClick(self, event, urls):
        """Open the corresponding region of the selected row in siibra-explorer."""
        item = self.selection()
        values = self.item(item, 'values')
        if values:
            webbrowser.open(urls[values[0]])

    def heading(self, column, sort_by=None, **kwargs):
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
