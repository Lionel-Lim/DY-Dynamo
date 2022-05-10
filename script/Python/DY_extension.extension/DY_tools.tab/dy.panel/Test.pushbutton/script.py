# from Autodesk.Revit.UI import IExternalEventHandler, ExternalEvent
# from Autodesk.Revit.Exceptions import InvalidOperationException
from event import CustomizableEvent
import rpw
from rpw import revit, db, ui, DB, UI
from pyrevit.forms import WPFWindow
from System.Collections.ObjectModel import ObservableCollection

__doc__ = "A simple modeless form sample"
__title__ = "Modeless Form"
__author__ = "Cyril Waechter"
__persistentengine__ = True

_ready_alignment=False
_placement_pts=[]

##################################################################################################
##################################################################################################
def select_element():
    global _val_alignment, _ready_alignment
    _ready_alignment=False
    with db.Transaction("selection"):
        ref=ui.Pick.pick_element("Select Reference").ElementId
        _val_alignment=revit.doc.GetElement(ref)
        _ready_alignment = True
        # UI.TaskDialog.Show("Selected Alignment Model","Name is {}".format(_val_alignment.Name))

def get_element(of_class,of_category):
    collect=db.Collector(of_class=of_class, of_category=of_category)
    collect_list=collect.get_elements()
    return collect_list

def set_geometry(alignment):
    global _placement_pts, _reference_pts, _HermiteCrv
    with db.Transaction('New Point on Plane'):
        #Read data from alignment model for placement
        _reference_pts=[]
        alignment_3dcrv=[]
        alignment_points=[]
        alignment_lines=[]
        opt = DB.Options()
        opt.ComputeReferences = True
        opt.IncludeNonVisibleObjects = False
        opt.View = revit.doc.ActiveView
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
        _HermiteCrv=alignment_3dcrv[0]
        #Extract line direction from inner to outer and coordinate of points
        alignment_lines_dir=[]
        alignment_points_coord=[]
        for line,pt in zip(alignment_lines,alignment_points):
            alignment_lines_dir.append(line.Direction)
            alignment_points_coord.append(pt.Coord)
            _reference_pts.append(pt.Coord)
        UI.TaskDialog.Show("Selected Alignment Model","Name is {}\n{}".format(_reference_pts[0],type(_reference_pts[0])))
        #Create placement plane and point
        # newpoints=[]
        for origin, tangent, dir in zip(alignment_points_coord, alignment_3dcrv_tangent, alignment_lines_dir):
            #Top surface normal vector
            nor=tangent.CrossProduct(dir.Normalize())
            #Create Plane object in Revit by placement point and normal vector
            pln=DB.Plane.CreateByNormalAndOrigin(nor, origin)
            #New Sketchplane and point_on_plane
            skp = DB.SketchPlane.Create(revit.doc, pln).GetPlaneReference()
            _placement_pts.append(DB.PointOnPlane.NewPointOnPlane(revit.doc,skp,origin,tangent))

def sort_points(pts):
    #Create placement point subset [StartPoint, EndPoint] ex)[[0,1],[1,2],[2,3]] from [0,1,2,3]
    placement_pts_set=[pts[i:i + 2] for i in range(0, len(pts), 1)] #User Input for work range
    return placement_pts_set[:-1]

def place_familyinstance(placement_pts_set,symbol):
    #Create Adaptive instance
    with db.Transaction('Place Family Instances'):
        UI.TaskDialog.Show("Selected Alignment Model","Inputs are {}".format(len(placement_pts_set)))
        i=0
        for pts in placement_pts_set:
            temp=[]
            e=DB.AdaptiveComponentInstanceUtils.CreateAdaptiveComponentInstance(revit.doc,symbol.unwrap())
            adaptive_pts_id=DB.AdaptiveComponentInstanceUtils.GetInstancePlacementPointElementRefIds(e)
            #Get Adaptive point id from Apdative Element
            for id in adaptive_pts_id:
                temp.append(revit.doc.GetElement(id))
            #Set adaptive point elevation and placement plane to be perpendicular to the alignment
            for adaptive_pt,newpt in zip(temp,pts):
                adaptive_pt.SetPointElementReference(newpt)
            
            #############for debug purpose only
            if(i<3):
                i=i+1
            else:
                break
            #############

