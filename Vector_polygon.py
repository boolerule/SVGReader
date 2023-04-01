from UM.Application import Application #传递给父构造函数。
from UM.Mesh.MeshBuilder import MeshBuilder #在场景中创建一个网格
from UM.Mesh.MeshReader import MeshReader #这是我们需要实现的插件对象，如果我们想要创建网格。否则从FileReader扩展。
#from UM.Math.Vector import Vector #网格生成器所需的助手类。
from UM.Math.Matrix import Matrix
from UM.Scene.SceneNode import SceneNode #阅读时必须返回结果。
from UM.Job import Job
from UM.Logger import Logger
from PyQt6.QtCore import QUrl

from UM.Message import Message
from UM.Application import Application
from UM.i18n import i18nCatalog
import UM.Math.Color as Color
from p3t import CDT,Point3
from collision import Concave_Poly,Vector,collide,test_aabb #为了检测碰撞（多边形）
from shapely.geometry.polygon import LineString,LinearRing
from shapely.geometry import Point,MultiLineString,Polygon,MultiPolygon,shape
import math
import numpy as np
import pyclipper

import matplotlib.pyplot as plt  #TODO:用作测试的 后期得删掉
# from mpl_toolkits.mplot3d import Axes3D
# from descartes.patch import PolygonPatch
_subdivision = 0.5

#去重，忽略掉小于细分的点
def NoRepetition(Plist):
    if len(Plist) < 1:#TODO:做一个简单的判空
        return []
    path_s = []
    p0 = Point(Plist[0][0],Plist[0][1])
    for p in Plist:
        p1 = Point(p[0],p[1])
        if p0.distance(p1) > _subdivision:#0.05
            p = list(p)
            #if not( p in path_s):#FIXME:这里取消 去重设定，
            path_s.append(p)
        p0 = p1
    #path_s = path_s[::-1]
    #path_s.append([Plist[0][0],Plist[0][1]])
    return path_s
def plot_coords(ax,ob,color):
    x,y = ob.xy
    ax.plot(x,y,"r--",color=color)

def Show(path,name,arg):
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
                plt.annotate('Start', xy=(point_s[0], point_s[1]), xytext=(point_s[0] + 3, point_s[1] + 1.5),
                             arrowprops=dict(facecolor='black', shrink=0.05),
                             )
                print("point:", point_s)
            index += 1
            x.append(point_s[0])
            y.append(point_s[1])

    plt.plot(x, y, 'r-')
    plt.xlabel('x')
    plt.ylabel('y')
    plt.axis('equal')
    plt.show()
    #plt.close()
#TODO：把多边形按层，按角度偏移
#TODO:coord_path --> 需要计算的路径
#TODO：offset -> 偏颇量
#TODO：slopeHeight -> 偏颇角度
def Layer_comput(coord_path,offset,slopeHeight):
    segments_path = []
    for segments in coord_path:
        #Show(segments, "segments", 2)  # TODO:把规划好的路径打印出来看看
        #TODO:查看一下是否有空洞
        polygon_hole = []
        #TODO:一般来说 第一个是外壳，其他的才是洞，所以从1 开始
        for coord_index in range(1,len(segments)):
            polygon_hole.append(segments[coord_index])
        #TODO:数据规整
        polygon_shell = Polygon(segments[0],polygon_hole)
        # FIXME：偏移量的细分(最小不会低于1)
        slope_subdivision = max(abs(int(offset / _subdivision)),1)
        #TODO:多边形偏移方向（正反）
        orientation = -1
        if offset < 0:
            orientation = 1
        #FIXME：斜坡的 高度细分
        #height_subdivison = slopeHeight / slope_subdivision
        polygon_ = []
        polygon_.append(polygon_shell) #TODO:初始值
        #polygon_shell = polygon_shell.simplify(0.1)
        for index in range(0,slope_subdivision+1):
            polygon_shell = polygon_shell.buffer((_subdivision * orientation),cap_style=3,join_style=2)
            if not polygon_shell.is_empty:
                polygon_.append(polygon_shell)
            else:
                break
        segments_path.append(polygon_)
    return segments_path
