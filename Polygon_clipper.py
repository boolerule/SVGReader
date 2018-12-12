# -*- coding: cp936 -*-
import math
from UM.Math.Vector import Vector #网格生成器所需的助手类。
import pyclipper
class Polygon(object):
    def __init__(self,ponits=[]):
        super(ponits,self).__init__()
        self._path = ponits
        self.pc = pyclipper.Pyclipper()
    #交集
    def Intersection(self,clip,subj):
        self.pc.AddPath(clip, pyclipper.PT_CLIP, True)
        self.pc.AddPaths(subj, pyclipper.PT_SUBJECT, True)
        solution = self.pc.Execute(pyclipper.CT_INTERSECTION, pyclipper.PFT_EVENODD, pyclipper.PFT_EVENODD)
        return solution
    #DIFFERENCE 差集
    def Difference(self,clip,subj):
        self.pc.AddPath(clip, pyclipper.PT_CLIP, True)
        self.pc.AddPaths(subj, pyclipper.PT_SUBJECT, True)
        solution = self.pc.Execute(pyclipper.CT_DIFFERENCE, pyclipper.PFT_EVENODD, pyclipper.PFT_EVENODD)
        return solution
    #并集
    def i(self,clip,subj):
        self.pc.AddPath(clip, pyclipper.PT_CLIP, True)
        self.pc.AddPaths(subj, pyclipper.PT_SUBJECT, True)
        solution = self.pc.Execute(pyclipper.CT_UNION, pyclipper.PFT_EVENODD, pyclipper.PFT_EVENODD)
        return solution
    #异或
    def Xor(self,clip,subj):
        self.pc.AddPath(clip, pyclipper.PT_CLIP, True)
        self.pc.AddPaths(subj, pyclipper.PT_SUBJECT, True)
        solution = self.pc.Execute(pyclipper.CT_XOR, pyclipper.PFT_EVENODD, pyclipper.PFT_EVENODD)
        return solution


