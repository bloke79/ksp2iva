// Moving around inside the cabin (unbuckled): a small sphere that floats in pod space and slides along the interior.
//
// No Unity physics: colliders on the interior would join the pod's rigidbody and could disturb the vessel. Instead the
// interior carries position-only markers (made by art/stock.py collision_markers) that describe its shape:
//   IVA_ColAxis_0/1      the pod axis, floor to top
//   IVA_ColHull_<k>      a point on the hull at each height (the radius profile)
//   IVA_ColDeck_<k>      deck heights; IVA_ColHole_<k>_c/x/y/z are the openings you can pass through
//   IVA_ColBox_<k>_c/x/y/z  oriented boxes round the larger equipment (centre and three half-axis tips)
//   IVA_Hatch_<name>     hatch positions, for a prompt
// Everything is converted to pod space once, when you unbuckle; the interior doesn't move inside the pod.

using System;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;
using ILogger = ReduxLib.Logging.ILogger;

namespace IVA
{
    public class FreeMove
    {
        private struct Box
        {
            public Vector3 C, X, Y, Z, E;   // centre, unit axes, half extents
            public float Reach;             // bounding radius, for a quick reject
        }

        private readonly List<Box> _boxes = new List<Box>();
        private readonly List<Box> _holes = new List<Box>();
        private readonly List<float> _decks = new List<float>();
        private readonly List<Vector2> _hull = new List<Vector2>();   // (height along the axis, radius), sorted
        public readonly List<KeyValuePair<string, Vector3>> Hatches = new List<KeyValuePair<string, Vector3>>();
        private Vector3 _a0, _u;
        private float _hMax;

        public Vector3 Pos;                 // pod space
        public Quaternion Rot = Quaternion.identity;
        private Vector3 _vel;
        private bool _ghost;                // ignore equipment until clear of it (you start inside your couch)
        public float Radius = 0.13f;

        public bool Valid => _hull.Count >= 2 && _hMax > 0.1f;
        public int BoxCount => _boxes.Count;
        public Vector3 Axis => _u;

        public static FreeMove Build(Transform interior, Transform pod, ILogger log)
        {
            var f = new FreeMove();
            var pts = new Dictionary<string, Vector3>(StringComparer.Ordinal);
            foreach (Transform t in interior.GetComponentsInChildren<Transform>(true))
                if (t.name.StartsWith("IVA_Col", StringComparison.Ordinal) || t.name.StartsWith("IVA_Hatch_", StringComparison.Ordinal))
                    pts[t.name] = pod.InverseTransformPoint(t.position);
            if (!pts.TryGetValue("IVA_ColAxis_0", out Vector3 a0) || !pts.TryGetValue("IVA_ColAxis_1", out Vector3 a1))
            {
                log?.LogWarning("IVA: this interior has no collision markers (re-export it); can't move around inside.");
                return f;
            }
            f._a0 = a0;
            f._u = (a1 - a0).normalized;
            f._hMax = (a1 - a0).magnitude;
            foreach (var kv in pts.Where(p => p.Key.StartsWith("IVA_ColHull_", StringComparison.Ordinal)))
            {
                Vector3 d = kv.Value - a0;
                float h = Vector3.Dot(d, f._u);
                f._hull.Add(new Vector2(h, (d - f._u * h).magnitude));
            }
            f._hull.Sort((p, q) => p.x.CompareTo(q.x));
            foreach (var kv in pts.Where(p => p.Key.StartsWith("IVA_ColDeck_", StringComparison.Ordinal)))
                f._decks.Add(Vector3.Dot(kv.Value - a0, f._u));
            ReadBoxes(pts, "IVA_ColHole_", f._holes);
            ReadBoxes(pts, "IVA_ColBox_", f._boxes);
            foreach (var kv in pts.Where(p => p.Key.StartsWith("IVA_Hatch_", StringComparison.Ordinal)))
                f.Hatches.Add(new KeyValuePair<string, Vector3>(kv.Key.Substring("IVA_Hatch_".Length), kv.Value));
            log?.LogInfo($"IVA: free movement ready: hull {f._hull.Count} rings over {f._hMax:F2} m, {f._decks.Count} deck(s), " +
                         $"{f._holes.Count} opening(s), {f._boxes.Count} equipment box(es), {f.Hatches.Count} hatch(es).");
            return f;
        }

        private static void ReadBoxes(Dictionary<string, Vector3> pts, string prefix, List<Box> into)
        {
            foreach (string cName in pts.Keys.Where(k => k.StartsWith(prefix, StringComparison.Ordinal) && k.EndsWith("_c", StringComparison.Ordinal)).ToList())
            {
                string stem = cName.Substring(0, cName.Length - 2);
                if (!pts.TryGetValue(stem + "_x", out Vector3 x) || !pts.TryGetValue(stem + "_y", out Vector3 y) || !pts.TryGetValue(stem + "_z", out Vector3 z)) continue;
                Vector3 c = pts[cName];
                Vector3 vx = x - c, vy = y - c, vz = z - c;
                var b = new Box
                {
                    C = c,
                    X = vx.normalized, Y = vy.normalized, Z = vz.normalized,
                    E = new Vector3(vx.magnitude, vy.magnitude, vz.magnitude),
                };
                b.Reach = b.E.magnitude;
                into.Add(b);
            }
        }

        public void Begin(Vector3 pos, Quaternion rot)
        {
            Pos = pos;
            Rot = rot;
            _vel = Vector3.zero;
            _ghost = true;
        }

