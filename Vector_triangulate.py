from UM.Logger import Logger
from UM.Math.Matrix import Matrix
from UM.Math.Vector import Vector
EPSILON = 0.000001

# Given a face as a sequence of vectors, returns a normal to the polygon place that forms a right triple
# with a vector along the polygon sequence and a vector backwards
#正常多边形是向量序列，多边形序列和向后向量
#发现外法向量
def findOuterNormal(face):
    n = len(face)
    for i in range(n):
        for j in range(i+1, n):
            edge = face[j] - face[i]
            if edge.length() > EPSILON:
                edge = edge.normalized()
                prev_rejection = Vector()
                is_outer = True
                for k in range(n):
                    if k != i and k != j:
                        pt = face[k] - face[i]
                        pte = pt.dot(edge)
                        rejection = pt - edge*pte
                        if rejection.dot(prev_rejection) < -EPSILON: # 边缘两边的点——不是外侧的点
                            is_outer = False
                            break
                        elif rejection.length() > prev_rejection.length(): # 选择一个更大的拒绝数字稳定性
                            prev_rejection = rejection

                if is_outer: # 找到一个外边缘，prev_rejection是面内的拒绝。生成一个正常。
                    return edge.cross(prev_rejection)

    return False

# 给定两个*共线*向量a和b，返回使b到a的系数。
# 没有错误处理
# 为了稳定性，取最大坐标之间的比值会更好……
#比率
def ratio(a, b):
    if b.x > EPSILON or b.x < -EPSILON:
        return a.x / b.x
    elif b.y > EPSILON or b.y < -EPSILON:
        return a.y / b.y
    else:
        return a.z / b.z
#点在三角形
def pointInsideTriangle(vx, next, prev, nextXprev):
    vxXprev = vx.cross(prev)
    r = ratio(vxXprev, nextXprev)
    if r < 0:
        return False
    vxXnext = vx.cross(next);
    s = -ratio(vxXnext, nextXprev)
    return s > 0 and (s + r) < 1

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



