#!/usr/bin/env python
# encoding: utf-8

import numpy
import math
from PyQt5.QtGui import QImage, qRed, qGreen, qBlue
from PyQt5.QtCore import Qt
from PyQt5.QtCore import QUrl
from UM.Mesh.MeshReader import MeshReader
from UM.Mesh.MeshBuilder import MeshBuilder
from UM.Scene.SceneNode import SceneNode
from UM.Math.Vector import Vector
from UM.Job import Job
from UM.Logger import Logger
from .VectorReaderUI import VectorReaderUI
import os
import re
from UM.Message import Message
from UM.Application import Application
from UM.i18n import i18nCatalog
import svg
i18n_catalog = i18nCatalog('cura')
#from cura.VectorUtil import VectorUtil, VectorPaths


class VectorReader(MeshReader):
    __qualname__ = 'VectorReader'

    def __init__(self):
        super(VectorReader, self).__init__()
        self._supported_extensions = ['.svg', '.nc', '.dxf']
        self._ui = VectorReaderUI(self)
        self._paths = None
        #self._vu = VectorUtil()

    def preRead(self, file_name, *args, **kwargs):
        self._paths = None
        if file_name.endswith('.svg'):
            self._paths = self._vu.readSvg(file_name)
        # elif file_name.endswith('.nc'):
        #     self._paths = self._vu.readNc(file_name)
        # elif file_name.endswith('.dxf'):
        #     self._paths = self._vu.readDxf(file_name)
        if not self._paths:
            Logger.log('e', "Conn't load paths.")
            return MeshReader.PreReadResult.failed
        None._paths.removeClosePoint()
        self._ui.showConfigUI()
        self._ui.waitForUIToClose()
        if self._ui.getCancelled():
            return MeshReader.PreReadResult.cancelled
        return None.PreReadResult.accepted

    
    def read(self, file_name):
        return self._generateSceneNode(
            file_name, self._ui.getOffset(), self._ui.peak_height,
            self._ui._slopeHeight, self._ui.closeTopButtonFace,
            self._ui.reversePathToration, self._ui.splitWord)

    def _generateSceneNode(self, file_name, offset, peak_height, slopeHeight,
                           closeTopButtonFace, reversePathToration, splitWord):
        Job.yieldThread()
        if not splitWord:
            scene_node = SceneNode()
            mesh = MeshBuilder()
        else:
            scene_node = []
        areaTop = 0
        areaBottom = 0
        pathDetectNotEqual = False
        for subPaths in self._paths:
            if splitWord:
                mesh = MeshBuilder()
            pros = self._vu._gen_offset_paths(subPaths)
            clocks = []
            for path in subPaths:
                reverse = file_name.endswith('.nc')
                if reverse == (not reversePathToration):
                    path.reverse()
                (clock, holePoint) = self._vu.clockWish(path)
                clocks.append(clock)

            lastPaths = self._vu._exec_offset(pros, clocks, 0)
            if offset != 0:
                currPaths = lastPaths
                self._vu.addSidFaces(lastPaths, currPaths, clocks, mesh, 0,
                                     peak_height - slopeHeight)
                currPaths = self._vu._exec_offset(pros, clocks, offset)
                pathDetectNotEqual = self._vu.addSidFaces(
                    lastPaths, currPaths, clocks, mesh,
                    peak_height - slopeHeight, peak_height)
            else:
                currPaths = lastPaths
                self._vu.addSidFaces(lastPaths, currPaths, clocks, mesh, 0,
                                     peak_height)
            if closeTopButtonFace:
                areaTop += self._vu.addTopButtonFace(True, currPaths, mesh,
                                                     peak_height)
                areaBottom += self._vu.addTopButtonFace(False, lastPaths, mesh,
                                                        0)
            if splitWord:
                mesh.calculateNormals(fast=True)
                _sceneNode = SceneNode()
                _sceneNode.setMeshData(mesh.build())
                scene_node.append(_sceneNode)
        if not splitWord:
            mesh.calculateNormals(fast=True)
            scene_node.setMeshData(mesh.build())
        else:
            scene_node.reverse()
        if closeTopButtonFace:
            if pathDetectNotEqual:
                m = Message(i18n_catalog.i18nc(
                    '@info:status',
                    'Top/Buttom area :{} mm\xc2\xb2 ,{} mm\xc2\xb2\n There may be broken, please reduce the offset',
                    round(areaTop, 2), round(areaBottom, 2)),
                            lifetime=0)
            else:
                m = Message(i18n_catalog.i18nc(
                    '@info:status',
                    'Top/Buttom area :{} mm\xc2\xb2 ,{} mm\xc2\xb2', round(
                        areaTop, 2), round(areaBottom, 2)),
                            lifetime=0)
            m.addAction('regenerate', i18n_catalog.i18nc('@action:button',
                                                         'regenerate'),
                        'regenerate', i18n_catalog.i18nc('@info:tooltip',
                                                         'Regenerating model'))
            m._filename = file_name
            m.actionTriggered.connect(self._onMessageActionTriggered)
            m.show()
        return scene_node

    def _onMessageActionTriggered(self, message, action):
        if action == 'regenerate' and hasattr(message, '_filename'):
            Application.getInstance().deleteAll()
            Application.getInstance().readLocalFile(
                QUrl.fromLocalFile(message._filename))
            message.hide()

        return (None, )