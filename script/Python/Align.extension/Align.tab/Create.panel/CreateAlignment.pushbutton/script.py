import math
import clr

clr.AddReference("PresentationCore")

import System
from System.Collections.ObjectModel import ObservableCollection

import rpw
from rpw import revit, db, ui, DB, UI

from rpw.exceptions import RevitExceptions
from pyrevit.forms import WPFWindow

from event import CustomizableEvent

import verticalcurve
import excel


__doc__ = "Alignment Manager"
__title__ = "Create Alignment Model"
__author__ = "DY Lim"
__persistentengine__ = True


curveType = ["Line", "Curve"]

customizable_event = CustomizableEvent()

selectCond= True
_drawingRef=None

def debug(self, line):
    self.debug.Text = "{}\n{}".format(self.debug.Text, line)
    self.debug.ScrollToEnd()

def debugHorizontal(self, line):
    self.debugHorizontal.Text = "{}\n{}".format(self.debugHorizontal.Text, line)
    self.debugHorizontal.ScrollToEnd()

def toFloat(input):
    try:
        return float(input)
    except:
        return None

def select_element():
    global _drawingRef
    with db.Transaction("selection"):
        ref = ui.Pick.pick_element("Select Reference").ElementId
        _drawingRef = revit.doc.GetElement(ref)



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


