"""
Copyright 2022 Dongyoung Lim

This file is a part of DY Work; you can redistribute it and/or
modify it under the terms of the GNU General Public License
version 2 as published by the Free Software Foundation.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

To receive the latest information, please visit https://github.com/Lionel-Lim.
"""
# coding: utf8


class VerticalCurve:
    def __init__(self, stationrange):
        (
            self._CurveType,
            self._K,
            self._CurveLength,
            self._Group,
            self._Elevation,
            self._slope,
        ) = ([], [], [], [], [], [])
        self._stationStart = stationrange[0]
        self._stationEnd = stationrange[1]

    def accumulate(list):
        total = 0
        for x in list:
            total += x
            yield total

    def isValidSlope(self, slope):
        for index, sl in enumerate(slope):
            if len(slope) % 2 == 0:
                return False
            if index == 0:
                if sl is None:
                    # First Slope must have value. None is not accecptable.
                    return False
                else:
                    validation = True
            if index != (len(slope) - 1):
                if type(slope[index]) == type(slope[index + 1]):
                    # Values in Slope must rotate None and value
                    return False
                else:
                    validation = True
            else:
                validation = True
        return validation

    def isValidStation(self, stations):
        for station in stations:
            if self._stationStart <= station <= self._stationEnd:
                continue
            else:
                return False
        return True

    def CalculateLineTypeAndK(self, curveLength, slope):
        for index, (sl, c_len) in enumerate(zip(slope, curveLength)):
            if sl is not None:
                self._CurveType.append("Line")
                self._K.append(None)
            else:
                self._CurveType.append("Curve")
                self._K.append(c_len / abs(slope[index - 1] - slope[index + 1]))

    def CalculateCurveLength(self, pvistation, curvelength, slope):
        if not self.isValidSlope(slope):
            return False
        self.CalculateLineTypeAndK(curvelength, slope)
        for index, (ct, cl) in enumerate(zip(self._CurveType, curvelength)):
            if index == 0:
                self._CurveLength.append(
                    (pvistation[index + 1] - (curvelength[index + 1] / 2))
                    - self._stationStart
                )
            elif ct == "Curve":
                self._CurveLength.append(cl)
            elif ct == "Line":
                if index == len(curvelength) - 1:
                    self._CurveLength.append(
                        self._stationEnd
                        - (pvistation[index - 1] + (curvelength[index - 1] / 2))
                    )
                else:
                    self._CurveLength.append(
                        (pvistation[index + 1] - (curvelength[index + 1] / 2))
                        - (pvistation[index - 1] + (curvelength[index + 1] / 2))
                    )

    def RangeTypeAtStation(self, stations, curvelength, accumulationrequired=True):
        group = []
        if accumulationrequired:
            accumulatedLength = list(self.accumulate(curvelength))
            accumulatedLength.insert(0, 0)
            accumulatedStation = [
                length + self._stationStart for length in accumulatedLength
            ]
        else:
            accumulatedStation = curvelength
        for station in stations:
            for index, acs in enumerate(accumulatedStation):
                if accumulatedStation[index] <= station < accumulatedStation[index + 1]:
                    group.append(index)
        return group

    def ElevationAtStation(
        self, group, stations, curvetype, curvelength, pvielevation, slope
    ):
        result = []
        accumulatedLength = list(self.accumulate(curvelength))
        accumulatedLength.insert(0, 0)
        accumulatedStation = [
            length + self._stationStart for length in accumulatedLength
        ]
        for g, st in zip(group, stations):
            # Station on Curve
            if curvetype[g] == "Curve":
                g1 = slope[g - 1] * 0.01
                g2 = slope[g + 1] * 0.01
                cl = curvelength[g]
                g1Elevation = pvielevation[g] - ((cl / 2) * g1)
                xDist = st - accumulatedStation[g]
                yDist = (
                    g1Elevation
                    + (g1 * xDist)
                    + (((g2 - g1) * (xDist * xDist)) / (2 * cl))
                )
                result.append(yDist)
                # print("{},{},{},{},{}".format(g1, g2, cl, g1Elevation, xDist))
            # Station on Line
            elif curvetype[g] == "Line":
                if g == 0:
                    g1 = slope[g] * 0.01
                    g1Elevation = pvielevation[g + 1] - (g1 * (curvelength[g + 1] / 2))
                    xDist = accumulatedStation[g + 1] - st
                    yDist = g1Elevation - (g1 * xDist)
                    result.append(yDist)
                    # print("{},{},{}".format(g1, g1Elevation, xDist))
                # This Line is not last one.
                elif g < max(group):
                    g1 = slope[g] * 0.01
                    g1Elevation = pvielevation[g - 1] - (g1 * (curvelength[g - 1] / 2))
                    xDist = accumulatedStation[g + 1] - st
                    yDist = g1Elevation - (g1 * xDist)
                    result.append(yDist)
                    # print("{},{},{}".format(g1, g1Elevation, xDist))
                # This Line is the last one.
                else:
                    g1 = slope[g] * 0.01
                    g1Elevation = pvielevation[g - 1] + (g1 * (curvelength[g - 1] / 2))
                    xDist = st - accumulatedStation[g]
                    yDist = g1Elevation + (g1 * xDist)
                    result.append(yDist)
                    # print("{},{},{}".format(g1, g1Elevation, xDist))
        self._Elevation = result
        self._group = group
        return result

    def SuperElevationAtStation(self, stations, slopeatmark, stationatmark):
        slopes = []
        superElevationGroup = self.RangeTypeAtStation(stations, stationatmark, False)
        for station, seg in zip(stations, superElevationGroup):
            slopes.append(
                slopeatmark[seg]
                + (
                    (slopeatmark[seg + 1] - slopeatmark[seg])
                    / (stationatmark[seg + 1] - stationatmark[seg])
                    * (station - stationatmark[seg])
                )
            )
        self._slope = slopes
        return slopes
