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
from .CDTUI import CDTUI
from .SVGjob import ProcessSVGJob
from UM.Message import Message
from UM.Application import Application
from UM.i18n import i18nCatalog
import UM.Math.Color as Color
#from cura.Vector_polygon import SBSBSBS

import svg
from .import polygon
from .triangulate import *
#import delaunay as DT
#from .Point import * #为了点计算
from . import Centerline
import pyclipper #为了点链表的计算 交叉并集等
from matplotlib.tri import triangulation
from scipy.spatial import ConvexHull
from scipy.spatial import Voronoi,Delaunay
from shapely.geometry import LineString
from shapely.geometry import MultiLineString
i18n_catalog = i18nCatalog('cura')
import matplotlib.pyplot as plt  #TODO:用作测试的 后期得删掉
import matplotlib.tri as tri
from mpl_toolkits.mplot3d import Axes3D
from p3t import CDT,Point3
import math
import numpy as np
import time

def load_points(file_name):
    infile = open(file_name, "r")
    points = []
    while infile:
        line = infile.readline()
        line = line.replace("[", "")
        line = line.replace("]", "")
        line = line.replace("\n", "")
       # ss = list_to_string(line)
        #ss = list(line)
        s = line.split(',')
        #print("SB:",s,len(s))
        if len(s) <= 2:
            break
        try:
            points.append([float(s[0]), float(s[1]), float(s[2])])
        except ValueError :
            print("ss")
    return points

