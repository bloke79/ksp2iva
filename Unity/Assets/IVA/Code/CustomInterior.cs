// Custom pod interiors shipped with the mod.
//
// Each interior is a prefab built from the Blender model by the "IVA > Set Up Interiors" editor
// button and packed into the mod as an addressable asset. At run time the mod loads it by address,
// places it inside the real pod (sized to the pod's measured shape), and puts the camera at one of
// its seat eye points. The game camera then draws the interior and the real world through its
// windows together.

using System;
using System.Collections.Generic;
using System.Linq;
using KSP.Game;
using KSP.Modules;
using KSP.Sim.impl;
using SpaceWarp2.API.Logging;
using UnityEngine;
using ILogger = SpaceWarp2.API.Logging.ILogger; // UnityEngine also defines ILogger

namespace IVA
{
    // An interior the mod ships with.
    public class InteriorDesign
    {
        public string Name;
        public string Address;
        public string[] Parts;     // part names this interior was designed for
        public int Seats;
        public float BaseRadius;   // outer pod radius at the base it was designed for (metres)
        public float Height;       // outer pod height it was designed for (metres)
        public float Yaw;          // turns the interior so its front lines up with the part's real front (degrees)
        public bool OnHull;        // built to the real hull: place at HullBaseY with no auto-fit scaling
        public float HullBaseY;    // part-local Y of the hull's base (from the extracted reference mesh)
        public bool UprightCrew;   // crew moved in from the portrait booth sit upright at the seat points (cabins, labs)
        public string[] HideRenderers;
        public string[] KeepRenderers;   // with HideExterior: part meshes that stay visible (seen through our windows)
        public bool HideExterior;  // hide the part's own outer meshes while inside (cabins: their recessed end hatches poke into the room)   // stock meshes of the part to hide while inside (they'd show through ours)
    }

    public static class InteriorCatalogue
    {
        public static readonly List<InteriorDesign> All = new List<InteriorDesign>
        {
            // The real Mk1-3's windows are symmetric about -Z, so the interior (front +Z) is turned 180 degrees.
            new InteriorDesign { Name = "Mk1-3", Address = "IVA/Interior_Mk1-3", Parts = new[] { "pod_2v_conical_crew" },
                                 Seats = 3, BaseRadius = 1.25f, Height = 1.95f, Yaw = 180f, OnHull = true, HullBaseY = -0.505f },
            // Built to the real hull (extracted reference: base radius 0.625 m, height 0.963 m); front at -Z like the Mk1-3.
            new InteriorDesign { Name = "Mk1", Address = "IVA/Interior_pod_1v_conical_crew", Parts = new[] { "pod_1v_conical_crew" },
                                 Seats = 1, BaseRadius = 0.625f, Height = 0.963f, Yaw = 180f, OnHull = true, HullBaseY = -0.363f },
            // Large 3v pod (hull base y -1.641, 1.91 m radius, 4.17 m tall). Its crew live in the portrait booth, so the
            // interior's own seat points are used and the crew are moved onto the couches while in IVA.
            new InteriorDesign { Name = "Mk3-5", Address = "IVA/Interior_pod_3v_conical_crew", Parts = new[] { "pod_3v_conical_crew" },
                                 Seats = 5, BaseRadius = 1.911f, Height = 4.169f, Yaw = 180f, OnHull = true, HullBaseY = -1.641f },
            // OSL-25 Starlab: an ISS-style rack room with our greenhouse in the ceiling; the floor opens onto the part's own
            // greenhouse pod (kept visible with its crops while inside).
            new InteriorDesign { Name = "Starlab", Address = "IVA/Interior_lab_2v_science_orbital", Parts = new[] { "lab_2v_science_orbital" },
                                 Seats = 3, BaseRadius = 1.48f, Height = 4.72f, Yaw = 180f, OnHull = true, HullBaseY = -2.352f,
                                 UprightCrew = true, HideExterior = true,
                                 KeepRenderers = new[] { "greenhouse", "plants" } },
            // PPD-10 Hitchhiker and PPD-20 Wayfarer crew cabins: rack rooms with a wardroom table (and a window lounge).
            new InteriorDesign { Name = "Hitchhiker", Address = "IVA/Interior_cabin_2v_crew_hitchhiker", Parts = new[] { "cabin_2v_crew_hitchhiker" },
                                 Seats = 4, BaseRadius = 1.38f, Height = 2.706f, Yaw = 180f, OnHull = true, HullBaseY = -1.353f, UprightCrew = true, HideExterior = true },
            new InteriorDesign { Name = "Wayfarer", Address = "IVA/Interior_cabin_3v_crew", Parts = new[] { "cabin_3v_crew" },
                                 Seats = 8, BaseRadius = 1.96f, Height = 5.0f, Yaw = 180f, OnHull = true, HullBaseY = -2.5f, UprightCrew = true, HideExterior = true },
            // Mk1 cockpit: shuttle-era flight deck built to the real hull (nose along the part's +Y, canopy up).
            new InteriorDesign { Name = "Mk1 Cockpit", Address = "IVA/Interior_cockpit_1v_m1_crew", Parts = new[] { "cockpit_1v_m1_crew" },
                                 Seats = 1, BaseRadius = 0.625f, Height = 2.1f, Yaw = 180f, OnHull = true, HullBaseY = -0.62f },
            // Mk3 cockpit: orbiter flight deck (four seats at the stock eye points) over a mid-deck reached by a floor hatch.
            new InteriorDesign { Name = "Mk3 Cockpit", Address = "IVA/Interior_cockpit_3v_m3_crew", Parts = new[] { "cockpit_3v_m3_crew" },
                                 Seats = 4, BaseRadius = 1.879f, Height = 4.48f, Yaw = 180f, OnHull = true, HullBaseY = -1.275f },
            // Lander cans: KSP1-style cramped cabins (seats at the panels, drawer banks, a ladder to the docking hatch).
            // No stock interiors, so the crew come from the portrait booth; the windows are painted on the hull, which
            // stays visible (one-sided: the openings in our shell show the world through it). You walk in them when landed.
            new InteriorDesign { Name = "Lander 1v", Address = "IVA/Interior_pod_1v_lander_crew", Parts = new[] { "pod_1v_lander_crew" },
                                 Seats = 1, BaseRadius = 0.89f, Height = 1.40f, Yaw = 180f, OnHull = true, HullBaseY = -0.701f, UprightCrew = true },
            new InteriorDesign { Name = "Lander 2v", Address = "IVA/Interior_pod_2v_lander_crew", Parts = new[] { "pod_2v_lander_crew" },
                                 Seats = 2, BaseRadius = 1.44f, Height = 1.40f, Yaw = 180f, OnHull = true, HullBaseY = -0.578f, UprightCrew = true },
            new InteriorDesign { Name = "Lander 3v", Address = "IVA/Interior_pod_3v_lander_crew", Parts = new[] { "pod_3v_lander_crew" },
                                 Seats = 4, BaseRadius = 2.05f, Height = 2.24f, Yaw = 180f, OnHull = true, HullBaseY = -1.119f, UprightCrew = true },
        };

