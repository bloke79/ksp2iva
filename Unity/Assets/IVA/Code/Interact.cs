// Things in the cabin you can use with the action key (F) while floating: look at one and press F.
//
// Everything comes from position-only markers and named moving parts in the interior (art/act.py):
//   IVA_Act_<Kind>_<name>     where to look: Door, Slide, Curtain, Lamp, Screen, Flush, Wash, Lights
//   ...__Live_Door / Slide / Curtain / Glow / Screen<name>   the parts that move or change (see Doors.cs for hinges)
// The target is whatever the view points at most directly within reach; the prompt says what F will do.

using System;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;
using ILogger = ReduxLib.Logging.ILogger;

namespace IVA
{
    public class Interact
    {
        public const float Reach = 1.4f;
        private const float MoveSeconds = 0.4f;

        public class Target
        {
            public string Kind, Name;
            public Vector3 Pod;          // where to look, pod space
            public Func<string> Prompt;  // "open the locker"
            public Action Use;
        }

        private class Mover
        {
            public string Name;
            public readonly List<Transform> Parts = new List<Transform>();
            public readonly List<Vector3> Rest = new List<Vector3>();
            public readonly List<Vector3> Delta = new List<Vector3>();   // slide: open offset in each part's parent space
            public Transform Pivot;       // curtain: stretched along its x axis
            public float Factor = 1f;     // curtain: scale when closed
            public float Open, Target;
        }

        private class LightRec { public Light L; public Color C; public float I; }
        private class Wheel { public readonly List<Transform> Parts = new List<Transform>(); public readonly List<Quaternion> Rest = new List<Quaternion>(); public readonly List<Vector3> Axis = new List<Vector3>(); }
        private class HatchRun { public Wheel W; public Doors.Door Lid; public Action Then; public float T; public int Phase; }
        private readonly Dictionary<string, Wheel> _wheels = new Dictionary<string, Wheel>(StringComparer.Ordinal);
        private HatchRun _hatchRun;
        public bool HatchBusy => _hatchRun != null;
        private class EmitRec { public Material M; public Color C; }

        public readonly List<Target> Targets = new List<Target>();
        public Doors Doors;
        public Sounds Sounds;   // set by the plugin; may be null
        private readonly List<Mover> _slides = new List<Mover>();
        private readonly List<Mover> _curtains = new List<Mover>();
        private readonly List<LightRec> _lights = new List<LightRec>();
        private readonly List<EmitRec> _emitters = new List<EmitRec>();
        private readonly List<Material> _pages = new List<Material>();
        private readonly List<KeyValuePair<float, string>> _later = new List<KeyValuePair<float, string>>();
        private int _lightMode;   // 0 normal, 1 night (red), 2 dim
        private static readonly string[] LightModes = { "normal", "night", "dim" };
        private float _clock;