#TODO: 把 shapely polygon 数据转换为cdt 需要的poly数据
def Poly2CDTData(poly,height):
    interiors = []
    exterior = []
   # poly_line = []
    poly_interiors = []
    poly_exterior = []
    if poly.interiors:#TODO:经验告诉我们 内部的洞只需要 第一个链表就好了（不要问我为啥）
        interiors = np.array(poly.interiors[0])
    if poly.exterior:
        # print("poly.exterior.is_ring:",poly.exterior.is_ring)
        # print("poly.exterior.is_ccw:", poly.exterior.is_ccw)
        # print("poly.exterior.is_valid:", poly.exterior.is_valid)
        # print("poly.exterior.is_ring:", poly.exterior.is_ring)
        # print("poly.exterior.is_ring:", poly.exterior.is_ring)

        # while not poly.exterior.is_valid:
        #     poly.exterior.coords = poly.exterior.simplify(0.1).coords[::-1]
        #     print("poly.exterior.is_ring:", poly.exterior.is_ring)
        #     print("poly.exterior.is_ccw:", poly.exterior.is_ccw)
        #     print("poly.exterior.is_valid:", poly.exterior.is_valid)

        if poly.exterior.is_valid:
            exterior = np.array(poly.exterior)
        else:
            exterior = np.array(poly.exterior)[::-1]
    for p in NoRepetition(interiors):
        poly_interiors.append(Point3(p[0], p[1], height))
    for p in NoRepetition(exterior):
        poly_exterior.append(Point3(p[0], p[1], height))
    return poly_interiors,poly_exterior
#TODO:将 多边形三角化，
def tri_polygon(poly_ext,poly_ints):
    cdt = CDT(poly_ext)
    for hole in poly_ints:
        cdt.add_hole(hole)
    triangles = cdt.triangulate()
    # FIXME:做一下简单的面检查
    max_height = poly_ext[0].z
    min_height = 0
    if poly_ints:
        min_height = poly_ints[0][0].z
    tir_index = 0
    while tir_index <  len(triangles):
        t =  triangles[tir_index]
        is_pop = False
        if t.a.z == min_height or t.b.z == min_height or t.c.z == min_height:
            pass
        else:
            is_pop = True
            #triangles.pop(tir_index)
            print("tir_index:",tir_index)
        if t.a.z == max_height or t.b.z == max_height or t.c.z == max_height:
            pass
        else:
            is_pop = True
            #triangles.pop(tir_index)
            print("tir_index:",tir_index)
        if is_pop:
            triangles.pop(tir_index)
            continue
        tir_index += 1


    # Vector_poly = []
    # for t in triangles:
    #     p0 = [t.a.x, t.a.y, t.a.z]
    #     p1 = [t.b.x, t.b.y, t.b.z]
    #     p2 = [t.c.x, t.c.y, t.c.z]
    #     Vector_poly.append(p0)
    #     Vector_poly.append(p1)
    #     Vector_poly.append(p2)


    # 创建 3D 图形对象
    # fig = plt.figure()
    # ax = Axes3D(fig)
    # x = [x[0] for x in Vector_poly]
    # y = [x[1] for x in Vector_poly]
    # z = [x[2] for x in Vector_poly]
    # # 绘制线型图
    # ax.set_title(str(1) + ":" + str(2))
    # ax.plot(x, y, z)
    # plt.show()
    return triangles
#TODO:三角化单个模块与下一层
def connect_layer(poly_dowm ,poly_up,init_height,curr_Height):

    poly_dowm_interiors, poly_dowm_exterior = Poly2CDTData(poly_dowm, init_height)
    Vector_polygon = []
    # TODO：上面那层的类型
    if isinstance(poly_up, Polygon):
        if poly_up.area < 1:
            return []
        poly_interiors, poly_exterior = Poly2CDTData(poly_up, curr_Height)
        # TODO:多边形洞
        if poly_dowm_interiors:
            if poly_interiors:
                triangles = tri_polygon(poly_dowm_interiors, [poly_interiors])
                Vector_polygon.append(triangles)
            else:
                #return []
                print("换层分界-- 从有洞换到无洞")
        # TODO：多边形外壳
        if poly_dowm_exterior:
            triangles = tri_polygon(poly_dowm_exterior, [poly_exterior])
            Vector_polygon.append(triangles)
    elif isinstance(poly_up, MultiPolygon):
        poly_ints = []
        poly_exts = []
        for _up in poly_up:
            if _up.area <1:
                continue
            #TODO:判断是否是该多边形的上层
            if poly_dowm.contains(_up):
                poly_interiors, poly_exterior  = Poly2CDTData(_up, curr_Height)
                if poly_interiors:
                    poly_ints.append(poly_interiors)
                if poly_exterior:
                    poly_exts.append(poly_exterior)
        # TODO:多边形洞
        if poly_dowm_interiors:
            triangles = tri_polygon(poly_dowm_interiors, poly_ints)
            Vector_polygon.append(triangles)
        # TODO：多边形外壳
        if poly_dowm_exterior:
            triangles = tri_polygon(poly_dowm_exterior, poly_exts)
            Vector_polygon.append(triangles)
    else:
        Logger.log("e", "ERROR Unsupported layer type:" + __file__)
    return Vector_polygon
