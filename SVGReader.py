# Copyright (c) 2018 Ultimaker B.V.
# This example is released under the terms of the AGPLv3 or higher.

from UM.Application import Application #传递给父构造函数。
from UM.Mesh.MeshBuilder import MeshBuilder #在场景中创建一个网格
from UM.Mesh.MeshReader import MeshReader #这是我们需要实现的插件对象，如果我们想要创建网格。否则从FileReader扩展。
from UM.Math.Vector import Vector #网格生成器所需的助手类。
from UM.Math.Matrix import Matrix
from UM.Scene.SceneNode import SceneNode #阅读时必须返回结果。
from UM.Job import Job
from UM.Logger import Logger
from PyQt6.QtCore import QUrl
#from .VectorReaderUI import VectorReaderUI
from .SVGReaderUI import SVGReaderUI
from .Vector_polygon import Vector_compute_Polygon_Shapely

from UM.Message import Message
from UM.Application import Application
from UM.i18n import i18nCatalog
import UM.Math.Color as Color


import svg

import pyclipper #为了点链表的计算 交叉并集等
from shapely.geometry import LineString,Point
from shapely.geometry import MultiLineString
i18n_catalog = i18nCatalog('cura')

import matplotlib.pyplot as plt  #TODO:用作测试的 后期得删掉
# import matplotlib.tri as tri
# from mpl_toolkits.mplot3d import Axes3D

import math
import numpy as np
# TODO: 等高线三角化最主要的模块
#from p3t import CDT, Point3
import sys, subprocess, os
import time


_subdivision = 0.52 #细分问题
EPSILON = 0.0001


def run_command_notfixed(*kwargs):
    cmd_path = os.path.abspath('.')  # 获取当前文件路径
    print("cmd_path:", cmd_path)
    parameters_str = ''
    for i in kwargs:
        parameters_str = parameters_str + " " + str(i)
    cmd_path = cmd_path + "/Vector_compute.exe" + parameters_str
    print(cmd_path)
    # print(os.popen(cmd_path))
    value = os.system(cmd_path)  # 执行命令
    print(value)
    if value == 0:
        print("run ok")
        # subprocess.Popen([cmd_path])
#        sys.exit(0)