        public static Interact Build(GameObject interior, Transform pod, ILogger log)
        {
            var ix = new Interact();
            Transform[] all = interior.GetComponentsInChildren<Transform>(true);
            Dictionary<string, Transform> live = Doors.Markers(all, "IVA_Live");
            Dictionary<string, Transform> acts = Doors.Markers(all, "IVA_Act_");
            Vector3 P(Transform t) => pod.InverseTransformPoint(t.position);
            Vector3 ActAt(string kind, string name, Vector3 fallback) => acts.TryGetValue($"IVA_Act_{kind}_{name}", out Transform m) ? P(m) : fallback;

            // hinged: doors, lockers, the food warmer, freezers
            ix.Doors = Doors.Find(interior, pod, log);
            foreach (Doors.Door d in ix.Doors.All)
            {
                if (d.Name.StartsWith("DoorHatch", StringComparison.Ordinal)) continue;   // hatch lids open with the hatch (OpenHatch)
                Doors.Door door = d;
                string what = Noun(door.Name);
                ix.Targets.Add(new Target
                {
                    Kind = "Door", Name = door.Name, Pod = ActAt("Door", door.Name.Substring(4), door.CentrePod + door.OutPod * 0.02f),
                    Prompt = () => (door.Target > 0.5f ? "close the " : "open the ") + what,
                    Use = () =>
                    {
                        door.Target = door.Target > 0.5f ? 0f : 1f;
                        bool big = door.IsRoomDoor;
                        ix.Sounds?.Play(door.Target > 0.5f ? (big ? Sounds.DoorOpen : Sounds.LockerOpen) : (big ? Sounds.DoorClose : Sounds.LockerClose));
                        if (what == "food warmer" && door.Target < 0.5f) ix.Later(0.7f, Sounds.OvenStart);
                    },
                });
            }

            // groups of moving parts by kind
            var groups = new Dictionary<string, List<Transform>>(StringComparer.Ordinal);
            foreach (Transform t in all)
                foreach (string kind in new[] { "Slide", "Curtain", "Glow", "Screen", "Wheel" })
                {
                    string key = Doors.LiveKey(t.name, kind, out bool main);
                    if (key == null || t.parent == null) continue;
                    if (!groups.TryGetValue(key, out var list)) groups[key] = list = new List<Transform>();
                    if (main) list.Insert(0, t); else list.Add(t);
                }

            foreach (var kv in groups)
            {
                string key = kv.Key;
                Transform main = kv.Value[0];
                if (key.StartsWith("Slide", StringComparison.Ordinal))
                {
                    if (!live.TryGetValue("IVA_LiveTo_" + key, out Transform to)) { log?.LogWarning($"IVA: {key} has no IVA_LiveTo_ marker."); continue; }
                    var m = new Mover { Name = key };
                    Vector3 travelW = to.position - main.position;
                    foreach (Transform t in kv.Value)
                    {
                        m.Parts.Add(t);
                        m.Rest.Add(t.localPosition);
                        m.Delta.Add(t.parent.InverseTransformVector(travelW));
                    }
                    ix._slides.Add(m);
                    ix.Targets.Add(new Target
                    {
                        Kind = "Slide", Name = key, Pod = ActAt("Slide", key.Substring(5), P(main)),
                        Prompt = () => m.Target > 0.5f ? "close the drawer" : "open the drawer",
                        Use = () => { m.Target = m.Target > 0.5f ? 0f : 1f; ix.Sounds?.Play(m.Target > 0.5f ? Sounds.DrawerOpen : Sounds.DrawerClose); },
                    });
                }
                else if (key.StartsWith("Curtain", StringComparison.Ordinal))
                {
                    if (!live.TryGetValue("IVA_LiveOpen_" + key, out Transform openM) || !live.TryGetValue("IVA_LiveEdge_" + key, out Transform edgeM))
                    { log?.LogWarning($"IVA: {key} is missing its markers."); continue; }
                    Vector3 dirW = edgeM.position - main.position;
                    float now = Vector3.Distance(openM.position, main.position);
                    if (now < 0.01f || dirW.magnitude < 0.01f) continue;
                    var pivot = new GameObject("IVA_CurtainPivot_" + key).transform;
                    pivot.SetParent(main.parent, false);
                    pivot.SetPositionAndRotation(main.position, Quaternion.FromToRotation(main.parent.right, dirW.normalized) * main.parent.rotation);
                    var m = new Mover { Name = key, Pivot = pivot, Factor = dirW.magnitude / now };
                    foreach (Transform t in kv.Value) { t.SetParent(pivot, true); m.Parts.Add(t); }
                    ix._curtains.Add(m);
                    ix.Targets.Add(new Target
                    {
                        Kind = "Curtain", Name = key, Pod = ActAt("Curtain", key.Substring(7), P(main)),
                        Prompt = () => m.Target > 0.5f ? "open the curtain" : "close the curtain",
                        Use = () => { m.Target = m.Target > 0.5f ? 0f : 1f; ix.Sounds?.Play(Sounds.Curtain); },
                    });
                }
                else if (key.StartsWith("Glow", StringComparison.Ordinal))
                {
                    Renderer r = main.GetComponent<Renderer>();
                    if (r == null) continue;
                    ix.Targets.Add(new Target
                    {
                        Kind = "Lamp", Name = key, Pod = ActAt("Lamp", key.Substring(4), P(main)),
                        Prompt = () => r.enabled ? "turn the reading lamp off" : "turn the reading lamp on",
                        Use = () => { r.enabled = !r.enabled; ix.Sounds?.Play(Sounds.Switch); },
                    });
                }
                else if (key.StartsWith("Wheel", StringComparison.Ordinal))
                {
                    if (!live.TryGetValue("IVA_LiveAxis_" + key, out Transform axisM)) continue;
                    var w = new Wheel();
                    Vector3 axisW = (axisM.position - main.position).normalized;
                    foreach (Transform t in kv.Value)
                    {
                        w.Parts.Add(t);
                        w.Rest.Add(t.localRotation);
                        w.Axis.Add(t.parent.InverseTransformDirection(axisW).normalized);
                    }
                    ix._wheels[key.Substring(5)] = w;   // "Hatch<name>"
                }
                else if (key.StartsWith("Screen", StringComparison.Ordinal))
                {
                    Renderer r = main.GetComponent<Renderer>();
                    if (r == null) continue;
                    ix.Targets.Add(new Target
                    {
                        Kind = "Screen", Name = key, Pod = ActAt("Screen", key.Substring(6), P(main)),
                        Prompt = () => "next page",
                        Use = () => ix.NextPage(r),
                    });
                }
            }

            // sound-only and cabin-wide
            foreach (var kv in acts)
            {
                string[] bits = kv.Key.Split(new[] { '_' }, 4);   // IVA, Act, Kind, name
                if (bits.Length < 4) continue;
                Vector3 at = P(kv.Value);
                switch (bits[2])
                {
                    case "Flush":
                        ix.Targets.Add(new Target { Kind = "Flush", Name = bits[3], Pod = at, Prompt = () => "flush",
                            Use = () => { ix.Sounds?.Play(Sounds.FlushStart); ix.Later(1.6f, Sounds.FlushStop); } });
                        break;
                    case "Wash":
                        ix.Targets.Add(new Target { Kind = "Wash", Name = bits[3], Pod = at, Prompt = () => "run the water",
                            Use = () => { ix.Sounds?.Play(Sounds.FlushStart); ix.Later(0.8f, Sounds.FlushStop); } });
                        break;
                    case "Lights":
                        ix.Targets.Add(new Target { Kind = "Lights", Name = bits[3], Pod = at,
                            Prompt = () => $"cabin lights: {LightModes[(ix._lightMode + 1) % LightModes.Length]}", Use = ix.NextLightMode });
                        break;
                }
            }

            // cabin lights and lit faces, for the light modes; screen pages
            foreach (Light l in interior.GetComponentsInChildren<Light>(true))
                ix._lights.Add(new LightRec { L = l, C = l.color, I = l.intensity });
            var mats = new HashSet<Material>();
            foreach (Renderer r in interior.GetComponentsInChildren<Renderer>(true))
                foreach (Material m in r.sharedMaterials)
                    if (m != null) mats.Add(m);
            foreach (Material m in mats)
            {
                if ((m.name.StartsWith("IVA_LightPanel", StringComparison.Ordinal) || m.name.StartsWith("IVA_LightStrip", StringComparison.Ordinal)) && m.HasProperty("_EmissionColor"))
                    ix._emitters.Add(new EmitRec { M = m, C = m.GetColor("_EmissionColor") });
                if (m.name.StartsWith("IVA_MFD_", StringComparison.Ordinal)) ix._pages.Add(m);
            }
            ix._pages.Sort((a, b) => string.CompareOrdinal(a.name, b.name));

            log?.LogInfo($"IVA: {ix.Targets.Count} thing(s) to use: " +
                         string.Join(", ", ix.Targets.GroupBy(t => t.Kind).Select(g => $"{g.Count()} {g.Key}")) + $"; {ix._pages.Count} screen page(s).");
            return ix;
        }

