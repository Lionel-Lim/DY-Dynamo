################PYREVIT PROPERTY##########################
__doc__ = "Set location of an object to a target category"
__title__ = "Set Object Location"
__author__ = "DY Lim"
################PYREVIT PROPERTY##########################

import clr, System, sys
clr.AddReference('revitAPI')
clr.AddReference('revitAPIUI')
from Autodesk.Revit.UI.Selection import ObjectType
from Autodesk.Revit.UI import TaskDialog
from Autodesk.Revit.DB import *
from Autodesk.Revit import Exceptions

app = __revit__.Application
doc = __revit__.ActiveUIDocument.Document
uidoc = __revit__.ActiveUIDocument
currentview=doc.ActiveView
builtInCategory_List = System.Enum.GetValues(BuiltInCategory)

#Convert Object to List[Object]
def tolist(input):
    try:
        input.Count
        return input
    except:
        return [input]

#Revit Popup Message
def message(string):
    dialog = TaskDialog('General Message')
    dialog.MainInstruction = string
    dialog.Show()

#Convert Revit Internal Unit(ft, inch) to Parameter Display Unit
def convertUnit(value, displayunittype):
    UnitUtils.ConvertFromInternalUnits(value, displayunittype)

#Get Built In Category of an input object
def getBuiltInCategory(element):
    element_builtInCategory = []
    for elem in element:
        for bic in builtInCategory_List:
            if "OST_" + elem.Category.Name == bic.ToString():
                element_builtInCategory.append(bic)
                break
            elif bic.value__ == elem.Category.Id.IntegerValue:
                element_builtInCategory.append(bic)
    return element_builtInCategory

#Pick multiple elements(True) or single element(False)
def pickObject(multiple = False):
    pickedElem=[]
    # __window__.Hide()
    try:
        if multiple:
            pickedRef = uidoc.Selection.PickObjects(ObjectType.Element,'Pick Objects')
        else:
            pickedRef = uidoc.Selection.PickObject(ObjectType.Element,'Pick Object')
    except Exceptions.OperationCanceledException:
        print("Pick Object Operation Cenceled")
        sys.exit(1)
    # __window__.Show()
    # __window__.Topmost = True
    pickedRef = tolist(pickedRef)
    for ref in pickedRef:
        pickedElem.append(doc.GetElement(ref))
    return pickedElem

#Turn on SlabShapeEditor and get points. Must be within Transaction.
def getSlabShapeVertex(floor):
    position = []
    editor = floor.SlabShapeEditor
    if editor.IsEnabled == False:
        editor.Enable()
        doc.Regenerate()
    ptsArray = editor.SlabShapeVertices
    for pt in ptsArray:
        position.append(pt.Position)
    return position

#Set slab points height by input offset. SlabShapeEditor must be enabled.
def setSlabShapeVertex(floor, offset):
    editor = floor.SlabShapeEditor
    ptsArray = editor.SlabShapeVertices
    for pt, height in zip(ptsArray, offset):
        editor.ModifySubElement(pt, height)
    return floor

#Get AdaptivePoint(s) of Adaptive Family
def getAdaptivePoint(familyinstance, toxyz):
    isValid = AdaptiveComponentInstanceUtils.IsAdaptiveComponentInstance(familyinstance)
    if isValid:
        ref_points = []
        ids = AdaptiveComponentInstanceUtils.GetInstancePlacementPointElementRefIds(familyinstance)
        for id in ids:
            if toxyz:
                ref_points.append(doc.GetElement(id).GetCoordinateSystem().Origin)
            else:
                ref_points.append(doc.GetElement(id))
        return ref_points
    else:
        return False

#set Location.Curve Type object height.
def setCurveTypeLocation(instance, offset):
    original = instance.Location.Curve.Tessellate()
    newLine = Line.CreateBound(
        XYZ(original[0].X,original[0].Y,offset[0]),
        XYZ(original[1].X,original[1].Y,offset[1])
    )
    instance.Location.Curve = newLine

#set Location.Point Type object height.
def setPointTypeLocation(instance, offset):
    original = instance.Location.Point
    newPoint = XYZ(original.X,original.Y,offset[0])
    instance.Location.Point = newPoint

#Select Target Category Object and Target Object to be moved.
message('Select element to be reference category.')
obj_category = pickObject(False)
message('Select element to be moved')
obj_move = pickObject(True)
selected_id = [i.Id.IntegerValue for i in obj_move]

#########################Main Transaction Start########################
t = Transaction(doc)
t.Start("Align - Set Location")

#Get Location Reference by Type
pts_move = []
for obj in obj_move:
    catName = obj.GetType().Name
    if catName == 'Floor':
        pts_move.append(getSlabShapeVertex(obj))
    elif catName == 'FamilyInstance':
        if AdaptiveComponentInstanceUtils.IsAdaptiveComponentInstance(obj):
            pts_move.append(getAdaptivePoint(obj, True))
        else:
                try:
                    pts_move.append([obj.Location.Point])
                except:
                    pts_move.append(obj.Location.Curve.Tessellate())
    else:
        try:
            pts_move.append([obj.Location.Point])
        except:
            pts_move.append(obj.Location.Curve.Tessellate())

#Set target category filter
filters = [ElementCategoryFilter(bic) for bic in getBuiltInCategory(obj_category)]
filter_set = LogicalOrFilter(filters)
refIntersector = ReferenceIntersector(filter_set, FindReferenceTarget.All, currentview)
refIntersector.FindReferencesInRevitLinks = True

#Project Location Reference to target category to Z direction and find farthest height.
#If there is no projected point, stop running the script and show pop up message.
highestProjection = []
for index, pt_set in enumerate(pts_move):
    highestProjection.append([])
    for pt in pt_set:
        projectedPts = []
        projectedReference = refIntersector.Find(XYZ(pt.X,pt.Y,0),XYZ(0,0,1))
        if len(projectedReference) == 0:
            message("Object must be within the target boundary. {}".format(obj_move[index].Name))
            t.Commit()
            sys.exit(1)
        else:
            for refContext in projectedReference:
                ref = refContext.GetReference()
                if not doc.GetElement(ref.ElementId).Id.IntegerValue in selected_id:
                    projectedPts.append(ref.GlobalPoint)
            # projectedPts = [ref.GetReference().GlobalPoint for ref in projectedReference if not doc.GetElement(ref.ElementId).Id.IntegerValue == ]
            highestProjection[index].append(max([coordinates.Z for coordinates in projectedPts]))

#Set Objects location by projected point
for obj, elevation, pt_move in zip(obj_move,highestProjection, pts_move):
    catName = obj.GetType().Name
    if catName == 'Floor':
        setSlabShapeVertex(obj, elevation)
    elif catName == 'FamilyInstance':
        if AdaptiveComponentInstanceUtils.IsAdaptiveComponentInstance(obj):
            adaptivePoints = getAdaptivePoint(obj, False)
            for point, el, pt in zip(adaptivePoints, elevation, pt_move):
                ElementTransformUtils.MoveElement(doc, point.Id, XYZ(0,0,(-pt.Z)+el))
        elif "LocationCurve" in obj.Location.ToString():
            setCurveTypeLocation(obj,elevation)
        elif "LocationPoint" in obj.Location.ToString():
                setPointTypeLocation(obj, elevation)
        else:
            print("Not Support Type")
    else:
        if "LocationCurve" in obj.Location.ToString():
            setCurveTypeLocation(obj,elevation)
        elif "LocationPoint" in obj.Location.ToString():
                setPointTypeLocation(obj, elevation)
        else:
            print("Not Support Type")

t.Commit()
#########################Main Transaction End########################