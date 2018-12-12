# coding=utf-8
"""
多边形模块具有辅助处理二维凸多边形的功能。
"""
__copyright__ = "Copyright (C) 2013 David Braam - Released under terms of the AGPLv3 License"

import numpy


def _isLeft(a, b, c):
	""" 检查C是否在从A到B的无限长的直线上 """
	return ((b[0] - a[0])*(c[1] - a[1]) - (b[1] - a[1])*(c[0] - a[0])) > 0


def _isRightTurn(xxx_todo_changeme):
	(p, q, r) = xxx_todo_changeme
	sum1 = q[0]*r[1] + p[0]*q[1] + r[0]*p[1]
	sum2 = q[0]*p[1] + r[0]*q[1] + p[0]*r[1]

	if sum1 - sum2 < 0:
		return 1
	else:
		return 0


def convexHull(pointList):
	""" 从一个点列表创建一个凸包。 """
	unique = {}
	for p in pointList:
		unique[p[0], p[1]] = 1

	points = list(unique.keys())
	points.sort()
	if len(points) < 1:
		return numpy.zeros((0, 2), numpy.float32)
	if len(points) < 2:
		return numpy.array(points, numpy.float32)

	# 建造船体的上半部分.
	upper = [points[0], points[1]]
	for p in points[2:]:
		upper.append(p)
		while len(upper) > 2 and not _isRightTurn(upper[-3:]):
			del upper[-2]

	# 建造船体下半部分。
	points = points[::-1]
	lower = [points[0], points[1]]
	for p in points[2:]:
		lower.append(p)
		while len(lower) > 2 and not _isRightTurn(lower[-3:]):
			del lower[-2]

	# 删除重复值
	del lower[0]
	del lower[-1]

	return numpy.array(upper + lower, numpy.float32)


def minkowskiHull(a, b):
	"""计算两个凸多边形的闵可夫斯基壳"""
	points = numpy.zeros((len(a) * len(b), 2))
	for n in range(0, len(a)):
		for m in range(0, len(b)):
			points[n * len(b) + m] = a[n] + b[m]
	return convexHull(points.copy())


def _projectPoly(poly, normal):
	"""
	在给定法线上投影凸多边形。
凸多边形在无限线上的投影是有限线。
给出法线上的最小值和最大值。
	"""
	pMin = numpy.dot(normal, poly[0])
	pMax = pMin
	for n in range(1 , len(poly)):
		p = numpy.dot(normal, poly[n])
		pMin = min(pMin, p)
		pMax = max(pMax, p)
	return pMin, pMax


def polygonCollision(polyA, polyB):
	""" 检查凸多边形A和B是否碰撞，如果是这样，返回True. """
	for n in range(0, len(polyA)):
		p0 = polyA[n-1]
		p1 = polyA[n]
		normal = (p1 - p0)[::-1]
		normal[1] = -normal[1]
		normal /= numpy.linalg.norm(normal)
		aMin, aMax = _projectPoly(polyA, normal)
		bMin, bMax = _projectPoly(polyB, normal)
		if aMin > bMax:
			return False
		if bMin > aMax:
			return False
	for n in range(0, len(polyB)):
		p0 = polyB[n-1]
		p1 = polyB[n]
		normal = (p1 - p0)[::-1]
		normal[1] = -normal[1]
		normal /= numpy.linalg.norm(normal)
		aMin, aMax = _projectPoly(polyA, normal)
		bMin, bMax = _projectPoly(polyB, normal)
		if aMin > bMax:
			return False
		if bMin > aMax:
			return False
	return True


def polygonCollisionPushVector(polyA, polyB):
	""" 检查凸多边形A和B是否发生碰撞，如果是这种情况则返回穿透矢量，否则返回False。 """
	retSize = 10000000.0
	ret = False
	for n in range(0, len(polyA)):
		p0 = polyA[n-1]
		p1 = polyA[n]
		normal = (p1 - p0)[::-1]
		normal[1] = -normal[1]
		normal /= numpy.linalg.norm(normal)
		aMin, aMax = _projectPoly(polyA, normal)
		bMin, bMax = _projectPoly(polyB, normal)
		if aMin > bMax:
			return False
		if bMin > aMax:
			return False
		size = min(aMax, bMax) - max(aMin, bMin)
		if size < retSize:
			ret = normal * (size + 0.1)
			retSize = size
	for n in range(0, len(polyB)):
		p0 = polyB[n-1]
		p1 = polyB[n]
		normal = (p1 - p0)[::-1]
		normal[1] = -normal[1]
		normal /= numpy.linalg.norm(normal)
		aMin, aMax = _projectPoly(polyA, normal)
		bMin, bMax = _projectPoly(polyB, normal)
		if aMin > bMax:
			return False
		if bMin > aMax:
			return False
		size = min(aMax, bMax) - max(aMin, bMin)
		if size < retSize:
			ret = normal * -(size + 0.1)
			retSize = size
	return ret


def fullInside(polyA, polyB):
	"""
	检查凸多边形A是否完全在凸多边形B内。
	"""
	for n in range(0, len(polyA)):
		p0 = polyA[n-1]
		p1 = polyA[n]
		normal = (p1 - p0)[::-1]
		normal[1] = -normal[1]
		normal /= numpy.linalg.norm(normal)
		aMin, aMax = _projectPoly(polyA, normal)
		bMin, bMax = _projectPoly(polyB, normal)
		if aMax > bMax:
			return False
		if aMin < bMin:
			return False
	for n in range(0, len(polyB)):
		p0 = polyB[n-1]
		p1 = polyB[n]
		normal = (p1 - p0)[::-1]
		normal[1] = -normal[1]
		normal /= numpy.linalg.norm(normal)
		aMin, aMax = _projectPoly(polyA, normal)
		bMin, bMax = _projectPoly(polyB, normal)
		if aMax > bMax:
			return False
		if aMin < bMin:
			return False
	return True


def lineLineIntersection(p0, p1, p2, p3):
	""" 返回无限大线槽点p0和p1的交点，以及无限大线槽点p2和p3的交点。 """
	A1 = p1[1] - p0[1]
	B1 = p0[0] - p1[0]
	C1 = A1*p0[0] + B1*p0[1]

	A2 = p3[1] - p2[1]
	B2 = p2[0] - p3[0]
	C2 = A2 * p2[0] + B2 * p2[1]

	det = A1*B2 - A2*B1
	if det == 0:
		return p0
	return [(B2*C1 - B1*C2)/det, (A1 * C2 - A2 * C1) / det]


def clipConvex(poly0, poly1):
	""" 对凸多边形0进行裁剪，使其完全符合凸多边形1，任何超出凸多边形1的部分都被剪掉"""
	res = poly0
	for p1idx in range(0, len(poly1)):
		src = res
		res = []
		p0 = poly1[p1idx-1]
		p1 = poly1[p1idx]
		for n in range(0, len(src)):
			p = src[n]
			if not _isLeft(p0, p1, p):
				if _isLeft(p0, p1, src[n-1]):
					res.append(lineLineIntersection(p0, p1, src[n-1], p))
				res.append(p)
			elif not _isLeft(p0, p1, src[n-1]):
				res.append(lineLineIntersection(p0, p1, src[n-1], p))
	return numpy.array(res, numpy.float32)
