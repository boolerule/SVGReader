# Copyright (c) 2018 Ultimaker B.V.
# This example is released under the terms of the AGPLv3 or higher.

from UM.Application import Application #To pass to the parent constructor.
from UM.Mesh.MeshBuilder import MeshBuilder #To create a mesh to put in the scene.
from UM.Mesh.MeshReader import MeshReader #This is the plug-in object we need to implement if we want to create meshes. Otherwise extend from FileReader.
from UM.Math.Vector import Vector #Helper class required for MeshBuilder.
from UM.Scene.SceneNode import SceneNode #The result we must return when reading.
from UM.Job import Job
from UM.Logger import Logger
from PyQt5.QtCore import QUrl
from .VectorReaderUI import VectorReaderUI
from UM.Message import Message
from UM.Application import Application
from UM.i18n import i18nCatalog
import UM.Math.Color as Color

import svg
i18n_catalog = i18nCatalog('cura')

class SVGFileReader(MeshReader):

    def __init__(self):
        super().__init__()
        self._supported_extensions = [".svg"] #抱歉，你还必须在这里指定它。
        self._ui = VectorReaderUI(self)
        self._paths = None

    def preRead(self, file_name, *args, **kwargs):
        self._paths = None
        svg_file = 0
        if file_name.endswith('.svg'):
            svg_file = svg.parse(file_name)  # 打开并解析svg文件
            #TODO:这里应该有一个判空
            #self._paths = self._vu.readSvg(file_name)
            #svg_file.scale(0.2)
            svg_segments = svg_file.flatten()

            self._paths = []
            for d in svg_segments:
                if hasattr(d, 'segments'):
                    for l in d.segments(1):
                        x, y = l[0].coord()
                        print("move:(%f,%f)" % (x, y))
                        hull_poins1 = [Vector(x, y, 0)]
                        for pt in l[1:]:
                            x, y = pt.coord()
                            hull_poins1.append(Vector(x, y, 0))
                        self._paths.append(hull_poins1)
                else:
                    Logger.log('e', "Unsupported SVG element")
                    #print("Unsupported SVG element")

        if not self._paths:
            Logger.log('e', "Conn't load paths.")
            return MeshReader.PreReadResult.failed
        #None._paths.removeClosePoint()
        self._ui.showConfigUI()
        self._ui.waitForUIToClose()
        if self._ui.getCancelled():
            return MeshReader.PreReadResult.cancelled
        return MeshReader.PreReadResult.accepted

    def read(self, file_name):
        return self._generateSceneNode(
            file_name, self._ui.getOffset(), self._ui.peak_height,
            self._ui._slopeHeight, self._ui.closeTopButtonFace,
            self._ui.reversePathToration, self._ui.splitWord)


    def _generateSceneNode(self, file_name, offset, peak_height, slopeHeight,
                           closeTopButtonFace, reversePathToration, splitWord):
        #Job.yieldThread()
        # if not splitWord:
        scene_node = SceneNode()
        mesh = MeshBuilder()
        # else:
        #     scene_node = []
        #TODO:
        #self._paths.scale(0.2)
        for poins in self._paths:
            indx = 0
            while indx < len(poins) -1:
                print("Ver:",poins[indx])
                a = poins[indx]
                b = Vector(poins[indx].x, poins[indx].y, peak_height)
                c = poins[indx+1]
                #build_list.append(poins[indx],poins[indx])
                mesh.addFace(a,b,c)
                #下一个面
                b1 = Vector(poins[indx+1].x, poins[indx+1].y, peak_height)
                mesh.addFace(c, b1, b)
                indx += 1

        areaTop = 0
        areaBottom = 0
        pathDetectNotEqual = False
        # for subPaths in self._paths:
        #     if splitWord:
        #         mesh = MeshBuilder()
        #     pros = self._vu._gen_offset_paths(subPaths)
        #     clocks = []
        #     for path in subPaths:
        #         reverse = file_name.endswith('.nc')
        #         if reverse == (not reversePathToration):
        #             path.reverse()
        #         (clock, holePoint) = self._vu.clockWish(path)
        #         clocks.append(clock)
        #
        #     lastPaths = self._vu._exec_offset(pros, clocks, 0)
        #     if offset != 0:
        #         currPaths = lastPaths
        #         self._vu.addSidFaces(lastPaths, currPaths, clocks, mesh, 0,
        #                              peak_height - slopeHeight)
        #         currPaths = self._vu._exec_offset(pros, clocks, offset)
        #         pathDetectNotEqual = self._vu.addSidFaces(
        #             lastPaths, currPaths, clocks, mesh,
        #             peak_height - slopeHeight, peak_height)
        #     else:
        #         currPaths = lastPaths
        #         self._vu.addSidFaces(lastPaths, currPaths, clocks, mesh, 0,
        #                              peak_height)
        #     if closeTopButtonFace:
        #         areaTop += self._vu.addTopButtonFace(True, currPaths, mesh,
        #                                              peak_height)
        #         areaBottom += self._vu.addTopButtonFace(False, lastPaths, mesh,
        #                                                 0)
        #     if splitWord:
        #         mesh.calculateNormals(fast=True)
        #         _sceneNode = SceneNode()
        #         _sceneNode.setMeshData(mesh.build())
        #         scene_node.append(_sceneNode)
        # if not splitWord:
        #     mesh.calculateNormals(fast=True)
        #     scene_node.setMeshData(mesh.build())
        # else:
        #     scene_node.reverse()
        #TODO:要记得高开
        # if closeTopButtonFace:
        #     if pathDetectNotEqual:
        #         m = Message(i18n_catalog.i18nc(
        #             '@info:status',
        #             'Top/Buttom area :{} mm\xc2\xb2 ,{} mm\xc2\xb2\n There may be broken, please reduce the offset',
        #             round(areaTop, 2), round(areaBottom, 2)),
        #             lifetime=0)
        #     else:
        #         m = Message(i18n_catalog.i18nc(
        #             '@info:status',
        #             'Top/Buttom area :{} mm\xc2\xb2 ,{} mm\xc2\xb2', round(
        #                 areaTop, 2), round(areaBottom, 2)),
        #             lifetime=0)
        #     m.addAction('regenerate', i18n_catalog.i18nc('@action:button',
        #                                                  'regenerate'),
        #                 'regenerate', i18n_catalog.i18nc('@info:tooltip',
        #                                                  'Regenerating model'))
        #     m._filename = file_name
        #     m.actionTriggered.connect(self._onMessageActionTriggered)
        #     m.show()

        mesh.calculateNormals()

        # 将网格放到场景节点中。
        #result_node = SceneNode()
        scene_node.setMeshData(mesh.build())
        scene_node.setName(file_name)  # Ty举例来说，网格起源的文件名是节点的好名字。
        return scene_node

    def _onMessageActionTriggered(self, message, action):
        if action == 'regenerate' and hasattr(message, '_filename'):
            Application.getInstance().deleteAll()
            Application.getInstance().readLocalFile(
                QUrl.fromLocalFile(message._filename))
            message.hide()

        return (None, )