        // The interior made for this part; otherwise, with anyPod, one with the same seat count (or the first).
        public static InteriorDesign ForPod(string partName, int seats, bool anyPod)
        {
            InteriorDesign exact = All.FirstOrDefault(d => d.Parts != null && d.Parts.Any(p => string.Equals(p, partName, StringComparison.OrdinalIgnoreCase)));
            if (exact != null || !anyPod) return exact;
            return All.FirstOrDefault(d => d.Seats == seats) ?? All.FirstOrDefault();
        }
    }

    public class PodInfo
    {
        public PartBehavior Pod;
        public int Seats;
        public string Name;
    }

    public static class PodLocator
    {
        public const string KerbalCameraName = "kerbalCam";
        public const string KerbalBodyBoneName = "bone_kerbal_master_parent";

        public static VesselBehavior ActiveVessel(GameInstance game)
        {
            try
            {
                var vc = game != null ? game.ViewController : null;
                if (vc == null) return null;
                VesselComponent v = vc.GetActiveSimVessel(true);
                return v != null ? vc.GetBehaviorIfLoaded(v) : null;
            }
            catch (Exception) { return null; }
        }

        // Picks the crew pod on the active vessel: the name filter if set, else 3-seat pods, else the biggest.
        // Every crewed part with an interior design, command pods first (then by seats), for cycling through with N.
        public static List<PodInfo> FindAll(GameInstance game, bool anyPod)
        {
            var list = new List<KeyValuePair<int, PodInfo>>();
            VesselBehavior vessel = ActiveVessel(game);
            if (vessel == null) return new List<PodInfo>();
            foreach (PartBehavior pb in vessel.parts)
            {
                if (pb == null) continue;
                var crewed = pb.GetComponentInChildren<Module_CrewedInterior>(true);
                if (crewed == null || crewed.IsProbe) continue;
                int seats = crewed.crew != null ? crewed.crew.Length : 0;
                string name = PartName(pb);
                if (InteriorCatalogue.ForPod(name, seats, anyPod) == null) continue;
                bool command = pb.GetComponentInChildren<Module_Command>(true) != null;
                list.Add(new KeyValuePair<int, PodInfo>((command ? 100000 : 0) + seats, new PodInfo { Pod = pb, Seats = seats, Name = name }));
            }
            return list.OrderByDescending(kv => kv.Key).Select(kv => kv.Value).ToList();
        }

        public static PodInfo FindPod(GameInstance game, string nameFilter, ILogger log)
        {
            VesselBehavior vessel = ActiveVessel(game);
            if (vessel == null) { log.LogInfo("IVA: no loaded active vessel."); return null; }

            PodInfo best = null;
            int bestScore = int.MinValue;
            var found = new List<string>();
            foreach (PartBehavior pb in vessel.parts)
            {
                if (pb == null) continue;
                var crewed = pb.GetComponentInChildren<Module_CrewedInterior>(true);
                if (crewed == null || crewed.IsProbe) continue;

                int seats = crewed.crew != null ? crewed.crew.Length : 0;
                string name = PartName(pb);
                found.Add($"{name} (seats {seats})");

                int score;
                if (!string.IsNullOrEmpty(nameFilter))
                {
                    if (name.IndexOf(nameFilter, StringComparison.OrdinalIgnoreCase) < 0) continue;
                    score = 10000;
                }
                else score = (pb.GetComponentInChildren<Module_Command>(true) != null ? 100000 : 0) + (seats == 3 ? 1000 : 0) + seats;   // the command pod first

                if (score > bestScore)
                {
                    bestScore = score;
                    best = new PodInfo { Pod = pb, Seats = seats, Name = name };
                }
            }

            log.LogInfo(found.Count == 0 ? "IVA: no crewed pods on the active vessel."
                                         : "IVA: crewed parts on vessel: " + string.Join("; ", found));
            if (best == null && !string.IsNullOrEmpty(nameFilter))
                log.LogWarning($"IVA: no crewed part matches the pod name filter '{nameFilter}'.");
            return best;
        }

