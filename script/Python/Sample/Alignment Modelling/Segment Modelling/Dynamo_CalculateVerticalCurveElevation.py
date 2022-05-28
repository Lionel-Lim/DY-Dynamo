# Load the Python Standard and DesignScript Libraries
import sys
import clr
clr.AddReference('ProtoGeometry')
from Autodesk.DesignScript.Geometry import *

# The inputs to this node will be stored as a list in the IN variables.
dataEnteringNode = IN
data = IN[0]

for index, item in enumerate(data[1]):
    if data[1][index] == data[1][index+1]:
        range=index+1
        break

# Place your code below this line
length = data[0][0:range]
pviElevation = data[1][0:range]
pviStation = data[2][0:range]
slope = data[3][0:range]
superElevationStation = data[4]
superElevation = data[5]

_stationStart =superElevationStation[0]
_stationEnd = superElevationStation[-1]
_CurveType = []
_CurveLength = []

target = [(item*0.001) + _stationStart for item in IN[1]]

def accumulate(list):
    total = 0
    for x in list:
        total += x
        yield total
            

def RangeTypeAtStation(stations, curvelength, accumulationrequired=True):
    group = []
    if accumulationrequired:
        accumulatedLength = list(accumulate(curvelength))
        accumulatedLength.insert(0, 0)
        accumulatedStation = [length + _stationStart for length in accumulatedLength]
    else:
        accumulatedStation = curvelength
#    return accumulatedStation

    for station in stations:
        for index, acs in enumerate(accumulatedStation):
            if accumulatedStation[index] <= station < accumulatedStation[index + 1]:
                group.append(index)
    return group
    
def ElevationAtStation(group, stations, curvetype, curvelength, pvielevation, slope):
    result = []
    accumulatedLength = list(accumulate(curvelength))
    accumulatedLength.insert(0, 0)
    accumulatedStation = [length + _stationStart for length in accumulatedLength]
    for g, st in zip(group, stations):
        # Station on Curve
        if curvetype[g] == "Curve":
            g1 = slope[g - 1] * 0.01
            g2 = slope[g + 1] * 0.01
            cl = curvelength[g]
            g1Elevation = pvielevation[g] - ((cl / 2) * g1)
            xDist = st - accumulatedStation[g]
            yDist = (g1Elevation + (g1 * xDist) + (((g2 - g1) * (xDist * xDist)) / (2 * cl)))
            result.append(yDist)
        # Station on Line
        elif curvetype[g] == "Line":
            if g == 0:
                g1 = slope[g] * 0.01
                g1Elevation = pvielevation[g + 1] - (g1 * (curvelength[g + 1] / 2))
                xDist = accumulatedStation[g + 1] - st
                yDist = g1Elevation - (g1 * xDist)
                result.append(yDist)
            # This Line is not last one.
            elif g < max(group):
                g1 = slope[g] * 0.01
                g1Elevation = pvielevation[g + 1] - (g1 * (curvelength[g + 1] / 2))
                xDist = accumulatedStation[g + 1] - st
                yDist = g1Elevation - (g1 * xDist)
                result.append(yDist)
            # This Line is the last one.
            else:
                g1 = slope[g] * 0.01
                g1Elevation = pvielevation[g - 1] + (g1 * (curvelength[g - 1] / 2))
                xDist = st - accumulatedStation[g]
                yDist = g1Elevation + (g1 * xDist)
                result.append(yDist)
    return result

def SuperElevationAtStation(stations, slopeatmark, stationatmark):
    slopes = []
    superElevationGroup = RangeTypeAtStation(stations, stationatmark, False)
    for station, seg in zip(stations, superElevationGroup):
        slopes.append(
            slopeatmark[seg] + (
                (slopeatmark[seg + 1] - slopeatmark[seg])
                / (stationatmark[seg + 1] - stationatmark[seg])
                * (station - stationatmark[seg])
            )
        )
    return slopes


for index, (sl, c_len) in enumerate(zip(slope, length)):
    if sl is not None:
        _CurveType.append("Line")
    else:
        _CurveType.append("Curve")

for index, (ct, cl) in enumerate(zip(_CurveType, length)):
    if index == 0:
        _CurveLength.append((pviStation[index + 1] - (length[index + 1] / 2)) - _stationStart)
    elif ct == "Curve":
	    _CurveLength.append(cl)
    elif ct == "Line":
	    if index == len(length) - 1:
	        _CurveLength.append(_stationEnd - (pviStation[index - 1] + (length[index - 1] / 2)))
	    else:
	        _CurveLength.append((pviStation[index + 1] - (length[index + 1] / 2)) - (pviStation[index - 1] + (length[index - 1] / 2)))
group = RangeTypeAtStation(target, _CurveLength)
ydisp = ElevationAtStation(group, target, _CurveType, _CurveLength, pviElevation, slope)
se = SuperElevationAtStation(target,superElevation , superElevationStation)

# Assign your output to the OUT variable.
OUT = ydisp, se