class SVGFileReader(MeshReader):

    def __init__(self):
        super().__init__()
        self._supported_extensions = [".svg"] #抱歉，你还必须在这里指定它。
        self._ui = SVGReaderUI(self)
        self._paths = None
        #self._Points = None
        self.poly_count = 0 #多边形个数 用了判断可不可以拆分--> 应该吧计算出来的东西放在一个结构里面 而不是直接这么用


    def Show(self,path,name,arg):
        plt.title(name)

        x = []
        y = []
        index = 0
        if arg > 3:
            for point_s in path:
                for point_11 in point_s:
                    for point_ in point_11:
                        for point in point_:
                            if index == 0 or index == len(point_s) - 1:
                                plt.annotate('Start', xy=(point[0], point[1]), xytext=(point[0]+3, point[1]+1.5),
                                             arrowprops=dict(facecolor='black', shrink=0.05),
                                             )
                                #print("point:",point)
                            index += 1
                            x.append(point[0])
                            y.append(point[1])
        elif arg > 2:
            for point_s in path:
                for point_ in point_s:
                    for point in point_:
                        if index == 0 or index == len(point_s) - 1:
                            plt.annotate('Start', xy=(point[0], point[1]), xytext=(point[0]+3, point[1]+1.5),
                                         arrowprops=dict(facecolor='black', shrink=0.05),
                                         )
                            #print("point:",point)
                        index += 1
                        x.append(point[0])
                        y.append(point[1])
        elif arg > 1:
            for point_s in path:
                for point in point_s:
                    if index == 0 or index == len(point_s) - 1:
                        plt.annotate('Start', xy=(point[0], point[1]), xytext=(point[0]+3, point[1]+1.5),
                                     arrowprops=dict(facecolor='black', shrink=0.05),
                                     )
                        #print("point:",point)
                    index += 1
                    x.append(point[0])
                    y.append(point[1])
        else:
            for point_s in path:
                if index == 0 or index == len(path) - 1:
                    plt.annotate('Start', xy=(point_s.x, point_s.y), xytext=(point_s.x + 3, point_s.y + 1.5),
                                 arrowprops=dict(facecolor='black', shrink=0.05),
                                 )
                    print("point:", point_s)
                index += 1
                x.append(point_s.x)
                y.append(point_s.y)

        plt.plot(x, y, 'r--')
        plt.xlabel('x')
        plt.ylabel('y')
        plt.axis('equal')

        plt.show()
        #plt.close()



    def preRead(self, file_name, *args, **kwargs):
        self._paths = None
        svg_file = 0
        if file_name.endswith('.svg'):
            svg_file = svg.parse(file_name)  # 打开并解析svg文件
            #TODO:这里应该有一个判空
            #self._paths = self._vu.readSvg(file_name)
            svg_file.scale(25.4/96) #我们计算出来的是像素点需要转换成mm
            print("bbox:",svg_file.bbox())
            svg_segments = svg_file.flatten()
            self._paths = []
            def MM2Int(a):
                return (a*1)
            #poly_count = 0 #多边形个数 用了判断可不可以拆分
            segments_count = 0
            svg_segments_count = 0
            coord_count = 0
            for d in svg_segments:
                svg_segments_Path = []
                svg_segments_count += 1
                if hasattr(d, 'segments'):
                    segments_count += 1
                    segments_Path = []
                    for l in d.segments(1):
                        coord_count += 1
                        x, y = l[0].coord()
                        coord_Path = [(x,y)]
                        #coord_Path = []
                        self.poly_count += 1 #多边形个数 用了判断可不可以拆分
                        for pt in l[1:]:
                            x, y = pt.coord()
                            coord_Path.append((x,y))
                        segments_Path.append(coord_Path)
                    svg_segments_Path.append(segments_Path)
                else:
                    Logger.log('e', "Unsupported SVG element")

                    #print("Unsupported SVG element")
                self._paths.append(svg_segments_Path)

        print ("svg_segments:",svg_segments_count)
        print ("segments:", segments_count)
        print ("coord:", coord_count)
        if not self._paths:
            Logger.log('e', "Conn't load paths.")
            return MeshReader.PreReadResult.failed

        # start = time.clock()
        # #self.Show(self._paths,"self._paths",4)



        # print(("Poly-Load: %.2fs" % (time.clock() - start)))

        self._ui.showConfigUI()
        self._ui.waitForUIToClose()
        if self._ui.getCancelled():
            return MeshReader.PreReadResult.cancelled
        #self._start_SvG_job.start()
        return MeshReader.PreReadResult.accepted


    def read(self, file_name):
        return self._generateSceneNode(
            file_name, 0, self._ui.peak_height,
            0, self._ui.closeTopButtonFace,
            self._ui.reversePathToration, self._ui.splitWord)
        #         return self._generateSceneNode(
        #             file_name, self._ui.getOffset(), self._ui.peak_height,
        #             self._ui._slopeHeight, self._ui.closeTopButtonFace,
        #             self._ui.reversePathToration, self._ui.splitWord)


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
        scene_node = SceneNode()
        mesh = MeshBuilder()
        # TODO:#创建一个转换矩阵，从3mf世界空间转换为我们的。
        # 第一步:翻转y轴和z轴。
        transformation_matrix = Matrix()
        print("Matrix:", transformation_matrix)
        range_s = 0
        #FIXME:这是直接翻转不行
        # if offset < 0:
        #     range_s = 180
        #     offset = -offset
        # i
        transformation_matrix._data[1, 1] = math.sin(math.radians(range_s))
        transformation_matrix._data[1, 2] = math.cos(math.radians(range_s))
        # j
        transformation_matrix._data[2, 1] = math.sin(math.radians(range_s + 90))
        transformation_matrix._data[2, 2] = math.cos(math.radians(range_s + 90))
        """
        [[1. 0. 0. 0.]
         [0. 1. 0. 0.]
         [0. 0. 1. 0.]
         [0. 0. 0. 1.]]
        """
        # run_command_notfixed(int(offset), int(peak_height), int(slopeHeight),
        #                    int(closeTopButtonFace), int(reversePathToration), int(splitWord))
        #


        #Vector_polygon = load_points("./outputVector.dat")
        triangles_list = Vector_compute_Polygon_Shapely(self._paths,int(offset), int(peak_height), int(slopeHeight),
                           int(closeTopButtonFace), int(reversePathToration), int(splitWord))
        #print ("SB:",triangles)
        Vector_polygon = []
        for triangles in triangles_list:
            for t in triangles:
                p0 = [t.a.x, t.a.y, t.a.z]
                p1 = [t.b.x, t.b.y, t.b.z]
                p2 = [t.c.x, t.c.y, t.c.z]
                Vector_polygon.append(p0)
                Vector_polygon.append(p1)
                Vector_polygon.append(p2)
        # # 创建 3D 图形对象
        # fig = plt.figure()
        # ax = Axes3D(fig)
        # x = [x[0] for x in Vector_polygon]
        # y = [x[1] for x in Vector_polygon]
        # z = [x[2] for x in Vector_polygon]
        # #绘制线型图
        # ax.plot(x, y, z)
        # plt.show()
        indx = 0
        while indx < len(Vector_polygon):
            # print("Ver:",poins[indx])
            a = Vector(x=Vector_polygon[indx][0], y=Vector_polygon[indx][1], z=Vector_polygon[indx][2]).multiply(transformation_matrix)
            b = Vector(x=Vector_polygon[indx+1][0], y=Vector_polygon[indx+1][1], z=Vector_polygon[indx+1][2]).multiply(transformation_matrix)
            c = Vector(Vector_polygon[indx + 2][0], Vector_polygon[indx + 2][1],z=Vector_polygon[indx+2][2]).multiply(transformation_matrix)
            # build_list.append(poins[indx],poins[indx])
            # mesh.addFace(a,b,c)
            mesh.addFaceByPoints(a.x, a.y, a.z, b.x, b.y, b.z, c.x, c.y, c.z)
            # 下一个面
            # b1 = Vector(x=poins[indx + 1][0], y=poins[indx + 1][1], z=peak_height - slopeHeight).multiply(
            #     transformation_matrix)
            # # mesh.addFace(c, b1, b)
            # mesh.addFaceByPoints(c.x, c.y, c.z, b1.x, b1.y, b1.z, b.x, b.y, b.z)
            indx += 3
        mesh.calculateNormals()

        # 将网格放到场景节点中。
        # result_node = SceneNode()
        scene_node.setMeshData(mesh.build())

        # scene_node.setMirror(transformation_matrix)
        scene_node.setName(file_name)  # Ty举例来说，网格起源的文件名是节点的好名字。
        return scene_node

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