        public static string PartName(PartBehavior pb)
        {
            try { return !string.IsNullOrEmpty(pb.Name) ? pb.Name : pb.name; }
            catch (Exception) { return pb.name; }
        }

        public static string HierarchyPath(Transform t, Transform root)
        {
            var parts = new List<string>();
            while (t != null && t != root)
            {
                parts.Add(t.name + "#" + t.GetSiblingIndex());
                t = t.parent;
            }
            parts.Reverse();
            return string.Join("/", parts);
        }

        public static Transform FindChildRecursive(Transform parent, string name)
        {
            for (int i = 0; i < parent.childCount; i++)
            {
                Transform child = parent.GetChild(i);
                if (child.name == name) return child;
                Transform found = FindChildRecursive(child, name);
                if (found != null) return found;
            }
            return null;
        }
    }

    // Placement settings read from config each time IVA starts.
    public class PlacementSettings
    {
        public bool FitToPod = true;
        public Vector3 Offset;           // metres, in pod space
        public float Yaw;                // degrees round the pod axis
        public float ExtraScale = 1f;    // multiplies the fitted scale
    }

    // The pod's measured size in its own local space.
    public struct PodMeasure
    {
        public bool Valid;
        public Vector3 AxisCentre;  // x/z centre of the pod, at y = 0
        public float YMin, YMax;
        public float BaseRadius;
        public string Source;
    }

    // One IVA visit inside a custom interior. Created on entry, ended on exit.
    public class CustomInteriorSession
    {
        public PartBehavior Pod { get; private set; }
        public InteriorDesign Design { get; private set; }
        public readonly List<Transform> Seats = new List<Transform>();
        // The game's own seated kerbals and their "IVA EyeTransform" points. When present, the camera goes there
        // (the game draws these kerbals in the pod, so any other eye point ends up inside one of them).
        public readonly List<Transform> Eyes = new List<Transform>();
        public readonly List<Kerbal3DModel> EyeKerbals = new List<Kerbal3DModel>();
        private readonly List<Renderer> _hiddenBody = new List<Renderer>();
        public int SeatCount => Eyes.Count > 0 ? Eyes.Count : Seats.Count;
        public bool UsesGameEyes => Eyes.Count > 0;
        public PodMeasure Measure { get; private set; }
        // Window views (IVA_View_<name> camera point, IVA_ViewAt_<name> aim point), in the order the model lists them.
        public readonly List<KeyValuePair<Transform, Transform>> Views = new List<KeyValuePair<Transform, Transform>>();
        public readonly List<string> ViewNames = new List<string>();
        public Transform PodTransform => Pod != null ? Pod.transform : null;
        public LiveInstruments Live { get; private set; }
        public void DisableLive() => Live = null;

        private GameObject _instance;
        public Transform Root => _instance != null ? _instance.transform : null;

        // Hide the whole body of a seat's kerbal: its player has unbuckled and is floating round the cabin.
        public void HideWholeKerbal(int seat)
        {
            foreach (Renderer r in _hiddenBody) if (r != null) r.enabled = true;
            _hiddenBody.Clear();
            if (seat < 0 || seat >= EyeKerbals.Count || EyeKerbals[seat] == null) return;
            foreach (Renderer r in EyeKerbals[seat].GetComponentsInChildren<Renderer>(false))
                if (r.enabled) { _hiddenBody.Add(r); r.enabled = false; }
        }
        private Vector3 _fitScale = Vector3.one;
        private readonly List<Renderer> _hiddenExterior = new List<Renderer>();
        private readonly List<Renderer> _hiddenStockCabin = new List<Renderer>();
        private bool _dumpPoses = true;
        private CustomInteriorSession() { }

        public bool IsValid => Pod != null && _instance != null && SeatCount > 0;

