import math
import numpy
import pyclipper
import itertools as IT
def scale_polygon(path,offset):
    center = centroid_of_polygon(path)
    for i in path:
        if i[0] > center[0]:
            i[0] += offset
        else:
            i[0] -= offset
        if i[1] > center[1]:
            i[1] += offset
        else:
            i[1] -= offset
    return path

"""
nums:circle
r:radius
points:baseboard data(numpy.array)
data_list:list for circle center point[[1,2],[2,3]]
"""
def set_circle(nums,radius,points,data_list):
    x_list=[]
    y_list=[]
    r_list=[]
    for i in points:
        x_list.append(i[0])
        y_list.append(i[1])
    x, y = numpy.meshgrid(numpy.array(x_list), numpy.array(y_list))
    for i in data_list:
        r = numpy.sqrt((x - i[0]) ** 2 + (y - i[1]) ** 2)
        r_list.append(r)
    outside = r > radius
    return (x[outside], y[outside])

def area_of_polygon(x, y):
    """Calculates the signed area of an arbitrary polygon given its verticies
    http://stackoverflow.com/a/4682656/190597 (Joe Kington)
    http://softsurfer.com/Archive/algorithm_0101/algorithm_0101.htm#2D%20Polygons
    """
    area = 0.0
    for i in range(-1, len(x) - 1):
        area += x[i] * (y[i + 1] - y[i - 1])
    return area / 2.0

def centroid_of_polygon(points):
    """
    http://stackoverflow.com/a/14115494/190597 (mgamba)
    """
    area = area_of_polygon(*zip(*points))
    result_x = 0
    result_y = 0
    N = len(points)
    points = IT.cycle(points)
    x1, y1 = next(points)
    for i in range(N):
        x0, y0 = x1, y1
        x1, y1 = next(points)
        cross = (x0 * y1) - (x1 * y0)
        result_x += (x0 + x1) * cross
        result_y += (y0 + y1) * cross
    result_x /= (area * 6.0)
    result_y /= (area * 6.0)
    return (result_x, result_y)

	# /*
	# \date 2016年6月28日 10:29:51
	# \brief 这是求一序列点所组成面的中点（中心点）
	# \author TwoSilly
	# */
def centerOfMass( polygon ):
	x = 0
	y = 0
	p0 = polygon[len(polygon)-1];
	for p1 in polygon:
		second_factor = ((p0[0] * p1[1]) - (p1[0] * p0[1]))
		x += (p0[0] + p1[0]) * second_factor
		y += (p0[1] + p1[1]) * second_factor
		p0 = p1
	area = pyclipper.Area(polygon);
	x = x / 6 / area;
	y = y / 6 / area;

	if (x < 0):
		x = -x;
		y = -y;
	return (x,y);





def IsConvex(a, b, c): #是凸面
	# 只有逆时针穿越时才凸起!
	crossp = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
	if crossp >= 0:
		return True 
	return False 
#属于三角形
def InTriangle(a, b, c, p):
	L = [0, 0, 0]
	eps = 0.0000001
	# 因为对于非常小的距离denom-> 0，需要计算点p eps的重心系数作为误差校正
	L[0] = ((b[1] - c[1]) * (p[0] - c[0]) + (c[0] - b[0]) * (p[1] - c[1])) \
		  /(((b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])) + eps)
	L[1] = ((c[1] - a[1]) * (p[0] - c[0]) + (a[0] - c[0]) * (p[1] - c[1])) \
		  /(((b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])) + eps)
	L[2] = 1 - L[0] - L[1]
	# 检查p是否位于三角形（a，b，c）
	for x in L:
		if x > 1 or x < 0:
			return False  
	return True  
# 顺时针方向的
def IsClockwise(poly):
	# 用最后一个元素初始化和
	sum = (poly[0][0] - poly[len(poly)-1][0]) * (poly[0][1] + poly[len(poly)-1][1])
	# 迭代所有其他元素（0到n-1）
	for i in range(len(poly)-1):
		sum += (poly[i+1][0] - poly[i][0]) * (poly[i+1][1] + poly[i][1])
	if sum > 0:
		return True
	return False

def GetEar(poly):
	size = len(poly)
	if size < 3:
		return [],0
	if size == 3:
		tri = (poly[0], poly[1], poly[2])
		#del poly[:]
		return tri , 0
	for i in range(size):
		tritest = False
		p1 = poly[(i-1) % size]
		p2 = poly[i % size]
		p3 = poly[(i+1) % size]
		if IsConvex(p1, p2, p3):
			for x in poly:
				if not (x in numpy.array([p1, p2, p3])) and InTriangle(p1, p2, p3, x):
					tritest = True
			if tritest == False:
				#del poly[i % size]
				#poly = numpy.delete(poly,i % size,axis = 0)
				return (p1, p2, p3),i % size
	print('GetEar(): no ear found')
	return [],0
