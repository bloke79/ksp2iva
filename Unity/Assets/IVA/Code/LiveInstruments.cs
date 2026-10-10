// Live instruments for the custom interiors: the navball turns with the vessel's attitude and the dial needles show
// altitude, outside pressure and outside temperature.
//
// The interior model carries the moving parts as separate objects named "...__Live_<name>" (pivot at the object's
// origin) plus position-only marker objects ("IVA_Live<Role>_<name>") that say which way things point. Using marker
// positions rather than object rotations keeps this independent of how Blender's axes were converted on import.

using System;
using System.Collections.Generic;
using System.Linq;
using KSP.Game;
using KSP.Sim.impl;
using UnityEngine;
using ILogger = ReduxLib.Logging.ILogger;

namespace IVA
{
    public class LiveInstruments
    {
        private const float DialSweep = 270f;

        private class Needle
        {
            public string Kind;
            public Transform T;
            public Quaternion RestLocal;
            public Vector3 AxisLocal;      // in the parent's space
            public float Sign;             // +1/-1: which way increasing values turn round AxisLocal
            public float Shown;            // smoothed 0..1
        }

        private class Ball
        {
            public Transform T;
            public Quaternion RestLocal;
            public Vector3 RestScale;
            public Vector3 ZenithLocal, NorthLocal, FacingLocal, UpLocal;   // rest directions, parent space
        }

        private readonly List<Needle> _needles = new List<Needle>();
        private readonly List<Ball> _balls = new List<Ball>();
        public int Count => _needles.Count + _balls.Count;

        public static LiveInstruments Find(GameObject interior, ILogger log)
        {
            var li = new LiveInstruments();
            Transform[] all = interior.GetComponentsInChildren<Transform>(true);
            var byName = new Dictionary<string, Transform>();
            foreach (Transform t in all) byName[t.name] = t;
            foreach (Transform t in all)
            {
                int k = t.name.IndexOf("__Live_", StringComparison.Ordinal);
                if (k < 0) continue;
                string name = t.name.Substring(k + "__Live_".Length);
                int dot = name.IndexOf(" (", StringComparison.Ordinal);
                if (dot > 0) name = name.Substring(0, dot);
                Transform parent = t.parent;
                Vector3 Dir(string role)
                {
                    Transform m;
                    return byName.TryGetValue($"IVA_Live{role}_{name}", out m) && parent != null
                        ? parent.InverseTransformDirection(m.position - t.position).normalized : Vector3.zero;
                }
                if (name.StartsWith("Navball", StringComparison.Ordinal))
                {
                    var b = new Ball
                    {
                        T = t, RestLocal = t.localRotation, RestScale = t.localScale,
                        ZenithLocal = Dir("Zenith"), NorthLocal = Dir("North"), FacingLocal = Dir("Axis"), UpLocal = Dir("Up")
                    };
                    if (b.ZenithLocal == Vector3.zero || b.NorthLocal == Vector3.zero || b.FacingLocal == Vector3.zero || b.UpLocal == Vector3.zero)
                    { log.LogWarning($"IVA: navball {name} is missing its markers; it won't move."); continue; }
                    li._balls.Add(b);
                }
                else if (name.StartsWith("Needle_", StringComparison.Ordinal))
                {
                    Vector3 axis = Dir("Axis"), zero = Dir("Zero"), mid = Dir("Mid");
                    if (axis == Vector3.zero || zero == Vector3.zero || mid == Vector3.zero)
                    { log.LogWarning($"IVA: needle {name} is missing its markers; it won't move."); continue; }
                    string kind = name.Substring("Needle_".Length);
                    int us = kind.LastIndexOf('_');
                    if (us > 0) kind = kind.Substring(0, us);
                    li._needles.Add(new Needle
                    {
                        Kind = kind, T = t, RestLocal = t.localRotation, AxisLocal = axis,
                        Sign = Mathf.Sign(Vector3.SignedAngle(zero, mid, axis))
                    });
                }
            }
            log.LogInfo($"IVA: live instruments: {li._balls.Count} navball(s), {li._needles.Count} needle(s) " +
                        $"({string.Join(", ", li._needles.GroupBy(n => n.Kind).Select(g => $"{g.Key} x{g.Count()}"))}).");
            return li;
        }

