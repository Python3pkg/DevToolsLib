import maya.cmds as cmds

from DTL.api import Enum, apiUtils, BaseDict

SelectionTypes = Enum("Vertex","Edge","Face","UV","VertexFace","Polygon","Object")

#--------------------------------------------------------
#--------------------------------------------------------
class ObjSelData(BaseDict):
    _compPrefixes = {SelectionTypes.Vertex:'vtx',
                     SelectionTypes.Edge:'e',
                     SelectionTypes.Face:'f',
                     SelectionTypes.UV:'map',
                     SelectionTypes.VertexFace:'vtxFace'}
    
    _filterExpandMap = {SelectionTypes.Vertex:31,
                        SelectionTypes.Edge:32,
                        SelectionTypes.Face:34,
                        SelectionTypes.UV:35,
                        SelectionTypes.VertexFace:70}
    
    #--------------------------------------------------------
    def __init__(self, *args, **kwds):
        #For each type of component add list var for it
        for compPrefix in list(ObjSelData._compPrefixes.values()):
            self.__setitem__(compPrefix, [])
        super(ObjSelData, self).__init__(*args, **kwds)
    
    #------------------------------------------------------------
    def serialize(self):
        return (self.add_quotes(self.object),
                self.hilite,
                dict(self),
                self.vtxFaceColorData)
    
    #------------------------------------------------------------
    def deserialize(self, obj='', hilite=False, compData={}, vtxFaceColorData={}):
        apiUtils.synthesize(self, 'object', obj)
        apiUtils.synthesize(self, 'hilite', hilite)
        apiUtils.synthesize(self, 'vtxFaceColorData', vtxFaceColorData)
        if compData:
            self._set_data(data_dict=compData)
    
    #--------------------------------------------------------
    def populateSubSelection(self):
        '''Populates the class with the objects component selection'''
        self._getSelectedComp(SelectionTypes.Vertex)
        self._getSelectedComp(SelectionTypes.Edge)
        self._getSelectedComp(SelectionTypes.Face)
        self._getSelectedComp(SelectionTypes.UV)
        self._getSelectedComp(SelectionTypes.VertexFace)
    
    #--------------------------------------------------------
    def _populateVertColorData(self):
        '''Populates a dictionary of color/alpha key -> vtxFace list'''
        rgbaDict = dict()
        if cmds.listRelatives(self.object,s=1) :
            for vtxFace in self.getVtxFaceList() :
                try:
                    colorList = cmds.polyColorPerVertex(vtxFace,q=1,rgb=1)
                except:
                    cmds.polyColorPerVertex(self.object,rgb=[0,0,0],a=1)
                    colorList = cmds.polyColorPerVertex(vtxFace,q=1,rgb=1)
                alpha = cmds.polyColorPerVertex(vtxFace,q=1,a=1)
                rgba = (colorList[0],colorList[1],colorList[2],alpha[0])
                if rgba not in rgbaDict :
                    rgbaDict[rgba] = []
                rgbaDict[rgba].append(vtxFace)
        self.setVtxFaceColorData(rgbaDict)

    #--------------------------------------------------------
    def _getSelectedComp(self, selType):
        '''Populates a dictionary of selected components of the given type'''
        compType = ObjSelData._filterExpandMap[selType]
        compPrefix = ObjSelData._compPrefixes[selType]
        selectedComp = cmds.filterExpand(ex=1,fp=1,sm=compType) or []
        for comp in selectedComp :
            parent_transform = comp.split('.')[0].rsplit('|',1)[0]
            if parent_transform == self.object :
                compNum = comp.split('[')[-1].split(']')[0]
                self.__getitem__(compPrefix).append(compNum)
            

    #--------------------------------------------------------
    def getDescendents(self, obj=None):
        '''Return a list of all of the objects descendents(without shape nodes)'''
        allChilden = set(cmds.listRelatives(self.object, ad=1, f=1) or [])
        allShapes = set()
        for item in allChilden:
            allShapes.update(cmds.listRelatives(item, s=1, f=1) or [])
        
        return list(allChilden - allShapes)
            
    #--------------------------------------------------------
    def getVtxFaceList(self):
        '''Returns the objects vtxFace list'''
        return list(cmds.ls(cmds.polyListComponentConversion(self.object,tvf=1),l=1,fl=1))
            

