# coding: utf8
import clr
clr.AddReference('System.Windows.Forms')
clr.AddReference('IronPython.Wpf')
import math

from pyrevit import script, forms
xamlfile = script.get_bundle_file('ui.xaml')

from rpw import revit, db, ui, DB, UI
from rpw.exceptions import RevitExceptions
ObjectType=UI.Selection.ObjectType

import wpf
from System import Windows
from System.Collections.ObjectModel import ObservableCollection
##########################################################################
# noinspection PyUnresolvedReferences
from Autodesk.Revit.Exceptions import InvalidOperationException, OperationCanceledException, ArgumentException

class CustomizableEvent:
    def __init__(self):
        """ An instance of this class need to be created before any modeless operation.
        You can then call the raise_event method to perform any modeless operation.
        Any modification to Revit DB need to be performed inside a valid Transaction.
        This Transaction needs to be open inside the function_or_method, NOT before calling raise_event.
        >>> customizable_event = CustomizableEvent()
        >>> customizable_event.raise_event(rename_views, views_and_names)
        """
        # Create an handler instance and his associated ExternalEvent
        custom_handler = _CustomHandler()
        custom_handler.customizable_event = self
        self.custom_event = UI.ExternalEvent.Create(custom_handler)

        # Initialise raise_event variables
        self.function_or_method = None
        self.args = ()
        self.kwargs = {}

    def _raised_method(self):
        """ !!! DO NOT USE THIS METHOD IN YOUR SCRIPT !!!
        Method executed by IExternalEventHandler.Execute when ExternalEvent is raised by ExternalEvent.Raise.
        """
        self.function_or_method(*self.args, **self.kwargs)

    def raise_event(self, function_or_method, *args, **kwargs):
        """
        Method used to raise an external event with custom function and parameters
        Example :
        >>> customizable_event = CustomizableEvent()
        >>> customizable_event.raise_event(rename_views, views_and_names)
        """
        self.args = args
        self.kwargs = kwargs
        self.function_or_method = function_or_method
        self.custom_event.Raise()


class _CustomHandler(UI.IExternalEventHandler):
    """ Subclass of IExternalEventHandler intended to be used in CustomizableEvent class
    Input : function or method. Execute input in a IExternalEventHandler"""
    def __init__(self):
        self.customizable_event = None

    # Execute method run in Revit API environment.
    # noinspection PyPep8Naming, PyUnusedLocal
    def Execute(self, application):
        try:
            self.customizable_event._raised_method()
        except InvalidOperationException:
            # If you don't catch this exeption Revit may crash.
            print("InvalidOperationException catched")

    # noinspection PyMethodMayBeStatic, PyPep8Naming
    def GetName(self):
        return "Execute an function or method in a IExternalHandler"

customizable_event = CustomizableEvent()
###################################################################
def select_element():
	try:
		message="Pick Alignment Model"
		with forms.WarningBar(title=message):
			ref=ui.Pick.pick_element("Select Reference").ElementId
		return revit.doc.GetElement(ref)
	except RevitExceptions.OperationCanceledException:
		UI.TaskDialog.Show("Selected Alignment Model","Fail")
		return False

def set_geometry(alignment):
	with db.Transaction('New Point on Plane'):
		#Read data from alignment model for placement
		alignment_3dcrv=[]
		alignment_points=[]
		alignment_lines=[]

		opt = DB.Options()
		opt.ComputeReferences = True
		opt.IncludeNonVisibleObjects = False
		opt.View = revit.doc.ActiveView
		UI.TaskDialog.Show("Selected Alignment Model","Target Alignment is {}".format(alignment))
			#HermiteSpline - 3D alignment, Point - Placement Point, Line - Direction from Inner to Outer
		alignment_geometry=alignment.get_Geometry(opt)
		for item in alignment_geometry:
			geoInst = item
			geoElem = geoInst.GetInstanceGeometry()
			for geoObj in geoElem:
				if 'DB.HermiteSpline' in geoObj.GetType().ToString():
					alignment_3dcrv.append(geoObj)
				if 'DB.Point' in geoObj.GetType().ToString():
					alignment_points.append(geoObj)
				if 'DB.Line' in geoObj.GetType().ToString():
					alignment_lines.append(geoObj)

		#Process incoming information from alignment model
			#All tangent vector on 3D Alignment
		alignment_3dcrv_tangent=alignment_3dcrv[0].Tangents
			#Extract line direction from inner to outer and coordinate of points
		alignment_lines_dir=[]
		alignment_points_coord=[]
		for line,pt in zip(alignment_lines,alignment_points):
			alignment_lines_dir.append(line.Direction)
			alignment_points_coord.append(pt.Coord)

		# #Create placement plane and point
		newpoints=[]
		for origin, tangent, dir in zip(alignment_points_coord, alignment_3dcrv_tangent, alignment_lines_dir):
			#Top surface normal vector
			nor=tangent.CrossProduct(dir.Normalize())
			#Create Plane object in Revit by placement point and normal vector
			pln=DB.Plane.CreateByNormalAndOrigin(nor, origin)
			#New Sketchplane and point_on_plane
			skp = DB.SketchPlane.Create(revit.doc, pln).GetPlaneReference()
			newpoints.append(DB.PointOnPlane.NewPointOnPlane(revit.doc,skp,origin,tangent))
	#Create placement point subset [StartPoint, EndPoint] ex)[[0,1],[1,2],[2,3]] from [0,1,2,3]
	placement_pts_set=[newpoints[i:i + 2] for i in range(0, len(newpoints), 1)] #User Input for work range
	placement_pts_set=placement_pts_set[:-1]
	newpoints=[]

def get_familysymbol(category):
	collect=db.Collector(of_class="FamilySymbol",of_category=category)
	return collect.get_elements()


class MyWindow(Windows.Window):
	def __init__(self):
		wpf.LoadComponent(self, xamlfile)
		self.alignment_model="none"
		self.family_symbol.ItemsSource=["none"]
		self.placement_pts_set=[]
		self.run_script=False
		self.family_symbol.ItemsSource=get_familysymbol("OST_GenericModel")

	def select_alignment(self, sender, args):
		self.Visibility=self.Visibility.Collapsed
		try:
			picked=select_element()
			alignment_model=revit.doc.GetElement(picked)
			self.alignment_button.Content=alignment_model.Name
			self.alignment_model=alignment_model
		except:
			self.alignment_button.Content="Please Restart The App"
		self.Visibility=self.Visibility.Visible
		self.Topmost = True

	def place_family(self, sender, args):
		self.Visibility=self.Visibility.Collapsed
		#self.datacontent = ObservableCollection[object]()
		alignment=select_element()
		UI.TaskDialog.Show("Selected Alignment Model","first{}".format(alignment))
		a=customizable_event.raise_event(set_geometry,alignment)
		#get_geometry(self.alignment_model)
		UI.TaskDialog.Show("Selected Alignment Model","second{}".format(a))
		self.Visibility=self.Visibility.Visible

MyWindow().ShowDialog()







# win=MyWindow()
# win.ShowDialog()
# name=win.alignment.Name
# UI.TaskDialog.Show("Selected Alignment Model","Target Alignment is {}".format(name))
# alignment=win.alignment_model
# symbol=win.family_symbol.SelectedItem

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
# 		if(i<3):
# 			i=i+1
# 		else:
# 			break
# 		#############

