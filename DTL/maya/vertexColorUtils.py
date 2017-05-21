import os, sys, traceback
import maya.cmds as cmds
from functools import partial

#Needs refactoring
from ..utils.funcs import selection

from DTL.api import Safe

"""
#------------------------------------------------------------
def buildChannelMatrixFromUI():
    '''Helper Function to build the channel matrix from the UI'''
    channelMatrix = []

    redMix = (cmds.floatField('CM_red_red',q=1,v=1),cmds.floatField('CM_red_green',q=1,v=1),cmds.floatField('CM_red_blue',q=1,v=1),cmds.floatField('CM_red_alpha',q=1,v=1))
    greenMix = (cmds.floatField('CM_green_red',q=1,v=1),cmds.floatField('CM_green_green',q=1,v=1),cmds.floatField('CM_green_blue',q=1,v=1),cmds.floatField('CM_green_alpha',q=1,v=1))
    blueMix = (cmds.floatField('CM_blue_red',q=1,v=1),cmds.floatField('CM_blue_green',q=1,v=1),cmds.floatField('CM_blue_blue',q=1,v=1),cmds.floatField('CM_blue_alpha',q=1,v=1))
    alphaMix = (cmds.floatField('CM_alpha_red',q=1,v=1),cmds.floatField('CM_alpha_green',q=1,v=1),cmds.floatField('CM_alpha_blue',q=1,v=1),cmds.floatField('CM_alpha_alpha',q=1,v=1))

    channelMatrix = [redMix,greenMix,blueMix,alphaMix]
    return channelMatrix
"""

#------------------------------------------------------------
def vertColorAction(action='apply',rgba=[1,1,1,1],channelMatrix=[],blendMix=None,sel=None):
    '''Wrapper Function to aid in vertex color actions - handles selection data for you to get around memory leak'''

    #cmds.progressWindow( title='Coloring Verts',progress=0,	status='Processing:',isInterruptable=False )
    cmds.undoInfo(openChunk=True)
    if sel == None :
        sel = selection()
    try:
        for obj in list(sel.selection.keys()):
            vertDict = sel.selection[obj][5]
            cmds.polyOptions(obj, cs=1, cm='none')
            progressCount = 1
            #Added the plus one so the dialogue to the user never reaches full  -  its a perception thing
            #cmds.progressWindow(edit=True,max=len(vertDict.keys())+1)
            for colorKey, vertFaceList in list(vertDict.items()):
                #cmds.progressWindow( edit=True, progress=progressCount, status=('Processing - ' + str(len(vertFaceList)) + ' - Vertex Faces'))
                if action == 'apply':
                    vertexColorApply(vertFaceList,rgba[0],rgba[1],rgba[2],rgba[3])
                if action == 'add':
                    vertexColorAdd(vertFaceList,colorKey,rgba[0],rgba[1],rgba[2])
                if action == 'tint':
                    vertexColorTint(vertFaceList,colorKey,rgba[0],rgba[1],rgba[2],rgba[3])
                if action == 'gamma':
                    vertexColorGamma(vertFaceList,colorKey,rgba[0],rgba[1],rgba[2])
                if action == 'blend':
                    if blendMix == None:
                        blendMix = cmds.floatSliderGrp('blendMixSlider',q=1,v=1)
                    vertexColorBlend(vertFaceList,colorKey,rgba[0],rgba[1],rgba[2],blendMix)
                if action == 'average':
                    vertexColorAvg(vertFaceList,colorKey,list(vertDict.keys()))
                if action == 'channel':
                    vertexColorChannelMix(vertFaceList,colorKey,channelMatrix)
                if action == 'channelAlpha':
                    vertexColorChannelMixAlpha(vertFaceList,colorKey,channelMatrix)

                progressCount = progressCount + 1

            cmds.delete(obj,ch=1)
    except Exception:
        traceback.print_exc()
    finally:
        cmds.undoInfo(closeChunk=True)
        #cmds.progressWindow(endProgress=1)



#------------------------------------------------------------
@Safe
def vertexColorApply(vertList=None, red=1, green=1, blue=1, alpha=1 ):
    '''Straight Color/Alpha Apply'''
    if vertList == None or vertList == []:
        return
    bufferSize = 2000
    for begin in range(0, len(vertList), bufferSize):
        vertBatch = vertList[begin: begin+bufferSize]
        cmds.polyColorPerVertex(vertBatch, r=red, g=green, b=blue, a=alpha)

#------------------------------------------------------------
def vertexColorAdd(vertList=None, currentRGBA=None, red=0, green=0, blue=0 ):
    '''Add New Color to Current Color - Alpha Excluded'''
    if currentRGBA == None:
        return

    newR = currentRGBA[0] + red
    newG = currentRGBA[1] + green
    newB = currentRGBA[2] + blue

    vertexColorApply(vertList,newR,newG,newB,currentRGBA[3])

#------------------------------------------------------------
def vertexColorTint(vertList=None, currentRGBA=None, red=1, green=1, blue=1, alpha=1 ):
    '''Multiply New Color to Current Color - Alpha Included'''
    if currentRGBA == None:
        return

    newR = currentRGBA[0]*red
    newG = currentRGBA[1]*green
    newB = currentRGBA[2]*blue
    newA = currentRGBA[3]*alpha

    vertexColorApply(vertList,newR,newG,newB,newA)

