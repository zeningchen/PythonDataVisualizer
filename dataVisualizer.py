from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import pyqtSlot, Qt, QSize
import matplotlib
import functools
matplotlib.use("Qt5Agg")
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from collections import OrderedDict
from datetime import datetime
import time
import iso8601
import os
import sys
import traceback
import pandas as pd
import itertools
import numpy as np

#Geometry Settings
WINDOW_MARGIN = 256
WINDOW_HEIGHT = 1024
WINDOW_WIDTH = 1200
SEQUENCER_MARGIN = 10
SELECTOR_HEIGHT = WINDOW_HEIGHT
SELECTOR_WIDTH = WINDOW_WIDTH/3
FILTER_WIDTH = WINDOW_WIDTH/6
FILTER_HEIGHT = WINDOW_HEIGHT/6
FIG_WIDTH = 2*SELECTOR_WIDTH
FIG_HEIGHT = SELECTOR_HEIGHT
FILE_PATH = os.path.dirname(os.path.realpath(__file__))

class DataSelector(QGroupBox):
    MAX_FILTER_SIZE = 20

    def __init__(self, dataset, groupName='Data', exclusive=False, enableFilters=False):
        super(DataSelector, self).__init__(groupName)
        self.layout = QFormLayout()
        self.setLayout(self.layout)
        self.checkBoxLookup = {}
        self.checkboxGroup = QButtonGroup()

        for field in dataset:
            checkbox = QCheckBox(field)
            self.layout.addRow(checkbox)
            #Don't like random flag
            if enableFilters:
                checkbox.stateChanged.connect(functools.partial(self._set_filters, field=field))
            self.checkboxGroup.addButton(checkbox)
            self.checkBoxLookup[field] = checkbox

        if enableFilters:
            self.enableFilters = True
            self.scrollArea = QScrollArea()
            self.filterGroup = QGroupBox('Filters')
            self.filterGroup.layout = QFormLayout()
            self.filterGroup.setLayout(self.filterGroup.layout)
            self.scrollArea.setWidgetResizable(True)
            self.scrollArea.setMinimumSize(QSize(SELECTOR_WIDTH, SELECTOR_HEIGHT))
            self.scrollArea.setWidget(self.filterGroup)
            self.layout.addRow(self.scrollArea)
            self.dataset = dataset
            self.filterGroupLookup = {}
        else:
            self.enableFilters = False
            self.dataset = None

        self.checkboxGroup.setExclusive(exclusive)

    def _clear_layout(self, layout):
        for i in reversed(range(layout.count())):
            if i is not None:
                layout.itemAt(i).widget().setParent(None)

    def _get_checked_boxes(self, checkLookup):
        enabled_fields = []
        for field in checkLookup:
            if checkLookup[field].checkState() == Qt.Checked:
                enabled_fields.append(field)
        return enabled_fields

    def _filter_check(self, field):
        if not self.enableFilters or not self.checkboxGroup.exclusive() or \
                len(pd.unique(self.dataset[field].values)) > self.MAX_FILTER_SIZE:
            return False
        else:
            return True

    def get_checked_datasets(self):
        return self._get_checked_boxes(self.checkBoxLookup)

    def get_checked_filters(self, field):
        print 'FilterGroup Lookup =', self.filterGroupLookup
        if self._filter_check(field):
            print 'Passed field check'
            print self._get_checked_boxes(self.filterGroupLookup)
            return self._get_checked_boxes(self.filterGroupLookup)
        else:
            return self.filterGroupLookup.keys()

    def _set_filters(self, field):
        try:
            self._clear_layout(self.filterGroup.layout)
            if not self._filter_check(field):
                print 'Failing filter Check'
                self.filterGroup.layout.addRow(QLabel('Filter Not Available for this Field!'))
            else:
                if self.checkBoxLookup[field].checkState() == Qt.Unchecked:
                    self._clear_layout(self.filterGroup.layout)
                else:
                    unique_vals = pd.unique(self.dataset[field].values)
                    print unique_vals
                    for val in unique_vals:
                        checkBox = QCheckBox(str(val))
                        self.filterGroup.layout.addRow(checkBox)
                        self.filterGroupLookup[val] = checkBox
        except:
            traceback.print_exc()


