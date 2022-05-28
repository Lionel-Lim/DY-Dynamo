#Alban de Chasteigner 2020
#twitter : @geniusloci_bim
#geniusloci.bim@gmail.com

import clr
clr.AddReference('RevitAPI')
import Autodesk
from Autodesk.Revit.DB import *

clr.AddReference("RevitServices")
import RevitServices
from RevitServices.Persistence import DocumentManager
from RevitServices.Transactions import TransactionManager
doc = DocumentManager.Instance.CurrentDBDocument

paramName = IN[0]
parameterType = IN[1]
parameterGroup = IN[2]
instance = IN[3]
reporting = IN[4]
dimension = UnwrapElement(IN[5])
famParameter = UnwrapElement(IN[6])

TransactionManager.Instance.EnsureInTransaction(doc)
if famParameter == None:
	if isinstance(parameterGroup, basestring):
		exec("paramGroup = BuiltInParameterGroup.%s" % parameterGroup)
	else:
		paramGroup = parameterGroup
	
	if isinstance(parameterType, basestring):
		exec("paramType = ParameterType.%s" % parameterType)
	else :
		paramType = parameterType
	for name in paramName:
		try:
			familyParam = doc.FamilyManager.AddParameter(name, paramGroup, paramType, instance)
		except:
			True
	if reporting == True:
		doc.FamilyManager.MakeReporting(familyParam)
else:
	familyParam = famParameter

if dimension :
	dimension.FamilyLabel = familyParam
else:
	pass
TransactionManager.Instance.TransactionTaskDone()	
OUT = familyParam.Definition.Name