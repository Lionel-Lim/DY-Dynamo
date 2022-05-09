"""Set Adaptive Point on Floor Reference."""
# coding: utf8

__doc__ = """Set Adaptive Point on Floor Reference."""
__title__ = "SetElevation"
__author__ = "DY Lim"

import clr
import math
clr.AddReference('RevitAPI') 
clr.AddReference('RevitAPIUI') 
from Autodesk.Revit.DB import * 
from Autodesk.Revit.UI.Selection import ObjectType
clr.AddReference("RevitServices")
import RevitServices
from RevitServices.Persistence import DocumentManager

app = __revit__.Application
doc = __revit__.ActiveUIDocument.Document
uidoc = __revit__.ActiveUIDocument
currentview=doc.ActiveView


def tolist(input):
	if isinstance(input,list):
		return input
	else:
		return [input]

def pickobject():
#    __window__.Hide()
    picked = uidoc.Selection.PickObjects(ObjectType.Element,"Pick Ojbects")
#    __window__.Show()
#    __window__.Topmost = True
    for i in picked:
        picked_elements.append(doc.GetElement(i))

picked_elements=[]
pickobject()


ref_points = []
for each in picked_elements:
	ref_points_ids = AdaptiveComponentInstanceUtils.GetInstancePlacementPointElementRefIds(each)
	temp = []
	for id in ref_points_ids:
		temp.append(doc.GetElement(id))
	ref_points.append(temp)

ref_points_xyz=[]
for each in ref_points:
    ref_points_xyz.append([])
    i=0
    for ref_pt in each:
        pts_xyz=ref_pt.GetCoordinateSystem().Origin
        ref_points_xyz[i].append(pts_xyz)

#print(ref_points_xyz)
for index,pts in enumerate(ref_points_xyz):
    for i,pt in enumerate(pts):
        ref_points_xyz[index][i]=pt.Add(XYZ(0,0,100))
#print(ref_points_xyz)


ptsset = []
elem=[]
elems = []
cat=[ElementCategoryFilter(BuiltInCategory.OST_Floors)]
filter = LogicalOrFilter(cat)

ri = ReferenceIntersector(filter,FindReferenceTarget.All,currentview)
ri.FindReferencesInRevitLinks = True
ref_points_xyz
for pts in ref_points_xyz:
    for pt in pts:
        try:
            ref = ri.FindNearest(pt,XYZ(0,0,-1))
        except:
            pass
        if ref == None:
            ptsset.append(None)
            elems.append(None)
        else:
            refel = ref.GetReference()
            linkinstance = doc.GetElement(refel.ElementId)
            try:
                elem = linkinstance.GetLinkDocument().GetElement(refel.LinkedElementId)
                elems.append(elem)
                refp = ref.GetReference().GlobalPoint
                ptsset.append(XYZ(refp.X*1,refp.Y*1,refp.Z*1))
            except:
                elems.append(linkinstance)
                refp = ref.GetReference().GlobalPoint
                ptsset.append(XYZ(refp.X*1,refp.Y*1,refp.Z*1))

tran=Transaction(doc)
tran.Start("SetOffset")

ref_points
i=0
for ref_pts in ref_points:
    for ref_pt in ref_pts:
        param=ref_pt.LookupParameter("Offset")
        param.Set(ptsset[i].Z)
        i=i+1


tran.Commit()

#print(elems,ptsset)