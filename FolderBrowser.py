import sys
import os
from matplotlib.backends import qt_compat
use_pyside = qt_compat.QT_API == qt_compat.QT_API_PYSIDE
if use_pyside:
    from PySide import QtGui, QtCore
else:
    from PyQt4 import QtGui, QtCore

from FileListWidget import FileList
from sweep import Sweep
from customcomboboxes import CustomComboBoxes

from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg
from matplotlib.backends.backend_qt4 import NavigationToolbar2QT
import matplotlib.pyplot as plt
import numpy as np


class MplLayout(QtGui.QWidget):
    """
    Contains canvas, toolbar and a customcomboboxes object.
    """
    def __init__(self, statusBar=None):
        super(MplLayout, self).__init__()
        plt.ioff()
        fig, _ = plt.subplots()
        plt.ion()
        self.statusBar = statusBar
        self.fig_canvas = FigureCanvasQTAgg(fig)
        self.comboBoxes = CustomComboBoxes(3, self.update_sel_cols)
        self.navi_toolbar = NavigationToolbar2QT(self.fig_canvas, self)
        layout = QtGui.QGridLayout()
        n_rows_canvas = 3
        n_cols_canvas = 3
        for i, box in enumerate(self.comboBoxes.boxes):
            layout.addWidget(box, n_rows_canvas+1, i, 1, 1)
        layout.addWidget(self.fig_canvas, 1, 0, n_rows_canvas, n_cols_canvas)
        layout.addWidget(self.navi_toolbar, 0, 0, 1, n_cols_canvas)
        self.setLayout(layout)
        self.none_str = '---'
        self.sel_col_names = self.comboBoxes.get_sel_texts()
        self.cbar = None
        self.image = None

    def update_sel_cols(self, new_num=None):
        """
        To maintain a consistent state we must update the plot at the end.
        """
        self.prev_sel_col_names = self.sel_col_names
        self.sel_col_names = self.comboBoxes.get_sel_texts()
        self.label_names = self.sel_col_names
        # Try to make 1D plot if '---' is selected in the third comboBox.
        self.plot_is_2D = self.sel_col_names[2] != self.none_str
        self.data_is_1D = self.sweep.dimension == 1
        plot_is_invalid = self.plot_is_2D and self.data_is_1D
        if plot_is_invalid:
            if self.statusBar is not None:
                msg = "You can't do an image plot, since the data is only 1D."
                self.statusBar.showMessage(msg, 2000)
            self.comboBoxes.set_text_on_box(2, self.none_str)
        self.update_plot()

    def reset_and_plot(self, sweep=None):
        if sweep is not None:
            self.sweep = sweep
        raw_cols = self.sweep.data.dtype.names
        col3_names = raw_cols + (self.none_str,)
        col_names = [raw_cols, raw_cols, col3_names]
        self.comboBoxes.reset(col_names)
        self.update_sel_cols()

    def update_plot(self):
        if self.plot_is_2D: self.update_2D_plot()
        else: self.update_1D_plot()

    def update_1D_plot(self):
        if self.cbar is not None:
            self.cbar.remove()
            self.cbar = None
            self.image = None
        plot_data = self.load_data_for_plot(dim=2)
        for ax in self.fig_canvas.figure.get_axes():
            ax.cla()
            ax.plot(plot_data[0], plot_data[1])
            ax.autoscale_view(True, True, True)
        self.common_plot_update()

    def update_2D_plot(self):
        plot_data = self.load_data_for_plot(dim=3)
        col0_axis = arr_varies_monotonically_on_axis(plot_data[0])
        col1_axis = arr_varies_monotonically_on_axis(plot_data[1])
        if not set((col0_axis, col1_axis)) == set((0, 1)):
            msg = 'Selected columns not valid for image plot. No action taken.'
            self.sel_col_names = self.prev_sel_col_names
            self.statusBar.showMessage(msg)
            return
        col0_lims = [plot_data[0][0,0], plot_data[0][-1,-1]]
        col1_lims = [plot_data[1][0,0], plot_data[1][-1,-1]]
        if col0_axis == 0:
            data_for_imshow = np.transpose(plot_data[2])
        else:
            data_for_imshow = plot_data[2]
        extent = col0_lims + col1_lims
        self.label_names = self.sel_col_names
        fig = self.fig_canvas.figure
        ax = fig.get_axes()[0]
        try:
            self.image.set_data(data_for_imshow)
            self.image.set_extent(extent)
            self.image.autoscale()
        except AttributeError as error:
            self.statusBar.showMessage('self.image does not exist')
            ax.cla()
            self.image = ax.imshow(
                data_for_imshow,
                aspect='auto',
                cmap='bwr',
                interpolation='none',
                origin='lower',
                extent=extent,
            )
            self.cbar = fig.colorbar(mappable=self.image)
            self.cbar.set_label(self.sel_col_names[2])
        ax.autoscale_view(True, True, True)
        self.common_plot_update()

    def common_plot_update(self):
        # Sometimes we'll get an error:
        # ValueError: bottom cannot be >= top
        # This is a confirmed bug when using tight_layout():
        # https://github.com/matplotlib/matplotlib/issues/5456
        ax = self.fig_canvas.figure.get_axes()[0]
        ax.relim()
        ax.set_xlabel(self.label_names[0])
        ax.set_ylabel(self.label_names[1])
        ax.set_title(self.sweep.meta['name'])
        # self.fig_canvas.figure.tight_layout()
        self.fig_canvas.figure.canvas.draw()

    def load_data_for_plot(self, dim):
        plot_data = [None] * dim
        for i in range(dim):
            plot_data[i] = self.sweep.data[self.sel_col_names[i]]
        return plot_data