        public static CustomInteriorSession Create(PodInfo pod, InteriorDesign design, GameObject prefab,
            PlacementSettings place, ILogger log, bool dumpPoses = true)
        {
            var s = new CustomInteriorSession { Pod = pod.Pod, Design = design };
            s._dumpPoses = dumpPoses;
            s.Measure = MeasurePod(pod.Pod);   // before adding anything to the pod

            // Instantiate inactive, set it up, then show it.
            var holder = new GameObject("IVA_Interior_" + design.Name);
            holder.SetActive(false);
            holder.transform.SetParent(pod.Pod.transform, false);
            GameObject inst = UnityEngine.Object.Instantiate(prefab, holder.transform, false);
            inst.name = design.Name;

            // Draw on the same layer as the pod so the flight camera renders it with the pod.
            int layer = pod.Pod.gameObject.layer;
            var podRenderer = pod.Pod.GetComponentsInChildren<Renderer>(false).FirstOrDefault(r => r.GetComponentInParent<PartBehavior>() == pod.Pod);
            if (podRenderer != null) layer = podRenderer.gameObject.layer;
            SetLayerRecursive(holder.transform, layer);

            // No physics: strip any colliders that came with the model.
            foreach (Collider c in inst.GetComponentsInChildren<Collider>(true)) UnityEngine.Object.DestroyImmediate(c);

            foreach (Transform t in inst.GetComponentsInChildren<Transform>(true)
                         .Where(t => t.name.StartsWith("IVA_Seat", StringComparison.Ordinal))
                         .OrderBy(t => t.name, StringComparer.Ordinal))
                s.Seats.Add(t);

            var all = inst.GetComponentsInChildren<Transform>(true);
            foreach (Transform v in all.Where(t => t.name.StartsWith("IVA_View_", StringComparison.Ordinal)).OrderBy(t => t.name, StringComparer.Ordinal))
            {
                string n = v.name.Substring("IVA_View_".Length);
                Transform at = all.FirstOrDefault(t => t.name == "IVA_ViewAt_" + n);
                if (at == null) continue;
                s.Views.Add(new KeyValuePair<Transform, Transform>(v, at));
                s.ViewNames.Add(n);
            }

            s.Live = LiveInstruments.Find(inst, log);
            CorrectOrientation(inst, s.Seats, log);
            s.FindGameEyes(log);
            s.HideStockCabin(log);
            s.MoveCrewIntoSeats(log);

            s._instance = holder;
            s.ComputeFit(place);
            s.ApplyPlacement(place);

            holder.SetActive(true);

            log.LogInfo($"IVA: placed the {design.Name} interior in {pod.Name}. Pod measured from {s.Measure.Source}: " +
                        $"base radius {s.Measure.BaseRadius:F2} m, height {s.Measure.YMax - s.Measure.YMin:F2} m " +
                        $"(from {s.Measure.YMin:F2} to {s.Measure.YMax:F2}). Fit scale ({s._fitScale.x:F2}, {s._fitScale.y:F2}). " +
                        $"{s.Seats.Count} seat(s), {s.Views.Count} window view(s){(s.Views.Count > 0 ? " (" + string.Join(", ", s.ViewNames) + ")" : "")}.");
            LogPodWindows(pod.Pod, s.Measure, log);
            return s;
        }

        // The seat eye points sit about a metre above the cabin floor. If the model was imported tipped
        // over (a common Blender-to-Unity axis mix-up), they'll be off to one side instead; rotate the
        // model so they're up again.
        private static void CorrectOrientation(GameObject inst, List<Transform> seats, ILogger log)
        {
            if (seats.Count == 0) return;
            Vector3 mean = Vector3.zero;
            foreach (Transform t in seats) mean += inst.transform.InverseTransformPoint(t.position);
            mean /= seats.Count;
            Vector3 up = Vector3.up;
            float ax = Mathf.Abs(mean.x), ay = Mathf.Abs(mean.y), az = Mathf.Abs(mean.z);
            if (ay >= ax && ay >= az) up = mean.y >= 0 ? Vector3.up : Vector3.down;
            else if (az >= ax) up = mean.z >= 0 ? Vector3.forward : Vector3.back;
            else up = mean.x >= 0 ? Vector3.right : Vector3.left;
            if (up == Vector3.up) return;
            inst.transform.localRotation = Quaternion.FromToRotation(up, Vector3.up);
            log.LogWarning($"IVA: the interior model came in tipped over (seats along {up}); rotated it upright.");
        }

        private static void SetLayerRecursive(Transform t, int layer)
        {
            t.gameObject.layer = layer;
            for (int i = 0; i < t.childCount; i++) SetLayerRecursive(t.GetChild(i), layer);
        }

        // Effect and helper meshes that aren't part of the hull (re-entry glow, RCS plumes, lower LODs).
        private static readonly string[] NonHullNames = { "reentry", "vfx", "exh", "lod_1", "lod_2", "lod_3", "IVA_" };

        private static bool IsHullRenderer(Renderer r)
        {
            if (r is ParticleSystemRenderer || r is TrailRenderer || r is LineRenderer) return false;
            for (Transform t = r.transform; t != null; t = t.parent)
            {
                string n = t.name;
                if (NonHullNames.Any(x => n.IndexOf(x, StringComparison.OrdinalIgnoreCase) >= 0)) return false;
                if (t.GetComponent<PartBehavior>() != null) break;
            }
            return true;
        }

        // Measures the pod's hull in its own local space: from its mesh colliders (the hull collision shape),
        // else its hull meshes. Box colliders are skipped: pods carry audio volumes and ladder/airlock boxes
        // that reach well outside the hull (the Mk1-3's audio box made it measure 2.61 m tall instead of 1.81 m).
        public static PodMeasure MeasurePod(PartBehavior pod)
        {
            var m = new PodMeasure();
            Transform pt = pod.transform;
            var bounds = new List<Bounds>();
            foreach (MeshCollider c in pod.GetComponentsInChildren<MeshCollider>(false))
                if (c != null && c.enabled && !c.isTrigger && c.GetComponentInParent<PartBehavior>() == pod) bounds.Add(c.bounds);
            m.Source = "mesh colliders";
            if (bounds.Count == 0)
            {
                foreach (Renderer r in pod.GetComponentsInChildren<Renderer>(false))
                    if (r != null && r.GetComponentInParent<PartBehavior>() == pod && IsHullRenderer(r)) bounds.Add(r.bounds);
                m.Source = "hull meshes";
            }
            if (bounds.Count == 0) { m.Source = "nothing"; return m; }

            bool any = false;
            Vector3 min = Vector3.zero, max = Vector3.zero;
            foreach (Bounds b in bounds)
            {
                for (int i = 0; i < 8; i++)
                {
                    var corner = new Vector3((i & 1) == 0 ? b.min.x : b.max.x, (i & 2) == 0 ? b.min.y : b.max.y, (i & 4) == 0 ? b.min.z : b.max.z);
                    Vector3 p = pt.InverseTransformPoint(corner);
                    if (!any) { min = p; max = p; any = true; }
                    else { min = Vector3.Min(min, p); max = Vector3.Max(max, p); }
                }
            }
            m.Valid = true;
            m.AxisCentre = new Vector3((min.x + max.x) * 0.5f, 0f, (min.z + max.z) * 0.5f);
            m.YMin = min.y;
            m.YMax = max.y;
            m.BaseRadius = Mathf.Max(max.x - min.x, max.z - min.z) * 0.5f;
            return m;
        }

