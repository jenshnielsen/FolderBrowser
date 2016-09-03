from __future__ import unicode_literals
import sys
import os
from matplotlib.backends import qt_compat
use_pyside = qt_compat.QT_API == qt_compat.QT_API_PYSIDE
if use_pyside:
    from PySide import QtGui, QtCore
else:
    from PyQt4 import QtGui, QtCore

#fjoweifjwe
from FileListWidget import FileList
sys.path.append('C:/git_repos')
from data_loader.sweep import Sweep

import numpy as np
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4 import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt


class MyNewMplCanvas(FigureCanvas):
    """Ultimately, this is a QWidget (as well as a FigureCanvasAgg, etc.)."""
    def __init__(self, fig, parent=None):
        self.fig = fig
        FigureCanvas.__init__(self, fig)
        self.setParent(parent)
        self.axes = fig.get_axes()

        self.load_and_plot_data()

        FigureCanvas.setSizePolicy(self,
                                   QtGui.QSizePolicy.Expanding,
                                   QtGui.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

    def load_and_plot_data(self, file_list_item=None):
        if file_list_item is None:
            # raise RuntimeError('file_list_item is None')
            return
        sweep_path = file_list_item.data(QtCore.Qt.UserRole)
        self.sweep = Sweep(sweep_path)
        sweep_names = self.sweep.data.dtype.names
        x_data = self.sweep.data[sweep_names[0]]
        y_data = self.sweep.data[sweep_names[1]]
        for ax in self.axes:
            ax.cla()
            ax.plot(x_data, y_data)
            ax.relim()
            ax.autoscale_view(True, True, True)
        self.fig.canvas.draw()


class FolderBrowser(QtGui.QMainWindow):
    def __init__(self, fig, dir_path):
        self.fig = fig
        self.axes = fig.get_axes()
        self.dir_path = dir_path
        QtGui.QMainWindow.__init__(self)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setWindowTitle("application main window")

        self.file_menu = QtGui.QMenu('&File', self)
        self.file_menu.addAction('&Quit', self.fileQuit,
                                 QtCore.Qt.CTRL + QtCore.Qt.Key_Q)
        self.menuBar().addMenu(self.file_menu)

        self.main_widget = QtGui.QWidget(self)
        grid = QtGui.QVBoxLayout(self.main_widget)

        canvas = MyNewMplCanvas(fig, parent=self.main_widget)
        self.navi_toolbar = NavigationToolbar(canvas, self)
        self.file_list = FileList(self.dir_path)
        self.file_list.itemClicked.connect(canvas.load_and_plot_data)
        # Creates navigation toolbar for our plot canvas.
        comboBox = QtGui.QComboBox(self)
        comboBox.addItems(['wejoif','wjeofij'])

        grid.addWidget(canvas)
        grid.addWidget(comboBox)
        grid.addWidget(self.navi_toolbar)
        grid.addWidget(self.file_list)

        self.main_widget.setFocus()
        self.setCentralWidget(self.main_widget)


    def fileQuit(self):
        self.close()

    def closeEvent(self, ce):
        self.fileQuit()


qApp = QtGui.QApplication(sys.argv)

data_path = 'C:/Dropbox/PhD/sandbox_phd/load_in_jupyter/data'
fig, _ = plt.subplots()
aw = FolderBrowser(fig, data_path)
aw.setWindowTitle('Some cool title for the window')
aw.show()
sys.exit(qApp.exec_())
#qApp.exec_()
