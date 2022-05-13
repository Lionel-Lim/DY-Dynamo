from System.Collections.ObjectModel import ObservableCollection

import rpw
from rpw import revit, db, ui, DB, UI

from rpw.exceptions import RevitExceptions
from pyrevit.forms import WPFWindow

from event import CustomizableEvent
# from verticalcurve import VerticalCurve

__doc__ = "Alignment Manager"
__title__ = "Create Alignment Model"
__author__ = "DY Lim"
__persistentengine__ = True


def debug(self, line):
    self.debug.Text = "{}\n{}".format(self.debug.Text, line)
    self.debug.ScrollToEnd()


class verticalAlignmentFormat:
    def __init__(
        self,
        index=None,
        pviStation=None,
        pviElevation=None,
        grade=None,
        _CurveType=None,
        _CurveLength=None,
        _K=None,
    ):
        self.index = index
        self.pviStation = pviStation
        self.pviElevation = pviElevation
        self.grade = grade
        self._CurveType = _CurveType
        self._CurveLength = _CurveLength
        self._K = _K


curveType = ["Line", "Curve"]


class form_window(WPFWindow):
    def __init__(self, xaml_file_name):
        WPFWindow.__init__(self, xaml_file_name)
        self.Show()

        self.VAContents = ObservableCollection[object]()
        self.VAContents.Add(verticalAlignmentFormat(0))
        self.VerticalCurveTable.ItemsSource = self.VAContents
        self.curveType = ObservableCollection[object]()
        [self.curveType.Add(ct) for ct in curveType]
        self.curveTypeBox.ItemsSource = self.curveType

        self.input_curveType.ItemsSource = self.curveType

        self.debug.Text = "Initializing Success\nWaiting Task..."

    def addrow(self, sender, e):
        for i in self.VAContents:
            lastIndex = i.index
        self.VAContents.Add(verticalAlignmentFormat(lastIndex + 1))
        #
        debug(self, "{} Row Added".format(lastIndex + 1))

    def clearRow(self, sender, e):
        selectedIndex = self.VerticalCurveTable.SelectedIndex
        if selectedIndex == -1:
            debug(self, "Please Select Row To Be Cleared".format(selectedIndex))
        else:
            self.VAContents.RemoveAt(selectedIndex)
            self.VAContents.Insert(
                selectedIndex, verticalAlignmentFormat(selectedIndex)
            )
            debug(self, "{} Row Cleared".format(selectedIndex))

    def removeRow(self, sender, e):
        index = self.VAContents.Count - 1
        if index == 0:
            debug(self, "Cannot Remove All")
        else:
            self.VAContents.RemoveAt(index)
            debug(self, "{} Row Removed".format(index))
    
    def valueUpdated(self, sender, e):
        index = self.input_curveType.SelectedIndex
        if index == 0:
            self.input1.Text = "PVI Station Start"
            self.input2.Text = "PVI Station End"
            self.input3.Text = "Line Slope"
        else:
            self.input1.Text = "PVI Station"
            self.input2.Text = "PVI Elevation"
            self.input3.Text = "Curve Length"            
        debug(self, "{}".format(index))

    def input1Updated(self, sender, e):
        value1_count = len(self.input1_1.Text)
        if value1_count > 0:
            self.input3_1.IsReadOnly = True
        else:
            self.input3_1.IsReadOnly = False
        debug(self, "{}".format(value1_count))


form = form_window("ui.xaml")