class DataWidget(QWidget):

    def __init__(self):
        super(DataWidget, self).__init__()
        self.layout = QHBoxLayout()
        self.setLayout(self.layout)
        self.dataSelectors = OrderedDict()

    def add_dataset(self, dataset, ds_name, exclusive=False, enableFilters=False):
        self.dataSelectors[ds_name] = DataSelector(dataset, ds_name, exclusive=exclusive, enableFilters=enableFilters)
        self.layout.addWidget(self.dataSelectors[ds_name])

    def get_checked_data_sets(self, lookup):
        return self.dataSelectors[lookup].get_checked_datasets()

    def get_checked_filters(self, lookup, field):
        return self.dataSelectors[lookup].get_checked_filters(field)


class DataTab(QTabWidget):

    INDEPENDENT_VARS = 'X-axis-SELECT_ONE'
    DEPENDENT_VARS = 'Y-axis-SELECT_MULTIPLE'
    OVER_VARS = '(Data Filter)-SELECT_ONE'


    def __init__(self):
        super(DataTab, self).__init__()
        self.resize(SELECTOR_WIDTH, SELECTOR_HEIGHT)
        self.tab_lookup = {}

    def get_new_name(self, ds_name):
        i = 0
        ds_name_check = ds_name
        while ds_name_check in self.tab_lookup:
            ds_name_check = ds_name + str(i)
            i += 1
        print ds_name_check
        return ds_name_check

    def add_dataset(self, dataset, ds_name):
        self.dataWidget = DataWidget()
        self.addTab(self.dataWidget, ds_name)
        self.tab_lookup[ds_name] = self.dataWidget
        self.dataWidget.add_dataset(dataset, self.INDEPENDENT_VARS, exclusive=True)
        self.dataWidget.add_dataset(dataset, self.DEPENDENT_VARS)
        self.dataWidget.add_dataset(dataset, self.OVER_VARS, exclusive=True, enableFilters=True)

    def get_checked_independent_sets(self, tab_name):
        return self.tab_lookup[tab_name].get_checked_data_sets(self.INDEPENDENT_VARS)

    def get_checked_dependent_sets(self, tab_name):
        return self.tab_lookup[tab_name].get_checked_data_sets(self.DEPENDENT_VARS)

    def get_checked_overvar_sets(self, tab_name):
        return self.tab_lookup[tab_name].get_checked_data_sets(self.OVER_VARS)

    def get_checked_overvar_filters(self, tab_name, field):
        return self.tab_lookup[tab_name].get_checked_filters(self.OVER_VARS, field)


