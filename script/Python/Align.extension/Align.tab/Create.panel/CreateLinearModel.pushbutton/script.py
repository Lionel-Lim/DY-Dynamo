import re
from event import CustomizableEvent
import rpw
from rpw import revit, db, ui, DB, UI
from rpw.ui.forms import CheckBox, Separator, Button, FlexForm
from rpw.exceptions import RevitExceptions
from pyrevit.forms import WPFWindow
from System.Collections.ObjectModel import ObservableCollection
from collections import Iterable, defaultdict

__doc__ = "Create Civil Model Along an Alignment"
__title__ = "Linear Modelling"
__author__ = "DY Lim"
__persistentengine__ = True

"""
Global Parameter Start
"""
_cond_alignment = False
_cond_plot = False
_placement_pts = []
alingment, updatedAlignment = False, False
""""
Global Parameter End
"""
"""
General Functions Start
"""
def ft2mm(ft):
    return ft * 304.8

def mm2ft(mm):
    return mm * 0.00328084
    
def Flatten(x):
    if isinstance(x, Iterable):
        return [a for i in x for a in Flatten(i)]
    else:
        return [x]

def sublist(iterable, interval=2, overlap=1):
    # Create list subset ex)[[0,1],[1,2],[2,3]] from [0,1,2,3]
    if interval == 1:
        return False
    placement_pts_set = []
    i = 0
    while(True):
        placement_pts_set.append(iterable[i : i + interval])
        i = i + (interval - overlap)
        if len(iterable) <= i:
            break
    return placement_pts_set[:-1]
"""
General Functions End
"""
##################################################################################################
##################################################################################################
def selectAlignment():
    global alingment, updatedAlignment
    with db.Transaction("selection"):
        ref = ui.Pick.pick_element("Select Alignment Model", False)
        try:
            alingment = revit.doc.GetElement(ref.ElementId)
            updatedAlignment = True
        except:
            updatedAlignment = False

def CreateModels(self, origin, XVec, ZAxis):
    try:
        with db.Transaction("Create Linear Model"):
            Plane = [DB.Plane.CreateByNormalAndOrigin(normal, o) for normal, o in zip(ZAxis, origin)]
            sketchPln = [DB.SketchPlane.Create(revit.doc, p).GetPlaneReference() for p in Plane]
            RefPoints = [DB.PointOnPlane.NewPointOnPlane(revit.doc, sp, o, x.Negate()) for sp, o, x in zip(sketchPln, origin, XVec)]
            symbol = []
            for i in self.SegmentContents:
                if not i.IsExcluded:
                    symbol = self.FamSymbolDic[i.Type]
                    group = i.Group.Split("-")
                    e = DB.AdaptiveComponentInstanceUtils.CreateAdaptiveComponentInstance(revit.doc, symbol) 
                    AdaptivePointIDs = DB.AdaptiveComponentInstanceUtils.GetInstancePlacementPointElementRefIds(e)
                    for g, id in zip(group, AdaptivePointIDs):
                        AdaptivePoint = revit.doc.GetElement(id)
                        AdaptivePoint.SetPointElementReference(RefPoints[int(g)])
        log(self, "Add Family Success")
    except Exception as e:
        UI.TaskDialog.Show("Error", "{}".format(e))

def get_element(of_class, of_category):
    collect = db.Collector(of_class=of_class, of_category=of_category)
    collect_list = collect.get_elements()
    return collect_list

def log(self, line):
    self.Log.Text = "{}\n{}".format(self.Log.Text, line)
    self.Log.ScrollToEnd()


##################################################################################################
##################################################################################################

customizable_event = CustomizableEvent()

class AlignmentPointTableFormat:
    def __init__(self, index, name, station, elevation, slope, id):
        self.Index = index
        self.Name = name
        self.Station = station
        self.Elevation = elevation
        self.Slope = slope
        self.ID = id

class SegmentTableFormat:
    def __init__(self, index, group=None, familytype=None, isexcluded=False, isadded=False, id=None):
        self.Index = index
        self.Group = group
        self.Type = familytype
        self.IsExcluded = isexcluded
        self.IsAdded = isadded
        self.ID = id

# A simple WPF form used to call the ExternalEvent
class form_window(WPFWindow):
    def __init__(self, xaml_file_name):
        WPFWindow.__init__(self, xaml_file_name)
        self.Show()
        FamilySymbols = get_element("FamilySymbol", "OST_GenericModel")
        FamilySymbolName = [symbol.name for symbol in FamilySymbols]
        self.FamSymbolDic = {}
        for symbol, name in zip(FamilySymbols, FamilySymbolName):
            self.FamSymbolDic[name] = symbol.unwrap()
        
        self.AlignmentPointContents = ObservableCollection[object]()
        self.AlignmentPointTable.ItemsSource = self.AlignmentPointContents

        self.SegmentContents = ObservableCollection[object]()
        self.SegmentTable.ItemsSource = self.SegmentContents
        
        self.Show()

        self.FamilyType.ItemsSource = FamilySymbolName
        self.Combo_FamilySymbol.ItemsSource = FamilySymbolName
        log(self, "Ready")

    def NumberValidationTextBox(self, sender, e):
        #Accecpt only Integer
        if re.search("[^0-9.-]+", e.Text):
            e.Handled = True
        else:
            e.Handled = False

    def Clk_SelectAlignment(self, sender, e):
        customizable_event.raise_event(selectAlignment)
        #Log
        log(self, "Revit Object is selected.")

    def Clk_RefreshAlignmentTable(self, sender, e):
        global alingment, updatedAlignment
        self.AlignmentPointContents.Clear()
        if updatedAlignment:
            try:
