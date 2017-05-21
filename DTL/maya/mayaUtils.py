import math, traceback
from functools import partial

import maya.cmds as cmds
import maya.OpenMaya as om

from DTL.gui import guiUtils

#------------------------------------------------------------
def checkSave(self,filePath=''):
    '''Returns bool based on the save state of the maya scene'''
    if filePath == '' :
        filePath = cmds.file(q=True,sn=True)
    saved = cmds.file(q=True,mf=True)
    if saved :
        saved = guiUtils.getConfirmDialog("Your current file contains unsaved changes. Please save the file first.")
    return saved

#------------------------------------------------------------
def toggleIsolateSelected():
    '''Toggles Isolate Selected'''
    cmds.undoInfo(swf=0)
    try:
        panel = cmds.getPanel(wf=1)
        if cmds.isolateSelect(panel,q=1,s=1): 
            cmds.isolateSelect(panel,s=0)
        else :
            cmds.isolateSelect(panel,s=1)
            cmds.isolateSelect(panel,addSelected=1)
    except Exception as e:
        print(e)
    finally:
        cmds.undoInfo(swf=1)

#--------------------------------------------------------
def returnTranslate():
    '''Returns selected objects to their worldspace translation value'''
    sel = selection()

    for item in sel.selection:
        cmds.makeIdentity(item,a=1,t=1,r=1,s=1)
        translate = cmds.xform(item,q=1,ws=1,rp=1)
        cmds.xform(item,ws=1,t=[translate[0]*-1,translate[1]*-1,translate[2]*-1])
        cmds.makeIdentity(item,a=1,t=1,r=1,s=1)
        cmds.xform(item,ws=1,t=translate)

#--------------------------------------------------------
def expandSelection():
    '''Expands current component selection to its max bounds'''
    oldSize = len(cmds.filterExpand(sm=[28,29,31,32,33,34,35]))
    while(1):
        cmds.polySelectConstraint(pp=1,t=0x00100)
        newSize = len(cmds.filterExpand(sm=[28,29,31,32,33,34,35]))
        if oldSize == newSize: break
        oldSize = newSize

#------------------------------------------------------------
def manipMoveToggle():
    '''Toggles the Translate Manip Context Through the useful modes'''
    try:
        if cmds.manipMoveContext('Move',q=1, mode=1 ) == 0:
            cmds.manipMoveContext('Move',e=1,mode=2)
        else:
            cmds.manipMoveContext('Move',e=1,mode=0)
    except Exception as e:
        print(e)

#------------------------------------------------------------
def manipRotateToggle():
    '''Toggles the Rotate Manip Context Through the useful modes'''
    try:
        if cmds.manipRotateContext('Rotate',q=1, mode=1 ) == 0:
            cmds.manipRotateContext('Rotate',e=1,mode=1)
        elif cmds.manipRotateContext('Rotate',q=1, mode=1 ) == 1:
            cmds.manipRotateContext('Rotate',e=1,mode=2)
        else:
            cmds.manipRotateContext('Rotate',e=1,mode=0)
    except Exception as e:
        print(e)

#------------------------------------------------------------
def toggleShadedWireframe():
    pass
#string $currentPanel = `getPanel -wf`;
#int $isolateState = `isolateSelect -q -state $currentPanel`;
    #modelEditor -edit -displayAppearance smoothShaded -activeOnly false -wireframeOnShaded 1 $editor;

#------------------------------------------------------------
def componentWrapper( command ):
    '''Wrapper for mel commands that don't work on components selected across multiple objects'''
    sel = selection()
    for obj in list(sel.selection.keys()) :
        for compList in [compList for compList in sel.selection[obj] if compList != None] :
            try: 
                partial(eval("cmds." + command),*compList)()
            except Exception:
                traceback.print_exc()
                print("Component Wrapper Fail")
    cmds.select(cl=1)

#------------------------------------------------------------
def getFaceArea(faceNum=None):
    '''Uses the Maya API to get the face area of an obj or Face Number of that object that is selected'''
    selection = om.MSelectionList()
    dagPath = om.MDagPath()
    mObj = om.MObject()
    areaParam = om.MScriptUtil()
    areaParam.createFromDouble(0.0)
    areaPtr = areaParam.asDoublePtr()
    area = om.MScriptUtil(areaPtr).asDouble()
    totalFaceArea = 0

    om.MGlobal.getActiveSelectionList( selection );
    selection.getDagPath(0, dagPath )
    selection.getDependNode(0, mObj )
    # Turn the dag node into an iterable mesh object
    iterPolys = om.MItMeshPolygon( dagPath )

    while not iterPolys.isDone():
        # If face flag is set work on that face otherwise find the area of the entire object
        if faceNum == None:
            iterPolys.getArea(areaPtr,om.MSpace.kWorld)
            area = om.MScriptUtil(areaPtr).asDouble()
            totalFaceArea += area # add up the faces to get total area
        else:
            if (iterPolys.index() == faceNum):
                iterPolys.getArea(areaPtr,om.MSpace.kWorld)
                area = om.MScriptUtil(areaPtr).asDouble()
                totalFaceArea = area # use only user specified face for total area

        next(iterPolys)

    return totalFaceArea

