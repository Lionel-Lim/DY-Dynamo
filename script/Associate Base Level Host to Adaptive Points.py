import clr
clr.AddReference('ProtoGeometry')
from Autodesk.DesignScript import Geometry as geo

# EXTENSION Enable ToDSType
clr.AddReference('RevitNodes')
import Revit
clr.ImportExtensions(Revit.Elements)

# Enable Revit Elements
from Revit.Elements import *

# Enable Revit API
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import *

# Enable DocumentManager and TransactionManager
clr.AddReference('RevitServices')
from RevitServices.Persistence import DocumentManager
from RevitServices.Transactions import TransactionManager


doc = DocumentManager.Instance.CurrentDBDocument
app = doc.Application

#Input
elements=UnwrapElement(IN[0])

#Store IDs of input elements into ref_points list
ref_points = []
for each in elements:
	ref_points_ids = AdaptiveComponentInstanceUtils.GetInstancePlacementPointElementRefIds(each)
	temp = []
	for id in ref_points_ids:
		temp.append(doc.GetElement(id))
	ref_points.append(temp)

#Transaction for NewPointOnPlane and SetPointElementReference
TransactionManager.Instance.EnsureInTransaction(doc)

for each in ref_points:
	for ref_pt in each:
		ref_plane=Plane.CreateByNormalAndOrigin(XYZ(0,0,1),XYZ(0,0,0))
		skp = SketchPlane.Create(doc, ref_plane).GetPlaneReference()
		pts_xyz=ref_pt.GetCoordinateSystem().Origin
		
		check=PointOnPlane.IsValidPlaneReference(doc,skp)
		if check:
			dynpoints = PointOnPlane.NewPointOnPlane(doc,skp,pts_xyz,XYZ(1,0,0))
			ref_pt.SetPointElementReference(dynpoints)
		else:
			OUT="Reference Plane Error"
			
TransactionManager.Instance.TransactionTaskDone()

OUT=elements,ref_points