def cal_chainage(crv):
    tangents=DB.HermiteSplineTangents()
    CtlPts_Zero=[DB.XYZ(CtlPt.X,CtlPt.Y,0) for CtlPt in crv.ControlPoints]
    tangents.StartTangent=DB.XYZ(crv.Tangents[0].X,crv.Tangents[0].Y,0).Normalize()
    tangents.EndTangent=DB.XYZ(crv.Tangents[len(CtlPts_Zero)-1].X,crv.Tangents[len(CtlPts_Zero)-1].Y,0).Normalize()
    spline_zero=DB.HermiteSpline.Create(CtlPts_Zero,False)
    chainage = [ch*3.28084 for ch in spline_zero.Parameters]
    UI.TaskDialog.Show("Selected Alignment Model","Name is {}\n{}".format(chainage[0],chainage[-1]))

def debug(self,line):
    self.debug.Text = "{}\n{}".format(self.debug.Text,line)
    self.debug.ScrollToEnd()
##################################################################################################
##################################################################################################

customizable_event = CustomizableEvent()

class DataModel_Stage1:
    def __init__(self, Alignment_Name, Family_Symbol):
        self.Alignment = Alignment_Name
        self.Family = Family_Symbol

class DataModel_Stage2:
    def __init__(self, Number, ptsX, ptsY, ptsZ):
        self.number = Number
        self.ptsX = ptsX
        self.ptsY = ptsY
        self.ptsZ = ptsZ
        

# A simple WPF form used to call the ExternalEvent
class ModelessForm(WPFWindow):
    def __init__(self, xaml_file_name):
        WPFWindow.__init__(self, xaml_file_name)
        self.symbol_list=get_element('FamilySymbol','OST_GenericModel')
        self.Symbols.ItemsSource=[symbol.name for symbol in self.symbol_list]
        self.Show()
        self.debug.Text = "Initializing Success\nWaiting Task..."

    def select_target(self, sender, e):
        customizable_event.raise_event(select_element)
        #
        debug(self, "Revit Object is selected.")

    def get_update(self, sender, e):
        if _ready_alignment == False:
            alignment_cond="Not Selected"
        else:
            alignment_cond = _val_alignment.Name
        if self.Symbols.SelectedIndex == -1:
            symbol_cond = "Not Selected"
        else:
            symbol_cond = self.Symbols.SelectedValue
        #
        self.datagrid.ItemsSource = [DataModel_Stage1(alignment_cond,symbol_cond)]

    def Create_Points(self, sender, e):
        if _ready_alignment == False or self.Symbols.SelectedIndex == -1:
            self.button_pts.Content = "Fail"
        else:
            cond=customizable_event.raise_event(set_geometry,_val_alignment)
            self.button_pts.Content = "Success{}".format(cond)

    def Plot_Points(self, sender, e):
        global _placement_pts_set
        _placement_pts_set = sort_points(_placement_pts)
        number = range(len(_placement_pts))
        dataset=[DataModel_Stage2(num,pt.X,pt.Y,pt.Z) for num,pt in zip(number,_reference_pts)]
        self.datagrid_pts.ItemsSource = dataset
        #
        cal_chainage(_HermiteCrv)
        debug(self, "Number of points is {}.".format(len(_reference_pts)))


    def Execution2(self, sender, e):
        customizable_event.raise_event(place_familyinstance,_placement_pts_set,self.symbol_list[self.Symbols.SelectedIndex])

# Let's launch our beautiful and useful form !
modeless_form = ModelessForm("ModelessForm.xaml")
