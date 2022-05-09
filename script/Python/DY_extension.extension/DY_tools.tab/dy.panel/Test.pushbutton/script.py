from Autodesk.Revit.UI import IExternalEventHandler, ExternalEvent
from Autodesk.Revit.Exceptions import InvalidOperationException
from event import CustomizableEvent
import rpw
from rpw import revit, db, ui, DB, UI
from pyrevit.forms import WPFWindow

__doc__ = "A simple modeless form sample"
__title__ = "Modeless Form"
__author__ = "Cyril Waechter"
__persistentengine__ = True

_ready_alignment=False

##################################################################################################
##################################################################################################
def select_element():
    global _val_alignment, _ready_alignment
    _ready_alignment=False
    with db.Transaction("selection"):
        ref=ui.Pick.pick_element("Select Reference").ElementId
        _val_alignment=revit.doc.GetElement(ref)
        _ready_alignment = True
        UI.TaskDialog.Show("Selected Alignment Model","Name is {}".format(_val_alignment.Name))


def set_geometry():
    global _val_alignment
    with db.Transaction('New Point on Plane'):
        #Read data from alignment model for placement
        alignment_3dcrv=[]
        alignment_points=[]
        alignment_lines=[]
        opt = DB.Options()
        opt.ComputeReferences = True
        opt.IncludeNonVisibleObjects = False
        opt.View = revit.doc.ActiveView

        #HermiteSpline - 3D alignment, Point - Placement Point, Line - Direction from Inner to Outer
        alignment_geometry=_val_alignment.get_Geometry(opt)
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
        #Create placement plane and point
        newpoints=[]
        for origin, tangent, dir in zip(alignment_points_coord, alignment_3dcrv_tangent, alignment_lines_dir):
            #Top surface normal vector
            nor=tangent.CrossProduct(dir.Normalize())
            #Create Plane object in Revit by placement point and normal vector
            pln=DB.Plane.CreateByNormalAndOrigin(nor, origin)
            #New Sketchplane and point_on_plane
            skp = DB.SketchPlane.Create(revit.doc, pln).GetPlaneReference()
            newpoints.append(DB.PointOnPlane.NewPointOnPlane(revit.doc,skp,origin,tangent))
        UI.TaskDialog.Show("Selected Alignment Model","Target Alignment is {},{}".format(_val_alignment,newpoints[0]))

##################################################################################################
##################################################################################################

customizable_event = CustomizableEvent()

# A simple WPF form used to call the ExternalEvent
class ModelessForm(WPFWindow):
    def __init__(self, xaml_file_name):
        WPFWindow.__init__(self, xaml_file_name)
        self.simple_text.Text = "Hello World"
        self.Show()

    def select_target(self, sender, e):
        # This Raise() method launch a signal to Revit to tell him you want to do something in the API context
            customizable_event.raise_event(select_element)

    def get_update(self, sender, e):
        if _ready_alignment:
            self.select_button.Content = _val_alignment.Name+".rfa"
        else:
            self.select_button.Content = "Not Selected"
    
    def Execution(self, sender, e):
        customizable_event.raise_event(set_geometry)

# Let's launch our beautiful and useful form !
modeless_form = ModelessForm("ModelessForm.xaml")
