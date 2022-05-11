import math

(
    chainage_start,
    chainage_end,
    curve_length,
    pvi_elevation,
    pvi_chainage,
    superelevation,
) = 0

def curve_type(curve_length,superelevation):
    

class vc_dataset:
    def __init__(
        self,
        chainage_start,
        chainage_end,
        curve_length,
        pvi_elevation,
        pvi_chainage,
        superelevation,
    ):
        if len(superelevation) == 2:
            curve_type = "Line"
            val_k = -1
        else:
            curve_type = "Curve"
            val_k = curve_length / abs(superelevation[-1] - superelevation[0])