        private void ComputeFit(PlacementSettings place)
        {
            _fitScale = Vector3.one;
            if (!place.FitToPod || !Measure.Valid) return;
            float sxz = Mathf.Clamp(Measure.BaseRadius / Design.BaseRadius, 0.6f, 1.6f);
            float sy = Mathf.Clamp((Measure.YMax - Measure.YMin) / Design.Height, 0.6f, 1.6f);
            // Keep the proportions unless the pod is clearly a different shape.
            if (Mathf.Abs(sy / sxz - 1f) < 0.08f) sy = sxz;
            _fitScale = new Vector3(sxz, sy, sxz);
        }

        // Called every frame so the alignment keys take effect immediately.
        public void ApplyPlacement(PlacementSettings place)
        {
            if (_instance == null) return;
            Transform t = _instance.transform;
            Vector3 basePos;
            if (Design.OnHull) basePos = new Vector3(0f, Design.HullBaseY, 0f);    // built to the real hull: exact
            else basePos = Measure.Valid && place.FitToPod ? Measure.AxisCentre + new Vector3(0f, Measure.YMin, 0f) : Vector3.zero;
            t.localPosition = basePos + place.Offset;
            t.localRotation = Quaternion.Euler(0f, Design.Yaw + place.Yaw, 0f);
            t.localScale = (Design.OnHull ? Vector3.one : _fitScale) * Mathf.Clamp(place.ExtraScale, 0.5f, 2f);
        }

        // Logs where the pod's own window meshes are, to help line the interior up.
        private static void LogPodWindows(PartBehavior pod, PodMeasure m, ILogger log)
        {
            var found = new List<string>();
            foreach (Renderer r in pod.GetComponentsInChildren<Renderer>(false))
            {
                if (r == null || r.GetComponentInParent<PartBehavior>() != pod) continue;
                string label = r.gameObject.name.ToLowerInvariant();
                try { label += " " + string.Join(" ", r.sharedMaterials.Where(x => x != null).Select(x => x.name.ToLowerInvariant())); }
                catch (Exception) { }
                if (!(label.Contains("window") || label.Contains("glass"))) continue;
                Vector3 c = pod.transform.InverseTransformPoint(r.bounds.center) - m.AxisCentre;
                float angle = Mathf.Atan2(c.x, c.z) * Mathf.Rad2Deg;
                found.Add($"{r.gameObject.name} at {angle:F0} deg, height {c.y:F2}");
            }
            if (found.Count > 0) log.LogInfo("IVA: the pod's own window meshes: " + string.Join("; ", found) +
                                              ". The interior's front windows face 0 deg; set Alignment > Yaw to the pod's forward window angle if they differ.");
        }

        public void HidePodExterior()
        {
            foreach (Renderer r in Pod.GetComponentsInChildren<Renderer>(false))
            {
                if (r == null || !r.enabled || r.GetComponentInParent<PartBehavior>() != Pod) continue;
                if (_instance != null && r.transform.IsChildOf(_instance.transform)) continue;
                if (r.GetComponentInParent<KSP.Game.Kerbal3DModel>() != null) continue;   // the crew stay visible
                if (Design != null && Design.KeepRenderers != null &&
                    Design.KeepRenderers.Any(n => r.name.IndexOf(n, StringComparison.OrdinalIgnoreCase) >= 0)) continue;
                r.enabled = false;
                _hiddenExterior.Add(r);
            }
        }

        // Positions the flight camera at a seat.
        // Finds the game's seated kerbals in this pod and their IVA eye points, and logs where they are.
        // For pods without an interior yet: log the seated kerbals and write the pose capture (IVA-pose/<part>.obj), so a
        // bespoke interior can be designed round them. Nothing is placed or changed.
        public static void CapturePoses(PodInfo pod, ILogger log)
        {
            try
            {
                var s = new CustomInteriorSession { Pod = pod.Pod };
                log.LogInfo($"IVA: capturing poses in {pod.Name}.");
                s.FindGameEyes(log);
                var stock = new HashSet<string>();
                foreach (Kerbal3DModel k in s.EyeKerbals)
                    for (Transform t = k != null ? k.transform.parent : null; t != null && t != pod.Pod.transform; t = t.parent)
                        if (t.name.StartsWith("interior_", StringComparison.OrdinalIgnoreCase)) stock.Add(t.name);
                log.LogInfo($"IVA: {pod.Name} uses the stock interior {string.Join(", ", stock)}.");
            }
            catch (Exception e) { log.LogWarning("IVA: pose capture failed: " + e.Message); }
        }

