// Going through hatches: into the next crewed part (a real crew transfer), or out on EVA.
//
// Each interior marks its hatches (IVA_Hatch_<name>, pod space). What lies beyond a hatch is the crewed part of ours on
// the active vessel whose centre is most nearly in that direction from this part (within 45 degrees and 8 m), so a
// docking port or adapter in between doesn't matter. The game calls used:
//   KerbalRosterManager.SetKerbalLocation(kerbal, part GlobalId, IGGuid.Empty, seat)   moves a kerbal between parts
//   EVAUtils.TryStartEVA(part, seat)        puts that seat's kerbal outside at the part's airlock or ladder
//   EVAUtils.GetFirstLadderOrAirlockPhysicsSpacePosRot   whether the part has one at all

using System;
using System.Collections.Generic;
using KSP;
using KSP.Game;
using KSP.Sim.impl;
using UnityEngine;
using ILogger = ReduxLib.Logging.ILogger;

namespace IVA
{
    public static class Hatches
    {
        public class Hatch
        {
            public string Name;
            public Vector3 Pod;          // pod space
            public PodInfo Beyond;       // crewed part of ours on the other side (null: none)
            public bool Outside => Beyond == null;
        }

        // Which way a hatch leads, in world space: end hatches along the part's axis (Aft down it; Fore, Tunnel and Docking
        // up it), others from the part's centre out through the hatch. (Measuring from the part's origin alone picked the
        // wrong end of long cabins and the side hatch of pods.)
        public static Vector3 Facing(string name, Vector3 hatchWorld, Transform pod)
        {
            if (name == "Aft") return -pod.up;
            if (name == "Fore" || name == "Tunnel" || name == "Docking") return pod.up;
            return hatchWorld - pod.position;
        }

        public static List<Hatch> Find(Transform interior, PodInfo here, GameInstance game, bool anyPod)
        {
            var list = new List<Hatch>();
            if (interior == null || here?.Pod == null) return list;
            Transform pod = here.Pod.transform;
            List<PodInfo> parts = PodLocator.FindAll(game, anyPod);
            foreach (Transform t in interior.GetComponentsInChildren<Transform>(true))
            {
                if (!t.name.StartsWith("IVA_Hatch_", StringComparison.Ordinal)) continue;
                var h = new Hatch { Name = t.name.Substring("IVA_Hatch_".Length), Pod = pod.InverseTransformPoint(t.position) };
                Vector3 dir = Facing(h.Name, t.position, pod);
                if (h.Name != "Side" && dir.sqrMagnitude > 1e-4f)
                {
                    float best = float.MaxValue;
                    foreach (PodInfo p in parts)
                    {
                        if (p.Pod == null || p.Pod == here.Pod) continue;
                        Vector3 to = p.Pod.transform.position - pod.position;
                        if (to.magnitude > 8f || Vector3.Angle(dir, to) > 45f) continue;
                        if (to.magnitude < best) { best = to.magnitude; h.Beyond = p; }
                    }
                }
                list.Add(h);
            }
            return list;
        }

        public static KerbalRosterManager Roster(GameInstance game) => game?.SessionManager?.KerbalRosterManager;

        public static int FreeSeat(GameInstance game, PartBehavior part)
        {
            KerbalRosterManager roster = Roster(game);
            if (roster == null || part?.Model?.PartData == null) return -1;
            for (int i = 0; i < part.Model.PartData.crewCapacity; i++)
                if (!roster.IsSeatOccupied(part.Model.GlobalId, IGGuid.Empty, i)) return i;
            return -1;
        }

        public static bool HasAirlock(PartBehavior part)
        {
            try { return part != null && EVAUtils.GetFirstLadderOrAirlockPhysicsSpacePosRot(part, false, out Vector3 _, out Quaternion _); }
            catch (Exception) { return false; }
        }

        // Moves the kerbal into a free seat of the part beyond. Returns false (and says why) if it can't.
        public static bool Transfer(GameInstance game, KerbalInfo kerbal, PartBehavior to, ILogger log)
        {
            int seat = FreeSeat(game, to);
            if (seat < 0) { log?.LogInfo("IVA: the part beyond the hatch is full."); return false; }
            bool ok = Roster(game)?.SetKerbalLocation(kerbal, to.Model.GlobalId, IGGuid.Empty, seat) ?? false;
            log?.LogInfo(ok ? $"IVA: moved {kerbal.Attributes.GetFullName()} into seat {seat} of {PodLocator.PartName(to)}."
                            : $"IVA: the game refused to move {kerbal.Attributes.GetFullName()} across.");
            return ok;
        }

        public static bool StartEva(PartBehavior part, KerbalInfo kerbal, ILogger log)
        {
            int seat = kerbal.Location.PositionIndex;
            bool ok;
            try { ok = EVAUtils.TryStartEVA(part, seat); }
            catch (Exception e) { log?.LogError("IVA: starting EVA failed: " + e); return false; }
            log?.LogInfo(ok ? $"IVA: {kerbal.Attributes.GetFullName()} is going out on EVA." : "IVA: the game couldn't start the EVA.");
            return ok;
        }
    }
}
