# -*- coding: cp936 -*-
import math
from UM.Math.Vector import Vector #��������������������ࡣ
import pyclipper
class Polygon(object):
    def __init__(self,ponits=[]):
        super(ponits,self).__init__()
        self._path = ponits
        self.pc = pyclipper.Pyclipper()
    #����
    def Intersection(self,clip,subj):
        self.pc.AddPath(clip, pyclipper.PT_CLIP, True)
        self.pc.AddPaths(subj, pyclipper.PT_SUBJECT, True)
        solution = self.pc.Execute(pyclipper.CT_INTERSECTION, pyclipper.PFT_EVENODD, pyclipper.PFT_EVENODD)
        return solution
    #DIFFERENCE �
    def Difference(self,clip,subj):
        self.pc.AddPath(clip, pyclipper.PT_CLIP, True)
        self.pc.AddPaths(subj, pyclipper.PT_SUBJECT, True)
        solution = self.pc.Execute(pyclipper.CT_DIFFERENCE, pyclipper.PFT_EVENODD, pyclipper.PFT_EVENODD)
        return solution
    #����
    def i(self,clip,subj):
        self.pc.AddPath(clip, pyclipper.PT_CLIP, True)
        self.pc.AddPaths(subj, pyclipper.PT_SUBJECT, True)
        solution = self.pc.Execute(pyclipper.CT_UNION, pyclipper.PFT_EVENODD, pyclipper.PFT_EVENODD)
        return solution
    #���
    def Xor(self,clip,subj):
        self.pc.AddPath(clip, pyclipper.PT_CLIP, True)
        self.pc.AddPaths(subj, pyclipper.PT_SUBJECT, True)
        solution = self.pc.Execute(pyclipper.CT_XOR, pyclipper.PFT_EVENODD, pyclipper.PFT_EVENODD)
        return solution