_subdivision = 0.5 #细分问题
EPSILON = 0.000001
class SVGFileReader(MeshReader):

    def __init__(self):
        super().__init__()
        self._supported_extensions = [".svg"] #抱歉，你还必须在这里指定它。
        self._ui = VectorReaderUI(self)
        self._Cdt = CDTUI(self)
        self._paths = None
        self._start_SvG_job = ProcessSVGJob(None,None)
        #self._Points = None
        self.poly_count = 0 #多边形个数 用了判断可不可以拆分--> 应该吧计算出来的东西放在一个结构里面 而不是直接这么用


    def Show(self,path,name,arg):
        plt.title(name)

        x = []
        y = []
        index = 0
        if arg > 1:
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
                    plt.annotate('Start', xy=(point_s[0], point_s[1]), xytext=(point_s[0] + 3, point_s[1] + 1.5),
                                 arrowprops=dict(facecolor='black', shrink=0.05),
                                 )
                    print("point:", point_s)
                index += 1
                x.append(point_s[0])
                y.append(point_s[1])

        plt.plot(x, y, 'r--')
        plt.xlabel('x')
        plt.ylabel('y')
        plt.axis('equal')
        #plt.show()
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
            #self._Points = []
            #v = Vector
            #Point_s = []
            def MM2Int(a):
                return (a*1)
            #poly_count = 0 #多边形个数 用了判断可不可以拆分
            for d in svg_segments:
                if hasattr(d, 'segments'):
                    for l in d.segments(1):
                        x, y = l[0].coord()
                        print("move:(%f,%f)" % (x, y))
                        #hull_poins1 = [Vector(x=x, y=y, z=0)]
                        hull_poins1 = [[x,y]]
                       # Point_s = [[MM2Int(x), MM2Int(y)]]
                        self.poly_count += 1 #多边形个数 用了判断可不可以拆分
                        for pt in l[1:]:
                            x, y = pt.coord()
                            #hull_poins1.append(Vector(x=x, y=y, z=0))
                            hull_poins1.append([x,y])
                            #Point_s.append([MM2Int(x), MM2Int(y)])
                        hull_poins1.append(hull_poins1[0])
                        self._paths.append(hull_poins1)
                        #self._Points.append(Point_s)
                    #self._Points.append(point_list)
                else:
                    Logger.log('e', "Unsupported SVG element")
                    #print("Unsupported SVG element")


        if not self._paths:
            Logger.log('e', "Conn't load paths.")
            return MeshReader.PreReadResult.failed
        #Point_s = expand_polygon(reult)
        paths = []
        for p in self._paths:
            paths += p
        paths_line = LineString(paths)
        # 基地层
        polygon = paths_line.buffer(0.001)
        path = list(np.asarray(polygon.interiors[0]))

        pco = pyclipper.PyclipperOffset()
        for points in self._paths:
            points = np.array(points)*1000
            pco.AddPath(points, pyclipper.JT_ROUND, pyclipper.ET_CLOSEDPOLYGON)
        #pco.AddPath(p, pyclipper.JT_ROUND, pyclipper.ET_CLOSEDPOLYGON)
        solution = pco.Execute(-1)
        self.Show(solution, "solution", 2)
        start = time.clock()
        name = "./output"+"Temp" + ".dat"
        f = open(name, 'w')
        for point in self._paths:
            point = np.array(point) * 1000
            for point_s in point:
                f.write(str(int(point_s[0])/1000)+" "+ str(int(point_s[1])/1000) + "\n")
        f.close()

        # i = 0
        # name = "./output"+"Temp" + ".dat"
        # f = open(name, 'w')
        # for point_s in self._paths:
        #     #index = len(point_s)
        #     #f.write(str(index)+"\n")
        #     #for point_s in self._paths:
        #     for point in point_s:
        #         f.write(str(point)+"\n")
        #     i += 1
        # f.close()

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
            offset_count = offset_set/_subdivision
            curr_height = peak_height - slopeHeight
            paths = []
            for p in self._paths:
                paths += p

            line_path = LineString(paths)
            polygon = line_path.buffer(0.001)
            path = list(np.asarray(polygon.interiors[0]))
            for p in range(len(path)):
                path[p] = np.append(path[p],curr_height)
            Vector_polygon = []
            Vector_polygon.append(path)
            height_subdivsion = slopeHeight / offset_count
                                    #
                                    # self._Cdt.showConfigUI()
                                    # self._Cdt.waitForUIToClose()
                                    # if self._Cdt.getCancelled():
                                    #     return MeshReader.PreReadResult.cancelled
                                    #
                                    # Vector_polygon_SBSBSBSB = load_points("./Vector_SBA1.txt")
                                    # index = 3
                                    # while index < len(Vector_polygon_SBSBSBSB):
                                    #     v0 = Vector(x=Vector_polygon_SBSBSBSB[index - 3][0], y=Vector_polygon_SBSBSBSB[index - 3][1],
                                    #                 z = Vector_polygon_SBSBSBSB[index - 3][2])#.multiply(transformation_matrix)
                                    #     v1 = Vector(x=Vector_polygon_SBSBSBSB[index - 2][0], y=Vector_polygon_SBSBSBSB[index - 2][1],
                                    #                 z=Vector_polygon_SBSBSBSB[index - 2][2])#.multiply(transformation_matrix)
                                    #     v2 = Vector(x=Vector_polygon_SBSBSBSB[index - 1][0], y=Vector_polygon_SBSBSBSB[index - 1][1],
                                    #                 z=Vector_polygon_SBSBSBSB[index - 1][2])#.multiply(transformation_matrix)
                                    #     mesh.addFace(v0, v1, v2)
                                    #     index += 3

            for index_ in range(1, int(offset_count)+1):
                polygon1 = line_path.buffer(index_*_subdivision)
                curr_height = curr_height + height_subdivsion
                if len(polygon1.interiors) < 1:
                    continue
                path1 = list(np.asarray(polygon1.interiors[0]))
                for p in range(len(path1)):
                    path1[p] = np.append(path1[p], curr_height)
                Vector_polygon.append(path1)
            polyLine = []
            for p in Vector_polygon[0]:
                polyLine.append(Point3(p[0],p[1],p[2]))
            for index_ in range(1, len(Vector_polygon)):
                self._start_SvG_job.setPolyLine(polyLine)

                #cdt = CDT(polyLine)
                hole_polyLine = []
                for p in Vector_polygon[index_]:
                    hole_polyLine.append(Point3(p[0], p[1], 10))
                self._start_SvG_job.setHole_polyLine(hole_polyLine)
                #self._start_SvG_job.start()
                triangles = self._start_SvG_job.getTriangles()
                print ("sss",triangles)
                #triangles = SBSBSBS(polyLine,hole_polyLine)
                #triangles = cdt.triangulate()
                polyLine = hole_polyLine
                # # 创建 3D 图形对象
                # fig = plt.figure()
                # ax = Axes3D(fig)
                # for t in triangles:
                #     p0 = [t.a.x, t.a.y, t.a.z]
                #     p1 = [t.b.x, t.b.y, t.b.z]
                #     p2 = [t.c.x, t.c.y, t.c.z]
                #     x = [t.a.x, t.b.x, t.c.x, t.a.x]
                #     y = [t.a.y, t.b.y, t.c.y, t.a.y]
                #     z = [t.a.z, t.b.z, t.c.z, t.a.z]
                #     # 绘制线型图
                #     ax.plot(x, y, z)
                #
                # # 显示图
                # plt.show()
            # cdt = CDT(polyLine)
            # for index_ in range(1, len(Vector_polygon)):
            #     hole_polyLine = []
            #     for p in Vector_polygon[index_]:
            #         hole_polyLine.append(Point3(p[0],p[1],p[2]))
            #     Job.yieldThread()
            #
            #     Job.yieldThread()
            #     if hole_polyLine:
            #         cdt.add_hole(hole_polyLine)
            #     Job.yieldThread()
            #     triangle = cdt.triangulate()
            #     print("""SBSBBSBSBS""")
            # tmap_vertices = []
            # for temp_poly in Vector_polygon:
            #     tmap_vertices.extend(temp_poly)

            _matrix = Matrix()
            print("Matrix:", _matrix)

            #TODO:吧所有多边形依次相加因为我打算排序
            self.Show(Vector_polygon, "Vector_polygon", 2)
            tmap_vertices = []
            for temp_poly in Vector_polygon:
                tmap_vertices.extend(temp_poly)
            max_x = max(tmap_vertices, key=lambda x: x[0])
            max_y = max(tmap_vertices, key=lambda x: x[1])
            max_z = max(tmap_vertices, key=lambda x: x[2])
            min_x = min(tmap_vertices, key=lambda x: x[0])
            min_y = min(tmap_vertices, key=lambda x: x[1])
            min_z = min(tmap_vertices, key=lambda x: x[2])

            xs = [x[0] for x in tmap_vertices]
            ys = [x[1] for x in tmap_vertices]
            zs = [x[2] for x in tmap_vertices]
            # num_faces = len(tmap_vertices) // 3
            # num_verts = len(tmap_vertices)
            # self.reserveFaceAndVertexCount(num_faces,num_verts)
            # self.addFace(tmap_vertices,True)
            # # # 创建 3D 图形对象
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