        private void FindGameEyes(ILogger log)
        {
            Module_CrewedInterior crewed = Pod.GetComponentInChildren<Module_CrewedInterior>(true);
            if (crewed == null || crewed.crew == null) { log.LogInfo("IVA: no crew list on the pod; using the interior's seat points."); return; }
            for (int i = 0; i < crewed.crew.Length; i++)
            {
                Kerbal3DModel k = crewed.crew[i];
                if (k == null || k.ThisKerbalInfo == null) continue;
                Transform eye = PodLocator.FindChildRecursive(k.transform, "IVA EyeTransform");
                Vector3 kp = Pod.transform.InverseTransformPoint(k.transform.position);
                string where = eye != null ? $"eye at {Pod.transform.InverseTransformPoint(eye.position):F3}" : "no IVA EyeTransform";
                log.LogInfo($"IVA: seat {i}: kerbal {k.name} at {kp:F3} (pod space), layer {k.gameObject.layer}, active {k.gameObject.activeInHierarchy}, {where}.");
                if (eye == null || Vector3.Distance(eye.position, Pod.transform.position) > 5f) continue;   // not in the pod (e.g. a separate internal space)
                // Only kerbals the flight camera draws (Local.Characters). Pods without a stock cabin (e.g. the 3v) keep their
                // crew in the portrait booth on another layer, beside the pod; those aren't seats in our cabin.
                if (k.gameObject.layer != 17) continue;
                Eyes.Add(eye);
                EyeKerbals.Add(k);
            }
            log.LogInfo(Eyes.Count > 0 ? $"IVA: using the game's eye points for {Eyes.Count} seated kerbal(s)."
                                       : "IVA: no usable game eye points; using the interior's seat points.");
            if (_dumpPoses) DumpPoses(log);
        }

        // Development aid: writes the seated kerbals' posed meshes (pod space, Unity axes) to an OBJ once per pod type,
        // so interiors can be modelled around the real poses. Output: <persistentDataPath>/IVA-pose/<pod>.obj.
        private void DumpPoses(ILogger log)
        {
            try
            {
                string dir = System.IO.Path.Combine(Application.persistentDataPath, "IVA-pose");
                string part = Pod.name.Replace("(Clone)", "").Trim();
                int cut = part.IndexOf(".prefab", StringComparison.Ordinal);   // instance names carry ".prefab_<guid>"
                if (cut > 0) part = part.Substring(0, cut);
                string file = System.IO.Path.Combine(dir, part + ".obj");
                if (System.IO.File.Exists(file) || EyeKerbals.Count == 0) return;
                System.IO.Directory.CreateDirectory(dir);
                var sb = new System.Text.StringBuilder();
                var ci = System.Globalization.CultureInfo.InvariantCulture;
                int vbase = 1, parts = 0;
                Transform pod = Pod.transform;
                for (int s = 0; s < EyeKerbals.Count; s++)
                {
                    Vector3 e = pod.InverseTransformPoint(Eyes[s].position);
                    sb.AppendLine(string.Format(ci, "# seat {0} eye {1:F4} {2:F4} {3:F4} fwd {4:F3} {5:F3} {6:F3}", s, e.x, e.y, e.z,
                        pod.InverseTransformDirection(Eyes[s].forward).x, pod.InverseTransformDirection(Eyes[s].forward).y, pod.InverseTransformDirection(Eyes[s].forward).z));
                    foreach (Renderer r in EyeKerbals[s].GetComponentsInChildren<Renderer>(true))
                    {
                        Mesh mesh = null;
                        Matrix4x4 m;
                        if (r is SkinnedMeshRenderer smr)
                        {
                            mesh = new Mesh();
                            smr.BakeMesh(mesh, true);
                            m = Matrix4x4.TRS(r.transform.position, r.transform.rotation, Vector3.one);
                        }
                        else
                        {
                            MeshFilter mf = r.GetComponent<MeshFilter>();
                            if (mf == null || mf.sharedMesh == null || !mf.sharedMesh.isReadable) continue;
                            mesh = mf.sharedMesh;
                            m = r.transform.localToWorldMatrix;
                        }
                        Vector3[] v = mesh.vertices;
                        int[] t = mesh.triangles;
                        if (v.Length == 0) continue;
                        sb.AppendLine($"g seat{s}_{r.name.Replace(' ', '_')}");
                        foreach (Vector3 p in v)
                        {
                            Vector3 q = pod.InverseTransformPoint(m.MultiplyPoint3x4(p));
                            sb.AppendLine(string.Format(ci, "v {0:F4} {1:F4} {2:F4}", q.x, q.y, q.z));
                        }
                        for (int i = 0; i + 2 < t.Length; i += 3)
                            sb.AppendLine($"f {t[i] + vbase} {t[i + 1] + vbase} {t[i + 2] + vbase}");
                        vbase += v.Length;
                        parts++;
                    }
                }
                System.IO.File.WriteAllText(file, sb.ToString());
                log.LogInfo($"IVA: wrote the seated kerbal poses ({parts} meshes) to {file}.");
            }
            catch (Exception ex)
            {
                log.LogWarning($"IVA: couldn't write the kerbal poses: {ex.Message}");
            }
        }