        private static string Noun(string doorName)
        {
            if (doorName.Contains("Hygiene")) return "door";
            if (doorName.Contains("Oven")) return "food warmer";
            if (doorName.Contains("Freezer")) return "freezer";
            return "locker";
        }

        // A hatch with a handwheel and a lid (round floor hatches): turn the wheel, swing the lid open with the wheel on it,
        // then call `then`. Without them, `then` runs at once. Returns false if nothing is animated.
        public bool OpenHatch(string hatchName, Action then)
        {
            _wheels.TryGetValue("Hatch" + hatchName, out Wheel w);
            Doors.Door lid = Doors?.All.Find(d => d.Name == "DoorHatch" + hatchName);
            if (w == null && lid == null) { then(); return false; }
            _hatchRun = new HatchRun { W = w, Lid = lid, Then = then };
            Sounds?.Play(Sounds.HatchWheel);
            return true;
        }

        private void UpdateHatch(float dt)
        {
            HatchRun h = _hatchRun;
            if (h == null) return;
            h.T += dt;
            if (h.Phase == 0)
            {
                float a = 360f * Mathf.SmoothStep(0f, 1f, Mathf.Clamp01(h.T / 0.9f));
                if (h.W != null)
                    for (int i = 0; i < h.W.Parts.Count; i++)
                        if (h.W.Parts[i] != null) h.W.Parts[i].localRotation = Quaternion.AngleAxis(a, h.W.Axis[i]) * h.W.Rest[i];
                if (h.T < 0.9f) return;
                if (h.Lid != null && h.Lid.Parts.Count > 0 && h.Lid.Parts[0].T != null)
                {
                    if (h.W != null)
                        foreach (Transform t in h.W.Parts) if (t != null) t.SetParent(h.Lid.Parts[0].T, true);   // the wheel rides on the lid
                    h.Lid.Target = 1f;
                    Sounds?.Play(Sounds.HatchLid);
                }
                h.Phase = 1;
                h.T = 0f;
                return;
            }
            if (h.T < Doors.SwingSeconds + 0.25f) return;
            _hatchRun = null;
            h.Then?.Invoke();
        }

