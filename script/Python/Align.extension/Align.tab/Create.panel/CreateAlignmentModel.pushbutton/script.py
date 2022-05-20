# from Autodesk.Revit.UI import IExternalEventHandler, ExternalEvent
# from Autodesk.Revit.Exceptions import InvalidOperationException
from event import CustomizableEvent
import rpw
from rpw import revit, db, ui, DB, UI
from rpw.exceptions import RevitExceptions
from pyrevit.forms import WPFWindow
from System.Collections.ObjectModel import ObservableCollection

__doc__ = "Create Civil Model Along an Alignment"
__title__ = "Viaduct Modeling"
__author__ = "DY Lim"
__persistentengine__ = True

_cond_alignment = False
_cond_plot = False
_placement_pts = []

##################################################################################################
##################################################################################################
def select_element():
    global _val_alignment, _cond_alignment
    _cond_alignment = False
    with db.Transaction("selection"):
        ref = ui.Pick.pick_element("Select Reference").ElementId
        _val_alignment = revit.doc.GetElement(ref)
        _cond_alignment = True
        # UI.TaskDialog.Show("Selected Alignment Model","Name is {}".format(_val_alignment.Name))
    return _val_alignment


def get_element(of_class, of_category):
    collect = db.Collector(of_class=of_class, of_category=of_category)
    collect_list = collect.get_elements()
    return collect_list


def set_geometry(alignment):
    global _placement_pts, _reference_pts, _HermiteCrv
    with db.Transaction("New Point on Plane"):
        # Read data from alignment model for placement
        _reference_pts = []
        alignment_3dcrv = []
        alignment_points = []
        alignment_lines = []
        alignment_ellipse = []
        alignment_3dcrv_tangent = []
        opt = DB.Options()
        opt.ComputeReferences = True
        opt.IncludeNonVisibleObjects = False
        opt.View = revit.doc.ActiveView
        # HermiteSpline - 3D alignment, Point - Placement Point, Line - Direction from Inner to Outer
        alignment_geometry = alignment.get_Geometry(opt)
        for item in alignment_geometry:
            geoInst = item
            geoElem = geoInst.GetInstanceGeometry()
            for geoObj in geoElem:
                if "DB.HermiteSpline" in geoObj.GetType().ToString():
                    alignment_3dcrv.append(geoObj)
                if "DB.Point" in geoObj.GetType().ToString():
                    alignment_points.append(geoObj)
                if "DB.Line" in geoObj.GetType().ToString():
                    alignment_lines.append(geoObj)
                if "DB.Ellipse" in geoObj.GetType().ToString():
                    alignment_ellipse.append(geoObj)
        # Process incoming information from alignment model
        # All tangent vector on 3D Alignment
        for ellipse in alignment_ellipse:
            alignment_3dcrv_tangent.append(ellipse.XDirection)
        _HermiteCrv = alignment_3dcrv[0]
        # Extract line direction from inner to outer and coordinate of points
        alignment_lines_dir = []
        alignment_points_coord = []
        for line, pt in zip(alignment_lines, alignment_points):
            alignment_lines_dir.append(line.Direction)
            alignment_points_coord.append(pt.Coord)
            _reference_pts.append(pt.Coord)
        # Create placement plane and point
        for origin, tangent, dir in zip(
            alignment_points_coord, alignment_3dcrv_tangent, alignment_lines_dir
        ):
            # Top surface normal vector
            nor = tangent.CrossProduct(dir.Normalize())
            # Create Plane object in Revit by placement point and normal vector
            pln = DB.Plane.CreateByNormalAndOrigin(nor, origin)
            # New Sketchplane and point_on_plane
            skp = DB.SketchPlane.Create(revit.doc, pln).GetPlaneReference()
            _placement_pts.append(
                DB.PointOnPlane.NewPointOnPlane(revit.doc, skp, origin, tangent)
            )


def split_points(pts):
    # Create placement point subset [StartPoint, EndPoint] ex)[[0,1],[1,2],[2,3]] from [0,1,2,3]
    placement_pts_set = [
        pts[i : i + 2] for i in range(0, len(pts), 1)
    ]  # User Input for work range
    return placement_pts_set[:-1]


def place_familyinstance(placement_pts_set, symbol):
    # Create Adaptive instance
    with db.Transaction("Place Family Instances"):
        UI.TaskDialog.Show(
            "Selected Alignment Model", "Inputs are {}".format(len(placement_pts_set))
        )
        i = 0
        for pts in placement_pts_set:
            temp = []
            e = DB.AdaptiveComponentInstanceUtils.CreateAdaptiveComponentInstance(
                revit.doc, symbol.unwrap()
            )
            adaptive_pts_id = DB.AdaptiveComponentInstanceUtils.GetInstancePlacementPointElementRefIds(
                e
            )
            # Get Adaptive point id from Apdative Element
            for id in adaptive_pts_id:
                temp.append(revit.doc.GetElement(id))
            # Set adaptive point elevation and placement plane to be perpendicular to the alignment
            for adaptive_pt, newpt in zip(temp, pts):
                adaptive_pt.SetPointElementReference(newpt)
            #
            # #############for debug purpose only
            # if i < 10:
            #     i = i + 1
            # else:
            #     break
            # #############


