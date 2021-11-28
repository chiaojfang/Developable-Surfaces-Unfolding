from math import sqrt
from itertools import chain
import openmesh as om
from shapely.geometry import LineString
from unfolding_helper import *

class Vec:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

    def len(self):
        return sqrt(self.x**2 + self.y**2 + self.z**2)

    def normal(self):
        l = self.len()
        return Vec(self.x/l, self.y/l, self.z/l)

    def add(self, v):
        return Vec(self.x + v.x, self.y + v.y, self.z + v.z)

    def s_mult(self, s):
        return Vec(self.x * s, self.y * s, self.z * s)

    def dif(self, v):
        return Vec(self.x - v.x, self.y - v.y, self.z - v.z)

class Insertion_Vertex:
    def __init__(self, edge_id, dist):
        self.edge_id = edge_id
        self.dist = dist


    def calc_pos(self, edge):
        edge = ( Vec(edge[0][0], edge[0][1], edge[0][2]), Vec(edge[1][0], edge[1][1], edge[1][2]))
        #BA/len(BA) * dist + A = point between B and A dist away from A
        return (edge[1].dif(edge[0])).normal().s_mult(self.dist).add(edge[0])

def strip_2_tree(mesh, strip):
    root = node(strip.pop(0))
    curr = root
    while strip:
        #find all adjacent_faces to current face curr 
        children = [f for f in strip if f in mesh.get_adjacent_faces_idx(curr.val)]

        child_id = children[0]
        strip.remove(child_id)
        child_node = node(child_id)
        curr.add_child_node(child_node)
        curr = child_node

    return root

def get_unfolding(mesh, faces):
    tree = node(faces[0])
    tree.add_child(faces[1])
    return tree.unfold(mesh)

def get_2d_points(mesh, unfold, cut_faces):
    faces_as_vert = [list(vert) for vert in mesh.model.face_vertex_indices()]
    cut_faces_as_vert = [faces_as_vert[f_id] for f_id in cut_faces]
    points_2d = {}
    for face_id, polygon in enumerate(unfold):
        for i, coords_2d in enumerate(polygon):
            vertex_id = cut_faces_as_vert[face_id][i]
            points_2d[vertex_id] = coords_2d
    return points_2d

def get_cutted_edges(mesh):
    all_edges = list(mesh.model.face_edge_indices())
    cut_edges = [e for i, e in enumerate(all_edges) if i in cut_faces]
    cut_edges = list(chain.from_iterable(cut_edges))
    cut_edges = list(dict.fromkeys(cut_edges))
    return cut_edges

if __name__ == '__main__':
    mesh = Mesh('test.obj')
    cut_faces = [5, 2]
    end_point_id = 2
    starting_point_3d = (0.5, 0.5, 1)

    unfold = get_unfolding(mesh, cut_faces)

    starting_point_2d = starting_point_3d_2_2d(mesh, node(cut_faces[0]), starting_point_3d)

    points_2d = get_2d_points(mesh, unfold, cut_faces)
    end_point_2d = points_2d[end_point_id]
    cut_edges = get_cutted_edges(mesh)

    edge_as_vertex_ids = [list(e) for e in mesh.model.edge_vertex_indices()]
    # [(0, 1), (1, 5), (5, 4)]
    lines = []
    for e in cut_edges:
        verts = edge_as_vertex_ids[e]
        nl = LineString((tuple(points_2d[verts[0]]), tuple(points_2d[verts[1]])))
        lines.append(nl)

    main_line = LineString((starting_point_2d, end_point_2d))
    new_vertices = []

    for i, l in enumerate(lines):
        p = main_line.intersection(l)
        if p:
            p = tuple(p.coords)[0]
            p = Vec(p[0], p[1], 0)
            A = tuple(l.coords)[0]
            A = Vec(A[0], A[1], 0)
            dist = (p.dif(A)).len()
            new_vertices.append(Insertion_Vertex(cut_edges[i], dist))

    #map to 3d
    points_3d = [tuple(p) for p in mesh.model.points()]
    new_points_3d = []
    for v in new_vertices:
        edge = edge_as_vertex_ids[v.edge_id]
        edge = [points_3d[id] for id in edge]
        v = v.calc_pos(edge)
        new_points_3d.append(v)

    for p in new_points_3d:
        print(p.x, p.y, p.z)
