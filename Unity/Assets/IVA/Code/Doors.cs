// Doors in the interiors (hygiene compartments) that open and close.
//
// The interior carries each door leaf as a separate moving part ("...__Live_Door<name>", pivot on the hinge line) plus
// position-only markers: IVA_LiveAxis_Door<name> (up the hinge, half the door's height from the pivot),
// IVA_LiveEdge_Door<name> (the free edge when closed) and IVA_LiveOut_Door<name> (the side it opens towards). Using
// marker positions keeps this independent of how Blender's axes were converted on import (as for the instruments).

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

        public class Door
        {
            public string Name;
            public Transform T;
            public Quaternion RestLocal;
            public Vector3 AxisLocal;    // hinge axis in the leaf's parent space
            public float Sign;           // rotation sense that swings the free edge towards the open side
            public float Open, Target;   // 0 closed .. 1 open
            public Vector3 HingePod, AxisPod, EdgePod, OutPod;   // pod space: pivot, half-height up the hinge, pivot to free edge, open side
            public Vector3 CentrePod => HingePod + EdgePod * 0.5f;
        }

        public readonly List<Door> All = new List<Door>();

        public static Doors Find(GameObject interior, Transform pod, ILogger log)
        {
            var d = new Doors();
            Transform[] all = interior.GetComponentsInChildren<Transform>(true);
            var byName = new Dictionary<string, Transform>(StringComparer.Ordinal);
            foreach (Transform t in all)
                if (t.name.StartsWith("IVA_Live", StringComparison.Ordinal) && !byName.ContainsKey(t.name)) byName[t.name] = t;
            foreach (Transform t in all)
            {
                int k = t.name.IndexOf("__Live_Door", StringComparison.Ordinal);
                if (k < 0) continue;
                string name = t.name.Substring(k + "__Live_".Length);
                int dot = name.IndexOf(" (", StringComparison.Ordinal);
                if (dot > 0) name = name.Substring(0, dot);
                if (!byName.TryGetValue("IVA_LiveAxis_" + name, out Transform axisM) || !byName.TryGetValue("IVA_LiveEdge_" + name, out Transform edgeM) ||
                    !byName.TryGetValue("IVA_LiveOut_" + name, out Transform outM) || t.parent == null)
                {
                    log?.LogWarning($"IVA: door {name} is missing its markers; it won't open.");
                    continue;
                }
                Vector3 axisW = axisM.position - t.position, edgeW = edgeM.position - t.position, outW = outM.position - t.position;
                Vector3 swung = Quaternion.AngleAxis(30f, axisW.normalized) * edgeW;
                d.All.Add(new Door
                {
                    Name = name, T = t, RestLocal = t.localRotation,
                    AxisLocal = t.parent.InverseTransformDirection(axisW).normalized,
                    Sign = Vector3.Dot(swung - edgeW, outW) >= 0f ? 1f : -1f,
                    HingePod = pod.InverseTransformPoint(t.position),
                    AxisPod = pod.InverseTransformDirection(axisW),
                    EdgePod = pod.InverseTransformDirection(edgeW),
                    OutPod = pod.InverseTransformDirection(outW).normalized,
                });
            }
            if (d.All.Count > 0) log?.LogInfo($"IVA: {d.All.Count} door(s): {string.Join(", ", d.All.Select(x => x.Name))}.");
            return d;
        }

        public void Update(float dt)
        {
            foreach (Door x in All)
            {
                if (x.T == null || Mathf.Approximately(x.Open, x.Target)) continue;
                x.Open = Mathf.MoveTowards(x.Open, x.Target, dt / SwingSeconds);
                x.T.localRotation = Quaternion.AngleAxis(x.Sign * OpenAngle * Mathf.SmoothStep(0f, 1f, x.Open), x.AxisLocal) * x.RestLocal;
            }
        }

        public Door Nearest(Vector3 podPos, float reach)
        {
            Door best = null;
            float bestD = reach;
            foreach (Door x in All)
            {
                float dist = Vector3.Distance(podPos, x.CentrePod);
                if (dist < bestD) { bestD = dist; best = x; }
            }
            return best;
        }

        public void CloseAll()
        {
            foreach (Door x in All)
            {
                x.Open = x.Target = 0f;
                if (x.T != null) x.T.localRotation = x.RestLocal;
            }
        }
    }
}