#------------------------------------------------------------
#------------------------------------------------------------
class Selection(BaseDict):
    '''Custom Class to handle selection data as well as helper commands to use/parse the selection data'''
    #--------------------------------------------------------
    def __init__(self, *args, **kwds):
        super(Selection, self).__init__(*args, **kwds)

    #--------------------------------------------------------
    def storeSelection(self):
        #Handle Object Selection
        for item in cmds.ls(sl=1,tr=1,l=1):
            obj = ObjSelData(item)
            self.__setitem__(item, obj)
        
        #Handle Component Selection
        for item in cmds.ls(hl=1,l=1):
            obj = ObjSelData(item, hilite=True)
            obj.populateSubSelection()
            self.__setitem__(item, obj)
        
        #Handle Components whose mesh is hilited
        sel_comps = []
        clean_set = set()
        for compType in list(ObjSelData._filterExpandMap.values()):
            sel_comps += cmds.filterExpand(ex=0,fp=1,sm=compType) or []
        for item in sel_comps:
            shape = item.split('.')[0]
            parent = shape.rsplit('|',1)[0]
            clean_set.add(parent)
        for item in list(clean_set) :
            obj = ObjSelData(item, hilite=True)
            obj.populateSubSelection()
            self.__setitem__(item, obj)
        
    
    #--------------------------------------------------------
    def clear(self):
        for key in list(self.keys()):
            self.pop(key, None)

    #--------------------------------------------------------
    def select(self,obj,compType,clearSel=1,addVal=0):
        '''Allow easy reselection of specific selection data'''
        cmds.select(cl=clearSel)
        if self[obj][compType] != None :
            cmds.hilite(obj)
            cmds.select(self[obj][compType],add=addVal)

    #--------------------------------------------------------
    def restoreSelection(self):
        '''Restores the selection back to how it was when the class populated its selection data'''
        cmds.select(cl=1)
        for obj in list(self.keys()):
            cmds.select(obj,add=1)
            self.select(obj, 0, 0, addVal=1)
            self.select(obj, 1, 0, addVal=1)
            self.select(obj, 2, 0, addVal=1)
            self.select(obj, 3, 0, addVal=1)

    #--------------------------------------------------------
    def getFirstMesh(self):
        '''Returns the first mesh it finds in the selection list'''
        for item in list(self.keys()) :
            if cmds.listRelatives(item,s=1) :
                return item

    #--------------------------------------------------------
    def getCompList(self,obj,compIndex=0):
        compList = []
        if self[obj][compIndex] == None : #Return all
            return cmds.ls(obj + "." + self.compPrefixes[compIndex] + '[*]',l=1,fl=1)
        else:
            return self[obj][compIndex]

    #--------------------------------------------------------
    def getCompIndex(self,obj,compIndex=0):
        indexList = []
        if self[obj][compIndex] :
            for comp in self[obj][compIndex] :
                compNum = comp.split('[')[-1].split(']')[0]
                indexList.append(compNum)
        return indexList

    #--------------------------------------------------------
    def getInverseCompIndex(self,obj,compIndex=0):
        indexList = []
        fullCompList = []
        if self[obj][compIndex] :
            fullCompList = cmds.ls(obj + "." + self.compPrefixes[compIndex] + '[*]',l=1,fl=1)
            selCompList = cmds.ls(self[obj][compIndex],l=1,fl=1)
            for comp in [comp for comp in fullCompList if comp not in selCompList ] :
                compNum = comp.split('[')[-1].split(']')[0]
                indexList.append(compNum)

        return indexList