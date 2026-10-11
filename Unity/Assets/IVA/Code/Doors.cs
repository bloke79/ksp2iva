// Hinged parts in the interiors that open and close: hygiene doors, lockers, the food warmer, freezers.
//
// The interior carries each leaf as a separate moving part ("...__Live_Door<name>", pivot on the hinge line; a leaf with
// parts of other materials, like a pull, is a group "...__Live_Door<name>__p<k>" sharing that pivot) plus position-only
// markers: IVA_LiveAxis_Door<name> (a point up the hinge line), IVA_LiveEdge_Door<name> (the free edge when closed) and
// IVA_LiveOut_Door<name> (the side it opens towards). Using marker positions keeps this independent of how Blender's
// axes were converted on import (as for the instruments). See art/act.py.

using System;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;
using ILogger = ReduxLib.Logging.ILogger;

namespace IVA
{
    public class Doors
    {
        public const float OpenAngle = 100f;
        public const float SwingSeconds = 0.5f;

        public class Part
        {
            public Transform T;
            public Quaternion RestLocal;
            public Vector3 AxisLocal;    // hinge axis in the part's parent space
        }

        public class Door
        {
            public string Name;
            public readonly List<Part> Parts = new List<Part>();
            public float Sign;           // rotation sense that swings the free edge towards the open side
            public float Open, Target;   // 0 closed .. 1 open
            public Vector3 HingePod, AxisPod, EdgePod, OutPod;   // pod space: pivot, a unit step up the hinge, pivot to free edge, open side
            public float HalfHeight;     // from the axis marker's distance up the hinge (the hygiene doors put it at half height)
            public Vector3 CentrePod => HingePod + EdgePod * 0.5f;
            public bool IsRoomDoor => EdgePod.magnitude > 0.35f;   // big enough to block you (hygiene doors, not lockers)
        }

        public readonly List<Door> All = new List<Door>();

        // "...__Live_Door<name>__p1 (Clone)" -> "Door<name>"
        public static string LiveKey(string objectName, string kind, out bool isMain)
        {
            isMain = false;
            int k = objectName.IndexOf("__Live_" + kind, StringComparison.Ordinal);
            if (k < 0) return null;
            string name = objectName.Substring(k + "__Live_".Length);
            int dot = name.IndexOf(" (", StringComparison.Ordinal);
            if (dot > 0) name = name.Substring(0, dot);
            int p = name.IndexOf("__p", StringComparison.Ordinal);
            isMain = p < 0;
            return p < 0 ? name : name.Substring(0, p);
        }

        public static Dictionary<string, Transform> Markers(Transform[] all, string prefix)
        {
            var byName = new Dictionary<string, Transform>(StringComparer.Ordinal);
            foreach (Transform t in all)
                if (t.name.StartsWith(prefix, StringComparison.Ordinal) && !byName.ContainsKey(t.name)) byName[t.name] = t;
            return byName;
        }

        public static Doors Find(GameObject interior, Transform pod, ILogger log)
        {
            var d = new Doors();
            Transform[] all = interior.GetComponentsInChildren<Transform>(true);
            Dictionary<string, Transform> byName = Markers(all, "IVA_Live");
            var groups = new Dictionary<string, List<Transform>>(StringComparer.Ordinal);
            foreach (Transform t in all)
            {
                string key = LiveKey(t.name, "Door", out bool main);
                if (key == null || t.parent == null) continue;
                if (!groups.TryGetValue(key, out var list)) groups[key] = list = new List<Transform>();
                if (main) list.Insert(0, t); else list.Add(t);
            }
            foreach (var kv in groups)
            {
                string name = kv.Key;
                Transform t = kv.Value[0];
                if (!byName.TryGetValue("IVA_LiveAxis_" + name, out Transform axisM) || !byName.TryGetValue("IVA_LiveEdge_" + name, out Transform edgeM) ||
                    !byName.TryGetValue("IVA_LiveOut_" + name, out Transform outM))
                {
                    log?.LogWarning($"IVA: door {name} is missing its markers; it won't open.");
                    continue;
                }
                Vector3 axisRaw = axisM.position - t.position;
                Vector3 axisW = axisRaw.normalized, edgeW = edgeM.position - t.position, outW = outM.position - t.position;
                Vector3 swung = Quaternion.AngleAxis(30f, axisW) * edgeW;
                var door = new Door
                {
                    Name = name,
                    Sign = Vector3.Dot(swung - edgeW, outW) >= 0f ? 1f : -1f,
                    HingePod = pod.InverseTransformPoint(t.position),
                    AxisPod = pod.InverseTransformDirection(axisW),
                    EdgePod = pod.InverseTransformDirection(edgeW),
                    OutPod = pod.InverseTransformDirection(outW).normalized,
                    HalfHeight = pod.InverseTransformVector(axisRaw).magnitude,
                };
                foreach (Transform p in kv.Value)
                    if (p.parent != null)
                        door.Parts.Add(new Part { T = p, RestLocal = p.localRotation, AxisLocal = p.parent.InverseTransformDirection(axisW).normalized });
                d.All.Add(door);
            }
            if (d.All.Count > 0) log?.LogInfo($"IVA: {d.All.Count} hinged part(s): {string.Join(", ", d.All.Select(x => x.Name))}.");
            return d;
        }

        public void Update(float dt)
        {
            foreach (Door x in All)
            {
                if (Mathf.Approximately(x.Open, x.Target)) continue;
                x.Open = Mathf.MoveTowards(x.Open, x.Target, dt / SwingSeconds);
                float a = x.Sign * OpenAngle * Mathf.SmoothStep(0f, 1f, x.Open);
                foreach (Part p in x.Parts)
                    if (p.T != null) p.T.localRotation = Quaternion.AngleAxis(a, p.AxisLocal) * p.RestLocal;
            }
        }

        public void CloseAll()
        {
            foreach (Door x in All)
            {
                x.Open = x.Target = 0f;
                foreach (Part p in x.Parts)
                    if (p.T != null) p.T.localRotation = p.RestLocal;
            }
        }
    }
}