#------------------------------------------------------------
def vertexColorGamma(vertList=None, currentRGBA=None, red=2, green=2, blue=2 ):
    '''Multiply New Color Exponetionally to Current Color - Alpha Excluded'''
    if currentRGBA == None:
        return

    newR = currentRGBA[0] ** red
    newG = currentRGBA[1] ** green
    newB = currentRGBA[2] ** blue

    vertexColorApply(vertList,newR,newG,newB,currentRGBA[3])

#------------------------------------------------------------
def vertexColorBlend(vertList=None, currentRGBA=None, red=1, green=1, blue=1, mix=0.5 ):
    '''Blend New Color with Current Color - Alpha Excluded'''
    if currentRGBA == None:
        return

    newR = currentRGBA[0]*(1-mix) + red*mix
    newG = currentRGBA[1]*(1-mix) + green*mix
    newB = currentRGBA[2]*(1-mix) + blue*mix

    vertexColorApply(vertList,newR,newG,newB,currentRGBA[3])

#------------------------------------------------------------
def vertexColorAvg(vertList=None, currentRGBA=None, colorKeyList=None):
    '''Average the Color of the vert list based on the entire obj - Alpha Excluded'''
    if currentRGBA == None:
        return
    if colorKeyList == None:
        return

    vertColorAvg = [0,0,0]
    for colorKey in colorKeyList:
        vertColorAvg[0] += colorKey[0]
        vertColorAvg[1] += colorKey[1]
        vertColorAvg[2] += colorKey[2]

    colorKeyCount = len(colorKeyList)
    newR = vertColorAvg[0]/colorKeyCount
    newG = vertColorAvg[1]/colorKeyCount
    newB = vertColorAvg[2]/colorKeyCount

    vertexColorApply(vertList,newR,newG,newB,currentRGBA[3])


#------------------------------------------------------------
def vertexColorChannelMix(vertList=None, currentRGBA=None, channelMatrix=[[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]]):
    '''Channel Mixes Current Color - Alpha Excluded'''
    if currentRGBA == None:
        return
    try:
        redMix, greenMix, blueMix, alphaMix = channelMatrix
    except:
        raise Exception("Unable to unpack channelMatrix")
    if len(redMix) != 4:
        raise Exception("Must pass a 4-tuple as redMix")
    if len(greenMix) != 4:
        raise Exception("Must pass a 4-tuple as greenMix")
    if len(blueMix) != 4:
        raise Exception("Must pass a 4-tuple as blueMix")

    newR = currentRGBA[0]*redMix[0] + currentRGBA[1]*redMix[1] + currentRGBA[2]*redMix[2]
    newG = currentRGBA[0]*greenMix[0] + currentRGBA[1]*greenMix[1] + currentRGBA[2]*greenMix[2]
    newB = currentRGBA[0]*blueMix[0] + currentRGBA[1]*blueMix[1] + currentRGBA[2]*blueMix[2]

    vertexColorApply(vertList,newR,newG,newB,currentRGBA[3])

#------------------------------------------------------------
def vertexColorChannelMixAlpha(vertList=None, currentRGBA=None, channelMatrix=[[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]] ):
    '''Channel Mixes Current Color - Alpha Included'''
    if currentRGBA == None:
        return
    try:
        redMix, greenMix, blueMix, alphaMix = channelMatrix
    except:
        raise Exception("Unable to unpack channelMatrix")
    if len(redMix) != 4:
        raise Exception("Must pass a 4-tuple as redMix")
    if len(greenMix) != 4:
        raise Exception("Must pass a 4-tuple as greenMix")
    if len(blueMix) != 4:
        raise Exception("Must pass a 4-tuple as blueMix")
    if len(alphaMix) != 4:
        raise Exception("Must pass a 4-tuple as alphaMix")

    newR = currentRGBA[0]*redMix[0] + currentRGBA[1]*redMix[1] + currentRGBA[2]*redMix[2] + currentRGBA[3]*redMix[3]
    newG = currentRGBA[0]*greenMix[0] + currentRGBA[1]*greenMix[1] + currentRGBA[2]*greenMix[2] + currentRGBA[3]*greenMix[3]
    newB = currentRGBA[0]*blueMix[0] + currentRGBA[1]*blueMix[1] + currentRGBA[2]*blueMix[2] + currentRGBA[3]*blueMix[3]
    newA = currentRGBA[0]*alphaMix[0] + currentRGBA[1]*alphaMix[1] + currentRGBA[2]*alphaMix[2] + currentRGBA[3]*alphaMix[3]

    vertexColorApply(vertList,newR,newG,newB,newA)

#------------------------------------------------------------
def toggleVertColor():
    '''Util for toggling the vertex color per obj selected'''
    sel = selection()
    for obj in list(sel.selection.keys()):
        cmds.polyOptions(obj,cs=1-cmds.polyOptions(obj,q=1,cs=1)[0],cm='none')