#Update Topo(Append or Move Point)
#Created By DY Lim - dylim@tssni.com
#Inspired By Karam Baki : karam@aecedx.com

import clr
clr.AddReference('ProtoGeometry')
from Autodesk.DesignScript import Geometry as dg

# EXTENSION Enable ToDSType
clr.AddReference('RevitNodes')
import Revit
clr.ImportExtensions(Revit.Elements)

# Enable Revit Elements
from Revit.Elements import *

# EXTENSION Enable Geometry Conversion Methods
clr.ImportExtensions(Revit.GeometryConversion)

# Enable Revit API
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import *
import Autodesk.Revit.DB
# Enable DocumentManager and TransactionManager
clr.AddReference('RevitServices')
from RevitServices.Persistence import DocumentManager
from RevitServices.Transactions import TransactionManager

# Enable ICollection List Translate
clr.AddReference("System")
import System.Collections.Generic
from System.Collections.Generic import List
doc = DocumentManager.Instance.CurrentDBDocument
uidoc = DocumentManager.Instance.CurrentUIApplication.ActiveUIDocument
uiapp = DocumentManager.Instance.CurrentUIApplication
app = uiapp.Application

class WarnSwallow(IFailuresPreprocessor):
	def PreprocessFailures(self, failuresAccessor):
		failuresAccessor.DeleteAllWarnings()
		return FailureProcessingResult.Continue

def append_point(pts_added,topoid):
    Revit.Transaction.Transaction.End(doc)
    editsession.Start(topoid)
    TransactionManager.Instance.EnsureInTransaction(doc)
    topo.AddPoints(pts_added)
    TransactionManager.Instance.ForceCloseTransaction()
    editsession.Commit(failproc)

def remove_point(pts_removed,topoid):
    Revit.Transaction.Transaction.End(doc)
    editsession.Start(topoid)
    TransactionManager.Instance.EnsureInTransaction(doc)
    topo.DeletePoints(pts_remove)
    TransactionManager.Instance.ForceCloseTransaction()
    editsession.Commit(failproc)

#####################################################################
#Data Input
dataEnteringNode = IN
# Use UnwrapElement(IN[0]) When Translating From Dynamo to Revit
pts_new = [i.ToXyz() for i in UnwrapElement(IN[0])]
pts_remove = [i.ToXyz() for i in UnwrapElement(IN[1])]
topo = UnwrapElement(IN[2])
append_or_move=IN[3]
#Data Input
#####################################################################

#For Topo Edit Scope
failproc = WarnSwallow()
editsession = Architecture.TopographyEditScope(doc,"Main Session")
editsessioncl = Architecture.TopographyEditScope(doc,"Clean Up Session")
topo_id=topo.Id

#append point if true or move point to closest edge point
if append_or_move == True:
    append_point(pts_new,topo_id)
elif append_or_move == False:
    append_point(pts_new,topo_id)
    remove_point(pts_remove,topo_id)

###################
#Data Output
OUT = topo
#Data Output
###################