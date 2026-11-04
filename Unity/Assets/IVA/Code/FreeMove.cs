// Moving around inside the cabin (unbuckled): a small sphere that floats in pod space and slides along the interior.
//
// No Unity physics: colliders on the interior would join the pod's rigidbody and could disturb the vessel. Instead the
// interior carries position-only markers (made by art/stock.py collision_markers) that describe its shape:
//   IVA_ColAxis_0/1      the pod axis, floor to top
//   IVA_ColHull_<k>      a point on the hull at each height (the radius profile)
//   IVA_ColDeck_<k>      deck heights; IVA_ColHole_<k>_c/x/y/z are the openings you can pass through
//   IVA_ColBox_<k>_c/x/y/z  oriented boxes round the larger equipment (centre and three half-axis tips)
//   IVA_Hatch_<name>     hatch positions, for a prompt
//   IVA_Floor_<k>_p/_n   floors you can walk on under gravity (a point on the plane, and 0.1 m along its up normal)
// Everything is converted to pod space once, when you unbuckle; the interior doesn't move inside the pod.
//
// Two modes. Floating (zero g): the sphere is the eye, it moves where you look. Walking (landed, with a floor that
// faces up): the eye stands EyeStand above the feet, gravity pulls the feet to the highest support under them (a floor,
// or the top of a box no more than StepUp up), walls and equipment push sideways only, and the view turns about up.

