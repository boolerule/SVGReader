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
from collision import Concave_Poly,collide #为了检测多边形是否包含
#from scipy.spatial import Delaunay
#from .delaunay import *
#from .test import testPath
#from .delaunay import Delaunay_Triangulation,Delaunay_Point
from .triangulate import *
#import delaunay as DT
#from .Point import * #为了点计算
import pyclipper #为了点链表的计算 交叉并集等
i18n_catalog = i18nCatalog('cura')
import matplotlib.pyplot as plt  #TODO:用作测试的 后期得删掉
import matplotlib.tri as tri
import math
import numpy as np
import time
import polytri

class SVGFileReader(MeshReader):

    def __init__(self):
        super().__init__()
        self._supported_extensions = [".svg"] #抱歉，你还必须在这里指定它。
        self._ui = VectorReaderUI(self)
        self._paths = None
        self._Points = None
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

        plt.plot(x, y, 'r')
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
            self._Points = []
            v = Vector
            Point_s = []
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
                        Point_s = [v(MM2Int(x), MM2Int(y))]
                        self.poly_count += 1 #多边形个数 用了判断可不可以拆分
                        for pt in l[1:]:
                            x, y = pt.coord()
                            #hull_poins1.append(Vector(x=x, y=y, z=0))
                            hull_poins1.append([x,y])
                            Point_s.append(v(MM2Int(x), MM2Int(y)))
                        hull_poins1.append(hull_poins1[0])
                        self._paths.append(hull_poins1)
                        self._Points.append(Point_s)
                    #self._Points.append(point_list)
                else:
                    Logger.log('e', "Unsupported SVG element")
                    #print("Unsupported SVG element")


        if not self._paths:
            Logger.log('e', "Conn't load paths.")
            return MeshReader.PreReadResult.failed
        #TODO：我打算通过算交集来算出他们是否相交这是不合理的，暂时用着
        if self.poly_count >= 2:
            for index in  range(1,len(self._paths)):
                temp = polygon.polygonCollision(np.array(self._paths[index - 1]),np.array(self._paths[index]))
                print("Temp:",temp)

                if not isinstance(temp , bool):
                    self.Show(self._paths, "solution-" + str(temp), 2)
        else:
            self._Split = False #多边形少于2
        #整理一下数据
        count = len(self._Points)

        result = []
        Curr_orientation = True #顺时针为正 逆时针为负
        Prev_orientation = True
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

        #链接多个模型

        for index in range(1,len(self._Points)):
            endPoint1 = self._Points[index - 1][len(self._Points[index - 1]) - 1]
            self._Points[index].insert(0, endPoint1)#开头加一个
            self._Points[index].append(endPoint1)#后面加一个
        reult = self._Points[0]
        for index in range(1,len(self._Points)):
            reult = np.concatenate([reult,self._Points[index]])

        self._Points = reult
        #Point_s = expand_polygon(reult)
       # self.Show(self._Points,"SB",1)
        i = 0
        name = "./output" + svg_file.title() + ".txt"
        f = open(name, 'w')
        for point_s in self._paths:
            index = len(point_s)
            f.write(str(index)+"\n")
            #for point_s in self._paths:
            for point in point_s:
                f.write(str(point)+"\n")

            i += 1
        f.close()

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
        areaTop = 0
        areaBottom = 0
        pathDetectNotEqual = False #路径检测不相等
        #TODO:#创建一个转换矩阵，从3mf世界空间转换为我们的。
        #第一步:翻转y轴和z轴。
        transformation_matrix = Matrix()
        transformation_matrix._data[1, 1] = 0
        transformation_matrix._data[1, 2] = 1
        transformation_matrix._data[2, 1] = 1
        transformation_matrix._data[2, 2] = 0
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
            angle =  offset*(math.pi/180)
            #实际偏移
            offset_set = slopeHeight * math.cos(angle)


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
            #TODO:上下底
            # tri = []
            # plist = self._Points[::-1] if IsClockwise(self._Points) else self._Points[:]
            # while len(plist) >= 3:
            #     if len(plist) == 10:
            #         print("SB:",plist[0])
            #     a ,b= GetEar(plist)
            #     if a == []:
            #         break
            #     tri.append(a)
            #     plist = numpy.delete(plist, b, axis=0)
            # ppp = []
            # for tt in tri:
            #     for p in tt:
            #         ppp.append(p)
            #     v0 = Vector(x=tt[0][0], y=tt[0][1], z=0).multiply(transformation_matrix)
            #     v1 = Vector(x=tt[1][0], y=tt[1][1], z=0).multiply(transformation_matrix)
            #     v2 = Vector(x=tt[2][0], y=tt[2][1], z=0).multiply(transformation_matrix)
            #     mesh.addFace(v0,v1,v2)
            #     v0 = Vector(x=tt[0][0], y=tt[0][1], z=peak_height - slopeHeight).multiply(transformation_matrix)
            #     v1 = Vector(x=tt[1][0], y=tt[1][1], z=peak_height - slopeHeight).multiply(transformation_matrix)
            #     v2 = Vector(x=tt[2][0], y=tt[2][1], z=peak_height - slopeHeight).multiply(transformation_matrix)
            #     mesh.addFace(v0,v1,v2)
            #
            # self.Show(ppp,"qqqq",1)
                #mesh.addConvexPolygonExtrusion(poins,1,10)
            scale_Paths = []
            if self.poly_count >= 2:
                for index in  range(0,len(self._paths)):#全部等比例放大
                    scale_Paths.append(pyclipper.scale_to_clipper(self._paths[index], offset_set))
                    # temp = polygon.polygonCollision(np.array(self._paths[index]),np.array(self._paths[index+1]))
                    # print("Temp:",temp)
                    # # if not isinstance(temp , bool):
                    # #     self.Show(self._paths, "solution-" + str(temp), 2)
                    # if temp:#如果有嵌套
                    #     area0 = abs(pyclipper.Area(self._paths[index]))  # TODO:面积
                    #     area1 = abs(pyclipper.Area(self._paths[index+1]))
                    #
                    # if not temp:
                    #     scale_Paths.append(pyclipper.scale_to_clipper(self._paths[index], offset))
            else:
                scale_Paths = pyclipper.scale_to_clipper(self._paths, offset)
            self.Show(scale_Paths,"scale_Paths",2)
            #path_s = self._paths
            #bbb = scale_polygon(self._paths[0], offset_set)
            #self.Show(bbb, "bbb", 1)
            #aaa = [bbb]
            #TODO:我需要把中心点归类
            for path_index in range(len(scale_Paths)):
                a_center = centerOfMass(scale_Paths[path_index])
                p_center = centerOfMass(self._paths[path_index])
                X_offset = a_center[0] - p_center[0]
                Y_offset = a_center[1] - p_center[1]
                print("SB:",a_center,p_center)
               # index = 0
                for index in range(len(scale_Paths[path_index])):
                    scale_Paths[path_index][index][0] -=  X_offset
                    scale_Paths[path_index][index][1] -=  Y_offset
                self.Show(scale_Paths[path_index], "scale_Paths[path_index]", 1)
            # while index < len(aaa) -1:
            #     # if aaa[index][0] > X_offset:
            #     #     aaa[index][0] += offset
            #     # else:
            #     #     aaa[index][0] -= offset
            #     # if aaa[index][1] > Y_offset:
            #     #     aaa[index][1] += offset
            #     # else:
            #     #     aaa[index][1] -= offset
            #     aaa[index][0] +=  X_offset
            #     aaa[index][1] +=  Y_offset
            #     index += 1


            for _index in range(len(self._paths)):
                indx = 0
                while indx < len(self._paths[_index]) - 1:
                    # print("Ver:",poins[indx])
                    a = Vector(x=self._paths[_index][indx][0], y=self._paths[_index][indx][1], z=peak_height - slopeHeight).multiply(transformation_matrix)
                    b = Vector(x=scale_Paths[_index][indx][0], y=scale_Paths[_index][indx][1], z=peak_height ).multiply(transformation_matrix)
                    c = Vector(self._paths[_index][indx + 1][0], self._paths[_index][indx + 1][1], z=peak_height - slopeHeight).multiply(transformation_matrix)
                    # build_list.append(poins[indx],poins[indx])
                    # mesh.addFace(a,b,c)
                    mesh.addFaceByPoints(a.x, a.y, a.z, b.x, b.y, b.z, c.x, c.y, c.z)
                    # 下一个面
                    a1 = Vector(x=scale_Paths[_index][indx][0], y=scale_Paths[_index][indx][1], z=peak_height).multiply(transformation_matrix)
                    b1 = Vector(x=scale_Paths[_index][indx + 1][0], y=scale_Paths[_index][indx + 1][1], z=peak_height).multiply(
                        transformation_matrix)
                    c1 = Vector(self._paths[_index][indx + 1][0], self._paths[_index][indx + 1][1], z=peak_height - slopeHeight).multiply(transformation_matrix)
                    # mesh.addFace(c, b1, b)
                    mesh.addFaceByPoints(a1.x, a1.y, a1.z, b1.x, b1.y, b1.z, c1.x, c1.y, c1.z)
                    indx += 1

            #self.Show(scale_Paths[_index], "aaa", 2)
            pcOffset = pyclipper.PyclipperOffset()
            pcOffset.AddPaths(self._paths, pyclipper.JT_SQUARE, pyclipper.ET_CLOSEDLINE)
            result = pcOffset.Execute(offset)
            i = 0

            for point_s in result:
                index = len(point_s)
                name = "./result_"+ str(offset)+ "倍"+str(i)+".txt"
                f = open(name, 'w')
                f.write(str(index) + "\n")
                # for point_s in self._paths:
                for point in point_s:
                    f.write(str(point) + "\n")
                f.close()
                i += 1

            self.Show(result[0], "result[0]", 1)
            self.Show(result, "result", 2)
            for path in self._paths:
                pcOffset = pyclipper.PyclipperOffset()
                pcOffset.AddPath(path, pyclipper.JT_SQUARE, pyclipper.ET_CLOSEDLINE)
                result = pcOffset.Execute(offset)
                #由于一些模型路径的关系我们只能用第一个链表
                if len(result) > 1:
                    m = Message(i18n_catalog.i18nc(
                        '@warning:status',
                        '模型偏移后的数据出现异常，这可能导致偏移部分的精度有一定误差！'),
                        lifetime=0)
                    m.addAction("MoreInfo", name=i18n_catalog.i18nc("@action:button", "More info"), icon=None,
                               description=i18n_catalog.i18nc("@action:tooltip",
                                                         "有问题请找twosilly."),
                               button_style=Message.ActionButtonStyle.LINK)
                    m._filename = file_name
                    m.actionTriggered.connect(self._onMessageActionTriggered)
                    m.show()
                self.Show(path, "path", 1)
                result[0].append(result[0][0])
                self.Show(result[0],"result[0]",1)
                i = 0
                for point_s in result:
                    index = len(point_s)
                    name = "./result" + str(i) + ".txt"
                    f = open(name, 'w')
                    f.write(str(index) + "\n")
                    # for point_s in self._paths:
                    for point in point_s:
                        f.write(str(point) + "\n")
                    f.close()
                    i += 1
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