def arr_varies_monotonically_on_axis(arr):
    for axis in (0,1):
        idx = [0,0]
        idx[axis] = slice(None)
        candidate = arr[idx]
        arr_diff = np.diff(candidate)
        # Check that there are non-zero elements in arr_diff.
        # Otherwise arr is constant.
        if not any(arr_diff):
            continue
        # Check that the elements are the same,
        # i.e., the slope of arr is constant.
        if not np.allclose(arr_diff, arr_diff[0]):
            continue
        # Check that arr consists solely of copies of candidate.
        # First, insert an np.newaxis in candidate so you can subtract it
        # from arr.
        if axis == 0:
            candidate = candidate[...,np.newaxis]
        if not np.allclose(arr, candidate):
            continue
        return axis
    return -1


class FolderBrowser(QtGui.QMainWindow):
    def __init__(self, n_figs, dir_path, window_title='FolderBrowser'):
        self.dir_path = dir_path
        QtGui.QMainWindow.__init__(self)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setWindowTitle(window_title)
        self.file_list = FileList(self.dir_path)
        self.statusBar = QtGui.QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Dad, I'm hungry. Hi Hungry, I'm dad.")
        self.mpl_layouts = [None] * n_figs
        for i in range(n_figs):
            self.mpl_layouts[i] = MplLayout(statusBar=self.statusBar)
        self.file_list.itemClicked.connect(self.delegate_new_sweep)
        self.dock_widgets = [None] * (n_figs+1)
        for i, mpl_layout in enumerate(self.mpl_layouts):
            widget_title = 'Plot {}'.format(i)
            dock_widget = QtGui.QDockWidget(widget_title, self)
            dock_widget.setWidget(mpl_layout)
            self.addDockWidget(QtCore.Qt.TopDockWidgetArea, dock_widget)
            dock_widget.setAllowedAreas(QtCore.Qt.AllDockWidgetAreas)
            self.dock_widgets[i] = dock_widget
        dock_widget = QtGui.QDockWidget('Browser', self)
        dock_widget.setWidget(self.file_list)
        self.addDockWidget(QtCore.Qt.BottomDockWidgetArea, dock_widget)
        dock_widget.setAllowedAreas(QtCore.Qt.AllDockWidgetAreas)
        file_list_item = self.file_list.currentItem()
        self.delegate_new_sweep(file_list_item)
        self.setDockNestingEnabled(True)
        self.show()

    def delegate_new_sweep(self, file_list_item):
        sweep_path = file_list_item.data(QtCore.Qt.UserRole)
        self.sweep = Sweep(sweep_path)
        for mpl_layout in self.mpl_layouts:
            mpl_layout.reset_and_plot(self.sweep)


if __name__=='__main__':
    n_figs = 2
    data_path = 'C:/Dropbox/PhD/sandbox_phd/load_in_jupyter/data'
    # data_path = 'C:/Dropbox/PhD/sandbox_phd/load_in_jupyter/data2D'
    qApp = QtGui.QApplication(sys.argv)
    brw = FolderBrowser(n_figs, data_path)
    sys.exit(qApp.exec_())
    #qApp.exec_()