        // Kerbals are assembled from separate head/hair/helmet/hat/face-decoration parts and a body. Only those
        // head parts are hidden for the kerbal you're looking out of, so you still see your own body and hands.
        private static readonly string[] HeadParts = { "head", "hair", "helm", "hat_", "deco_face", "glasses", "eye", "brow", "lash", "teeth", "tongue" };

        private static bool IsHeadPart(Renderer r, Transform kerbalRoot)
        {
            for (Transform t = r.transform; t != null && t != kerbalRoot; t = t.parent)
            {
                string n = t.name.ToLowerInvariant();
                if (n.Contains("body")) return false;
                if (HeadParts.Any(h => n.Contains(h))) return true;
            }
            return false;
        }

        // Hides the head of the kerbal you're looking out of (so you don't see the inside of it) and shows everyone else.
        // ---- crew kept in the portrait booth (pods with no stock cabin, e.g. the 3v): sit them in our couches ----
        // Offset from the eye point to the kerbal's root, and its rotation, as in the stock Mk1-3 interior (pod space).
        private static readonly Vector3 KerbalFromEye = new Vector3(0f, -0.149f, 0.518f);
        private static readonly Quaternion KerbalRotation = Quaternion.LookRotation(Vector3.up, Vector3.back);

        private class MovedKerbal
        {
            public Kerbal3DModel Kerbal;
            public Transform T;
            public Vector3 LocalPos;
            public Quaternion LocalRot;
            public int Seat;
            public readonly List<KeyValuePair<GameObject, int>> Layers = new List<KeyValuePair<GameObject, int>>();
            public readonly List<Renderer> Hidden = new List<Renderer>();
        }

        private readonly List<MovedKerbal> _moved = new List<MovedKerbal>();
        public bool MovesCrew => _moved.Count > 0;

        private void MoveCrewIntoSeats(ILogger log)
        {
            if (Eyes.Count > 0 || Seats.Count == 0) return;      // the game already seats its crew in this pod
            Module_CrewedInterior crewed = Pod.GetComponentInChildren<Module_CrewedInterior>(true);
            if (crewed == null || crewed.crew == null) return;
            EyeKerbals.Clear();
            for (int i = 0; i < Seats.Count; i++) EyeKerbals.Add(null);
            int seat = 0;
            foreach (Kerbal3DModel k in crewed.crew)
            {
                if (k == null || k.ThisKerbalInfo == null) continue;
                if (seat >= Seats.Count) break;
                var m = new MovedKerbal { Kerbal = k, T = k.transform, LocalPos = k.transform.localPosition, LocalRot = k.transform.localRotation, Seat = seat };
                foreach (Transform t in k.GetComponentsInChildren<Transform>(true))
                {
                    m.Layers.Add(new KeyValuePair<GameObject, int>(t.gameObject, t.gameObject.layer));
                    t.gameObject.layer = 17;    // Local.Characters: drawn by the flight camera
                }
                foreach (Renderer r in k.GetComponentsInChildren<Renderer>(true))
                    if (r.enabled && r.name.IndexOf("Backdrop", StringComparison.OrdinalIgnoreCase) >= 0) { r.enabled = false; m.Hidden.Add(r); }
                _moved.Add(m);
                EyeKerbals[seat] = k;
                seat++;
            }
            UpdateMovedCrew();
            if (_moved.Count > 0)
                log.LogInfo($"IVA: sat {_moved.Count} kerbal(s) from the portrait booth in the couches: " + string.Join(", ", _moved.Select(m => m.Kerbal.name)));
        }

        // Called every frame while in IVA (the booth may reposition them).
        public void UpdateMovedCrew()
        {
            if (_moved.Count == 0 || Pod == null) return;
            Transform pod = Pod.transform;
            foreach (MovedKerbal m in _moved)
            {
                if (m.T == null || m.Seat >= Seats.Count || Seats[m.Seat] == null) continue;
                Transform s = Seats[m.Seat];
                if (Design != null && Design.UprightCrew)
                {
                    // the booth's seated pose has the eye 0.518 m up and 0.149 m forward of the kerbal's root
                    Vector3 f = s.forward, u = s.up;
                    m.T.SetPositionAndRotation(s.position - u * 0.518f - f * 0.149f, Quaternion.LookRotation(f, u));
                    continue;
                }
                Vector3 eye = pod.InverseTransformPoint(s.position);
                m.T.SetPositionAndRotation(pod.TransformPoint(eye + KerbalFromEye), pod.rotation * KerbalRotation);
            }
        }

        private void RestoreMovedCrew()
        {
            foreach (MovedKerbal m in _moved)
            {
                if (m.T != null) { m.T.localPosition = m.LocalPos; m.T.localRotation = m.LocalRot; }
                foreach (var kv in m.Layers) if (kv.Key != null) kv.Key.layer = kv.Value;
                foreach (Renderer r in m.Hidden) if (r != null) r.enabled = true;
            }
            _moved.Clear();
        }