class form_window(WPFWindow):
    def __init__(self, xaml_file_name):
        WPFWindow.__init__(self, xaml_file_name)
        self.Show()

        self.VAContents = ObservableCollection[object]()
        # self.VAContents.Add(verticalAlignmentFormat(0))
        self.VerticalCurveTable.ItemsSource = self.VAContents

        self.curveType = ObservableCollection[object]()
        [self.curveType.Add(ct) for ct in curveType]
        self.input_curveType.ItemsSource = self.curveType

        self.debug.Text = "Initializing Success\nWaiting Task..."

    def addrow(self, sender, e):
        curveTypeIndex = self.input_curveType.SelectedIndex
        lastIndex = 0
        for i in self.VAContents:
            try:
                lastIndex = i.index
            except:
                continue
        if curveTypeIndex == 0:
            if lastIndex != 0 and lastIndex % 2 == 0:
                debug(self, "Item Must Be Line Type")
            else:
                if lastIndex == 0:
                    lastIndex = -1
                grade = self.inputValue5.Text
                self.VAContents.Add(
                    verticalAlignmentFormat(
                        lastIndex + 1,
                        None,
                        None,
                        grade,
                        "Line",
                        None,
                        None,
                    )
                )
        elif curveTypeIndex == 1:
            if lastIndex % 2 != 0:
                debug(self, "Item Must Be Curve Type")
            else:
                pviStation = self.inputValue1.Text
                pviElevation = self.inputValue2.Text
                curveLength = self.inputValue3.Text
                self.VAContents.Add(
                    verticalAlignmentFormat(
                        lastIndex + 1,
                        pviStation,
                        pviElevation,
                        None,
                        "Curve",
                        curveLength,
                        None,
                    )
                )
        else:
            debug(self, "Unidentified Curve Type")
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

    def examineRow(self, sender, e):
        selectedIndex = self.VerticalCurveTable.SelectedIndex
        if selectedIndex == -1:
            debug(self, "Please Select Row To Be Cleared".format(selectedIndex))
        else:
            val = self.VAContents.Item[selectedIndex].grade
            type_val = self.VAContents.Item[selectedIndex]._CurveType
            debug(self, "({},{})".format(val, type_val))

    def valueUpdated(self, sender, e):
        colour_grey = System.Windows.Media.Brushes.LightGray
        colour_black = System.Windows.Media.Brushes.Black
        index = self.input_curveType.SelectedIndex
        if index == 0:
            self.inputText1.Text = "PVI Station Start"
            self.inputText2.Text = "PVI Station End"
            self.inputText3.Text = "PVI Elevation Start"
            self.inputText4.Text = "PVI Elevation End"
            self.inputText5.Text = "Line Slope"
            self.inputText4.Foreground = colour_black
            self.inputValue4.IsReadOnly = False
            self.inputText5.Foreground = colour_black
            self.inputValue5.IsReadOnly = False
        else:
            self.inputText1.Text = "PVI Station"
            self.inputText2.Text = "PVI Elevation"
            self.inputText3.Text = "Curve Length"
            self.inputText4.Foreground = colour_grey
            self.inputValue4.IsReadOnly = True
            self.inputText5.Foreground = colour_grey
            self.inputValue5.IsReadOnly = True
        self.inputValue1.Text = ""
        self.inputValue2.Text = ""
        self.inputValue3.Text = ""
        self.inputValue4.Text = ""
        self.inputValue5.Text = ""

    def input1Updated(self, sender, e):
        index = self.input_curveType.SelectedIndex
        if index == 0:
            colour_grey = System.Windows.Media.Brushes.LightGray
            colour_white = System.Windows.Media.Brushes.White
            value1_count = len(self.inputValue1.Text)
            if value1_count > 0:
                self.inputValue5.IsReadOnly = True
                self.inputValue5.Background = colour_grey
            else:
                self.inputValue5.IsReadOnly = False
                self.inputValue5.Background = colour_white

    def input3Updated(self, sender, e):
        index = self.input_curveType.SelectedIndex
        if index == 0 and sender.IsReadOnly == False:
            colour_grey = System.Windows.Media.Brushes.LightGray
            colour_white = System.Windows.Media.Brushes.White
            value5_count = len(self.inputValue5.Text)
            if value5_count > 0:
                self.inputValue1.IsReadOnly = True
                self.inputValue1.Background = colour_grey
                self.inputValue1.Text = ""
                self.inputValue2.IsReadOnly = True
                self.inputValue2.Background = colour_grey
                self.inputValue2.Text = ""
                self.inputValue3.IsReadOnly = True
                self.inputValue3.Background = colour_grey
                self.inputValue3.Text = ""
                self.inputValue4.IsReadOnly = True
                self.inputValue4.Background = colour_grey
                self.inputValue4.Text = ""
            else:
                self.inputValue1.IsReadOnly = False
                self.inputValue1.Background = colour_white
                self.inputValue2.IsReadOnly = False
                self.inputValue2.Background = colour_white
                self.inputValue3.IsReadOnly = False
                self.inputValue3.Background = colour_white
                self.inputValue4.IsReadOnly = False
                self.inputValue4.Background = colour_white

    def inputValue34Updated(self, sender, e):
        index = self.input_curveType.SelectedIndex
        if index == 0:
            pviStationStart = self.inputValue1.Text
            pviStationEnd = self.inputValue2.Text
            pviElevStart = self.inputValue3.Text
            pviElevEnd = self.inputValue4.Text
            condition = all(
                [
                    pviStationStart.replace(".", "", 1).isdigit(),
                    pviStationEnd.replace(".", "", 1).isdigit(),
                    pviElevStart.replace(".", "", 1).replace("-", "", 1).isdigit(),
                    pviElevEnd.replace(".", "", 1).replace("-", "", 1).isdigit(),
                ]
            )
            debug(self, "{}".format(condition))
            if condition:
                xDist = float(pviStationEnd) - float(pviStationStart)
                yDist = float(pviElevEnd) - float(pviElevStart)
                grade = math.atan(yDist / xDist) * 100
                self.inputValue5.Text = str(grade)

    def selectFile(self, sender, e):
        path = excel.file_picker()

        self.app = excel.initialise()
        self.workbook = self.app.Workbooks.Add(path)
        self.sheet = [st.Name for st in self.workbook.Sheets]

        self.path.Content = "File Path : {}".format(path)
        self.sheetList.ItemsSource = self.sheet

    def importSheetData(self, sender, e):
        selectedSheetIndex = self.sheetList.SelectedIndex
        selectedSheet = self.workbook.Sheets(self.sheet[selectedSheetIndex])

        selectedRange = selectedSheet.UsedRange
        values = []
        rowCnt = selectedRange.Rows.Count
        colCnt = selectedRange.Columns.Count
        range(rowCnt)
        for row_py, row_excel in zip(range(rowCnt), range(1, rowCnt + 1)):
            values.append([])
            for col_excel in range(1, colCnt + 1):
                values[row_py].append(selectedRange.Cells(row_excel, col_excel).Value2)

        if "Vertical" in values[0][0]:
            isVerticalData = True
        else:
            isVerticalData = False

        slope = []
        curveLength = []
        pviElevation = []
        pviStation = []
        seStation = []
        sePercentage = []
        curveType = []

        if isVerticalData:
            for row in range(1, rowCnt):
                if row % 2 == 1:
                    slope.append(values[row][1])
                    curveLength.append(None)
                    pviElevation.append(None)
                    pviStation.append(None)
                    curveType.append("Line")
                else:
                    slope.append(None)
                    curveLength.append(values[row][1])
                    pviElevation.append(values[row][2])
                    pviStation.append(values[row][3])
                    curveType.append("Curve")
                seStation.append(values[row][4])
                sePercentage.append(values[row][5])

            for index in range(len(slope)):
                self.VAContents.Add(
                    verticalAlignmentFormat(
                        index,
                        pviStation[index],
                        pviElevation[index],
                        slope[index],
                        curveType[index],
                        curveLength[index],
                        "",
                    )
                )

            self.stationStart.Text = str(seStation[0])
            self.stationEnd.Text = str(seStation[-1])
            self.debug_external.Text = "{}\n{}".format(
                self.debug_external.Text, "Import Success"
            )
        else:
            self.debug_external.Text = "{}\n{}".format(
                self.debug_external.Text, "Under Develop"
            )

        excel.release(self.app)

    def calculateRows(self, sender, e):
        ss = self.stationStart.Text
        se = self.stationEnd.Text
        if ss != "" and se != "" and float(se) > float(ss):
            self.VC = verticalcurve.VerticalCurve(([float(ss), float(se)]))
            debug(self, "{}is loaded".format(self.VC))
            
            pviElevation = [toFloat(g.pviElevation) for g in self.VAContents]
            curveType = [g._CurveType for g in self.VAContents]
            grade = [toFloat(g.grade) for g in self.VAContents]
            curveLength = [toFloat(g._CurveLength) for g in self.VAContents]
            debug(self, "{} and {}".format(grade, curveLength))
            pviStation = [toFloat(g.pviStation) for g in self.VAContents]
            debug(self, "{}".format(pviStation))
            isValidGrade = self.VC.isValidSlope(grade)
            self.VC.CalculateLineTypeAndK(curveLength, grade)
            k = self.VC._K
            ltype = self.VC._CurveType
            debug(self, "{} and {}".format(grade, isValidGrade))
            debug(self, "{} and {}".format(k, ltype))
            self.VC.CalculateCurveLength(pviStation, curveLength, grade)
            debug(self, "Dummy")
            calculatedCurveLength = self.VC._CurveLength
            debug(self, "{}".format(calculatedCurveLength))
            # try:
            for index in range(self.VAContents.Count):
                self.VAContents[index] = verticalAlignmentFormat(
                    index,
                    pviStation[index], 
                    pviElevation[index],
                    grade[index],
                    curveType[index],
                    calculatedCurveLength[index],
                    k[index]
                )
            
            # self.VC.RangeTypeAtStation(stations, curvelength, accumulationrequired=True)
            # except:
            #     debug(self, "Fail")
        else:
            debug(self, "Check Start and End Stations in General")
    
    def selectRef(self, sender, e):
        # global selectCond
        global _drawingRef
        customizable_event.raise_event(select_element)
        debugHorizontal(self,"slected is {}".format(_drawingRef))
        try:
            opt = DB.Options()
            opt.ComputeReferences = True
            opt.IncludeNonVisibleObjects = False
            opt.View = revit.doc.ActiveView
            geometry = _drawingRef.get_Geometry(opt)
            debugHorizontal(self,"geometry:{}".format(geometry)) 
            for elem in geometry:
                self.objs = elem.GetInstanceGeometry()
            debugHorizontal(self,"objs:{}".format(self.objs))  
            self.layers = []
            for obj in self.objs:
                styleId = obj.GraphicsStyleId
                style = revit.doc.GetElement(styleId)
                try:
                    self.layers.append(style.GraphicsStyleCategory.Name)
                except:
                    self.layers.append(None)
            self.layers = list(set(self.layers))
            self.layerList.ItemsSource = self.layers
            debugHorizontal(self,"layers:{}".format(self.layers))
        except:
            debugHorizontal(self,"Fail")
    
    def setCurve(self, sender, e):
        try:
            index = self.layerList.SelectedIndex
            debugHorizontal(self,"index{}".format(index))
            layers = self.layers
            objs = self.objs
            selectedCurves = []
            hash = []
            for obj in objs:
                styleId = obj.GraphicsStyleId
                style = revit.doc.GetElement(styleId)
                try:
                    if style.GraphicsStyleCategory.Name == layers[index]:
                        selectedCurves.append(obj)
                        hash.append(obj.GetHashCode())
                except:
                    False
            list1, list2 = (list(t) for t in zip(*sorted(zip(hash, selectedCurves))))
            debugHorizontal(self,"curvenumber:{}".format(selectedCurves))
            debugHorizontal(self,"sorted:{}".format(list2))
        except:
            debugHorizontal(self,"Fail")
        



form = form_window("ui.xaml")
