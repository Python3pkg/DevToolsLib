import os
from DTL.qt import QtCore, QtGui

from DTL.api import apiUtils
from DTL.gui.base import BaseGUI


#------------------------------------------------------------
#------------------------------------------------------------
class PropertiesEditor(QtGui.QWidget, BaseGUI):
    #------------------------------------------------------------
    def __init__(self, model=None, proxyModel=None, editors={}, *args, **kwds):
        self._qtclass = QtGui.QWidget
        apiUtils.synthesize(self, 'model', model)
        apiUtils.synthesize(self, 'proxyModel', proxyModel)
        apiUtils.synthesize(self, 'editors', editors)
        apiUtils.synthesize(self, 'busy', False)
        
        BaseGUI.__init__(self, **kwds)
        
        if proxyModel :
            self.setProxyModel(proxyModel)
        elif model :
            self.setModel(model)
    
    #------------------------------------------------------------
    def onFinalize(self):
        self.main_splitter = QtGui.QSplitter()
        
        self.main_splitter.addWidget(self.treeView)
        self.main_splitter.addWidget(self.scrollArea)        
        
        self.mainLayout.addWidget(self.main_splitter)
        self.main_splitter.setSizes([150,250])     
        self.setEditors()
        for key, editor in list(self.editors.items()) :
            self.properties_layout.addWidget(editor)
            editor.setVisible(False)
        
    #------------------------------------------------------------
    def setEditors(self):
        '''For subclass to implement all of the editors'''
        self._editors['Node'] = NodeEditor()
        self._editors['FloatTransformNode'] = FloatTransformNodeEditor()
        self._editors['IntTransformNode'] = IntTransformNodeEditor()
        self._editors['Layer'] = LayerEditor()
        
    #------------------------------------------------------------
    def setProxyModel(self, proxyModel):
        self._proxyModel = proxyModel
        self.treeView.setModel(proxyModel)
        for editor in list(self.editors.values()) :
            editor.setProxyModel(proxyModel)
    
    #------------------------------------------------------------
    def setModel(self, model):
        self._model = model
        self.treeView.setModel(model)
        self.treeView.selectionModel().selectionChanged.connect(self.selectionChanged)
        for editor in list(self.editors.values()) :
            editor.setModel(model)
            
    #------------------------------------------------------------
    def selectionChanged(self):
        if not self.busy:
            self.setBusy(True)

            selectedIndexes = self.treeView.selectionModel().selectedIndexes()
            self.setSelection(selectedIndexes[-1])

            self.setBusy(False)
            
    #------------------------------------------------------------
    def clearSelection(self):
        for editor in list(self.editors.values()):
            editor.setVisible(False)          
    
    #------------------------------------------------------------
    def setSelection(self, index):
        if self.proxyModel is not None :
            index = self.proxyModel.mapToSource(index)

        self.clearSelection()

        node = index.internalPointer()
        if node is None :
            return
        
        for editor in list(self.editors.values()):
            editor.setSelection(index)
            
        for item in node.__class__.__mro__ :
            if not hasattr(item, '__name__') :
                continue
            
            if self.editors.get(item.__name__, False):
                self.editors[item.__name__].setVisible(True)


#------------------------------------------------------------
#------------------------------------------------------------
class Editor(QtGui.QWidget, BaseGUI):
    #------------------------------------------------------------
    def __init__(self, model=None, proxyModel=None, **kwds):
        self._qtclass = QtGui.QWidget       

        apiUtils.synthesize(self, 'model', model)
        apiUtils.synthesize(self, 'proxyModel', proxyModel)
        apiUtils.synthesize(self, 'dataMapper', QtGui.QDataWidgetMapper())        
        #self._dataMapper.setSubmitPolicy(QtGui.QDataWidgetMapper.ManualSubmit)
        
        BaseGUI.__init__(self, **kwds) 
    
    #------------------------------------------------------------
    def setProxyModel(self, proxyModel):
        self._proxyModel = proxyModel
        self.setModel(proxyModel.sourceModel())
    
    #------------------------------------------------------------
    def setModel(self, model):
        self._model = model
        self.dataMapper.setModel(self._model)
        
        self.setMappings()
    
    #------------------------------------------------------------
    def setMappings(self):
        '''For Subclass to implement to map the UI elements to the data'''
        #self.dataMapper.addMapping(self.uiName, 0)
        #self.dataMapper.addMapping(self.uiType, 1)
        pass
        
    #------------------------------------------------------------
    def setSelection(self, index):
        parent = index.parent()
        self.dataMapper.setRootIndex(parent)
        self.dataMapper.setCurrentModelIndex(index)


#------------------------------------------------------------
#------------------------------------------------------------
class NodeEditor(Editor):
    #------------------------------------------------------------
    def __init__(self, *args, **kwds):
        super(NodeEditor, self).__init__(*args, **kwds)
    
    #------------------------------------------------------------
    def setMappings(self):
        self.dataMapper.addMapping(self.prop_name, 0)
        
#------------------------------------------------------------
#------------------------------------------------------------
class FloatTransformNodeEditor(Editor):
    #------------------------------------------------------------
    def __init__(self, *args, **kwds):
        super(FloatTransformNodeEditor, self).__init__(*args, **kwds)
    
    #------------------------------------------------------------
    def setMappings(self):
        self.dataMapper.addMapping(self.prop_x, 1)
        self.dataMapper.addMapping(self.prop_y, 2)
        self.dataMapper.addMapping(self.prop_z, 3)
        

#------------------------------------------------------------
#------------------------------------------------------------
class IntTransformNodeEditor(Editor):
    #------------------------------------------------------------
    def __init__(self, *args, **kwds):
        super(IntTransformNodeEditor, self).__init__(*args, **kwds)
    
    #------------------------------------------------------------
    def setMappings(self):
        self.dataMapper.addMapping(self.prop_x, 1)
        self.dataMapper.addMapping(self.prop_y, 2)
        self.dataMapper.addMapping(self.prop_z, 3)
        
#------------------------------------------------------------
#------------------------------------------------------------
class LayerEditor(Editor):
    #------------------------------------------------------------
    def __init__(self, *args, **kwds):
        super(LayerEditor, self).__init__(*args, **kwds)
    
    #------------------------------------------------------------
    def setMappings(self):
        self.dataMapper.addMapping(self.prop_index, 1)
        

        
if __name__ == '__main__' :
    from DTL.db.models import SceneGraphModel
    from DTL.db.data import Node, FloatTransformNode, IntTransformNode, Layer
    from DTL.gui import Core
    
    root = Layer()
    node1 = Node(name='Node1', parent=root)
    node2 = Node(name='Node2', parent=root)
    layer1 = Layer(name='Layer1', parent=node2)
    node3 = Node(name='Node3', parent=layer1)
    trans1 = FloatTransformNode(name='Trans1', parent=node2)
    trans2 = FloatTransformNode(name='Trans2', parent=trans1)
    trans3 = IntTransformNode(name='Trans3', parent=trans1)
    
    model = SceneGraphModel(root)
    
    propeditor = PropertiesEditor(model=model)
    propeditor.show()
        
    Core.Start()