        public void ShowSeat(int seat, bool hideOwnHead, ILogger log = null)
        {
            foreach (Renderer r in _hiddenBody) if (r != null) r.enabled = true;
            _hiddenBody.Clear();
            if (!hideOwnHead || seat < 0 || seat >= EyeKerbals.Count || EyeKerbals[seat] == null) return;
            Transform root = EyeKerbals[seat].transform;
            Renderer[] all = root.GetComponentsInChildren<Renderer>(false);
            foreach (Renderer r in all)
                if (r.enabled && IsHeadPart(r, root)) _hiddenBody.Add(r);
            if (_hiddenBody.Count == 0 && seat < Eyes.Count && Eyes[seat] != null)
            {
                // fallback: anything centred close to the eye
                foreach (Renderer r in all)
                    if (r.enabled && Vector3.Distance(r.bounds.center, Eyes[seat].position) < 0.18f) _hiddenBody.Add(r);
            }
            foreach (Renderer r in _hiddenBody) r.enabled = false;
            if (log != null)
                log.LogInfo($"IVA: hid {_hiddenBody.Count} of {all.Length} renderers for seat {seat + 1}: " +
                            string.Join(", ", _hiddenBody.Select(r => r.name)) + ". All: " + string.Join(", ", all.Select(r => r.name)));
        }

        // Camera pose in pod space: a seat's eye (view < 0) or a window view, before the player's look rotation.
        public bool TryGetPose(int seat, int view, Vector3 eyeOffset, out Vector3 pos, out Quaternion rot)
        {
            pos = Vector3.zero;
            rot = Quaternion.identity;
            Transform pod = PodTransform;
            if (pod == null) return false;
            Quaternion toPod = Quaternion.Inverse(pod.rotation);
            if (view >= 0 && view < Views.Count && Views[view].Key != null && Views[view].Value != null)
            {
                Vector3 p = pod.InverseTransformPoint(Views[view].Key.position);
                Vector3 dir = pod.InverseTransformPoint(Views[view].Value.position) - p;
                if (dir.sqrMagnitude < 1e-6f) return false;
                pos = p;
                // level with the pod's nose as "up", unless the window looks almost straight along it
                Vector3 up = Mathf.Abs(Vector3.Dot(dir.normalized, Vector3.up)) > 0.95f ? Vector3.back : Vector3.up;
                rot = Quaternion.LookRotation(dir, up);
                return true;
            }
            Transform e = UsesGameEyes ? (seat >= 0 && seat < Eyes.Count ? Eyes[seat] : null)
                                       : (seat >= 0 && seat < Seats.Count ? Seats[seat] : null);
            if (e == null) return false;
            pos = pod.InverseTransformPoint(e.TransformPoint(eyeOffset));
            rot = toPod * e.rotation;
            return true;
        }

        // Index of the window view nearest a pod-space point (or -1).
        public int NearestView(Vector3 podPoint)
        {
            int best = -1;
            float bestD = float.MaxValue;
            for (int i = 0; i < Views.Count; i++)
            {
                if (Views[i].Key == null) continue;
                float d = (PodTransform.InverseTransformPoint(Views[i].Key.position) - podPoint).sqrMagnitude;
                if (d < bestD) { bestD = d; best = i; }
            }
            return best;
        }

        // The game draws its own cabin model round the seated kerbals in flight (it's what you see through the windows from
        // outside). Inside our interior it overlaps ours: extra window frames, its consoles and seats. Hide everything in that
        // stock interior except the kerbals themselves while ours is showing; End() puts it back.
        private void HideStockCabin(ILogger log)
        {
            var roots = new HashSet<Transform>();
            foreach (Kerbal3DModel k in EyeKerbals)
            {
                if (k == null) continue;
                Transform root = null;
                for (Transform t = k.transform.parent; t != null && t != Pod.transform; t = t.parent)
                    if (t.name.StartsWith("interior_", StringComparison.OrdinalIgnoreCase)) root = t;   // topmost one
                if (root != null) roots.Add(root);
            }
            foreach (Transform root in roots)
                foreach (Renderer r in root.GetComponentsInChildren<Renderer>(false))
                    if (r.enabled && r.GetComponentInParent<Kerbal3DModel>() == null)
                    {
                        r.enabled = false;
                        _hiddenStockCabin.Add(r);
                    }
            if (Design != null && Design.HideRenderers != null)
                foreach (Renderer r in Pod.GetComponentsInChildren<Renderer>(false))
                    if (r.enabled && (_instance == null || !r.transform.IsChildOf(_instance.transform)) &&
                        Design.HideRenderers.Any(n => r.name.IndexOf(n, StringComparison.OrdinalIgnoreCase) >= 0))
                    {
                        r.enabled = false;
                        _hiddenStockCabin.Add(r);
                    }
            log.LogInfo(roots.Count == 0 ? "IVA: no stock cabin found round the kerbals."
                : $"IVA: hid the stock cabin ({string.Join(", ", roots.Select(r => r.name))}): {_hiddenStockCabin.Count} renderers: " +
                  string.Join(", ", _hiddenStockCabin.Select(r => r.name)));
        }

        public void End()
        {
            RestoreMovedCrew();
            foreach (Renderer r in _hiddenStockCabin) if (r != null) r.enabled = true;
            _hiddenStockCabin.Clear();
            ShowSeat(-1, false);
            Eyes.Clear();
            EyeKerbals.Clear();
            Views.Clear();
            ViewNames.Clear();
            foreach (Renderer r in _hiddenExterior) if (r != null) r.enabled = true;
            _hiddenExterior.Clear();
            if (_instance != null) UnityEngine.Object.Destroy(_instance);
            _instance = null;
            Seats.Clear();
        }
    }
}