#TODO: 把得到的路径顺序先规划一下，返回规划好的数据
def initDate(poly_Line):
    coord_path = []
    for svg_segments in poly_Line:
        for segments in svg_segments:
            for coord_ in segments:
                if len(coord_path) <= 0:
                    coord_path.append([coord_])
                else:
                    out = Polygon(coord_)
                    curr_index = -1  # 当前需要添加的下标
                    for i in range(len(coord_path)):
                        ext = Polygon(coord_path[i][0])
                        inter = ext.contains(out)
                        if inter:  # TODO:存在交集
                            curr_index = i
                            break
                        else:
                            curr_index = len(coord_path)  # TODO:表示加在最后的意思
                    if curr_index != -1:
                        if curr_index >= len(coord_path):
                            coord_path.append([coord_])
                        else:
                            coord_path[curr_index].append(coord_)
    return coord_path

def Vector_compute_Polygon_Shapely(poly_Line,offset, peak_height, slopeHeight,
                           closeTopButtonFace, reversePathToration, splitWord):
    Vector_polygon = []  # TODO：这是最终的数据
    coord_path = initDate(poly_Line)#TODO:初始化路径数据，即，把现有不规则数据，规划一下
    #Show(coord_path, "coord_path", 3)  # TODO:把规划好的路径打印出来看看
    segments_path = Layer_comput(coord_path,offset,slopeHeight)#TODO:把路径按层分好
    #TODO:按照 每个单独的模块 上下层 三角化
    for part in segments_path:
        #Show(part, "part", 2)
        # 高度上的细分(最小不会低于1)
        slope_subdivision = max(abs(int(offset / _subdivision)),1)
        #TODO:斜坡为0 那么他的高度也应该是0
        if offset == 0:
            slopeHeight = 0
        curr_Height = peak_height - slopeHeight  # 实际高度等于总高度减去斜坡高度
        height_subdivison = slopeHeight / slope_subdivision
        init_height = 0
        polyline = []  # TODO:三角化的基础
        hole_polyline = []  # TODO：三角化的 空洞（小的那个部分的 多边形）
        if offset < 0:
            #TODO:反向是放大
            curr_Height = height_subdivison

        for layer_index in range(1, len(part)):
            poly_dowm = part[layer_index - 1]  # FIXME:层中靠下的一层
            poly_up = part[layer_index]  # FIXME:层中靠上的一层
            print("layer_index:", layer_index)
            print("init_height:", init_height)
            print("curr_Height:", curr_Height)
            if isinstance(poly_dowm, Polygon):
                #poly_dowm_exterior = []
                #poly_dowm_interiors = []
                Vector_ = connect_layer(poly_dowm, poly_up,init_height,curr_Height)
                if not Vector_:
                    init_height = init_height - height_subdivison
                    curr_Height -= height_subdivison
                    continue
                Vector_polygon += Vector_
                #TODO:这里判断缩小后的模型是否属于 大的
            elif isinstance(poly_dowm, MultiPolygon):
                for poly in poly_dowm:
                    #print("area:", poly.area)
                    if poly.area < 1:
                        continue
                    #TODO:现在唯一的问题了。
                    poly_dowm_interiors, poly_dowm_exterior = Poly2CDTData(poly, init_height)
                    Vector_ = connect_layer(poly, poly_up,init_height,curr_Height)
                    Vector_polygon += Vector_
            else:
                Logger.log("e", "ERROR Unsupported layer type:" + __file__)
            # init_height = curr_Height
            # curr_Height += height_subdivison
            # TODO:斜坡小于0， 其实就是z轴换一下方向
            if offset < 0:
                if curr_Height >= slopeHeight - height_subdivison:
                    init_height = curr_Height
                    # TODO:
                    curr_Height = peak_height
                    continue #TODO:赋值后直接重新循环

            else:
                pass
            init_height = curr_Height
            curr_Height += height_subdivison


    return Vector_polygon