class DataWindow(QDockWidget):
    TIME_SERIES_ADJUSTED = 'Time (Seconds)'

    def __init__(self, plotterObj=None):
        #Setup Window
        super(DataWindow, self).__init__()
        self.setWindowTitle('Data Selector')
        self.mainWidget = QWidget()
        self.mainWidgetLayout = QVBoxLayout()
        self.mainWidget.setLayout(self.mainWidgetLayout)
        self.setWidget(self.mainWidget)
        self.mainWidget.setMinimumSize(QSize(SELECTOR_WIDTH, SELECTOR_HEIGHT))
        self.plotterObj = plotterObj

        #Add Tab Widget
        self.dataTabWidget = DataTab()
        self.mainWidgetLayout.addWidget(self.dataTabWidget)

        #Add Button to Plot DataSet
        self.plotButton = QPushButton('PlotData')
        self.mainWidgetLayout.addWidget(self.plotButton)

        #Connect Button to Plot Procedure
        self.plotButton.clicked.connect(self.plot_routine)
        self.tabs = OrderedDict()

    def add_dataset(self, dataset, ds_name):
        ds_name = self.dataTabWidget.get_new_name(ds_name)
        self.tabs[ds_name] = dataset
        self.dataTabWidget.add_dataset(dataset, ds_name)

    def plot_routine(self):
        try:
            independentSets = {}
            dependentSets = {}
            overSets = {}
            for tab in self.tabs:
                independentSets[tab] = self.dataTabWidget.get_checked_independent_sets(tab)
                dependentSets[tab] = self.dataTabWidget.get_checked_dependent_sets(tab)
                overSets[tab] = self.dataTabWidget.get_checked_overvar_sets(tab)
            self._consolidated_plot(independentSets, dependentSets, overSets)
        except:
            traceback.print_exc()

    def _get_sec_manual(self, h, m, s):
        return int(h)*3600 + int(m)*60 + int(s)

    def _convert_datetime_to_epoch(self, df, x):
        try:
            datetime_start = iso8601.parse_date(df.loc[0, x])
            seconds_start = time.mktime(datetime_start.timetuple())
            df[self.TIME_SERIES_ADJUSTED] = pd.Series(0, index=df.index)
            for i in df.index:
                dt = iso8601.parse_date(df.loc[i, x])
                df.loc[i, self.TIME_SERIES_ADJUSTED] = time.mktime(dt.timetuple()) - seconds_start
        #Badly Formatted Time Series data
        except:
            df[self.TIME_SERIES_ADJUSTED] = pd.Series(0, index=df.index)
            hms_last = df[x].values[0].split(':')
            d_start = self._get_sec_manual(*hms_last)
            for i in df.index:
                hms_current = df.loc[i ,x].split(':')
                if int(hms_last[0]) > int(hms_current[0]):
                    hms_current[0] = str(int(hms_current[0]) + 24)

                df.loc[i, self.TIME_SERIES_ADJUSTED] = self._get_sec_manual(*hms_current) - d_start
                hms_last = hms_current
        finally:
            'Done'

        x = self.TIME_SERIES_ADJUSTED
        return x

    def _get_active_tabs(self, indTabSets):
        active_tabs = []
        for tab in indTabSets:
            if len(indTabSets[tab]) > 0:
                active_tabs.append(tab)
        return active_tabs

    def _get_subplot_str(self, numTabs):
        if numTabs % 2 == 1:
            return str(numTabs) + '1'
        else:
            return str(numTabs/2) + '2'


    def _consolidated_plot(self, indTabSets, depTabSets, overTabSets):
        #TODO: Comeup with something, more clever, for now just pick the first tab, first element

        #Multiplot case
        self.plotterObj.clear_plot()
        active_tabs = self._get_active_tabs(indTabSets)
        num_tabs = len(active_tabs)
        print 'num_tabs = {}'.format(num_tabs)
        subplot_str = self._get_subplot_str(num_tabs)

        for i, tab in enumerate(active_tabs):
            if len(indTabSets[tab]) == 0:
                continue
            df = self.tabs[tab]
            x = indTabSets[tab][0]

            #Instantiate Plotter Object
            subplotStrMod = subplot_str + str(i + 1)
            subplotNumber = int(subplotStrMod)
            self.plotterObj.set_axes(subplotNumber)
            axes = self.plotterObj.get_axes()

            if 'time' in x.lower():
                x = self._convert_datetime_to_epoch(df, x)
            self.plotterObj.set_xlabel(axes, '{}'.format(x))
            for j, y in enumerate(depTabSets[tab]):
                #Setup the Y-Axis
                if j > 0:
                    axes_set = axes.twinx()
                else:
                    axes_set = axes
                self.plotterObj.set_ylabel(axes_set, '{}'.format(y))

                if len(overTabSets[tab]) != 0:
                    z = overTabSets[tab][0]
                    z_unique_vals = self.dataTabWidget.get_checked_overvar_filters(tab, z)
                    self.plotterObj.plot(df, x, y, z, z_unique_vals=z_unique_vals)
                else:
                    z = None
                    subplotStrMod = subplot_str + str(i+1)
                    self.plotterObj.plot(df, x, y, z, z_unique_vals=None)
            self.plotterObj.set_title(axes, '{} {} vs {}'.format(tab, depTabSets[tab], x))
            self.plotterObj.set_legend(axes)
            self.plotterObj.draw()

        # #Default Independent Variable default tab
        # defTab = indTabSets.keys()[0]
        # x = indTabSets[defTab][0]
        #
        # #Get Data:
        # df = self.tabs[defTab]
        #
        # if 'time' in x.lower():
        #     x = self._convert_datetime_to_epoch(df, x)
        #
        # #Over Data Default
        # if len(overTabSets[defTab]) != 0:
        #     z = overTabSets[defTab][0]
        # else:
        #     z = None
        #
        # subplot_number = 111
        # #Dependent Vars
        # for y in depTabSets[defTab]:
        #     self.plotterObj.plot(df, x, y, z, subplot_number)