def cal_chainage(crv):
    parameters = crv.Parameters
    ft2mm = 304.8
    parameters_in_mm = [i * ft2mm for i in parameters]
    return parameters_in_mm


def point_index(pts_set, pts_flat):
    index_list = []
    for set_index, pts in enumerate(pts_set):
        index_list.append([])
        for pt in pts:
            for index, check_pt in enumerate(pts_flat):
                if pt == check_pt:
                    index_list[set_index].append(index)
                    break
    # UI.TaskDialog.Show("stat", "{}".format(pts_set[0:10]))
    for index, set in enumerate(index_list):
        index_list[index] = "-".join(str(e) for e in set)
    return index_list


def debug(self, line):
    self.debug.Text = "{}\n{}".format(self.debug.Text, line)
    self.debug.ScrollToEnd()


##################################################################################################
##################################################################################################

customizable_event = CustomizableEvent()


class DataModel_Stage1:
    def __init__(self, Alignment_Name, Family_Symbol):
        self.Alignment = Alignment_Name
        self.Family = Family_Symbol


class DataModel_Stage2:
    def __init__(self, index1, ptsX, ptsY, ptsZ, ch):
        self.index1 = index1
        self.ptsX = ptsX
        self.ptsY = ptsY
        self.ptsZ = ptsZ
        self.ch = ch


class DataModel_Stage3:
    def __init__(self, index2, pts_set):
        self.index2 = index2
        self.pts_set = pts_set


# A simple WPF form used to call the ExternalEvent
class ModelessForm(WPFWindow):
    def __init__(self, xaml_file_name):
        WPFWindow.__init__(self, xaml_file_name)
        self.symbol_list = get_element("FamilySymbol", "OST_GenericModel")
        self.Symbols.ItemsSource = [symbol.name for symbol in self.symbol_list]
        self.datagrid.ItemsSource = [DataModel_Stage1("", "")]
        self.Show()
        self.debug.Text = "Initializing Success\nWaiting Task..."

    def select_target(self, sender, e):
        customizable_event.raise_event(select_element)
        #
        debug(self, "Revit Object is selected.")

    def get_update(self, sender, e):
        if _cond_alignment == False:
            alignment_cond = "Not Selected"
        else:
            alignment_cond = _val_alignment.Name
        if self.Symbols.SelectedIndex == -1:
            cond_symbol = "Not Selected"
        else:
            cond_symbol = self.Symbols.SelectedValue
        #
        self.datagrid.ItemsSource = [DataModel_Stage1(alignment_cond, cond_symbol)]

    def Create_Points(self, sender, e):
        global _cond_plot
        if _cond_alignment == False or self.Symbols.SelectedIndex == -1:
            _cond_plot = False
            debug(self, "Create Point Fail")
        else:
            _cond_plot = True
            customizable_event.raise_event(set_geometry, _val_alignment)
            debug(self, "Create Point Success")

    def Plot_Points(self, sender, e):
        if _cond_plot:
            global _placement_pts_set
            chainage = cal_chainage(_HermiteCrv)
            _placement_pts_set = split_points(_placement_pts)
            ###############First Data Grid##########################################
            index1 = range(len(_placement_pts))
            dataset = [
                DataModel_Stage2(num, pt.X, pt.Y, pt.Z, ch)
                for num, pt, ch in zip(index1, _reference_pts, chainage)
            ]
            self.datagrid_pts.ItemsSource = dataset
            ###############Second Data Grid##########################################
            indices = point_index(_placement_pts_set, _placement_pts)
            index2 = range(len(indices))
            dataset_placement = [
                DataModel_Stage3(ind2, index) for ind2, index in zip(index2, indices)
            ]
            self.datagrid_pts_set.ItemsSource = dataset_placement
            #
            debug(self, "Total Number of Points is {}.".format(len(_reference_pts)))
        else:
            debug(self, "Points are not generated.")

    def Execution2(self, sender, e):
        if self.start.Text.isdigit() and self.end.Text.isdigit():
            start = int(self.start.Text)
            end = int(self.end.Text)
            if start > end or start == end:
                debug(self, "End Is Always Bigger Then Start")
            else:
                pts_WorkRange = _placement_pts_set[start:end]
                customizable_event.raise_event(
                    place_familyinstance,
                    pts_WorkRange,
                    self.symbol_list[self.Symbols.SelectedIndex],
                )
                debug(self, "Success from {} to {}".format(start, end))
        elif self.start.Text.isdigit() or self.end.Text.isdigit():
            debug(self, "Please Put Only Number")


# Let's launch our beautiful and useful form !
modeless_form = ModelessForm("ui.xaml")
if False:
    a = select_element()
    b = set_geometry(a)
    UI.TaskDialog.Show("Stat", "{},{}".format(a, b))
    c = cal_chainage(b)
    UI.TaskDialog.Show("Stat", "{}".format(c))