        private void Later(float seconds, string ev) => _later.Add(new KeyValuePair<float, string>(_clock + seconds, ev));

        private void NextPage(Renderer r)
        {
            if (_pages.Count < 2) return;
            int i = _pages.IndexOf(r.sharedMaterial);
            r.sharedMaterial = _pages[(i + 1) % _pages.Count];
            Sounds?.Play(Sounds.Button);
        }

        private void NextLightMode()
        {
            _lightMode = (_lightMode + 1) % LightModes.Length;
            Color tint = _lightMode == 1 ? new Color(1f, 0.22f, 0.15f) : Color.white;
            float k = _lightMode == 0 ? 1f : _lightMode == 1 ? 0.55f : 0.2f;
            foreach (LightRec l in _lights)
                if (l.L != null) { l.L.color = _lightMode == 1 ? tint : l.C; l.L.intensity = l.I * k; }
            foreach (EmitRec e in _emitters)
                if (e.M != null) e.M.SetColor("_EmissionColor", e.C * tint * k);
            Sounds?.Play(_lightMode == 2 ? Sounds.LightsOff : Sounds.LightsOn);
        }

        // The target the view points at most directly, within reach.
        public Target Pick(Vector3 eyePod, Vector3 fwdPod)
        {
            Target best = null;
            float bestAng = float.MaxValue;
            foreach (Target t in Targets)
            {
                Vector3 d = t.Pod - eyePod;
                float dist = d.magnitude;
                if (dist > Reach || dist < 0.05f) continue;
                float ang = Vector3.Angle(fwdPod, d);
                float allow = Mathf.Max(7f, Mathf.Rad2Deg * Mathf.Atan2(0.12f, dist));
                if (ang > allow) continue;
                float score = ang + dist * 2f;   // prefer the more central, then the nearer
                if (score < bestAng) { bestAng = score; best = t; }
            }
            return best;
        }

        public void Update(float dt)
        {
            _clock += dt;
            for (int i = _later.Count - 1; i >= 0; i--)
                if (_clock >= _later[i].Key) { Sounds?.Play(_later[i].Value); _later.RemoveAt(i); }
            Doors?.Update(dt);
            UpdateHatch(dt);
            foreach (Mover m in _slides)
            {
                if (Mathf.Approximately(m.Open, m.Target)) continue;
                m.Open = Mathf.MoveTowards(m.Open, m.Target, dt / MoveSeconds);
                float s = Mathf.SmoothStep(0f, 1f, m.Open);
                for (int i = 0; i < m.Parts.Count; i++)
                    if (m.Parts[i] != null) m.Parts[i].localPosition = m.Rest[i] + m.Delta[i] * s;
            }
            foreach (Mover m in _curtains)
            {
                if (Mathf.Approximately(m.Open, m.Target) || m.Pivot == null) continue;
                m.Open = Mathf.MoveTowards(m.Open, m.Target, dt / (MoveSeconds * 1.5f));
                m.Pivot.localScale = new Vector3(Mathf.Lerp(1f, m.Factor, Mathf.SmoothStep(0f, 1f, m.Open)), 1f, 1f);
            }
        }

        // Back as built (lights and materials are shared assets, so they must be put back).
        public void Reset()
        {
            Doors?.CloseAll();
            if (_lightMode != 0) { _lightMode = LightModes.Length - 1; Sounds = null; NextLightMode(); }
            foreach (Mover m in _slides)
            {
                m.Open = m.Target = 0f;
                for (int i = 0; i < m.Parts.Count; i++)
                    if (m.Parts[i] != null) m.Parts[i].localPosition = m.Rest[i];
            }
            foreach (Mover m in _curtains)
            {
                m.Open = m.Target = 0f;
                if (m.Pivot != null) m.Pivot.localScale = Vector3.one;
            }
        }
    }
}
