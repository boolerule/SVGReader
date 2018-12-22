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
from UM.Message import Message
from UM.Application import Application
from UM.i18n import i18nCatalog
import UM.Math.Color as Color

import svg
from .import polygon
from .triangulate import *
#import delaunay as DT
#from .Point import * #为了点计算
from . import Centerline
import pyclipper #为了点链表的计算 交叉并集等
from scipy.spatial import Voronoi,Delaunay
from shapely.geometry import LineString
from shapely.geometry import MultiLineString
i18n_catalog = i18nCatalog('cura')
import matplotlib.pyplot as plt  #TODO:用作测试的 后期得删掉
import matplotlib.tri as tri
from mpl_toolkits.mplot3d import Axes3D
import math
import numpy as np
import time

_subdivision = 0.12 #细分问题
EPSILON = 0.000001
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
        # minx = 0#int(min(self._paths[0])[0])
        # miny = 0#int(min(self._paths[0])[1])
        # tri = Delaunay(self._paths[0])
        # p = tri.points
        # c= tri.simplices
        # self.Show(c,"SB",2)
        # vor = Voronoi(tri)
        # vertex = vor.vertices
        # lst_lines = []
        # for j, ridge in enumerate(vor.ridge_vertices):
        #     if -1 not in ridge:
        #         line = LineString([
        #             (vertex[ridge[0]][0] + minx, vertex[ridge[0]][1] + miny),
        #             (vertex[ridge[1]][0] + minx, vertex[ridge[1]][1] + miny)])
        #
        #         if len(line.coords[0]) > 1:
        #             lst_lines.append(np.asarray(line))

        #return MultiLineString(lst_lines)
        # polygon = LineString(self._paths[0]).buffer(0.05)
        # centerline = Centerline.Centerline(polygon);
        # path = centerline.create_centerline();
        #self.Show( path,"haha",2)
        #TODO：我打算通过算交集来算出他们是否相交这是不合理的，暂时用着
        # if self.poly_count >= 2:
        #     for index in  range(1,len(self._paths)):
        #         temp = polygon.polygonCollision(np.array(self._paths[index - 1]),np.array(self._paths[index]))
        #         print("Temp:",temp)
        #
        #         if not isinstance(temp , bool):
        #             self.Show(self._paths, "solution-" + str(temp), 2)
        # else:
        #     self._Split = False #多边形少于2
        #整理一下数据
        # count = len(self._Points)
        #
        # result = []
        # Curr_orientation = True #顺时针为正 逆时针为负
        # Prev_orientation = True
        #TODO:当存在多个模型嵌套时，他们的方向要是相反的
        # for index in range(len(self._Points)):
        #     if len(self._Points[index]) == 2:
        #         self._Points = self._Points[::-1] if IsClockwise(self._Points) else self._Points[:]
        #         break
        #     Curr_orientation = IsClockwise(self._Points[index])# 当前链表的方向
        #     if Prev_orientation == Curr_orientation and index !=0:
        #         Curr_orientation = not Prev_orientation
        #
        #     if Curr_orientation:
        #         self._Points[index] = self._Points[index][::-1]
        #     else:
        #         self._Points[index] = self._Points[index][:]
        #     Prev_orientation = Curr_orientation

        # #链接多个模型
        #
        # for index in range(1,len(self._Points)):
        #     endPoint1 = self._Points[index - 1][len(self._Points[index - 1]) - 1]
        #     self._Points[index].insert(0, endPoint1)#开头加一个
        #     self._Points[index].append(endPoint1)#后面加一个
        # reult = self._Points[0]
        # for index in range(1,len(self._Points)):
        #     reult = np.concatenate([reult,self._Points[index]])
        #
        # self._Points = reult
        #Point_s = expand_polygon(reult)
       # self.Show(self._Points,"SB",1)
       #  i = 0
       #  name = "./output" + svg_file.title() + ".txt"
       #  f = open(name, 'w')
       #  for point_s in self._paths:
       #      index = len(point_s)
       #      f.write(str(index)+"\n")
       #      #for point_s in self._paths:
       #      for point in point_s:
       #          f.write(str(point)+"\n")
       #
       #      i += 1
       #  f.close()

        start = time.clock()

        print(("Poly-Triangulierung: %.2fs" % (time.clock() - start)))

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

            for index_ in range(1, int(offset_count)+1):
                polygon1 = line_path.buffer(index_*_subdivision)
                curr_height = curr_height + _subdivision
                if len(polygon1.interiors) < 1:
                    continue
                path1 = list(np.asarray(polygon1.interiors[0]))
                for p in range(len(path1)):
                    path1[p] = np.append(path1[p], curr_height)
                Vector_polygon.append(path1)
            tmap_vertices = []
            for temp_poly in Vector_polygon:
                tmap_vertices.extend(temp_poly)

            num_verts = len(tmap_vertices)
            num_faces = num_verts//3
            self.reserveFaceAndVertexCount(num_faces,num_verts)
            indices = [ i for i in range(len(tmap_vertices))]
            self.index_base = 0
            for p in path:
                self.addVertex(p[0],p[1],10)
            self.addFace(indices,False)

                #self.Show(path1,"path"+str(index_),1)
                #aaa = path#Polygon_subdivision(path, _subdivision)
                #bbb = path1# Polygon_subdivision(path1, _subdivision)
                # for ii in range(len(bbb) - 1):
                #     p0 = bbb[ii]
                #     p1 = bbb[ii + 1]
                #     p2 = aaa[ii + 1]
                #     # p_tri.append([p0, p1, p2])
                #     p3 = aaa[ii + 1]
                #     p4 = aaa[ii]
                #     p5 = bbb[ii]
                #     a = Vector(x=p0[0], y=p0[1], z=curr_height + _subdivision).multiply(transformation_matrix)
                #     b = Vector(x=p1[0], y=p1[1], z=curr_height + _subdivision).multiply(transformation_matrix)
                #     c = Vector(p2[0], p2[1], curr_height).multiply(transformation_matrix)
                #     # build_list.append(poins[indx],poins[indx])
                #     mesh.addFace(a, b, c)
                #     # mesh.addFaceByPoints(a.x, a.y, a.z, b.x, b.y, b.z, c.x, c.y, c.z)
                #     # 下一个面
                #     d = Vector(x=p4[0], y=p4[1], z=curr_height).multiply(
                #         transformation_matrix)
                #     mesh.addFace(c, d, a)
               # polygon = polygon1
               # path = path1
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

            # 创建 3D 图形对象
            fig = plt.figure()
            ax = Axes3D(fig)
            # 绘制线型图
            ax.plot(xs, ys, zs)
            # 显示图
            plt.show()
            #直角坐标系中，任意一点(x，y)到原点的距离d=√(x²+y²)
            tmap_vertices.sort(key=lambda dist:math.sqrt(dist[0]*dist[0] + dist[1]*dist[1]))#以 点到原点的距离为判断依据（不考虑z轴）





            #p_tri = []

                #mesh.addFaceByPoints(c.x, c.y, c.z, d.x, d.y, d.z, a.x, a.y, a.z)





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

            #
            # self.Show(ppp,"qqqq",1)
                #mesh.addConvexPolygonExtrusion(poins,1,10)
            scale_Paths = self._paths
            # if self.poly_count >= 2:
            #     for index in  range(0,len(self._paths)):#全部等比例放大
            #         scale_Paths.append(pyclipper.scale_to_clipper(self._paths[index], offset_set))
            # else:
            #     scale_Paths = pyclipper.scale_to_clipper(self._paths, offset)
            # #self.Show(scale_Paths,"scale_Paths",2)
            # #path_s = self._paths
            # #bbb = scale_polygon(self._paths[0], offset_set)
            # #self.Show(bbb, "bbb", 1)
            # #aaa = [bbb]
            # #TODO:我需要把中心点归类
            # for path_index in range(len(scale_Paths)):
            #     a_center = centerOfMass(scale_Paths[path_index])
            #     p_center = centerOfMass(self._paths[path_index])
            #     X_offset = a_center[0] - p_center[0]
            #     Y_offset = a_center[1] - p_center[1]
            #     print("SB:",a_center,p_center)
            #    # index = 0
            #     for index in range(len(scale_Paths[path_index])):
            #         scale_Paths[path_index][index][0] -=  X_offset
            #         scale_Paths[path_index][index][1] -=  Y_offset
                #self.Show(scale_Paths[path_index], "scale_Paths[path_index]", 1)


            #TODO:偏移点
            # for _index in range(len(self._paths)):
            #     indx = 0
            #     while indx < len(self._paths[_index]) - 1:
            #         # print("Ver:",poins[indx])
            #         a = Vector(x=self._paths[_index][indx][0], y=self._paths[_index][indx][1], z=peak_height - slopeHeight).multiply(transformation_matrix)
            #         b = Vector(x=scale_Paths[_index][indx][0], y=scale_Paths[_index][indx][1], z=peak_height ).multiply(_matrix)
            #         c = Vector(self._paths[_index][indx + 1][0], self._paths[_index][indx + 1][1], z=peak_height - slopeHeight).multiply(transformation_matrix)
            #         # build_list.append(poins[indx],poins[indx])
            #         # mesh.addFace(a,b,c)
            #         mesh.addFaceByPoints(a.x, a.y, a.z, b.x, b.y, b.z, c.x, c.y, c.z)
            #         # 下一个面
            #         a1 = Vector(x=scale_Paths[_index][indx][0], y=scale_Paths[_index][indx][1], z=peak_height).multiply(transformation_matrix)
            #         b1 = Vector(x=scale_Paths[_index][indx + 1][0], y=scale_Paths[_index][indx + 1][1], z=peak_height).multiply(
            #             _matrix)
            #         c1 = Vector(self._paths[_index][indx + 1][0], self._paths[_index][indx + 1][1], z=peak_height - slopeHeight).multiply(transformation_matrix)
            #         # mesh.addFace(c, b1, b)
            #         mesh.addFaceByPoints(a1.x, a1.y, a1.z, b1.x, b1.y, b1.z, c1.x, c1.y, c1.z)
            #         indx += 1
            #TODO:计算面积
            for i in range(len(self._paths)):
                areaTop += abs(pyclipper.Area(self._paths[i]))#TODO:面积
                areaBottom += abs(pyclipper.Area(scale_Paths[i]))
            #self.Show(scale_Paths[_index], "aaa", 2)
            # pcOffset = pyclipper.PyclipperOffset()
            # pcOffset.AddPaths(self._paths, pyclipper.JT_SQUARE, pyclipper.ET_CLOSEDLINE)
            # result = pcOffset.Execute(offset)
            # i = 0
            #
            # for point_s in result:
            #     index = len(point_s)
            #     name = "./result_"+ str(offset)+ "倍"+str(i)+".txt"
            #     f = open(name, 'w')
            #     f.write(str(index) + "\n")
            #     # for point_s in self._paths:
            #     for point in point_s:
            #         f.write(str(point) + "\n")
            #     f.close()
            #     i += 1
            #
            # self.Show(result[0], "result[0]", 1)
            # self.Show(result, "result", 2)
            # for path in self._paths:
            #     pcOffset = pyclipper.PyclipperOffset()
            #     pcOffset.AddPath(path, pyclipper.JT_SQUARE, pyclipper.ET_CLOSEDLINE)
            #     result = pcOffset.Execute(offset)
            #     #由于一些模型路径的关系我们只能用第一个链表
            #     if len(result) > 1:
            #         m = Message(i18n_catalog.i18nc(
            #             '@warning:status',
            #             '模型偏移后的数据出现异常，这可能导致偏移部分的精度有一定误差！'),
            #             lifetime=0)
            #         m.addAction("MoreInfo", name=i18n_catalog.i18nc("@action:button", "More info"), icon=None,
            #                    description=i18n_catalog.i18nc("@action:tooltip",
            #                                              "有问题请找twosilly."),
            #                    button_style=Message.ActionButtonStyle.LINK)
            #         m._filename = file_name
            #         m.actionTriggered.connect(self._onMessageActionTriggered)
            #         m.show()
            #     self.Show(path, "path", 1)
            #     result[0].append(result[0][0])
            #     self.Show(result[0],"result[0]",1)
            #     i = 0
            #     for point_s in result:
            #         index = len(point_s)
            #         name = "./result" + str(i) + ".txt"
            #         f = open(name, 'w')
            #         f.write(str(index) + "\n")
            #         # for point_s in self._paths:
            #         for point in point_s:
            #             f.write(str(point) + "\n")
            #         f.close()
            #         i += 1
            #
            #     #temp_path = path + result[0]
            #
            #     areaTop = abs(pyclipper.Area(path))#TODO:面积
            #     areaBottom = abs(pyclipper.Area(result[0]))
            #     #result[0] = pyclipper.CleanPolygon(result[0])#删除不必要的点
            #     #path = pyclipper.CleanPolygon(path)  # 删除不必要的点
            #     #TODO：把放大的模型以此打开看看
            #     # for pp in result:
            #     #     pp.append(pp[0])
            #     #     self.Show(pp, "result",1)
            #
            #     pc = pyclipper.Pyclipper()
            #     pc.AddPath(path, pyclipper.PT_CLIP, True)
            #     pc.AddPath(result[0], pyclipper.PT_SUBJECT, True)
            #     solution = pc.Execute(pyclipper.CT_DIFFERENCE, pyclipper.PFT_EVENODD, pyclipper.PFT_NEGATIVE)#交集
            #     self.Show(solution, "solution", 2)
            #
            #
            #     index = 0
            #     path_result = []
            #     for solut in solution:
            #         path_result += solut
            #     # res = result[0]
            #     # res.append(res[0])
            #     # path_result = res[::-1] if IsClockwise(res) else res[:]
            #     # pp_path = path
            #     # pp_path.append(res[len(res) - 1])#加一个未值
            #     # pp_path.insert(0,res[len(res) - 1])
            #     # path_result += pp_path[::-1] if IsClockwise(pp_path) else pp_path[:]
            #
            #
            #     # 创建一个三角;Delaunay三角剖分法没有创建三角形。
            #     tri = []
            #     plist = path_result[::-1] if IsClockwise(path_result) else path_result[:]
            #     while len(plist) >= 3:
            #         a,b = GetEar(plist)
            #         plist = numpy.delete(plist, b, axis=0)
            #         if a == []:
            #             break
            #         tri.append(a)
            #     ppp = []
            #
            #     for tt in tri:
            #         V = []
            #         for p in tt:
            #             if p in np.array(path):
            #                 V.append(Vector(x=p[0], y=p[1], z=peak_height - slopeHeight ).multiply(transformation_matrix))
            #             elif p in np.array(result[0]):
            #                 V.append(Vector(x=p[0], y=p[1], z=peak_height ).multiply(transformation_matrix))
            #             else:
            #                 V.append(Vector(x=p[0], y=p[1], z=peak_height - slopeHeight ).multiply(transformation_matrix))
            #                 print("other:")
            #                 #print("other:",V[2])
            #             ppp.append(p)
            #         mesh.addFace(V[0], V[1], V[2])
            #         v0 = Vector(x=tt[0][0], y=tt[0][1], z=0).multiply(transformation_matrix)
            #         v1 = Vector(x=tt[1][0], y=tt[1][1], z=0).multiply(transformation_matrix)
            #         v2 = Vector(x=tt[2][0], y=tt[2][1], z=0).multiply(transformation_matrix)
            #         mesh.addFace(v0, v1, v2)
            #         v0 = Vector(x=tt[0][0], y=tt[0][1], z=peak_height - slopeHeight).multiply(transformation_matrix)
            #         v1 = Vector(x=tt[1][0], y=tt[1][1], z=peak_height - slopeHeight).multiply(transformation_matrix)
            #         v2 = Vector(x=tt[2][0], y=tt[2][1], z=peak_height - slopeHeight).multiply(transformation_matrix)
            #         mesh.addFace(v0, v1, v2)
            #     self.Show(ppp, "ppp", 1)




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





    # 任意多边形三角剖分。
    # 不假定凸性，也不检查文件中的“凸”标志。
    # 采用“切耳”算法工作:
    # - 找到一个外部顶点，它的角度最小，相邻三角形内没有顶点
    # - 去掉那个顶点的三角形
    # - 重复,直到完成
    # 顶点坐标应该已经设置好了
    def addFace(self, indices, ccw):
        # 将索引解析为坐标，以便更快地进行数学运算
        face = [Vector(data=self.verts[0:3, i]) for i in indices]

        # 需要一个平面的法线这样我们就能知道哪些顶点构成内角
        normal = findOuterNormal(face)

        if not normal:  # 可能找不到外边，非平面多边形?
            return

        # 找到内角最小且内无点的顶点，将其截断，重复直至完成
        n = len(face)
        vi = [i for i in range(n)]  # 我们将用它来从表面踢顶点
        while n > 3:
            max_cos = EPSILON  # 我们不需要检查角度
            i_min = 0  # max cos对应的是最小角
            for i in range(n):
                inext = (i + 1) % n
                iprev = (i + n - 1) % n
                v = face[vi[i]]
                next = face[vi[inext]] - v
                prev = face[vi[iprev]] - v
                nextXprev = next.cross(prev)
                if nextXprev.dot(normal) > EPSILON:  # 如果是内角
                    cos = next.dot(prev) / (next.length() * prev.length())
                    if cos > max_cos:
                        # 检查三角形中是否有顶点
                        no_points_inside = True
                        for j in range(n):
                            if j != i and j != iprev and j != inext:
                                vx = face[vi[j]] - v
                                if pointInsideTriangle(vx, next, prev, nextXprev):
                                    no_points_inside = False
                                    break

                        if no_points_inside:
                            max_cos = cos
                            i_min = i

            self.addTriFlip(indices[vi[(i_min + n - 1) % n]], indices[vi[i_min]], indices[vi[(i_min + 1) % n]], ccw)
            vi.pop(i_min)
            n -= 1
        self.addTriFlip(indices[vi[0]], indices[vi[1]], indices[vi[2]], ccw)

    # Indices are 0-based for this shape, but they won't be zero-based in the merged mesh
    #这个形状的索引是基于0的，但是在合并后的网格中它们不是基于0的
    def addTri(self, a, b, c):
        if self.num_faces == 106:
            print("ds")
        self.faces[self.num_faces, 0] =  a
        self.faces[self.num_faces, 1] =  b
        self.faces[self.num_faces, 2] =  c
        self.num_faces += 1

    def addTriFlip(self, a, b, c, ccw):
        if ccw:
            self.addTri(a, b, c)
        else:
            self.addTri(b, a, c)
    def reserveFaceAndVertexCount(self, num_faces, num_verts):
        # 与Cura MeshBuilder不同，我们使用存储为列的4个向量来进行更简单的转换
        self.verts = numpy.zeros((4, num_verts), dtype=numpy.float32)
        self.verts[3,:] = numpy.ones((num_verts), dtype=numpy.float32)
        self.num_verts = 0
        self.reserveFaceCount(num_faces)
    def reserveFaceCount(self, num_faces):
        self.faces = numpy.zeros((num_faces, 3), dtype=numpy.int32)
        self.num_faces = 0
    def addVertex(self, x, y, z):
        if self.num_verts == 314:
            print("sd")
        self.verts[0, self.num_verts] = x
        self.verts[1, self.num_verts] = y
        self.verts[2, self.num_verts] = z
        self.num_verts += 1

