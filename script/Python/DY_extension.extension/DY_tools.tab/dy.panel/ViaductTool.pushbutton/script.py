#############For Dyanmo only
import sys
#rpw_path = IN[0]
# Or any location where rpw.zip is stored.
#sys.path.append(rpw_path)
#############
import clr
clr.AddReference('System.Windows.Forms')
clr.AddReference('IronPython.Wpf')
import math

from pyrevit import script
xamlfile = script.get_bundle_file('ui.xaml')

from rpw import revit, db, ui, DB, UI
ObjectType=UI.Selection.ObjectType

import wpf
from System import Windows

###################################################################
class MyWindow(Windows.Window):
	def __init__(self):
		wpf.LoadComponent(self, xamlfile)
		self.alignment="none"
	def select_alignment(self, sender, args):
		self.Visibility=self.Visibility.Collapsed
		try:
			#global alignment
			picked=ui.selection.PickObject(ObjectType.Element)
			alignment=revit.doc.GetElement(picked)
			self.alignment_button.Content=alignment.Name
		except:
			self.alignment_button.Content="Please Restart The App"
		self.alignment=alignment
		self.Visibility=self.Visibility.Visible

win=MyWindow()
win.ShowDialog()
name=win.alignment.Name
UI.TaskDialog.Show("Hello","this {}".format(name))
#alignment=MyWindow.alignment

# #Select Alignment model and get sub elements in alignment instance
# #def pickobject():
# #	__window__.Hide()
# #	picked=ui.selection.PickElementsByRectangle()
# #	__window__.Show()
# #	__window__.Topmost=True
# #	return picked

# #alignment=pickobject()[0]

# #Read data from alignment model for placement
# alignment_3dcrv=[]
# alignment_points=[]
# alignment_lines=[]

# opt = DB.Options()
# opt.ComputeReferences = True
# opt.IncludeNonVisibleObjects = False
# opt.View = revit.doc.ActiveView
# 	#HermiteSpline - 3D alignment, Point - Placement Point, Line - Direction from Inner to Outer
# alignment_geometry=alignment.get_Geometry(opt)
# for item in alignment_geometry:
#     geoInst = item
#     geoElem = geoInst.GetInstanceGeometry()
#     for geoObj in geoElem:
#         if 'DB.HermiteSpline' in geoObj.GetType().ToString():
#             alignment_3dcrv.append(geoObj)
#         if 'DB.Point' in geoObj.GetType().ToString():
#             alignment_points.append(geoObj)
#         if 'DB.Line' in geoObj.GetType().ToString():
#             alignment_lines.append(geoObj)

# #Process incoming information from alignment model
# 	#All tangent vector on 3D Alignment
# alignment_3dcrv_tangent=alignment_3dcrv[0].Tangents
# 	#Extract line direction from inner to outer and coordinate of points
# alignment_lines_dir=[]
# alignment_points_coord=[]
# for line,pts in zip(alignment_lines,alignment_points):
# 	alignment_lines_dir.append(line.Direction)
# 	alignment_points_coord.append(pts.Coord)

# #Find Adaptive Family Symbol
# symbolName='N111_Viaduct_DoubleCell_General_R20' #User Input
# collect=db.Collector(of_category='OST_GenericModel')
# collect=db.Collector(of_class='FamilySymbol')
# collect_list=collect.get_elements()
# for item in collect_list:
# 		if symbolName in item.name:
# 			symbol=item

# #Create placement plane and point
# newpoints=[]
# with db.Transaction('New Point on Plane'):
# 	for origin, tangent, dir in zip(alignment_points_coord, alignment_3dcrv_tangent, alignment_lines_dir):
# 		#Top surface normal vector
# 		nor=tangent.CrossProduct(dir.Normalize())
# 		#Create Plane object in Revit by placement point and normal vector
# 		pln=DB.Plane.CreateByNormalAndOrigin(nor, origin)
# 		#New Sketchplane and point_on_plane
# 		skp = DB.SketchPlane.Create(revit.doc, pln).GetPlaneReference()
# 		newpoints.append(DB.PointOnPlane.NewPointOnPlane(revit.doc,skp,origin,tangent))
# #Create placement point subset [StartPoint, EndPoint] ex)[[0,1],[1,2],[2,3]] from [0,1,2,3]
# placement_pts_set=[newpoints[i:i + 2] for i in range(0, len(newpoints), 1)] #User Input for work range
# placement_pts_set=placement_pts_set[:-1]
# newpoints=[]

# #Create Adaptive instance
# with db.Transaction('New Adaptive'):
# 	i=0
# 	for pts in placement_pts_set:
# 		temp=[]
# 		e=DB.AdaptiveComponentInstanceUtils.CreateAdaptiveComponentInstance(revit.doc,symbol.unwrap())
# 		adaptive_pts_id=DB.AdaptiveComponentInstanceUtils.GetInstancePlacementPointElementRefIds(e)
# 		#Get Adaptive point id from Apdative Element
# 		for id in adaptive_pts_id:
# 			temp.append(revit.doc.GetElement(id))
# 		#Set adaptive point elevation and placement plane to be perpendicular to the alignment
# 		for adaptive_pt,newpt in zip(temp,pts):
# 			adaptive_pt.SetPointElementReference(newpt)
		
# 		#############for debug purpose only
# 		if(i<10):
# 			i=i+1
# 		else:
# 			break
# 		#############
		
# #############For Dyanmo only
# #OUT=e
# #############