using System;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;
using ILogger = SpaceWarp2.API.Logging.ILogger;

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
        private readonly List<Box> _doors = new List<Box>();
        private readonly List<bool> _doorSolid = new List<bool>();
        private readonly List<float> _decks = new List<float>();
        private readonly List<Vector2> _hull = new List<Vector2>();   // (height along the axis, radius), sorted
        public readonly List<KeyValuePair<string, Vector3>> Hatches = new List<KeyValuePair<string, Vector3>>();
        private Vector3 _a0, _u;
        private float _hMax;

        // Ring mode (only when the interior has IVA_RingAxis_0/1 and IVA_RingRadius): the frame is the interior root, not the
        // pod, because the ring turns inside the part. Pos, Rot and every marker are in Frame space. Otherwise Frame is the pod.
        public Transform Frame { get; private set; }
        public bool RingMode { get; private set; }

        public Vector3 Pos;                 // pod space (ring mode: interior root space)
        public Quaternion Rot = Quaternion.identity;
        private Vector3 _vel;
        private bool _ghost;                // ignore equipment until clear of it (you start inside your couch)
        public float Radius = 0.13f;

        // walking
        public const float EyeStand = 0.86f, EyeCrouch = 0.55f, StepUp = 0.12f, JumpSpeed = 2.0f;
        private readonly List<KeyValuePair<Vector3, Vector3>> _floors = new List<KeyValuePair<Vector3, Vector3>>();   // point, up normal
        public bool Walking { get; private set; }
        public bool Grounded { get; private set; }
        private Vector3 _up = Vector3.up;
        private float _g;
        private Vector3 _heading = Vector3.forward;   // level look direction (perpendicular to up)
        private float _pitch;                         // degrees, + looks down
        private float _eyeH = EyeStand;
        public int FloorCount => _floors.Count;

        // Ladders (ring mode only): IVA_Ladder_<n>_0 (ring end), _1 (hub end) and optional _Radius, all in Frame space. The list stays
        // empty for every interior without those markers, so nothing that uses it runs for them.
        public struct Ladder
        {
            public int N;            // the number in the marker names
            public Vector3 A, B, U;  // ring end, hub end, unit direction A to B
            public float Len;        // |B - A|
            public float GrabR;      // capsule radius to grab it, and the tube radius round it
            public float SMin;       // lowest point on the climb: at or below A (0 to -3 m), so the eye can come down to standing height
        }

        private readonly List<Ladder> _ladders = new List<Ladder>();
        public int LadderCount => _ladders.Count;
        public Ladder GetLadder(int i) => _ladders[i];

        public bool Valid => _hull.Count >= 2 && _hMax > 0.1f;
        public int BoxCount => _boxes.Count;
        public Vector3 Axis => _u;
        public Vector3 Middle => _a0 + _u * (_hMax * 0.5f);   // halfway up the axis, pod space

        // True for a spinning-ring interior: the three optional ring markers are all there. Existing interiors have none.
        public static bool HasRingMarkers(Transform interior)
        {
            if (interior == null) return false;
            bool a0 = false, a1 = false, rad = false;
            foreach (Transform t in interior.GetComponentsInChildren<Transform>(true))
            {
                if (t.name == "IVA_RingAxis_0") a0 = true;
                else if (t.name == "IVA_RingAxis_1") a1 = true;
                else if (t.name == "IVA_RingRadius") rad = true;
            }
            return a0 && a1 && rad;
        }

        public static FreeMove Build(Transform interior, Transform pod, ILogger log)
        {
            var f = new FreeMove();
            bool ring = HasRingMarkers(interior);
            Transform frame = ring ? interior : pod;
            f.Frame = frame;
            var pts = new Dictionary<string, Vector3>(StringComparer.Ordinal);
            foreach (Transform t in interior.GetComponentsInChildren<Transform>(true))
                if (t.name.StartsWith("IVA_Col", StringComparison.Ordinal) || t.name.StartsWith("IVA_Hatch_", StringComparison.Ordinal)
                    || t.name.StartsWith("IVA_Floor_", StringComparison.Ordinal)
                    || t.name.StartsWith("IVA_Ring", StringComparison.Ordinal) || t.name.StartsWith("IVA_Ladder_", StringComparison.Ordinal))
                    pts[t.name] = frame.InverseTransformPoint(t.position);
            Vector3 a0 = Vector3.zero, a1 = Vector3.zero;
            float ringR = 0f;
            if (ring)
            {
                // No IVA_ColAxis in a ring: the spin axis is the movement axis, and the hull wall is a cylinder round it.
                a0 = pts["IVA_RingAxis_0"];
                a1 = pts["IVA_RingAxis_1"];
                Vector3 axis = (a1 - a0).normalized;
                Vector3 d = pts["IVA_RingRadius"] - a0;
                ringR = (d - axis * Vector3.Dot(d, axis)).magnitude;
                if ((a1 - a0).magnitude < 0.1f || ringR < 0.5f)
                {
                    log?.LogWarning("IVA: ring markers are degenerate (axis shorter than 0.1 m or radius under 0.5 m); can't move around inside.");
                    return f;
                }
            }
            else if (!pts.TryGetValue("IVA_ColAxis_0", out a0) || !pts.TryGetValue("IVA_ColAxis_1", out a1))
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
            if (ring)
            {
                f.RingMode = true;
                f._hull.Add(new Vector2(0f, ringR + 0.3f));          // wall just outside the floor ring; the underfloor slabs do the rest
                f._hull.Add(new Vector2(f._hMax, ringR + 0.3f));
            }
            f._hull.Sort((p, q) => p.x.CompareTo(q.x));
            foreach (var kv in pts.Where(p => p.Key.StartsWith("IVA_ColDeck_", StringComparison.Ordinal)))
                f._decks.Add(Vector3.Dot(kv.Value - a0, f._u));
            ReadBoxes(pts, "IVA_ColHole_", f._holes);
            ReadBoxes(pts, "IVA_ColBox_", f._boxes);
            foreach (var kv in pts.Where(p => p.Key.StartsWith("IVA_Hatch_", StringComparison.Ordinal)))
                f.Hatches.Add(new KeyValuePair<string, Vector3>(kv.Key.Substring("IVA_Hatch_".Length), kv.Value));
            foreach (var kv in pts.Where(p => p.Key.StartsWith("IVA_Floor_", StringComparison.Ordinal) && p.Key.EndsWith("_p", StringComparison.Ordinal)))
                if (pts.TryGetValue(kv.Key.Substring(0, kv.Key.Length - 2) + "_n", out Vector3 n))
                    f._floors.Add(new KeyValuePair<Vector3, Vector3>(kv.Value, (n - kv.Value).normalized));
            if (ring) ReadLadders(pts, f, log);
            log?.LogInfo($"IVA: free movement ready: hull {f._hull.Count} rings over {f._hMax:F2} m, {f._decks.Count} deck(s), " +
                         $"{f._holes.Count} opening(s), {f._boxes.Count} equipment box(es), {f.Hatches.Count} hatch(es), {f._floors.Count} floor(s)." +
                         (ring ? $" Ring mode: radius {ringR:F2} m, frame is the interior root." : ""));
            return f;
        }

        // Ring mode: the up direction at p (towards the spin axis, so "down" is outward) and the distance from the axis.
        public Vector3 RingUpAt(Vector3 p)
        {
            Vector3 d = p - _a0;
            Vector3 radial = d - _u * Vector3.Dot(d, _u);
            return radial.sqrMagnitude < 1e-6f ? _up : -radial.normalized;
        }

        public float RingRadiusAt(Vector3 p)
        {
            Vector3 d = p - _a0;
            return (d - _u * Vector3.Dot(d, _u)).magnitude;
        }

        // Reads IVA_Ladder_<n>_0 / _1 / _Radius (n a 0-based integer). A ladder missing an end, or shorter than 0.3 m, is skipped.
        private static void ReadLadders(Dictionary<string, Vector3> pts, FreeMove f, ILogger log)
        {
            const string prefix = "IVA_Ladder_";
            var byId = new SortedDictionary<int, Dictionary<string, Vector3>>();
            foreach (var kv in pts)
            {
                if (!kv.Key.StartsWith(prefix, StringComparison.Ordinal)) continue;
                string rest = kv.Key.Substring(prefix.Length);   // "<n>_0", "<n>_1" or "<n>_Radius"
                int us = rest.IndexOf('_');
                if (us <= 0 || !int.TryParse(rest.Substring(0, us), out int id) || id < 0) continue;
                if (!byId.TryGetValue(id, out var m)) byId[id] = m = new Dictionary<string, Vector3>(StringComparer.Ordinal);
                m[rest.Substring(us + 1)] = kv.Value;
            }
            foreach (var entry in byId)
            {
                Dictionary<string, Vector3> m = entry.Value;
                if (!m.TryGetValue("0", out Vector3 a) || !m.TryGetValue("1", out Vector3 b) || (b - a).magnitude < 0.3f)
                {
                    log?.LogWarning($"IVA: ladder {entry.Key}: markers missing, ladder ignored.");
                    continue;
                }
                var l = new Ladder { N = entry.Key, A = a, B = b, Len = (b - a).magnitude };
                l.U = (b - a) / l.Len;
                l.GrabR = 0.45f;
                if (m.TryGetValue("Radius", out Vector3 rp))
                {
                    Vector3 d = rp - a;
                    l.GrabR = Mathf.Max(0.05f, (d - l.U * Vector3.Dot(d, l.U)).magnitude);
                }
                // The climb may go below A until the eye is at standing height over the nearest floor plane, measured outward
                // from A (A sits on the ceiling hatch), so stepping off at the ring end needs no jump.
                Vector3 outward = -f.RingUpAt(a);
                float nearest = float.MaxValue;
                foreach (var fl in f._floors)
                {
                    float dn = Vector3.Dot(outward, fl.Value);
                    if (dn > -0.5f) continue;
                    float t = Vector3.Dot(fl.Key - a, fl.Value) / dn;
                    if (t > 0.01f && t < nearest) nearest = t;
                }
                l.SMin = nearest < float.MaxValue ? Mathf.Clamp(-(nearest - EyeStand), -3f, 0f) : 0f;
                f._ladders.Add(l);
                log?.LogInfo($"IVA: ladder {l.N} found: {l.Len:F1} m, bottom ({a.x:F2},{a.y:F2},{a.z:F2}) top ({b.x:F2},{b.y:F2},{b.z:F2}).");
                log?.LogInfo($"IVA: ladder {l.N}: grab radius {l.GrabR:F2} m, climb reaches {-l.SMin:F2} m below the ring end" +
                             (nearest < float.MaxValue ? $" (floor {nearest:F2} m below it)." : " (no floor found below it)."));
            }
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
            if (Walking)
            {
                // walking rebuilds Rot from these every frame
                Vector3 fwd = rot * Vector3.forward;
                _heading = Vector3.ProjectOnPlane(fwd, _up);
                _pitch = Mathf.Clamp(Vector3.Angle(fwd, _up) - 90f, -85f, 85f);
                Grounded = false;
            }
        }

        // Look: floating, yaw and pitch round the view's own axes (no horizon in zero g), roll from the keys; walking, yaw
        // about up and pitch clamped, no roll.
        public void Turn(float yawDeg, float pitchDeg, float rollDeg)
        {
            if (!Walking) { Rot = Rot * Quaternion.Euler(pitchDeg, yawDeg, rollDeg); return; }
            _heading = Quaternion.AngleAxis(yawDeg, _up) * _heading;
            _pitch = Mathf.Clamp(_pitch + pitchDeg, -85f, 85f);
            WalkRot();
        }

        private void WalkRot()
        {
            _heading = Vector3.ProjectOnPlane(_heading, _up);
            if (_heading.sqrMagnitude < 1e-6f) _heading = Vector3.ProjectOnPlane(Rot * Vector3.up, _up);
            if (_heading.sqrMagnitude < 1e-6f) _heading = Vector3.ProjectOnPlane(Vector3.forward, _up);
            _heading.Normalize();
            Rot = Quaternion.LookRotation(_heading, _up) * Quaternion.Euler(_pitch, 0f, 0f);
        }

        // The floor that faces up (within maxDeg), or -1.
        public int FloorFor(Vector3 up, float maxDeg = 35f)
        {
            float cos = Mathf.Cos(maxDeg * Mathf.Deg2Rad);
            int best = -1;
            float bestDot = cos;
            for (int i = 0; i < _floors.Count; i++)
            {
                float d = Vector3.Dot(_floors[i].Value, up.normalized);
                if (d >= bestDot) { bestDot = d; best = i; }
            }
            return best;
        }

        // Gravity from outside (pod space): on with up (opposite to the pull) and g in m/s^2, or off to float.
        public void SetWalking(bool on, Vector3 up, float g)
        {
            if (on)
            {
                _up = up.normalized;
                _g = g;
                if (!Walking)
                {
                    Vector3 fwd = Rot * Vector3.forward;
                    _heading = Vector3.ProjectOnPlane(fwd, _up);
                    _pitch = Mathf.Clamp(Vector3.Angle(fwd, _up) - 90f, -85f, 85f);
                    _eyeH = EyeStand;
                    Grounded = false;
                    Walking = true;
                }
                WalkRot();
            }
            else Walking = false;
        }

        // Walking: move x right / y forward (-1..1), relative to where you face.
        public void StepWalk(Vector2 move, bool jump, bool crouch, float dt, float speed)
        {
            if (dt <= 0f) return;
            dt = Mathf.Min(dt, 0.05f);
            Vector3 right = Vector3.Cross(_up, _heading).normalized;
            Vector3 wish = (_heading * move.y + right * move.x) * speed;
            float vUp = Vector3.Dot(_vel, _up);
            Vector3 vFlat = _vel - _up * vUp;
            vFlat = Vector3.MoveTowards(vFlat, wish, (Grounded ? 6f : 1f) * dt);
            if (Grounded && jump) { vUp = JumpSpeed; Grounded = false; }
            if (!Grounded) vUp = Mathf.Max(vUp - _g * dt, -10f);
            _vel = vFlat + _up * vUp;

            // eye height: crouch when asked, or when the cabin top is too low to stand
            float target = crouch ? EyeCrouch : EyeStand;
            Vector3 feetNow = Pos - _up * _eyeH;
            float headroom = (_hMax - Radius) - Height(feetNow) - 0.02f;   // along the pod axis (landers: the same as up)
            if (Vector3.Dot(_up, _u) > 0.8f) target = Mathf.Min(target, Mathf.Max(EyeCrouch, headroom));
            float eyeH = Mathf.MoveTowards(_eyeH, target, 1.5f * dt);

            Vector3 p = feetNow + _up * eyeH + _vel * dt;
            // walls and equipment: probe the head, chest and knees; keep only the sideways push
            float[] probes = { 0f, eyeH * 0.5f, eyeH - 0.27f };
            for (int it = 0; it < 3; it++)
                foreach (float o in probes)
                {
                    Vector3 q0 = p - _up * o, q = q0;
                    Resolve(q0 - _vel * dt, ref q);
                    Vector3 push = q - q0;
                    p += push - _up * Vector3.Dot(push, _up);
                }
            // ground
            Vector3 feet = p - _up * eyeH;
            float t = GroundBelow(feet);
            if (t > -0.02f && Vector3.Dot(_vel, _up) <= 0.01f)
            {
                p += _up * t;
                _vel -= _up * Vector3.Dot(_vel, _up);
                Grounded = true;
            }
            else Grounded = false;
            // head against the top
            if (Vector3.Dot(_up, _u) > 0.8f && Height(p) + Radius > _hMax && Vector3.Dot(_vel, _up) > 0f) _vel -= _up * Vector3.Dot(_vel, _up);
            _eyeH = eyeH;
            Pos = p;
            if (_ghost && !InsideAnyBox(Pos - _up * (eyeH * 0.5f)) && !InsideAnyBox(Pos)) _ghost = false;
        }

        // How far up (along up, from the feet) the highest support is, within StepUp above the feet; -inf if none.
        private float GroundBelow(Vector3 feet)
        {
            float best = float.NegativeInfinity;
            foreach (var fl in _floors)
            {
                float dn = Vector3.Dot(_up, fl.Value);
                if (dn < 0.5f) continue;
                float t = Vector3.Dot(fl.Key - feet, fl.Value) / dn;
                if (t > StepUp || t <= best) continue;
                Vector3 at = feet + _up * t;
                if (_holes.Any(b => Inside(b, at, -Radius * 0.5f))) continue;
                best = t;
            }
            if (_ghost) return best;
            foreach (Box b in _boxes)
            {
                Vector3 d = b.C - feet;
                if (d.sqrMagnitude > (b.Reach + 0.3f) * (b.Reach + 0.3f)) continue;
                float ext = 0f, flatMin = float.MaxValue;
                for (int i = 0; i < 3; i++)
                {
                    Vector3 ax = i == 0 ? b.X : i == 1 ? b.Y : b.Z;
                    float e = i == 0 ? b.E.x : i == 1 ? b.E.y : b.E.z;
                    float a = Mathf.Abs(Vector3.Dot(ax, _up));
                    ext += e * a;
                    if (a < 0.5f) flatMin = Mathf.Min(flatMin, e);
                }
                if (flatMin < 0.04f) continue;   // panels, labels, strips: not something to stand on
                float t = Vector3.Dot(d, _up) + ext;
                if (t > StepUp || t <= best) continue;
                if (!Inside(b, feet + _up * (t - 0.02f), 0.02f)) continue;
                best = t;
            }
            return best;
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
            // equipment boxes, then closed doors
            for (int i = 0; i < _boxes.Count + _doors.Count; i++)
            {
                if (i >= _boxes.Count && !_doorSolid[i - _boxes.Count]) continue;
                Box b = i < _boxes.Count ? _boxes[i] : _doors[i - _boxes.Count];
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

        // A door leaf (closed): centre and three half-axis vectors. Returns its index for SetDoorSolid.
        public int AddDoor(Vector3 c, Vector3 hx, Vector3 hy, Vector3 hz)
        {
            var b = new Box { C = c, X = hx.normalized, Y = hy.normalized, Z = hz.normalized, E = new Vector3(hx.magnitude, hy.magnitude, hz.magnitude) };
            b.Reach = b.E.magnitude;
            _doors.Add(b);
            _doorSolid.Add(true);
            return _doors.Count - 1;
        }

        public void SetDoorSolid(int i, bool solid)
        {
            if (i >= 0 && i < _doorSolid.Count) _doorSolid[i] = solid;
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
