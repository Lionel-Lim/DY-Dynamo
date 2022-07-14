from math import atan
import math
import re
from event import CustomizableEvent
import rpw
from rpw import revit, db, ui, DB, UI
from rpw.ui.forms import CheckBox, Separator, Button, FlexForm, Label, TextBox
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
class FamOpt1(DB.IFamilyLoadOptions):
    def __init__(self):
        pass
    def OnFamilyFound(self,familyInUse, overwriteParameterValues):
        return True
    def OnSharedFamilyFound(self,familyInUse, source, overwriteParameterValues):
        return True

def selectAlignment():
    global alingment, updatedAlignment
    with db.Transaction("Align - selection"):
        ref = ui.Pick.pick_element("Select Alignment Model", False)
        try:
            alingment = revit.doc.GetElement(ref.ElementId)
            updatedAlignment = True
        except:
            updatedAlignment = False

def createModels(self, origin, XVec, ZAxis, taskName):
    try:
        allsymbol = []
        for i in self.SegmentContents:
            if not i.IsExcluded:
                allsymbol.append(self.FamSymbolDic[i.Type])
        for i in list(set(allsymbol)):
            AddFamilyParameter(i.Family, "AlignID")
        with db.Transaction("Align - Create Linear Model"):
            Plane = [DB.Plane.CreateByNormalAndOrigin(normal, o) for normal, o in zip(ZAxis, origin)]
            sketchPln = [DB.SketchPlane.Create(revit.doc, p).GetPlaneReference() for p in Plane]
            RefPoints = [DB.PointOnPlane.NewPointOnPlane(revit.doc, sp, o, x.Negate()) for sp, o, x in zip(sketchPln, origin, XVec)]
            symbol = []
            createdFamily = []
            selected = ""
            for i in self.SegmentContents:
                if not i.IsExcluded:
                    selected = "{},{}".format(selected, i.Index)
                    symbol = self.FamSymbolDic[i.Type]
                    group = i.Group.Split("-")
                    e = DB.AdaptiveComponentInstanceUtils.CreateAdaptiveComponentInstance(revit.doc, symbol)
                    id = e.UniqueId
                    i.ID = id
                    i.IsAdded = True
                    createdFamily.append(e)
                    for parameter in e.Parameters:
                        if parameter.Definition.Name == "AlignID":
                            parameter.Set("{}/{}".format(i.Group, id))
                    AdaptivePointIDs = DB.AdaptiveComponentInstanceUtils.GetInstancePlacementPointElementRefIds(e)
                    for g, id in zip(group, AdaptivePointIDs):
                        AdaptivePoint = revit.doc.GetElement(id)
                        AdaptivePoint.SetPointElementReference(RefPoints[int(g)])
        index = self.AddedObjectContents.Count
        self.AddedObjectContents.Add(AddedObjectFormat(index, taskName, selected[1:], len(createdFamily)))
        parameters = {}
        familyList = defaultdict(list)
        for i in createdFamily:
            temp = getParameters(i)
            for key, value in temp.items():
                familyList[key].append(value["FamilyName"])
                parameters[key] = value
        self.PTable[taskName] = ObservableCollection[object]()
        for key, value in parameters.items():
            self.PTable[taskName].Add((ParameterTableFormat(index, ','.join(map(str, list(set(familyList[key])))), value["Name"], value["Type"], value["Object"])))
        self.SegmentTable.ItemsSource = None
        self.SegmentTable.ItemsSource = self.SegmentContents
        log(self, "Add Family Success")
    except Exception as e:
        UI.TaskDialog.Show("Error", "{}".format(e))

def AddFamilyParameter(family, name):
    try:
        famdoc = revit.doc.EditFamily(family)
        t = DB.Transaction(famdoc)
        for i in famdoc.FamilyManager.Parameters:
            if name == i.Definition.Name:
                return False
        t.Start("Add Parameter for Internal Use")
        famdoc.FamilyManager.AddParameter(name, DB.BuiltInParameterGroup.PG_TEXT, DB.ParameterType.Text, True)
        t.Commit()
        famdoc.LoadFamily(revit.doc, FamOpt1())
        famdoc.Close(True)
    except Exception as e:
        # if t.GetStatus() == DB.TransactionStatus.Started:
        #     t.Commit()
        UI.TaskDialog.Show("Error", "{}".format(e))

def SetParameter(self, parameterSet):
    try:
        with db.Transaction("Align - Set Parameter"):
            elementIds = {}
            ElemInActiveView = DB.FilteredElementCollector(revit.doc, revit.doc.ActiveView.Id).ToElements()
            for element in ElemInActiveView:
                parameter = element.GetParameters("AlignID")
                if parameter:
                    elementIds[parameter[0].AsString().split("/")[-1]] = element
            for index in self.AddedObjectTable.SelectedItem.Items.split(","):
                element = elementIds[self.SegmentContents.Item[int(index)].ID]
                UI.TaskDialog.Show("Element", "{}".format(element))
                for p in parameterSet:
                    UI.TaskDialog.Show("Element", "{}".format(p))
                    parameter = element.GetParameters(p[0])
                    UI.TaskDialog.Show("Element", "{}".format(parameter))
                    if parameter:
                        try:
                            value = self.parameterSet[p[2]][int(index)]
                        except:
                            value = p[2]
                        # value = convertByType(p[1], value)
                        parameter[0].Set(float(value))
    except Exception as e:
        UI.TaskDialog.Show("Error", "{}".format(e))

