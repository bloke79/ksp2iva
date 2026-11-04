// Spin gravity for a ring interior (one with IVA_RingAxis markers). IVA does not reference the mod that spins the ring and
// the mod does not reference IVA, so the link is a soft contract found by reflection at session start (retried at unbuckle if not found):
// any component on the part (or its children) with these public instance PROPERTIES (properties only, fields are ignored).
//   float IvaSpinRadPerSec { get; }   required: the ring's angular speed in rad/s (0 when it isn't turning; sign ignored)
//   Transform IvaSpinFrame { get; }   optional: the transform that turns with the ring (its Spinner node). IVA parents the
//                                     interior to it, so the corridor turns with the ring.
//   float IvaSpinAngleDeg { get; }    optional, with IvaSpinFrame: the angle in degrees the Spinner is turned now, about its local Z,
//                                     where Spinner.localRotation = restRotation * AngleAxis(angle, Z) (Module_RingSpin's SpinAngle).
//                                     Lets IVA place the interior as if the ring were at home when you enter mid-spin.
// The interior is laid out in the part frame with the ring at home, and Spinner's rest rotation is not identity in general (its
// spin axis is its local Z, the ring axis), so the re-parent never keeps local pose.
// Nothing here runs for an interior without the ring markers.

using System;
using System.Reflection;
using UnityEngine;
using ILogger = SpaceWarp2.API.Logging.ILogger;

namespace IVA
{
    public class RingSpinLink
    {
        private Component _source;
        private PropertyInfo _omega;
        private PropertyInfo _frame;
        private PropertyInfo _angle;
        private bool _failed;

        public bool Found => _source != null && _omega != null && !_failed;

        // Spin gravity at radius r (m) for angular speed omega (rad/s): centripetal acceleration, m/s^2.
        public static float GravityAt(float omega, float r) => omega * omega * Mathf.Max(0f, r);

        public static RingSpinLink Find(Transform pod, ILogger log)
        {
            if (pod == null) return null;
            try
            {
                foreach (Component c in pod.GetComponentsInChildren<MonoBehaviour>(true))
                {
                    if (c == null) continue;
                    PropertyInfo w = c.GetType().GetProperty("IvaSpinRadPerSec", BindingFlags.Instance | BindingFlags.Public);
                    if (w == null || w.PropertyType != typeof(float) || !w.CanRead) continue;
                    PropertyInfo fr = c.GetType().GetProperty("IvaSpinFrame", BindingFlags.Instance | BindingFlags.Public);
                    if (fr != null && (fr.PropertyType != typeof(Transform) || !fr.CanRead)) fr = null;
                    PropertyInfo an = c.GetType().GetProperty("IvaSpinAngleDeg", BindingFlags.Instance | BindingFlags.Public);
                    if (an != null && (an.PropertyType != typeof(float) || !an.CanRead)) an = null;
                    log?.LogInfo($"IVA: ring spin source {c.GetType().Name}{(fr != null ? " (with spin frame)" : "")}.");
                    return new RingSpinLink { _source = c, _omega = w, _frame = fr, _angle = an };
                }
                log?.LogInfo("IVA: ring interior, but no component with IvaSpinRadPerSec on the part; no spin gravity.");
            }
            catch (Exception e) { log?.LogWarning("IVA: ring spin lookup failed: " + e.Message); }
            return null;
        }

        // rad/s, 0 when unknown. Fails soft: one warning, then reads 0.
        public float Omega(ILogger log)
        {
            if (!Found) return 0f;
            try { return (float)_omega.GetValue(_source, null); }
            catch (Exception e)
            {
                _failed = true;
                log?.LogWarning("IVA: reading IvaSpinRadPerSec failed, spin gravity off: " + e.Message);
                return 0f;
            }
        }

        public bool TryAngleDeg(ILogger log, out float angle)
        {
            angle = 0f;
            if (_source == null || _angle == null) return false;
            try { angle = (float)_angle.GetValue(_source, null); return true; }
            catch (Exception e) { log?.LogWarning("IVA: reading IvaSpinAngleDeg failed: " + e.Message); return false; }
        }

        public Transform SpinFrame(ILogger log)
        {
            if (_source == null || _frame == null) return null;
            try { return _frame.GetValue(_source, null) as Transform; }
            catch (Exception e) { log?.LogWarning("IVA: reading IvaSpinFrame failed: " + e.Message); return null; }
        }
    }
}