#################Get All Reference Points
                family = alingment.Symbol.Family
                famdoc = revit.doc.EditFamily(family)
                collector = DB.FilteredElementCollector(famdoc)
                refPoints = collector.OfCategory(DB.BuiltInCategory.OST_ReferencePoints).ToElements()
################Get Name Parameter to display point information to the table
                name = [e.Name.split("/") for e in refPoints if e.Name]
                pointType = list(set([i[1] for i in name]))
                self.PointDic = defaultdict(list)
                for t in pointType:
                    for refpt, n in zip(refPoints, name):
                        if t in n:
                            self.PointDic[t].append([refpt, n])
                self.referenceName = ui.forms.SelectFromList("Select Refernce",pointType)
                selectedPointSet = self.PointDic[self.referenceName]
                self.RefPoint_XVec = []
                self.origin = []
                for ptset in selectedPointSet:
                    self.origin.append(ptset[0].GetCoordinateSystem().Origin)
                    self.RefPoint_XVec.append(ptset[0].GetCoordinateSystem().BasisX.Normalize().Negate())
                    index = self.AlignmentPointContents.Count
                    offset = round(ft2mm(ptset[0].GetCoordinateSystem().Origin.Z) * 0.001, 5)
                    format = AlignmentPointTableFormat(index, ptset[1][1], ptset[1][0], offset, ptset[1][2], ptset[1][-1])
                    self.AlignmentPointContents.Add(format)
################Get 3D Alignment and attrubutes for modelling
                collector = DB.FilteredElementCollector(famdoc)
                lines = collector.OfCategory(DB.BuiltInCategory.OST_Lines).ToElements()
                for line in lines:
                    if line.GeometryCurve.GetType().Name == "HermiteSpline":
                        alignment = line.GeometryCurve
                parameters = [p for p in alignment.Parameters]
                transform_Alignment = []
                for p in parameters:
                    transform_Alignment.append(alignment.ComputeDerivatives(p, False))
                Tangent = []
                self.ZAxis = []
                for t, xvec in zip(transform_Alignment, self.RefPoint_XVec):
                    tangent_temp = t.BasisX.Normalize()
                    self.ZAxis.append(tangent_temp.CrossProduct(xvec.Normalize()))
                    Tangent.append(tangent_temp)
################Close Family Document
                famdoc.Close(False)
                log(self, "Alignment Loaded")
                updatedAlignment = False
            except Exception as e:
                famdoc.Close(False)
                log(self, "Error: {}".format(e))
                return False
    
    def Clk_UpdateSegmentTable(self, sender, e):
        try:
            self.SegmentContents.Clear()
            subSetNum = int(ui.forms.TextInput("Divide List","2", "Group points every (Only Number) :"))
            referencePoints = []
            selectedPointSet = self.PointDic[self.referenceName]
            for ptset in selectedPointSet:
                referencePoints.append(ptset[0])
            if subSetNum == 1:
                UI.TaskDialog.Show("Error", "Divide Number must be more than 1")
                return False
            referencePointsIndex = sublist(range(len(referencePoints)), subSetNum)
            referencePoints = sublist(referencePoints, subSetNum)
            log(self, "{}\n {}\n {}\n".format(referencePoints, referencePointsIndex, selectedPointSet))
            for i in referencePointsIndex:
                index = self.SegmentContents.Count
                gorup = "-".join(str(num) for num in i)
                self.SegmentContents.Add(SegmentTableFormat(index, gorup))
        except Exception as e:
            log(self, "Error : {}".format(e))
    
    def Clk_UpdateTable(self, sender, e):
        try:
            if self.Start.Text == "" or self.End.Text == "":
                self.Start.Text = "0"
                self.End.Text = "{}".format(self.SegmentContents.Count - 1)
            startIndex = int(self.Start.Text)
            endIndex = int(self.End.Text)
            for i in self.SegmentTable.SelectedItems:
                i.Type = self.Combo_FamilySymbol.SelectedValue
            for i in self.SegmentContents:
                if i.IsExcluded == True:
                    i.Type = ""
                if startIndex <= i.Index <= endIndex:
                    i.IsExcluded = False
                else:
                    i.IsExcluded = True
                    i.Type = ""
            #To Refresh Table
            self.SegmentTable.ItemsSource = None        
            self.SegmentTable.ItemsSource = self.SegmentContents
        except Exception as e:
            log(self, "{}".format(e))
    
    def Clk_AddToRevit(self, sender, e):
        try:
            components = [CheckBox('ReverseProfile', 'Reverse Profile?'),Separator(), Button('Select')]
            form = FlexForm('Modelling Configuration', components)
            form.show()
            if form.values["ReverseProfile"]:
                self.RefPoint_XVec = [xvec.Negate() for xvec in self.RefPoint_XVec]
            customizable_event.raise_event(CreateModels, self, self.origin, self.RefPoint_XVec, self.ZAxis)
        except Exception as e:
            log(self, "{}".format(e))

form = form_window("ui.xaml")
if False:
    a = select_element()
    b = set_geometry(a)
    UI.TaskDialog.Show("Stat", "{},{}".format(a, b))
    c = cal_chainage(b)
    UI.TaskDialog.Show("Stat", "{}".format(c))