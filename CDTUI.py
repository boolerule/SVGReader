#!/usr/bin/env python
# encoding: utf-8

import os
import threading
from PyQt5.QtCore import Qt, QUrl, pyqtSignal, QObject
from PyQt5.QtQml import QQmlComponent, QQmlContext
from UM.FlameProfiler import pyqtSlot
from UM.Application import Application
from UM.PluginRegistry import PluginRegistry
from UM.Logger import Logger
from UM.Resources import Resources
import pickle
from UM.i18n import i18nCatalog
i18n_catalog = i18nCatalog('cura')

class CDTUI(QObject):
    __qualname__ = 'CDTUI'
    show_config_ui_trigger = pyqtSignal()
    
    def __init__(self, image_reader):
        super(CDTUI, self).__init__()
        self.image_reader = image_reader
        self._ui_view = None
        self.show_config_ui_trigger.connect(self._actualShowConfigUI)
        self._aspect = 1


        self.closeTopButtonFace = True
        self.reversePathToration = False
        self.splitWord = False
        self.image_color_invert = False
        self._ui_lock = threading.Lock()
        self._cancelled = False
        self._disable_size_callbacks = False
        pkFile = os.path.join(os.path.join(Resources.getStoragePath(Resources.Resources), 'plugins'), 'CDTUI.pk')
        self._pkDat = []
        if os.path.exists(pkFile):
            
            try:
                self._pkDat = pickle.load(open(pkFile, 'rb'))
                if isinstance(self._pkDat, list) and len(self._pkDat) == 6:
                    self.peak_height = self._pkDat[0]
                    self._offset = self._pkDat[1]
                    self._slopeHeight = self._pkDat[2]
                    self.closeTopButtonFace = self._pkDat[3]
                    self.reversePathToration = self._pkDat[4]
                    self.splitWord = self._pkDat[5]
            except:
                None



    
    def setOffsetAndSlopeHeight(self, offset, height):
        self._offset = offset
        self._slopeHeight = height

    
    def getOffset(self):
        return self._offset

    
    def getSlopeHeight(self):
        return self._slopeHeight

    
    def getCancelled(self):
        return self._cancelled

    
    def waitForUIToClose(self):
        self._ui_lock.acquire()
        self._ui_lock.release()

    
    def showConfigUI(self):
        self._ui_lock.acquire()
        self._cancelled = False
        self.show_config_ui_trigger.emit()

    
    def _actualShowConfigUI(self):
        self._disable_size_callbacks = True
        if self._ui_view is None:
            self._createConfigUI()
        self._ui_view.show()
        #self._ui_view.findChild(QObject, 'Offset').setProperty('text', str(self._offset))
        #self._ui_view.findChild(QObject, 'SlopHeight').setProperty('text', str(self._slopeHeight))
        #self._disable_size_callbacks = False
        #self._ui_view.findChild(QObject, 'Peak_Height').setProperty('text', str(self.peak_height))
        #TODO：被屏蔽的待做的功能 单选框
        self._ui_view.findChild(QObject, 'closeTopButtonFace').setProperty('checked', self.closeTopButtonFace)
        #self._ui_view.findChild(QObject, 'reversePathToration').setProperty('checked', self.reversePathToration)
        #self._ui_view.findChild(QObject, 'splitWord').setProperty('checked', self.splitWord)

    
    def _createConfigUI(self):
        if self._ui_view is None:
            Logger.log('d', 'Creating SVGReader CDT UI')
            path = QUrl.fromLocalFile(os.path.join(PluginRegistry.getInstance().getPluginPath('SVGReader'), 'CDTUI.qml'))
            component = QQmlComponent(Application.getInstance()._qml_engine, path)
            self._ui_context = QQmlContext(Application.getInstance()._qml_engine.rootContext())
            self._ui_context.setContextProperty('manager', self)
            self._ui_view = component.create(self._ui_context)
            self._ui_view.setFlags(self._ui_view.flags() & ~(Qt.WindowCloseButtonHint) & ~(Qt.WindowMinimizeButtonHint) & ~(Qt.WindowMaximizeButtonHint))
            self._disable_size_callbacks = False

    
    def onOkButtonClicked(self):
        print ("OK-twosillly")
        self._cancelled = False
        self._ui_view.close()
        self._ui_lock.release()


    onOkButtonClicked = pyqtSlot()(onOkButtonClicked)
    
    def onCancelButtonClicked(self):
        print ("Cance-twosillly")
        self._cancelled = True
        self._ui_view.close()
        self._ui_lock.release()

    onCancelButtonClicked = pyqtSlot()(onCancelButtonClicked)
    
    def onOffsetChanged(self, value):
        if self._ui_view and not (self._disable_size_callbacks):
            if len(value) > 0:
                self._offset = float(value)
            else:
                self._offset = 0
            self._disable_size_callbacks = True
            self._disable_size_callbacks = False

    onOffsetChanged = pyqtSlot(str)(onOffsetChanged)
    
    def onSlopHeightChanged(self, value):
        if self._ui_view and not (self._disable_size_callbacks):
            if len(value) > 0:
                self._slopeHeight = float(value)
            else:
                self._slopeHeight = 0
            self._disable_size_callbacks = True
            self._disable_size_callbacks = False

    onSlopHeightChanged = pyqtSlot(str)(onSlopHeightChanged)
    
    def oncloseTopButtonFaceChanged(self, value):
        self.closeTopButtonFace = value

    oncloseTopButtonFaceChanged = pyqtSlot(bool)(oncloseTopButtonFaceChanged)
    
    def onreversePathTorationChanged(self, value):
        self.reversePathToration = value

    onreversePathTorationChanged = pyqtSlot(bool)(onreversePathTorationChanged)
    
    def onsplitWordChanged(self, value):
        self.splitWord = value

    onsplitWordChanged = pyqtSlot(bool)(onsplitWordChanged)
    
    def onBaseHeightChanged(self, value):
        if len(value) > 0:
            self.base_height = float(value)
        else:
            self.base_height = 0

    onBaseHeightChanged = pyqtSlot(str)(onBaseHeightChanged)
    
    def onPeakHeightChanged(self, value):
        if len(value) > 0:
            self.peak_height = float(value)
        else:
            self.peak_height = 0

    onPeakHeightChanged = pyqtSlot(str)(onPeakHeightChanged)
    
    def onSmoothingChanged(self, value):
        self.smoothing = int(value)

    onSmoothingChanged = pyqtSlot(float)(onSmoothingChanged)
    
    def onImageColorInvertChanged(self, value):
        if value == 1:
            self.image_color_invert = True
        else:
            self.image_color_invert = False

    onImageColorInvertChanged = pyqtSlot(int)(onImageColorInvertChanged)
    #return (None,)
