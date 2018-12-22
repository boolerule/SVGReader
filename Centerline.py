#!/usr/bin/env python
# -*- coding: utf-8 -*-
from shapely.geometry import LineString
from shapely.geometry import MultiLineString
from scipy.spatial import Voronoi
import numpy as np


class Centerline(object):
    def __init__(self, inputGEOM, dist=0.5):
        self.inputGEOM = inputGEOM
        self.dist = abs(dist)

    def create_centerline(self):
        """
        计算多边形的中心线。



        加密随后表示的多边形的边框
                 通过创建数据所需的Numpy数组
                 Voronoi图。 一旦图表被创建，脊
                 位于多边形内的是连接并返回的。

        Returns:
            位于多边形内的多线串。
        """

        minx = int(min(self.inputGEOM.envelope.exterior.xy[0]))
        miny = int(min(self.inputGEOM.envelope.exterior.xy[1]))
        #加密边界
        border = np.array(self.densify_border(self.inputGEOM, minx, miny))
        #用边界生成Voronoi图
        vor = Voronoi(border)
        vertex = vor.vertices

        lst_lines = []
        for j, ridge in enumerate(vor.ridge_vertices):
            if -1 not in ridge:
                line = LineString([
                    (vertex[ridge[0]][0] + minx, vertex[ridge[0]][1] + miny),
                    (vertex[ridge[1]][0] + minx, vertex[ridge[1]][1] + miny)])

                if line.within(self.inputGEOM) and len(line.coords[0]) > 1:
                    lst_lines.append(np.asarray(line))

        return lst_lines

    def densify_border(self, polygon, minx, miny):
        """
       按给定因子加密多边形的边框
         （默认值：0.5）。

        该函数测试多边形的复杂性
         几何，即多边形是否有孔。
         如果多边形没有任何孔，则其外部
         由给定因子提取和致密化。 如果
         多边形有孔，每个孔的边界为
         以及它的外部被提取和致密化
         由一个给定的因素。

        Returns:
            表示每个点的点列表
             通过它的列表
             减少坐标。

        Example:
            [[X1, Y1], [X2, Y2], ..., [Xn, Yn]
        """

        if len(polygon.interiors) == 0:
            exterior_line = LineString(polygon.exterior)
            points = self.fixed_interpolation(exterior_line, minx, miny)

        else:
            exterior_line = LineString(polygon.exterior)
            points = self.fixed_interpolation(exterior_line, minx, miny)

            for j in range(len(polygon.interiors)):
                interior_line = LineString(polygon.interiors[j])
                points += self.fixed_interpolation(interior_line, minx, miny)

        return points

    def fixed_interpolation(self, line, minx, miny):
        """
       用于致密化的辅助功能
         多边形的边框。

       它在指定距离的边界上放置点。
         默认情况下，距离为0.5（米），这意味着
         第一点将放置在0.5米处
         起点，第二点将放在
         距离第一点1.0米的距离等。当然，
         当汇总距离超过时，循环中断
         线的长度。

        Returns:
            每个点由其表示的点列表
                         减少坐标的列表。

        Example:
            [[X1, Y1], [X2, Y2], ..., [Xn, Yn]
        """

        count = self.dist
        newline = []

        startpoint = [line.xy[0][0] - minx, line.xy[1][0] - miny]
        endpoint = [line.xy[0][-1] - minx, line.xy[1][-1] - miny]
        newline.append(startpoint)

        while count < line.length:
            point = line.interpolate(count)
            newline.append([point.x - minx, point.y - miny])
            count += self.dist

        newline.append(endpoint)

        return newline