        // Look: yaw and pitch round the view's own axes (no horizon in zero g), roll from the keys.
        public void Turn(float yawDeg, float pitchDeg, float rollDeg)
        {
            Rot = Rot * Quaternion.Euler(pitchDeg, yawDeg, rollDeg);
        }

        // move: thrust direction in view space (x right, y up, z forward), each -1..1.
        public void Step(Vector3 move, float dt, float accel, float maxSpeed, float damping)
        {
            if (dt <= 0f) return;
            dt = Mathf.Min(dt, 0.05f);
            _vel += Rot * move * (accel * dt);
            _vel *= Mathf.Exp(-damping * dt);
            if (_vel.magnitude > maxSpeed) _vel = _vel.normalized * maxSpeed;
            Vector3 old = Pos;
            Vector3 p = Pos + _vel * dt;
            for (int it = 0; it < 4; it++) Resolve(old, ref p);
            Pos = p;
            if (_ghost && !InsideAnyBox(Pos)) _ghost = false;
        }

        private float Height(Vector3 p) => Vector3.Dot(p - _a0, _u);

        private float HullRadius(float h)
        {
            if (h <= _hull[0].x) return _hull[0].y;
            for (int i = 1; i < _hull.Count; i++)
                if (h <= _hull[i].x)
                {
                    Vector2 a = _hull[i - 1], b = _hull[i];
                    return Mathf.Lerp(a.y, b.y, (h - a.x) / Mathf.Max(1e-5f, b.x - a.x));
                }
            return _hull[_hull.Count - 1].y;
        }

        private static bool Inside(Box b, Vector3 p, float grow = 0f)
        {
            Vector3 d = p - b.C;
            return Mathf.Abs(Vector3.Dot(d, b.X)) <= b.E.x + grow && Mathf.Abs(Vector3.Dot(d, b.Y)) <= b.E.y + grow && Mathf.Abs(Vector3.Dot(d, b.Z)) <= b.E.z + grow;
        }

        private bool InsideAnyBox(Vector3 p)
        {
            foreach (Box b in _boxes)
                if ((p - b.C).sqrMagnitude <= (b.Reach + Radius) * (b.Reach + Radius) && Inside(b, p, Radius * 0.5f)) return true;
            return false;
        }

        private void Stop(Vector3 n)   // n: the push-out direction; cancel motion into the obstacle
        {
            float vn = Vector3.Dot(_vel, n);
            if (vn < 0f) _vel -= n * vn;
        }

        private void Resolve(Vector3 old, ref Vector3 p)
        {
            // decks: can't pass through except at an opening
            float hOld = Height(old);
            foreach (float hd in _decks)
            {
                float h = Height(p);
                bool crossing = (hOld - hd) * (h - hd) < 0f || Mathf.Abs(h - hd) < Radius;
                if (!crossing) continue;
                Vector3 onDeck = p - _u * (h - hd);
                if (_holes.Any(b => Inside(b, onDeck, -Radius * 0.5f))) continue;
                float side = hOld >= hd ? 1f : -1f;
                p += _u * (hd + side * Radius - h);
                Stop(_u * side);
            }
            // floor and top
            {
                float h = Height(p);
                float lo = Radius, hi = _hMax - Radius;
                if (h < lo) { p += _u * (lo - h); Stop(_u); }
                else if (h > hi) { p -= _u * (h - hi); Stop(-_u); }
            }
            // hull wall
            {
                float h = Height(p);
                Vector3 radial = (p - _a0) - _u * h;
                float r = radial.magnitude, rMax = HullRadius(h) - Radius;
                if (r > rMax && r > 1e-5f)
                {
                    Vector3 n = -radial / r;
                    p += n * (r - Mathf.Max(0f, rMax));
                    Stop(n);
                }
            }
            if (_ghost) return;
            // equipment boxes
            for (int i = 0; i < _boxes.Count; i++)
            {
                Box b = _boxes[i];
                Vector3 d = p - b.C;
                if (d.sqrMagnitude > (b.Reach + Radius) * (b.Reach + Radius)) continue;
                float lx = Vector3.Dot(d, b.X), ly = Vector3.Dot(d, b.Y), lz = Vector3.Dot(d, b.Z);
                Vector3 q = b.C + b.X * Mathf.Clamp(lx, -b.E.x, b.E.x) + b.Y * Mathf.Clamp(ly, -b.E.y, b.E.y) + b.Z * Mathf.Clamp(lz, -b.E.z, b.E.z);
                Vector3 delta = p - q;
                float dist = delta.magnitude;
                if (dist >= Radius) continue;
                Vector3 n;
                if (dist > 1e-5f)
                {
                    n = delta / dist;
                    p = q + n * Radius;
                }
                else
                {
                    // centre inside the box: out through the nearest face
                    float px = b.E.x - Mathf.Abs(lx), py = b.E.y - Mathf.Abs(ly), pz = b.E.z - Mathf.Abs(lz);
                    if (px <= py && px <= pz) { n = b.X * Mathf.Sign(lx); p += n * (px + Radius); }
                    else if (py <= pz) { n = b.Y * Mathf.Sign(ly); p += n * (py + Radius); }
                    else { n = b.Z * Mathf.Sign(lz); p += n * (pz + Radius); }
                }
                Stop(n);
            }
        }

        // Nearest hatch within reach, for the prompt.
        public bool NearHatch(float reach, out string name)
        {
            name = null;
            float best = reach;
            foreach (var kv in Hatches)
            {
                float d = Vector3.Distance(kv.Value, Pos);
                if (d < best) { best = d; name = kv.Key; }
            }
            return name != null;
        }
    }
}
