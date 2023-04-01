# Copyright (c) 2020 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import os
import threading

from PyQt6.QtCore import Qt, pyqtSignal, QObject
from UM.FlameProfiler import pyqtSlot
from UM.Application import Application
from UM.PluginRegistry import PluginRegistry
from UM.Logger import Logger
from UM.Resources import Resources
import pickle
from UM.i18n import i18nCatalog
catalog = i18nCatalog("cura")


class SVGReaderUI(QObject):
    show_config_ui_trigger = pyqtSignal()

    def __init__(self, image_reader):
        super(SVGReaderUI, self).__init__()
        self.image_reader = image_reader
        self._ui_view = None
        self.show_config_ui_trigger.connect(self._actualShowConfigUI)
        self.default_offset = 0
        self.default_slopeHeight = 0
        self._aspect = 1
        self._offset = self.default_offset
        self._slopeHeight = self.default_slopeHeight
        self.base_height = 1
        self.peak_height = 30
        self.smoothing = 1
        self.closeTopButtonFace = True
        self.reversePathToration = False
        self.splitWord = False
        self.image_color_invert = False
        self._ui_lock = threading.Lock()
        self._cancelled = False
        self._disable_size_callbacks = False
        pkFile = os.path.join(os.path.join(Resources.getStoragePath(Resources.Resources), 'plugins'), 'VectorReaderUI.pk')
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
                self._pkDat = [30,0,0,1,1,1]
                pass
        else:
            # pkFile = os.path.join(os.path.join(Resources.getStoragePath(Resources.Resources), 'plugins'),'VectorReaderUI.pk')
            # print('pkFile:', pkFile)
            # pickle.dump(self._pkDat, open(pkFile, 'wb'))
            self._pkDat = [30, 0, 0, 1, 1, 1]
            #print("不存在")



    
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
        # self._ui_view.findChild(QObject, 'Offset').setProperty('text', str(self._offset))
        # self._ui_view.findChild(QObject, 'SlopHeight').setProperty('text', str(self._slopeHeight))
        # self._disable_size_callbacks = False
        self._ui_view.findChild(QObject, 'Peak_Height').setProperty('text', str(self.peak_height))
        #TODO：被屏蔽的待做的功能 单选框
        #self._ui_view.findChild(QObject, 'closeTopButtonFace').setProperty('checked', self.closeTopButtonFace)
        #self._ui_view.findChild(QObject, 'reversePathToration').setProperty('checked', self.reversePathToration)
        #self._ui_view.findChild(QObject, 'splitWord').setProperty('checked', self.splitWord)

    def _createConfigUI(self):
        if self._ui_view is None:
            Logger.log("d", "Creating SVGReader config UI")
            path = os.path.join(PluginRegistry.getInstance().getPluginPath("SVGReader"), "ConfigUI.qml")
            self._ui_view = Application.getInstance().createQmlComponent(path, {"manager": self})
            self._ui_view.setFlags(self._ui_view.flags() & ~Qt.WindowType.WindowCloseButtonHint & ~Qt.WindowType.WindowMinimizeButtonHint & ~Qt.WindowType.WindowMaximizeButtonHint)
            self._disable_size_callbacks = False

    @pyqtSlot()
    def onOkButtonClicked(self):
        self._cancelled = False
        self._ui_view.close()
        try:
            self._ui_lock.release()
        except RuntimeError:
        # We don't really care if it was held or not. Just make sure it's not held now
            pass
        pkFile = os.path.join(os.path.join(Resources.getStoragePath(Resources.Resources), 'plugins'), 'VectorReaderUI.pk')
        self._pkDat = [
        self.peak_height,
        self._offset,
        self._slopeHeight,
        self.closeTopButtonFace,
        self.reversePathToration,
        self.splitWord]
        pickle.dump(self._pkDat, open(pkFile, 'wb'))

    onOkButtonClicked = pyqtSlot()(onOkButtonClicked)

    @pyqtSlot()
    def onCancelButtonClicked(self):
        self._cancelled = True
        self._ui_view.close()
        try:
            self._ui_lock.release()
        except RuntimeError:
            # We don't really care if it was held or not. Just make sure it's not held now
            pass

    @pyqtSlot(str)
    def onOffsetChanged(self, value):
        if self._ui_view and not self._disable_size_callbacks:
            if len(value) > 0:
                try:
                    self._offset = float(value.replace(",", "."))
                except ValueError:  # Can happen with incomplete numbers, such as "-".
                    self._offset = 0
            else:
                self._offset = 0

            self._disable_size_callbacks = True
            self._disable_size_callbacks = False


    @pyqtSlot(str)
    def onSlopHeightChanged(self, value):
        if self._ui_view and not self._disable_size_callbacks:
            if len(value) > 0:
                try:
                    self._slopeHeight = float(value.replace(",", "."))
                except ValueError:  # Can happen with incomplete numbers, such as "-".
                    self._slopeHeight = 0
            else:
                self._slopeHeight = 0

            self._disable_size_callbacks = True
            self._disable_size_callbacks = False


    @pyqtSlot(str)
    def onBaseHeightChanged(self, value):
        if len(value) > 0:
            try:
                self.base_height = float(value.replace(",", "."))
            except ValueError:  # Can happen with incomplete numbers, such as "-".
                self.base_height = 0
        else:
            self.base_height = 0

    @pyqtSlot(str)
    def onPeakHeightChanged(self, value):
        if len(value) > 0:
            try:
                self.peak_height = float(value.replace(",", "."))
                if self.peak_height < 0:
                    self.peak_height = 2.5
            except ValueError:  # Can happen with incomplete numbers, such as "-".
                self.peak_height = 2.5  # restore default
        else:
            self.peak_height = 0

    @pyqtSlot(float)
    def onSmoothingChanged(self, value):
        self.smoothing = int(value)

    @pyqtSlot(int)
    def onImageColorInvertChanged(self, value):
        self.lighter_is_higher = (value == 1)

    @pyqtSlot(int)
    def onColorModelChanged(self, value):
        self.use_transparency_model = (value == 1)

    @pyqtSlot(int)
    def onTransmittanceChanged(self, value):
        self.transmittance_1mm = value
