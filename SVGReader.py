# Copyright (c) 2018 Ultimaker B.V.
# This example is released under the terms of the AGPLv3 or higher.

from UM.Application import Application #To pass to the parent constructor.
from UM.Mesh.MeshBuilder import MeshBuilder #To create a mesh to put in the scene.
from UM.Mesh.MeshReader import MeshReader #This is the plug-in object we need to implement if we want to create meshes. Otherwise extend from FileReader.
from UM.Math.Vector import Vector #Helper class required for MeshBuilder.
from UM.Math.Matrix import Matrix
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
#from .Point import * #为了点计算
import pyclipper #为了点链表的计算 交叉并集等
i18n_catalog = i18nCatalog('cura')
import matplotlib.pyplot as plt  #TODO:用作测试的 后期得删掉
import math
import numpy
from scipy.spatial import Delaunay

class SVGFileReader(MeshReader):

    def __init__(self):
        super().__init__()
        self._supported_extensions = [".svg"] #抱歉，你还必须在这里指定它。
        self._ui = VectorReaderUI(self)
        self._paths = None
        #self._Points = None
    def Show(self,path,name,arg):
        plt.title(name)

        x = []
        y = []
        if arg > 1:
            for point_s in path:
                for point in point_s:
                    x.append(point[0])
                    y.append(point[1])
        else:
            for point_s in path:
                x.append(point_s[0])
                y.append(point_s[1])

        plt.plot(x, y, 'r')
        plt.xlabel('x')
        plt.ylabel('y')
        plt.axis('equal')
        plt.show()
        plt.close()

    def preRead(self, file_name, *args, **kwargs):
        self._paths = None
        svg_file = 0
        if file_name.endswith('.svg'):
            svg_file = svg.parse(file_name)  # 打开并解析svg文件
            #TODO:这里应该有一个判空
            #self._paths = self._vu.readSvg(file_name)
            svg_file.scale(25.4/96) #我们计算出来的是像素点需要转换成mm
            svg_segments = svg_file.flatten()
            self._paths = []
            point_list = []
            for d in svg_segments:
                if hasattr(d, 'segments'):
                    for l in d.segments(1):
                        x, y = l[0].coord()
                        print("move:(%f,%f)" % (x, y))
                        #hull_poins1 = [Vector(x=x, y=y, z=0)]
                        hull_poins1 = [[x,y]]
                        point_list.append((x,y))
                        for pt in l[1:]:
                            x, y = pt.coord()
                            #hull_poins1.append(Vector(x=x, y=y, z=0))
                            hull_poins1.append([x,y])
                            point_list.append((x,y))
                        hull_poins1.append(hull_poins1[0])
                        self._paths.append(hull_poins1)
                        #self._Points.append(point_list)
                else:
                    Logger.log('e', "Unsupported SVG element")
                    #print("Unsupported SVG element")
        #print("area:",GetAreaOfPolyGon(self._Points))

        if not self._paths:
            Logger.log('e', "Conn't load paths.")
            return MeshReader.PreReadResult.failed
        #data = earcut.flatten([[(0,0), (100,0), (100,100), (0,100)], [(20,20), (80,20), (80,80), (20,80)]])
        #verts = numpy.array(self._paths[0])
        #rings = numpy.array(self._paths[1])

        #data = earcut.triangulate_float64(verts,rings)
        #triangles = earcut.earcut(data['vertices'], data['holes'], data['dimensions'])

        #self.Show(self._paths,"path",2)
        #None._paths.removeClosePoint()
        # 计算三角
        # triangulation = Delaunay(point_list)
        # point_s = triangulation.points[triangulation.vertices]
        # list_ = []
        # for tri in point_s:
        #     print("tri:",tri)
        #     list_.append([[tri[0][0],tri[0][1]],[tri[1][0],tri[1][1]],[tri[2][0],tri[2][1]]])
        #     #list_.append([tri[1][0],tri[1][1]])
        #     #list_.append([tri[2][0],tri[2][1]])
        # self.Show(list_, "path", 1)
        # for poins in self._paths:
        #     indx = 0
        #     while indx < len(poins) - 1:
        #        # poins[indx][0], y = poins[indx][1]
        #         tri = triangulation.find_simplex((poins[indx][0], poins[indx][1]))
        #
        #         print("triangulation",tri)
        #         indx +=1
        #     print("triangulation.simplices:",triangulation.simplices)

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


        ##  创建场景节点
        #   \param file_name 打开的文件的名字
        #   \param offset, 偏移的角度
        #   \param peak_height, 模型的高度
        #   \param slopeHeight, 斜坡的高度
        #   \param closeTopButtonFace, 是否生成一个封闭的顶底
        #   \param reversePathToration, 反转路径
        #   \param splitWord, 拆分模型
        #   \return success
    def _generateSceneNode(self, file_name, offset, peak_height, slopeHeight,
                           closeTopButtonFace, reversePathToration, splitWord):
        Job.yieldThread()
        if not splitWord:
            scene_node = SceneNode()
            mesh = MeshBuilder()
        else:
             scene_node = []
        #TODO:#创建一个转换矩阵，从3mf世界空间转换为我们的。
        #第一步:翻转y轴和z轴。
        transformation_matrix = Matrix()
        transformation_matrix._data[1, 1] = 0
        transformation_matrix._data[1, 2] = 1
        transformation_matrix._data[2, 1] = -1
        transformation_matrix._data[2, 2] = 0
        #TODO:WALL
        for poins in self._paths:
            indx = 0
            while indx < len(poins) -1:
                print("Ver:",poins[indx])
                a = Vector(x=poins[indx][0], y=poins[indx][1], z=0).multiply(transformation_matrix)
                b = Vector(x=poins[indx][0], y=poins[indx][1], z=peak_height - slopeHeight).multiply(transformation_matrix)
                c = Vector(poins[indx+1][0],poins[indx+1][1],0).multiply(transformation_matrix)
                #build_list.append(poins[indx],poins[indx])
                #mesh.addFace(a,b,c)
                mesh.addFaceByPoints(a.x,a.y,a.z, b.x,b.y,b.z, c.x,c.y,c.z)
                #下一个面
                b1 = Vector(x=poins[indx+1][0], y=poins[indx+1][1], z=peak_height - slopeHeight).multiply(transformation_matrix)
                #mesh.addFace(c, b1, b)
                mesh.addFaceByPoints(c.x, c.y, c.z, b1.x, b1.y,b1.z, b.x, b.y, b.z)
                indx += 1
        #TODO：有偏移的时候
        """若已知边为斜边c
            a=c*sinA（A为已知角）
            b=c*cosA
            若已知边为已知角的对边a
            斜边c=a/sinA
            另一直角边b=a/tanA=a*cotA
            若已知边为已知角的邻边b
            斜边c=b/cosA
            另一直角边a=b*tanA"""
        if offset != 0 and slopeHeight >0:
            angle = (math.pi * offset)/180
            #实际偏移
            offset_set = slopeHeight * math.cos(angle)
            self.Show(self._paths, "result1", 2)
            # indx = 0
            # indy = 0
            # while indx < len(self._paths) - 1:
            #
            #     while indy < len(self._paths[indx]) - 1:
            #         self._paths[indx][indy] = [self._paths[indx][indy][0]+offset_set, self._paths[indx][indy][1]+offset_set]
            #         indy += 1
            #     indx += 1
            # self.Show(self._paths, "result2", 2)
            for poins in self._paths:
                pcOffset = pyclipper.PyclipperOffset()
                pcOffset.AddPath(poins, pyclipper.JT_SQUARE, pyclipper.ET_CLOSEDLINE)
                result = pcOffset.Execute(offset_set)
                for res in result:
                    mesh.addVertex(res[0],res[1],0)
                self.Show(result, "result",2)
                del pcOffset
                # solution = result
                # if len(solution ) > len(poins):
                #     solution = poins
                #
                # indx = 0
                # while indx < len(solution) - 1:
                #     print("Ver:", solution[indx])
                #     a = Vector(x=poins[indx][0], y=poins[indx][1], z=peak_height - slopeHeight).multiply(transformation_matrix)
                #     b = Vector(x=solution[indx][0], y=solution[indx][1], z=peak_height).multiply(
                #         transformation_matrix)
                #     c = Vector(poins[indx + 1][0], poins[indx + 1][1], peak_height - slopeHeight).multiply(transformation_matrix)
                #     # build_list.append(poins[indx],poins[indx])
                #     # mesh.addFace(a,b,c)
                #     mesh.addFaceByPoints(a.x, a.y, a.z, b.x, b.y, b.z, c.x, c.y, c.z)
                #     # 下一个面
                #     b1 = Vector(x=solution[indx + 1][0], y=solution[indx + 1][1], z=peak_height).multiply(
                #         transformation_matrix)
                #     # mesh.addFace(c, b1, b)
                #     mesh.addFaceByPoints(c.x, c.y, c.z, b1.x, b1.y, b1.z, b.x, b.y, b.z)
                #     indx += 1


        areaTop = 0
        areaBottom = 0
        pathDetectNotEqual = False #路径检测不相等
        # TODO:Bottom
        """
        pc = pyclipper.Pyclipper()
        pc.AddPath(clip, pyclipper.PT_CLIP, True)
        pc.AddPaths(subj, pyclipper.PT_SUBJECT, True)        
        solution = pc.Execute(pyclipper.CT_INTERSECTION, pyclipper.PFT_EVENODD, pyclipper.PFT_EVENODD)
        """
        # pc = pyclipper.Pyclipper()
        # pc.AddPath(self._paths[0], pyclipper.PT_CLIP, True)
        # pc.AddPath(self._paths[1], pyclipper.PT_SUBJECT, True)
        # solution = pc.Execute(pyclipper.CT_UNION, pyclipper.PFT_EVENODD, pyclipper.PFT_EVENODD)
        # areaBottom = pyclipper.Area(solution[0])
        # print("area:", areaBottom)

        #print("area:",GetAreaOfPolyGon(self._Points))
        # areaBottom,area_list = GetAreaOfPolyGon(self._Points)
        # for area in area_list:
        #     areaP1 = Vector(area[0].x,area[0].y,peak_height).multiply(transformation_matrix)
        #     areaP2 = Vector(area[1].x, area[1].y, peak_height).multiply(transformation_matrix)
        #     areaP3 = Vector(area[2].x, area[2].y, peak_height).multiply(transformation_matrix)
        #     mesh.addFace(areaP1, areaP2, areaP3)
        # indx = 0
        # #solution = self._paths[1]
        # for so in solution:
        #     l = len(so)
        #     while indx <  l - 3:
        #         #area = solution[indx]
        #         areaP1 = Vector(so[indx][0],so[indx][1],peak_height)#.multiply(transformation_matrix)
        #         areaP2 = Vector(so[indx+1][0], so[indx+1][1], peak_height)#.multiply(transformation_matrix)
        #         areaP3 = Vector(so[indx+2][0], so[indx+2][1], peak_height)#.multiply(transformation_matrix)
        #         mesh.addFace(areaP1, areaP2, areaP3)
        #         indx += 3
        #TODO:要记得高开
        if closeTopButtonFace:
            if pathDetectNotEqual:
                m = Message(i18n_catalog.i18nc(
                    '@info:status',
                    'Top/Buttom area :{} mm² ,{} mm²\n There may be broken, please reduce the offset',
                    round(areaTop, 2), round(areaBottom, 2)),
                    lifetime=0)
            else:
                m = Message(i18n_catalog.i18nc(
                    '@info:status',
                    'Top/Buttom area :{} mm² ,{} mm²', round(
                        areaTop, 2), round(areaBottom, 2)),
                    lifetime=0)
                m.addAction('regenerate', i18n_catalog.i18nc('@action:button',
                                                             'regenerate'),
                            'regenerate', i18n_catalog.i18nc('@info:tooltip',
                                                             'Regenerating model'))
            m._filename = file_name
            m.actionTriggered.connect(self._onMessageActionTriggered)
            m.show()

        mesh.calculateNormals()

        # 将网格放到场景节点中。
        #result_node = SceneNode()
        scene_node.setMeshData(mesh.build())


        #scene_node.setMirror(transformation_matrix)
        scene_node.setName(file_name)  # Ty举例来说，网格起源的文件名是节点的好名字。
        return scene_node

    def _onMessageActionTriggered(self, message, action):
        if action == 'regenerate' and hasattr(message, '_filename'):
            Application.getInstance().deleteAll()
            Application.getInstance().readLocalFile(
                QUrl.fromLocalFile(message._filename))
            message.hide()

        return (None, )