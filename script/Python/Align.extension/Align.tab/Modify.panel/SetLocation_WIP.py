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
    return element_builtInCategory

def pickobject():
    pickedElem=[]
    __window__.Hide()
    pickedRef = uidoc.Selection.PickObjects(ObjectType.Element,'Pick Objects')
    __window__.Show()
    __window__.Topmost = True
    for ref in pickedRef:
        pickedElem.append(doc.GetElement(ref))
    return pickedElem

message("Select element to be reference category.")
obj_categoryTarget = pickobject()
message("Select element to be moved")
obj_toBeMoved = pickobject()
try:
    pts_toBeMoved = [obj.Location.Point for obj in obj_toBeMoved]
except:
    pts_toBeMoved = [obj.Location.Curve for obj in obj_toBeMoved]



filters = [ElementCategoryFilter(bic) for bic in getBuiltInCategory(obj_categoryTarget)]
filter_set = LogicalOrFilter(filters)
refIntersector = ReferenceIntersector(filter_set, FindReferenceTarget.All, currentview)
refIntersector.FindReferencesInRevitLinks = True

for pt in pts_toBeMoved:
    ref = refIntersector.Find(pt,XYZ(0,0,1))
    projectedPts = ref.GetReference().GlobalPoint

# t = Transaction(doc, "Move Object")
# t.Start()

# t.Commit()