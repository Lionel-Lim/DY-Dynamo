import CurveProcessor

pt1 = CurveProcessor.VectorEntity(10,50)
pt2 = CurveProcessor.VectorEntity(100,20)
create = CurveProcessor.CreateEntity()
vec = create.Vector_ByTwoPoints(pt1,pt2).normalise()
vec_en = CurveProcessor.VectorEntity(1,2)
print(vec())