# Given a face as a sequence of vectors, returns a normal to the polygon place that forms a right triple
# with a vector along the polygon sequence and a vector backwards
# 正常多边形是向量序列，多边形序列和向后向量
# 发现外法向量
def findOuterNormal(face):
    n = len(face)
    for i in range(n):
        for j in range(i + 1, n):
            edge = face[j] - face[i]
            if edge.length() > EPSILON:
                edge = edge.normalized()
                prev_rejection = Vector()
                is_outer = True
                for k in range(n):
                    if k != i and k != j:
                        pt = face[k] - face[i]
                        pte = pt.dot(edge)
                        rejection = pt - edge * pte
                        if rejection.dot(prev_rejection) < -EPSILON:  # 边缘两边的点——不是外侧的点
                            is_outer = False
                            break
                        elif rejection.length() > prev_rejection.length():  # 选择一个更大的拒绝数字稳定性
                            prev_rejection = rejection

                if is_outer:  # 找到一个外边缘，prev_rejection是面内的拒绝。生成一个正常。
                    return edge.cross(prev_rejection)

    return False

# 给定两个*共线*向量a和b，返回使b到a的系数。
# 没有错误处理
# 为了稳定性，取最大坐标之间的比值会更好……
# 比率
def ratio(a, b):
    if b.x > EPSILON or b.x < -EPSILON:
        return a.x / b.x
    elif b.y > EPSILON or b.y < -EPSILON:
        return a.y / b.y
    else:
        return a.z / b.z

# 点在三角形
def pointInsideTriangle(vx, next, prev, nextXprev):
    vxXprev = vx.cross(prev)
    r = ratio(vxXprev, nextXprev)
    if r < 0:
        return False
    vxXnext = vx.cross(next);
    s = -ratio(vxXnext, nextXprev)
    return s > 0 and (s + r) < 1
