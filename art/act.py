"""Interactive things: the moving parts and action markers the mod drives (Unity Interact.cs and Doors.cs).

All position-only, so nothing depends on how axes convert on import:
  IVA_Live_Door<name>[__p<k>]    hinged parts (every part of a group pivots on the same hinge point);
                                 markers IVA_LiveAxis_/IVA_LiveEdge_/IVA_LiveOut_Door<name>
  IVA_Live_Slide<name>[__p<k>]   sliding parts (drawers); marker IVA_LiveTo_Slide<name> = where the main part's pivot goes
  IVA_Live_Curtain<name>[__p<k>] a curtain modelled drawn back, pivot on its fixed edge; markers IVA_LiveOpen_Curtain<name>
                                 (its moving edge now) and IVA_LiveEdge_Curtain<name> (that edge when closed)
  IVA_Live_Glow<name>            a lamp's lit face, switched on and off
  IVA_Live_Screen<name>          a screen whose page (mfd_* material) can be changed
  IVA_Act_<Kind>_<name>          where to look to use it (Door, Slide, Curtain, Lamp, Screen, Flush, Wash, Lights)
Live parts carry one material each (the exporter keeps the first), so a door with a pull of another material is a group.
"""
import ivalib as L  # imports bpy first
import capsule as C
from mathutils import Matrix, Vector


def target(kind, name, p):
    return C.marker(f"IVA_Act_{kind}_{name}", Vector(p))


def _pivot(obj, p):
    """Move obj's origin to world point p without moving its geometry."""
    mw = obj.matrix_world.copy()
    local = mw.inverted() @ Vector(p)
    obj.data.transform(Matrix.Translation(-local))
    mw.translation = Vector(p)
    obj.matrix_world = mw


def _live(obj, stem, k):
    obj.name = f"IVA_Live_{stem}" + (f"__p{k}" if k else "")
    obj.data.name = obj.name
    return obj


def hinge(name, parts, hinge_pt, up, edge_pt, out, act_at=None):
    """parts swing together about the line through hinge_pt along up; edge_pt is the free edge (closed); out the side
    they open towards. The first part is the main one."""
    hinge_pt, up = Vector(hinge_pt), Vector(up).normalized()
    for k, o in enumerate(parts):
        _pivot(o, hinge_pt)
        _live(o, "Door" + name, k)
    C.marker(f"IVA_LiveAxis_Door{name}", hinge_pt + up * 0.1)
    C.marker(f"IVA_LiveEdge_Door{name}", Vector(edge_pt))
    C.marker(f"IVA_LiveOut_Door{name}", hinge_pt + Vector(out).normalized() * 0.1)
    target("Door", name, act_at if act_at is not None else (hinge_pt + Vector(edge_pt)) / 2)


def slide(name, parts, travel, act_at=None):
    """parts slide together by the vector travel when opened."""
    p0 = parts[0].matrix_world.translation.copy()
    for k, o in enumerate(parts):
        _pivot(o, p0)
        _live(o, "Slide" + name, k)
    C.marker(f"IVA_LiveTo_Slide{name}", p0 + Vector(travel))
    target("Slide", name, act_at if act_at is not None else p0)


def curtain(name, parts, anchor, open_edge, closed_edge, act_at=None):
    """parts: the curtain as modelled drawn back; drawing it stretches them along the rod from the fixed edge."""
    for k, o in enumerate(parts):
        _pivot(o, anchor)
        _live(o, "Curtain" + name, k)
    C.marker(f"IVA_LiveOpen_Curtain{name}", Vector(open_edge))
    C.marker(f"IVA_LiveEdge_Curtain{name}", Vector(closed_edge))
    target("Curtain", name, act_at if act_at is not None else (Vector(anchor) + Vector(closed_edge)) / 2)


def glow(name, obj, act_at=None):
    _pivot(obj, obj.matrix_world.translation)
    _live(obj, "Glow" + name, 0)
    target("Lamp", name, act_at if act_at is not None else obj.matrix_world.translation)


def screen(name, obj, act_at=None):
    _live(obj, "Screen" + name, 0)
    target("Screen", name, act_at if act_at is not None else obj.matrix_world.translation)