        // pod: the part the crew sit in (its +Y is the nose, -Z the kerbals' head end).
        public void Update(GameInstance game, VesselComponent vessel, Transform pod, float dt)
        {
            if (vessel == null || pod == null) return;
            double altKm = vessel.AltitudeFromSeaLevel / 1000.0;
            float k = 1f - Mathf.Exp(-dt * 5f);
            foreach (Needle n in _needles)
            {
                if (n.T == null) continue;
                float target;
                switch (n.Kind)
                {
                    case "alt": target = (float)((altKm % 10.0 + 10.0) % 10.0 / 10.0); break;          // long hand: km
                    case "alt10": target = (float)((altKm / 10.0 % 10.0 + 10.0) % 10.0 / 10.0); break; // short hand: tens of km
                    case "press": target = (float)(vessel.StaticPressure_kPa / 100.0); break;          // 0..100 kPa
                    case "temp": target = (float)(vessel.AtmosphericTemperature / 1000.0); break;       // 0..1000 K
                    default: continue;
                }
                if (float.IsNaN(target) || float.IsInfinity(target)) target = 0f;
                target = Mathf.Clamp01(target);
                // the altimeter hands wrap: jump rather than sweep backwards across the dial
                n.Shown = Mathf.Abs(target - n.Shown) > 0.5f && n.Kind.StartsWith("alt") ? target : Mathf.Lerp(n.Shown, target, k);
                n.T.localRotation = Quaternion.AngleAxis(n.Sign * DialSweep * n.Shown, n.AxisLocal) * n.RestLocal;
            }
            if (_balls.Count > 0) UpdateNavballs(game, vessel, pod);
        }

        private void UpdateNavballs(GameInstance game, VesselComponent vessel, Transform pod)
        {
            TelemetryComponent tel = vessel.SimulationObject != null ? vessel.SimulationObject.Telemetry : null;
            var space = game?.UniverseView?.PhysicsSpace;
            if (tel == null || space == null) return;
            Vector3 upW = ((Vector3)space.VectorToPhysics(tel.HorizonUp)).normalized;
            Vector3 northW = ((Vector3)space.VectorToPhysics(tel.HorizonNorth)).normalized;
            if (upW == Vector3.zero || northW == Vector3.zero) return;
            Vector3 eastW = Vector3.Cross(upW, northW);          // Unity: right = up x forward
            Vector3 fwd = pod.up, head = -pod.forward;

            foreach (Ball b in _balls)
            {
                if (b.T == null || b.T.parent == null) continue;
                Transform p = b.T.parent;
                Vector3 facing = p.TransformDirection(b.FacingLocal), panelUp = p.TransformDirection(b.UpLocal);
                Vector3 panelRight = Vector3.Cross(facing, panelUp).normalized;
                // Navball: the vessel's nose shows at the ball's face, its head end at the top, and the sky is seen
                // mirrored (as on any navball: with the nose on the horizon facing north, east is to the right).
                Quaternion q = Quaternion.LookRotation(facing, panelUp) * Quaternion.Inverse(Quaternion.LookRotation(fwd, head));
                Vector3 Show(Vector3 d) { Vector3 v = q * d; return v - 2f * Vector3.Dot(v, panelRight) * panelRight; }
                Vector3 dz = Show(upW), dn = Show(northW), de = Show(eastW);

                // rest directions of the ball's printed zenith/north/east, world space
                Vector3 zr = p.TransformDirection(b.ZenithLocal), nr = p.TransformDirection(b.NorthLocal);
                Vector3 er = Vector3.Cross(zr, nr);
                Vector3 Map(Vector3 v) => Vector3.Dot(v, er) * de + Vector3.Dot(v, zr) * dz + Vector3.Dot(v, nr) * dn;
                // The map is a mirror image, so apply it as a mirror along the ball's local X plus a rotation.
                Quaternion restW = p.rotation * b.RestLocal;
                Vector3 ax = restW * Vector3.right;
                Vector3 Refl(Vector3 v) => v - 2f * Vector3.Dot(v, ax) * ax;
                Vector3 f = Map(Refl(restW * Vector3.forward)), u = Map(Refl(restW * Vector3.up));
                if (f.sqrMagnitude < 1e-6f || u.sqrMagnitude < 1e-6f) continue;
                b.T.rotation = Quaternion.LookRotation(f, u);
                b.T.localScale = new Vector3(-Mathf.Abs(b.RestScale.x), b.RestScale.y, b.RestScale.z);
            }
        }
    }
}
