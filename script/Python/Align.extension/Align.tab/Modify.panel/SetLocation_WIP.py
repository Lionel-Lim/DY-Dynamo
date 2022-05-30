import clr, System
clr.AddReference('revitAPI')
clr.AddReference('revitAPIUI')
from Autodesk.Revit.UI.Selection import ObjectType
from Autodesk.Revit.UI import TaskDialog
from Autodesk.Revit.DB import *

app = __revit__.Application
doc = __revit__.ActiveUIDocument.Document
uidoc = __revit__.ActiveUIDocument
currentview=doc.ActiveView
builtInCategory_List = System.Enum.GetValues(BuiltInCategory)

def tolist(input):
    try:
        input.Count
        return input
    except:
        return [input]

def message(string):
    dialog = TaskDialog('General Message')
    dialog.MainInstruction = string
    dialog.Show()

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

def pickObject(multiple):
    pickedElem=[]
    __window__.Hide()
    if multiple:
        pickedRef = uidoc.Selection.PickObjects(ObjectType.Element,'Pick Objects')
    else:
        pickedRef = uidoc.Selection.PickObject(ObjectType.Element,'Pick Object')
    __window__.Show()
    __window__.Topmost = True
    pickedRef = tolist(pickedRef)
    for ref in pickedRef:
        pickedElem.append(doc.GetElement(ref))
    return pickedElem

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

def setSlabShapeVertex(floor, offset):
    editor = floor.SlabShapeEditor
    ptsArray = editor.SlabShapeVertices
    for pt, height in zip(ptsArray, offset):
        editor.ModifySubElement(pt, height)
    return floor

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
    

message('Select element to be reference category.')
obj_category = pickObject(False)
message('Select element to be moved')
obj_move = pickObject(True)

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


filters = [ElementCategoryFilter(bic) for bic in getBuiltInCategory(obj_category)]
filter_set = LogicalOrFilter(filters)
refIntersector = ReferenceIntersector(filter_set, FindReferenceTarget.All, currentview)
refIntersector.FindReferencesInRevitLinks = True

highestProjection = []
for index, pt_set in enumerate(pts_move):
    highestProjection.append([])
    for pt in pt_set:
        projectedReference = refIntersector.Find(pt,XYZ(0,0,1))
        projectedPts = [ref.GetReference().GlobalPoint for ref in projectedReference]
        highestProjection[index].append(max([coordinates.Z for coordinates in projectedPts]))

for obj, elevation, pt_move in zip(obj_move,highestProjection, pts_move):
    catName = obj.GetType().Name
    if catName == 'Floor':
        setSlabShapeVertex(obj, elevation)
    elif catName == 'FamilyInstance':
        if AdaptiveComponentInstanceUtils.IsAdaptiveComponentInstance(obj):
            adaptivePoints = getAdaptivePoint(obj, False)
            for point, el, pt in zip(adaptivePoints, elevation, pt_move):
                ElementTransformUtils.MoveElement(doc, point.Id, XYZ(0,0,(-pt.Z)+el))

t.Commit()