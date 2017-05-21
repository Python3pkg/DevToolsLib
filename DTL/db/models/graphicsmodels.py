from DTL.qt import QtCore, QtGui
from DTL.qt.QtCore import Qt

#------------------------------------------------------------
#------------------------------------------------------------
class GraphicsItemModel(QtGui.QGraphicsItem):
    unselected_color = QtGui.QColor(100,100,100)
    selected_color = QtGui.QColor(100,250,100)
    #------------------------------------------------------------
    def __init__(self, index, **kwds):
        super(GraphicsItemModel, self).__init__()
        self.index = QtCore.QPersistentModelIndex(index)
        self.rect = QtCore.QRectF(0,0,0,0)
        self.shape = QtGui.QPainterPath()
        self.brush = QtGui.QBrush()
        self.pen = QtGui.QPen()
        self.setFlags(self.ItemIsSelectable | self.ItemIsFocusable)
        self.onInit(**kwds)
        
    #------------------------------------------------------------
    def onInit(self, **kwds):      
        pass
    
    #------------------------------------------------------------
    def getIndex(self, column=0):
        if not self.index.isValid() :
            raise Exception('Persistent Model Index is not Valid!')
        return self.scene().model.index(self.index.row(), column, self.index.parent())        
    
    #------------------------------------------------------------
    def boundingRect(self):
        return self.rect
    
    #------------------------------------------------------------
    def shape(self):
        return self.shape
    
    #------------------------------------------------------------
    def paint(self, painter, option, widget):
        if self.isSelected() :
            self.brush.setColor(self.selected_color)
        else:
            self.brush.setColor(self.unselected_color)            
        painter.setBrush(self.brush)
        painter.setPen(self.pen)
        painter.drawPath(self.shape)
    
    #------------------------------------------------------------
    def data(self, column, role=Qt.DisplayRole):
        if self.scene() is None :
            return QtCore.QVariant()
        
        return self.scene().data(self.getIndex(column), role)
    
    #------------------------------------------------------------
    def setData(self, column, value, role=Qt.EditRole):
        if self.scene() is None :
            return False
        
        self.scene().setData(self.getIndex(column), QtCore.QVariant(value), role)
        

#------------------------------------------------------------
#------------------------------------------------------------
class GraphicsSceneModel(QtGui.QGraphicsScene):
    #------------------------------------------------------------
    def __init__(self, parent=None):
        super(GraphicsSceneModel, self).__init__(parent=parent)
        self.model = None
        
    #------------------------------------------------------------
    def data(self, index, role):
        return self.model.data(index, role)
    
    #------------------------------------------------------------
    def setData(self, index, value, role=Qt.EditRole):
        return self.model.setData(index, value, role)
    
    #------------------------------------------------------------
    def setModel(self, model):
        self.clear()
        self.model = model
        self.populateScene()
        self.disableItems()
    
    #------------------------------------------------------------
    def setSelection(self, index):
        item = self.modelIndexToSceneItem(index)
        if item :
            item.setSelected(True)
    
    #------------------------------------------------------------
    def disableItems(self):
        for item in list(self.items()):
            item.setVisible(False)
            item.setEnabled(False)
    
    #------------------------------------------------------------
    def modelIndexToSceneItem(self, index):
        index = index
        for item in list(self.items()) :
            if self.compareIndexes(index, item.getIndex()) :
                return item
        
        return None
    
    #------------------------------------------------------------
    def compareIndexes(self, index1, index2):
        if not index1.isValid() or not index2.isValid() :
            return False
        if index1.row() != index2.row() :
            return False
        if index1.internalPointer() != index2.internalPointer() :
            return False
        return True
    
    #------------------------------------------------------------
    def insertNode(self, node=None, parent=QtCore.QModelIndex()):
        if parent.isValid() :
            childCount = parent.internalPointer().childCount()
        else:
            childCount = 0
        self.model.insertRows(childCount, 1, parent, node)
        new_index = self.model.index(childCount, 0, parent)
        self.addIndex(new_index, False)
        return new_index
    
    #------------------------------------------------------------
    def removeNode(self, row, parent=QtCore.QModelIndex()):
        if parent.isValid() :
            childCount = parent.internalPointer().childCount()
        else:
            childCount = 0
        
        for i in range(childCount) :
            child_index = self.model.index(i, 0, parent)
            self.removeIndex(child_index)
            self.model.removeRows(i, 1, parent)
    
    #------------------------------------------------------------
    def populateScene(self):
        pass
    
    #------------------------------------------------------------
    def addIndex(self, index):
        pass
    
    #------------------------------------------------------------
    def removeIndex(self, index):
        pass
        