class PlotCanvas(FigureCanvas):
    '''
    Acts as a wrapper around the axes class to handle multiple axes
    '''

    def __init__(self, parent=None, width=FIG_WIDTH, height=FIG_HEIGHT, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)

        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self,
                                   QSizePolicy.Expanding,
                                   QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)
        self.axes = None

    def flatten(self, data):
        try:
            return list(itertools.chain.from_iterable(data))
        except:
            return data

    def clear_plot(self):
        self.fig.clf()
        self.axes = None

    def get_axes(self):
        return self.axes

    def set_axes(self, subplot):
        self.axes = self.fig.add_subplot(subplot)

    def set_title(self, axes, title):
        axes.set_title(title)

    def set_ylabel(self, axes, label):
        axes.set_ylabel(label)

    def set_xlabel(self, axes, label):
        axes.set_xlabel(label)

    def set_legend(self, axes):
        axes.legend()



    def plot(self, df, x, y, z=None, z_unique_vals=None):

        self.axes.grid()
        if z == None:
            x_vals = df[x].values.tolist()
            y_vals = df[y].values.tolist()
            self.axes.scatter(x_vals, y_vals, label='{}'.format(y))
        else:
            if z_unique_vals is None:
                z_unique = pd.unique(df[z].values.tolist())
            else:
                z_unique = z_unique_vals
            for z_val in z_unique:
                x_vals = df.loc[df[z] == z_val][x].values
                y_vals = df.loc[df[z] == z_val][y].values
                self.axes.scatter(x_vals, y_vals, label='{} {} = {}'.format(y, z, z_val))

class DataVisualizerGui(QMainWindow):

    def __init__(self):
        try:
            #Setup Window Size and Titlebar
            super(DataVisualizerGui, self).__init__()
            self.setWindowTitle('DATA VISUALIZER TOOL')
            self.setGeometry(WINDOW_MARGIN, WINDOW_MARGIN,
                             WINDOW_WIDTH, WINDOW_HEIGHT)

            #Set up Window Space
            self.mainWidget = QWidget()
            self.mainLayout = QVBoxLayout()
            self.mainWidget.setLayout(self.mainLayout)
            self.setCentralWidget(self.mainWidget)

            #Add Welcome Message
            label = QLabel('Welcome to the Data Visualizer!')
            self._set_font(label, 24, True)
            self.mainLayout.addWidget(label)

            # Add Button
            self.loadDsButton = QPushButton('Load New Dataset ---->')
            self.loadDsButton.setToolTip('Runs the Sequence Created on the DockedWindow')
            self.loadDsButton.clicked.connect(self._load_new_ds)
            self._set_font(self.loadDsButton, 14, True)
            self.mainLayout.addWidget(self.loadDsButton)

            # Add Plot Area
            self.scrollArea = QScrollArea()
            self.scrollArea.setWidgetResizable(True)
            self.pltCanvas = PlotCanvas(self, width=FIG_WIDTH, height=FIG_WIDTH)
            self.scrollArea.setWidget(self.pltCanvas)
            self.naviToolbar = NavigationToolbar(self.pltCanvas, self)
            self.mainLayout.addWidget(self.scrollArea)
            self.mainLayout.addWidget(self.naviToolbar)


            #Add Data Selector Dock Widget
            self.dataSelectorWindow = DataWindow(self.pltCanvas)
            self.dockRightArea = Qt.DockWidgetArea(2)
            self.addDockWidget(self.dockRightArea, self.dataSelectorWindow)

            self.show()
        except:
            traceback.print_exc()


    def _set_font(self, widget, font_size=12, bold=False):
        font = widget.font()
        font.setPointSize(font_size)
        font.setBold(bold)
        widget.setFont(font)


    def _load_new_ds(self):
        try:
            save_dir = FILE_PATH
            name, filter = QFileDialog.getOpenFileName(self, 'Save Sequencer Table', save_dir,
                                                       "CSV Files (*.csv);;Sqlite Files (*.db);;YAML Files (*.yaml)")
            file = open(name, 'r')
            file_extension = name.split('.')[-1]
            if file_extension == 'csv':
                try:
                    df = pd.read_csv(name, sep=',|;', comment='#', engine='python')
                except:
                    traceback.print_exc()
            else:
                print 'File format not supported yet'
            self.dataSelectorWindow.add_dataset(df, (name.split('.')[-2]).split('/')[-1])

        except:
            traceback.print_exc()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = DataVisualizerGui()
    sys.exit(app.exec_())