#------------------------------------------------------------
def getEdgeLengths(objList):
    edgeLenList = list()
    for edge in cmds.ls(cmds.polyListComponentConversion(objList, te=1),l=1, fl=1):
        edgeLength = getEdgeLength(edge)
        edgeLenList.append((edgeLength,edge))

    return edgeLenList

#------------------------------------------------------------
def getEdgeLength(edge):
    '''Returns the length of a given edge'''
    verts = cmds.ls(cmds.polyListComponentConversion( edge, tv=True), fl=True)
    pos1 = cmds.xform(verts[0], q=True, ws=True, t=True)
    pos2 = cmds.xform(verts[1], q=True, ws=True, t=True)
    #two point distance and pythagoreon calculation
    x = math.fabs(pos1[0] - pos2[0])
    y = math.fabs(pos1[1] - pos2[1])
    z = math.fabs(pos1[2] - pos2[2])
    a = math.sqrt((x*x) + (z*z))
    return math.sqrt((a*a) + (y*y))

# --------------------------------------------------------
def smartNormals(reverse=0):
    '''Changes the vertex normals on a edge by edge basis to that of the larger faces vertex normals'''
    #We start a new undo chunk to capture all the work
    cmds.undoInfo( ock=1 )
    try:
        sel = selection()
        edgeLengthList = getEdgeLengths(list(sel.selection.keys()))
        for key in sorted(edgeLengthList, reverse=1):
            key = key[-1]
            #Find the dag node name to be used in the polyNormalPerVertex command
            dagName = key.split('.')[0]
            cmds.select(dagName)
            vertices = cmds.ls(cmds.polyListComponentConversion(key,tv=1),fl=1)

            #Get the edges faces and check to make sure it finds two otherwise skip it because its a boarder edge
            faces = cmds.ls(cmds.polyListComponentConversion(key,tf=1),fl=1)
            if len(faces) == 2 :
                #Get the area of the two faces to compare their size
                face1Num = int(faces[0].split('[')[-1].split(']')[0])
                area1 = getFaceArea(face1Num)

                face2Num = int(faces[1].split('[')[-1].split(']')[0])
                area2 = getFaceArea(face2Num)
                if area1 > area2 :
                    if reverse:
                        largerFace , smallerFace = face2Num , face1Num
                    else:
                        largerFace , smallerFace = face1Num , face2Num
                else:
                    if reverse:
                        largerFace , smallerFace = face1Num , face2Num
                    else:
                        largerFace , smallerFace = face2Num , face1Num

                print("larger face - " + str(largerFace) + "  || smaller face - " + str(smallerFace))
                #For the two verts attached to the edge set the smaller faces vertex normals to the cooresponding larger faces vertex normals
                #This command is run on the vertex per face so that we can set each one independantly
                #EXAMPLE: We run it on pCube1.vtxFace [0] [1]  which only sets the vertex 0 attached to face 1
                #instead of all the faces vertex 0 is attached to if we used pCube1.vtx[0] as the compoenent
                for vert in vertices :
                    vertNum = int(vert.split('[')[-1].split(']')[0])
                    #Get the larger faces cooresponding vertex normal
                    normal = cmds.polyNormalPerVertex((dagName + '.vtxFace[' + str(vertNum) + '][' + str(largerFace) + ']'),q=1,xyz=1)
                    #Set the smaller faces cooresponding vertex normal
                    cmds.polyNormalPerVertex((dagName + '.vtxFace[' + str(vertNum) + '][' + str(smallerFace) + ']'),xyz=normal)
                    print("cmds.polyNormalPerVertex((" + dagName + '.vtxFace[' + str(vertNum) + '][' + str(smallerFace) + ']),xyz=' + str(normal) + ')')
        sel.restoreSelection()
    except Exception as e:
        traceback.print_exc()
    finally:
        #Don't Forget to close the undo que chunk
        cmds.undoInfo( cck=1 )

#------------------------------------------------------------
def shaderToMesh(faceList, shaderList):
    '''Given Faces and Materials it will return faces that belong to both'''
    matFaces = []
    for shader in shaderList:
        try:
            sg = cmds.listConnections(shader, t='shadingEngine')
        except Exception:
            traceback.print_exc()
            continue
        sgsetfaces = cmds.polyListComponentConversion(cmds.sets(sg, q=1), tf=1)
        sgsetfaces = cmds.ls( sgsetfaces, fl=1 )
        matFaces += sgsetfaces
    bothFaces = [val for val in faceList if val in matFaces]
    return bothFaces

#------------------------------------------------------------
def shaderToMeshSelect():
    '''Logic Wrapper for LBIpy_shaderMesh'''
    matSel = cmds.ls(sl=1, mat=1)
    if not len(matSel):
        cmds.warning("No shaders were selected to find assigned objects.")
        return
    objFaces = cmds.ls(cmds.polyListComponentConversion(cmds.ls(sl=1), tf=1),fl=1)
    if not len(objFaces):
        cmds.warning("No objects or faces were selected to find assigned shaders.")
        return

    bothFaces = shaderToMesh(objFaces,matSel)
    try: cmds.select(bothFaces)
    except: cmds.warning("No faces of your selection were assigned to that shader.")