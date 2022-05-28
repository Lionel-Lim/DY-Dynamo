import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import *

clr.AddReference('RevitNodes')

import Revit
clr.ImportExtensions(Revit.GeometryConversion)
clr.ImportExtensions(Revit.Elements)

clr.AddReference('RevitServices')
from RevitServices.Persistence import DocumentManager
from RevitServices.Transactions import TransactionManager

doc = DocumentManager.Instance.CurrentDBDocument


elements_set = IN[0]
epSearch = IN[1]
fpSearch_set = IN[2]

	
for elements, fpSearch in zip(elements_set, fpSearch_set):
	if not isinstance(elements, list):
		elements = [elements]
	if not isinstance(epSearch, list):
		epSearch = [epSearch]
	if not isinstance(fpSearch, list):
		fpSearch = [fpSearch]
	for e in elements:
		e = UnwrapElement(e)
		elemParams = e.Parameters
	
		epNames = []
		fpNames = []
		elemAssoc = []
		famAssoc = []
		
		for ep in elemParams:
			epNames.append(ep.Definition.Name)
			
		epDict = dict(zip(epNames,elemParams))
		elemAssoc = [epDict.get(ep, "none") for ep in epSearch]
		
		famParams = doc.FamilyManager.Parameters
		
		for fp in famParams:
			fpNames.append(fp.Definition.Name)
			
		fpDict = dict(zip(fpNames,famParams))
		famAssoc = [fpDict.get(fp,"none") for fp in fpSearch]
		
	
		TransactionManager.Instance.EnsureInTransaction(doc)
		
		for i,j in zip(elemAssoc,famAssoc):
			try:
				doc.FamilyManager.AssociateElementParameterToFamilyParameter(i, j)
				error_report = "No errors"
				
			except:
				error_report = "can't assign parameter"
		TransactionManager.Instance.TransactionTaskDone()


OUT = elements,error_report