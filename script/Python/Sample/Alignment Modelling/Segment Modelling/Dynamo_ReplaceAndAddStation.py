# Load the Python Standard and DesignScript Libraries
import sys
import clr
clr.AddReference('ProtoGeometry')
from Autodesk.DesignScript.Geometry import *

# The inputs to this node will be stored as a list in the IN variables.
dataEnteringNode = IN
original = IN[0]
add = IN[1]
interval = (original[1] - original[0])*1.5
# Place your code below this line
for a in add:
	candidate=[]
	candidate_index=[]
	for index, o in enumerate(original):
        #Outside of work boundary
		if original[0] > a:
			break
        #if additional station is within work boundary
		elif abs(o - a) < interval:
            #Get distance from candidate to stations
            #if the distance is less than interval
            #Store the value and index to candidate
			candidate.append(abs(o-a))
			candidate_index.append(index)
    #Among the candidate, take the minimum value candidate and replace it to original value
	for index, c in zip(candidate_index, candidate):
		if min(candidate) == c:
			original[index] = a
# Assign your output to the OUT variable.
OUT = original