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
from PyQt5.QtCore import QUrl
from .VectorReaderUI import VectorReaderUI
from cura.Vector_polygon import Vector_compute_Polygon

from UM.Message import Message
from UM.Application import Application
from UM.i18n import i18nCatalog
import UM.Math.Color as Color

import matplotlib.pyplot as plt
import svg

import pyclipper #为了点链表的计算 交叉并集等
from shapely.geometry import LineString,Point
from shapely.geometry import MultiLineString
i18n_catalog = i18nCatalog('cura')

import matplotlib.pyplot as plt  #TODO:用作测试的 后期得删掉
import matplotlib.tri as tri
from mpl_toolkits.mplot3d import Axes3D

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
        self._ui = VectorReaderUI(self)
        self._paths = None
        #self._Points = None
        self.poly_count = 0 #多边形个数 用了判断可不可以拆分--> 应该吧计算出来的东西放在一个结构里面 而不是直接这么用


    def Show(self,path,name,arg):
        plt.title(name)

        x = []
        y = []
        index = 0
        if arg > 2:
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

        start = time.clock()




        print(("Poly-Load: %.2fs" % (time.clock() - start)))

        self._ui.showConfigUI()
        self._ui.waitForUIToClose()
        if self._ui.getCancelled():
            return MeshReader.PreReadResult.cancelled
        #self._start_SvG_job.start()
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
        scene_node = SceneNode()
        mesh = MeshBuilder()
        # TODO:#创建一个转换矩阵，从3mf世界空间转换为我们的。
        # 第一步:翻转y轴和z轴。
        transformation_matrix = Matrix()
        print("Matrix:", transformation_matrix)

        range_s = 0
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
        triangles_list = Vector_compute_Polygon(self._paths,int(offset), int(peak_height), int(slopeHeight),
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
        # 创建 3D 图形对象
        fig = plt.figure()
        ax = Axes3D(fig)
        x = [x[0] for x in Vector_polygon]
        y = [x[1] for x in Vector_polygon]
        z = [x[2] for x in Vector_polygon]
        #绘制线型图
        ax.plot(x, y, z)
        plt.show()
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
        if not splitWord:
            scene_node = SceneNode()
            mesh = MeshBuilder()
        else:
             scene_node = []
        self.Show(self._paths, "_paths", 2)
        areaTop = 0
        areaBottom = 0
        pathDetectNotEqual = False #路径检测不相等
        #TODO:#创建一个转换矩阵，从3mf世界空间转换为我们的。
        #第一步:翻转y轴和z轴。
        transformation_matrix = Matrix()
        print("Matrix:",transformation_matrix)

        range_s = 0
        #i
        transformation_matrix._data[1, 1] = math.sin(math.radians(range_s))
        transformation_matrix._data[1, 2] = math.cos(math.radians(range_s))
        #j
        transformation_matrix._data[2, 1] = math.sin(math.radians(range_s+90))
        transformation_matrix._data[2, 2] = math.cos(math.radians(range_s+90))
        """
        [[1. 0. 0. 0.]
         [0. 1. 0. 0.]
         [0. 0. 1. 0.]
         [0. 0. 0. 1.]]
        """

        #TODO:WALL
        for poins in self._paths:
            if splitWord:
                mesh = MeshBuilder()
            indx = 0
            while indx < len(poins) -1:
                #print("Ver:",poins[indx])
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


            #angle =  offset*(math.pi/180)
            #实际偏移
            offset_set = slopeHeight / math.tan(math.radians(offset))
            #TODO：当前可以被细分到多小
            offset_count = int(abs(offset_set/_subdivision))
            curr_height = peak_height - slopeHeight

            #TODO:为了精度问题吧所有多边形放大1000 倍。即放大取整。
            # for idx in range(len(self._paths)):
            #     self._paths[idx] = np.array(self._paths[idx]) *1000
            # Vector_polygon = []
            # pco = pyclipper.PyclipperOffset()
            # for idx in range(len(self._paths)):
            #     pco.AddPath(self._paths[idx], pyclipper.JT_ROUND, pyclipper.ET_CLOSEDPOLYGON)
            # for index in range(1,offset_count):
            #     solution = pco.Execute(-_subdivision * 1000 * index)
            #     Vector_polygon.append(solution)
            temp = []
            for idx in range(len(self._paths)):
                temp += self._paths[idx]
            temp = np.array(temp)

                #self._paths[idx] = np.array(self._paths[idx]) *1000
            # line_path = LineString(temp)
            # polygon = line_path.buffer(0.001)
            # Vector_polygon = []
            # Vector_polygon.append(np.asarray(polygon.interiors[0]))
            # for index in range(1,offset_count):
            #     polygon1 = line_path.buffer(_subdivision*index)
            #     #solution = pco.Execute(-_subdivision * 1000 * index)
            #     Vector_polygon.append(np.asarray(polygon1.interiors[0]))
           #self.Show(Vector_polygon, "Vector_polygon", 1)
            # #TODO:保证多边形是闭合的
            # for index in range(1, len(Vector_polygon)):
            #     Vector_polygon[index] = Vector_polygon[index]
            #TODO:为了三角化
            polyline = []
            end_point = None
            temp_poly = []
            #for i in range(1,len(Vector_polygon[0])):
                #Vector_polygon[0][i].append(Vector_polygon[0][i-1][0])


            #for point_s in Vector_polygon[0]:
          #      temp_poly += point_s;
          #  temp_poly = np.array(temp_poly)
                #polyline.append(polyline[len(polyline) - 1])
          #   for p in Vector_polygon[0]:
          #
          #       #print(p)
          #       polyline.append(Point3(p[0], p[1], curr_height))
          #
          #
          # #  polyline.append(end_point)
          #   hole_polyline = []
          #
          #   height_subdivision = slopeHeight / offset_count
          #   self.Show(polyline, "polyline[" + str(0) + "]:", 1)


                #Job.yieldThread()
                # 创建 3D 图形对象
            fig = plt.figure()
            ax = Axes3D(fig)
            x = []
            y = []
            z = []
            for tri in Vector_polygon:
                x.append(tri[0])
                y.append(tri[1])
                z.append(tri[2])
                #for t in tri:
                    # p0 = [t.a.x, t.a.y, t.a.z]
                    # p1 = [t.b.x, t.b.y, t.b.z]
                    # p2 = [t.c.x, t.c.y, t.c.z]
                    # x += [t.a.x, t.b.x, t.c.x,t.a.x]
                    # y += [t.a.y, t.b.y, t.c.y,t.a.y]
                    # z += [t.a.z, t.b.z, t.c.z,t.a.z]
                    # 绘制线型图
            ax.plot(x, y, z)

            # 显示图
            plt.show()





            _matrix = Matrix()
            print("Matrix:", _matrix)

            #TODO:吧所有多边形依次相加因为我打算排序
            #self.Show(Vector_polygon, "Vector_polygon", 2)
            tmap_vertices = []
            for temp_poly in Vector_polygon:
                tmap_vertices.extend(temp_poly)

            # max_x = max(tmap_vertices, key=lambda x: x[0])
            # max_y = max(tmap_vertices, key=lambda x: x[1])
            # max_z = max(tmap_vertices, key=lambda x: x[2])
            # min_x = min(tmap_vertices, key=lambda x: x[0])
            # min_y = min(tmap_vertices, key=lambda x: x[1])
            # min_z = min(tmap_vertices, key=lambda x: x[2])
            #
            # xs = [x[0] for x in tmap_vertices]
            # ys = [x[1] for x in tmap_vertices]
            # zs = [x[2] for x in tmap_vertices]
            #
            # # 创建 3D 图形对象

            # fig = plt.figure()
            # ax = Axes3D(fig)
            # # 绘制线型图
            # ax.plot(xs, ys, zs)
            # # 显示图
            # plt.show()

            range_s = offset
            # i
            _matrix._data[1, 1] = math.sin(math.radians(range_s))
            _matrix._data[1, 2] = math.cos(math.radians(range_s))
            # j
            _matrix._data[2, 1] = math.sin(math.radians(range_s + 90))
            _matrix._data[2, 2] = math.cos(math.radians(range_s + 90))

            """它可以用来判断点在直线的某侧。进而可以解决点是否在三角形内，两个矩形是否重叠等问题。
              向量的叉积的模表示这两个向量围成的平行四边形的面积。   
                设矢量P = ( x1, y1 )，Q = ( x2, y2 )，则矢量叉积定义为由(0,0)、p1、p2和p1+p2所组成的平行四边形的带符号的面积，
                即：P×Q = x1*y2 - x2*y1，其结果是一个伪矢量。    
                显然有性质 P × Q = - ( Q × P ) 和 P × ( - Q ) = - ( P × Q )。    
            叉积的一个非常重要性质是可以通过它的符号判断两矢量相互之间的顺逆时针关系：    
            若 P × Q > 0 , 则P在Q的顺时针方向。     
            若 P × Q < 0 , 则P在Q的逆时针方向。      
            若 P × Q = 0 , 则P与Q共线，但可能同向也可能反向。      
            叉积的方向与进行叉积的两个向量都垂直，所以叉积向量即为这两个向量构成平面的法向量。    
            如果向量叉积为零向量，那么这两个向量是平行关系。    
            
            因为向量叉积是这两个向量平面的法向量，如果两个向量平行无法形成一个平面，其对应也没有平面法向量。所以，两个向量平行时，其向量叉积为零。
            """
            # 创建一个三角;Delaunay三角剖分法没有创建三角形。
            if closeTopButtonFace:
                #TODO:上下底
                tri = []
                plist = self._paths[0][::-1] if IsClockwise(self._paths[0]) else self._paths[0][:]
                while len(plist) >= 3:
                    a ,b= GetEar(plist)
                    if a == []:
                        break
                    tri.append(a)
                    plist = numpy.delete(plist, b, axis=0)
                ppp = []
                for tt in tri:
                    for p in tt:
                        ppp.append(p)
                    v0 = Vector(x=tt[0][0], y=tt[0][1], z=0).multiply(transformation_matrix)
                    v1 = Vector(x=tt[1][0], y=tt[1][1], z=0).multiply(transformation_matrix)
                    v2 = Vector(x=tt[2][0], y=tt[2][1], z=0).multiply(transformation_matrix)
                    mesh.addFace(v0,v1,v2)
                    v0 = Vector(x=tt[0][0], y=tt[0][1], z=peak_height - slopeHeight).multiply(transformation_matrix)
                    v1 = Vector(x=tt[1][0], y=tt[1][1], z=peak_height - slopeHeight).multiply(transformation_matrix)
                    v2 = Vector(x=tt[2][0], y=tt[2][1], z=peak_height - slopeHeight).multiply(transformation_matrix)
                    mesh.addFace(v0,v1,v2)



            #TODO:计算面积
            for i in range(len(self._paths)):
                areaTop += abs(pyclipper.Area(self._paths[i]))#TODO:面积
                areaBottom += abs(pyclipper.Area(self._paths[i]))
        # TODO:Bottom

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