def getParameters(family):
    definitions = {i.Id : {"FamilyName" : family.Symbol.Family.Name, "Name": i.Definition.Name, "Type": i.Definition.ParameterType.ToString(), "Object" : i} for i in family.Parameters if i.IsReadOnly == False}
    return definitions

def get_element(of_class, of_category):
    collect = db.Collector(of_class=of_class, of_category=of_category)
    collect_list = collect.get_elements()
    return collect_list

# def convertByType(RevitType, Value):
#     string = []
#     if RevitType in 

def log(self, line):
    self.Log.Text = "{}\n{}".format(self.Log.Text, line)
    self.Log.ScrollToEnd()

def log_p(self, line):
    self.Log_P.Text = "{}\n{}".format(self.Log_P.Text, line)
    self.Log_P.ScrollToEnd()


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

class AddedObjectFormat:
    def __init__(self, index, name, items, total):
        self.Index = index
        self.Name = name
        self.Items = items
        self.Total = total

class ParameterTableFormat:
    def __init__(self, index, familyname, parameter, valuetype, object, isincluded=False, customvalue=None):
        self.Index = index
        self.FamilyName = familyname
        self.Parameter = parameter
        self.ValueType = valuetype
        self.Object = object
        self.IsIncluded = isincluded
        self.CustomValue = customvalue

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

        self.AddedObjectContents = ObservableCollection[object]()
        self.AddedObjectTable.ItemsSource = self.AddedObjectContents

        self.parameterValues = ["Custom", True, False]
        self.PTable = {}

        self.FamilyType.ItemsSource = FamilySymbolName
        self.Combo_FamilySymbol.ItemsSource = FamilySymbolName
        self.Combo_CustomValue.ItemsSource = self.parameterValues
        
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
                self.parameterSet = defaultdict(list)
                for ptset in selectedPointSet:
                    origin = ptset[0].GetCoordinateSystem().Origin
                    self.origin.append(origin)
                    for key, value in self.PointDic.items():
                        if key == self.referenceName:
                            continue
                        else:
                            for v in value:
                                self.parameterSet["DistanceTo{}".format(key)].append(v[0].GetCoordinateSystem().Origin.DistanceTo(origin))
                    self.RefPoint_XVec.append(ptset[0].GetCoordinateSystem().BasisX.Normalize().Negate())
                    index = self.AlignmentPointContents.Count
                    offset = round(ft2mm(ptset[0].GetCoordinateSystem().Origin.Z) * 0.001, 5)
                    format = AlignmentPointTableFormat(index, ptset[1][1], ptset[1][0], offset, ptset[1][2], ptset[1][-1])
                    self.AlignmentPointContents.Add(format)
                #Parameters
                for i in self.AlignmentPointContents:
                    self.parameterSet["Station"].append(i.Station)
                    self.parameterSet["Elevation"].append(i.Elevation)
                    self.parameterSet["Slope(%)"].append(i.Slope)
                    self.parameterSet["Slope(deg)"].append(math.degrees(math.atan(float(i.Slope)/100)))
                for key in self.parameterSet.keys():
                    self.parameterValues.append(key)
                log(self, "Error: {}".format(self.parameterSet["Slope(deg)"]))
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
                self.ZAxis = []
                for t, xvec in zip(transform_Alignment, self.RefPoint_XVec):
                    tangent_temp = t.BasisX.Normalize()
                    self.ZAxis.append(tangent_temp.CrossProduct(xvec.Normalize()))
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
            components = [CheckBox('ReverseProfile', 'Reverse Profile?'),
            Label('Enter Task Name:'), TextBox('TaskName', Text="Batch{}".format(self.AddedObjectContents.Count)),
            Separator(), Button('Select')]
            form = FlexForm('Modelling Configuration', components)
            form.show()
            if form.values["ReverseProfile"]:
                self.RefPoint_XVec = [xvec.Negate() for xvec in self.RefPoint_XVec]
            taskName = form.values["TaskName"]
            self.parameterValues.append(taskName)
            for i in self.AddedObjectContents:
                if i.Items == taskName:
                    UI.TaskDialog.Show("Error", "{} is already in the table.".format(taskName))
                    return False
            customizable_event.raise_event(createModels, self, self.origin, self.RefPoint_XVec, self.ZAxis, taskName)
        except Exception as e:
            log(self, "{}".format(e))
    
    def ViewDetailTable(self, sender, e):
        try:
            Name = self.AddedObjectTable.SelectedItem.Name
            self.ParameterTable.ItemsSource = self.PTable[Name]
        except Exception as e:
            log_p(self, "{}".format(e))
    
    def valueUpdated(self, sender, e):
        try:
            Name = self.ParameterTable.SelectedItem.CustomValue
            if Name == "Custom":
                newvalue = ui.forms.TextInput("SetCustomValue","","Custom Value")
                self.parameterValues.append(newvalue)
                self.Combo_CustomValue.ItemsSource = self.parameterValues

        except Exception as e:
            log_p(self, "{}".format(e))
    
    def Clk_SetParameter(self, sender, e):
        try:
            currentParamTable = self.ParameterTable.ItemsSource
            appliedParameter = []
            for i in currentParamTable:
                if i.IsIncluded:
                    appliedParameter.append([i.Parameter, i.ValueType, i.CustomValue])
            customizable_event.raise_event(SetParameter, self, appliedParameter)
        except Exception as e:
            log_p(self, "{}".format(e))

form = form_window("ui.xaml")
if False:
    a = select_element()
    b = set_geometry(a)
    UI.TaskDialog.Show("Stat", "{},{}".format(a, b))
    c = cal_chainage(b)
    UI.TaskDialog.Show("Stat", "{}".format(c))