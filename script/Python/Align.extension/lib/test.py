# Load the Python Standard and DesignScript Libraries
import sys
import clr
clr.AddReference('ProtoGeometry')
from Autodesk.DesignScript.Geometry import *
sys.path.append('C:\Users\DY\Documents\GitHub\DY-Dynamo\script\Python\Align.extension\lib')

import CurveProcessor as CP

# The inputs to this node will be stored as a list in the IN variables.
dataEnteringNode = IN
isArc = IN[0]
vert3 = IN[1]
vert2 = IN[2]
create = CP.CreateEntity()
data= []
for i in range(len(isArc)):
	if isArc[i]:
		pts = vert3[i]
		data.append(create.ArcByThreePoints(pts[0],pts[2],pts[1]))
	else:
		pts = vert2[i]
		data.append(CP.LineEntity(pts[0],pts[1]))



OUT = data