// Sounds inside the interior, played through the game's own Wwise events (so there's nothing of ours to ship or licence).
//
// The sounds play from the pod's own part-audio object (KSPPartAudioBase), which the game has registered with Wwise
// and keeps its part parameters on (k_part_attachment_status = 1 and so on). A fresh emitter of our own played
// nothing in the first test (2026-10-11), most likely because part sounds are muted while that parameter is 0. If a
// part has no part-audio object we fall back to our own emitter at the camera with those parameters set. Event names
// were read from the game's banks for 26w41a; each event's first play is logged with its result.

using System;
using System.Collections.Generic;
using UnityEngine;
using ILogger = ReduxLib.Logging.ILogger;

namespace IVA
{
    public class Sounds
    {
        // The EVA jetpack's own sound: the kerbal's jetpack event reference has the same Wwise ID as the RCS thruster event.
        public const string ThrustStart = "Play_rcs_rocket_launch__";
        public const string ThrustStop = "Play_rcs_rocket_launch_STOP";
        public const string DoorOpen = "Play_An_Kerbal_science_tube_open";
        public const string DoorClose = "Play_An_Kerbal_science_tube_close";
        public const string Unbuckle = "Play_An_Kerbal_jetpack_open_end";
        public const string Buckle = "Play_An_Kerbal_jetpack_close_end";
        public const string LockerOpen = "Play_An_Landing_Leg_Medium_Extensible_LT_2_latch_open";
        public const string LockerClose = "Play_An_Landing_Leg_Medium_Extensible_LT_2_latch_close";
        public const string DrawerOpen = "Play_An_Kerbal_science_tube_pullout";
        public const string DrawerClose = "Play_An_Kerbal_science_tube_away";
        public const string Curtain = "Play_An_Kerbal_helmet_adjust";
        public const string Switch = "Play_An_Kerbal_jetpack_button";
        public const string Button = "Play_An_Kerbal_science_button";
        public const string LightsOn = "Play_light_ON";
        public const string LightsOff = "Play_light_OFF";
        public const string FlushStart = "Play_resources_fuel_flow_ON_to";
        public const string FlushStop = "Play_resources_fuel_flow_OFF_to";
        public const string OvenStart = "Play_gimbal_ON";
        public const string HatchClose = "Play_An_DockingPortMK2_close_5_shut";

        // Candidates for the interactive kit, to try in game with the audition keys (see IVAPlugin).
        public static readonly string[] Audition =
        {
            "Play_rcs_rocket_launch__", "Play_u_ENGINE_monoprop_0v_puff",
            "Play_An_Kerbal_jetpack_button", "Play_An_Kerbal_science_button", "Play_An_Kerbal_jetpack_open", "Play_An_Kerbal_jetpack_close",
            "Play_An_Kerbal_jetpack_open_end", "Play_An_Kerbal_jetpack_close_end", "Play_An_Kerbal_helmet_adjust", "Play_An_Kerbal_getUp_push",
            "Play_An_Kerbal_science_tube_open", "Play_An_Kerbal_science_tube_close", "Play_An_Kerbal_science_tube_pullout",
            "Play_An_Kerbal_science_tube_away", "Play_An_Kerbal_science_tube_shake", "Play_An_Kerbal_science_tube_scoop",
            "Play_light_ON", "Play_light_OFF", "Play_gimbal_ON", "Play_gimbal_OFF",
            "Play_science_experiment_start", "Play_science_experiment_stop", "Play_k_science_experiment_start",
            "Play_An_Landing_Leg_Medium_Extensible_LT_2_latch_open", "Play_An_Landing_Leg_Medium_Extensible_LT_2_latch_close",
            "Play_An_Landing_Leg_Medium_Extensible_LT_2_motor_a_deploy",
            "Play_An_DockingPortMK2_open_1__start", "Play_An_DockingPortMK2_close_5_shut", "Play_An_dockingPortShielded_close_4_shut",
            "Play_An_Service_Bay_Medium_open_1", "Play_An_Service_Bay_Medium_close_4", "Play_An_Cargo_Bay_Short_Mk2_open_1",
            "Play_SolarArray_circular_open_motor", "Play_An_antenna_dish_88_deploy_latch1",
            "Play_resources_fuel_flow_ON_to", "Play_resources_fuel_flow_OFF_to", "Play_docking_connected", "Play_decouple_separators",
            "Play_generator_thermoeletric_radiosotope_ON", "Play_u_amb_generator_fission_2v",
            "Play_s_An_lab_2v_science_orbital_open_1", "Play_s_An_collector_0v_radial_science_sampler_sample_01",
        };

        private GameObject _go;
        private ulong _id;
        private bool _borrowed;   // the pod's own audio object: don't move it, and only stop what we started
        private readonly List<uint> _playing = new List<uint>();
        private readonly HashSet<string> _logged = new HashSet<string>();
        private readonly ILogger _log;
        private readonly HashSet<string> _failed = new HashSet<string>();
        private bool _thrusting;
        private uint _auditionPlaying;
        private string _ambienceStop;

        public bool Valid => _go != null;

        public static Sounds Create(Component pod, ILogger log)
        {
            var s = new Sounds(log);
            try
            {
                KSPPartAudioBase partAudio = pod != null ? pod.GetComponentInChildren<KSPPartAudioBase>(true) : null;
                if (partAudio != null)
                {
                    s._go = partAudio.gameObject;
                    s._borrowed = true;
                }
                else
                {
                    s._go = new GameObject("IVA_Sounds");
                    UnityEngine.Object.DontDestroyOnLoad(s._go);
                    AkSoundEngine.RegisterGameObj(s._go, s._go.name);
                    KSPBaseAudio.SetRTPCValue(KSPAudioParams.k_part_attachment_status, 1f, s._go);
                    KSPBaseAudio.SetRTPCValue(KSPAudioParams.k_part_active_vessel_rtpc, 1f, s._go);
                    // a pressurised cabin: sounds as at sea level, whatever the vessel's surroundings
                    KSPBaseAudio.SetRTPCValue(KSPAudioParams.k_part_static_pressure_kPa_rtpc, 101.325f, s._go);
                    KSPBaseAudio.SetRTPCValue(KSPAudioParams.k_part_atmos_density_rtpc, 1.225f, s._go);
                }
                s._id = AkSoundEngine.GetAkGameObjectID(s._go);
                log?.LogInfo($"IVA: cabin sounds play from '{s._go.name}' ({(s._borrowed ? "the pod's own part audio" : "our own emitter")}, registered {AkSoundEngine.IsGameObjectRegistered(s._go)}).");
            }
            catch (Exception e)
            {
                log?.LogWarning("IVA: sounds unavailable: " + e.Message);
                s.End();
            }
            return s;
        }

        private Sounds(ILogger log) { _log = log; }

        // 0..1, applied to everything this emitter plays.
        public void SetVolume(float v)
        {
            if (_go == null) return;
            try
            {
                GameObject listener = KSPAudioListenerManager.GetListenerGameObject();
                ulong lid = listener != null ? AkSoundEngine.GetAkGameObjectID(listener) : AkSoundEngine.AK_INVALID_GAME_OBJECT;
                AKRESULT r = AkSoundEngine.SetGameObjectOutputBusVolume(_id, lid, Mathf.Clamp01(v));
                if (r != AKRESULT.AK_Success) _log?.LogWarning($"IVA: setting the sound volume returned {r}.");
            }
            catch (Exception e) { _log?.LogWarning("IVA: couldn't set the sound volume: " + e.Message); }
        }

        public void Place(Transform at)
        {
            if (_go == null || at == null || _borrowed) return;
            _go.transform.SetPositionAndRotation(at.position, at.rotation);
            AkSoundEngine.SetObjectPosition(_go, _go.transform);
        }

        public uint Play(string ev)
        {
            if (_go == null || string.IsNullOrEmpty(ev)) return 0u;
            uint id = KSPBaseAudio.PostEvent(ev, _go);
            if (id == 0u && _failed.Add(ev)) _log?.LogWarning($"IVA: sound event '{ev}' didn't play (not in the loaded banks?).");
            else if (id != 0u && _logged.Add(ev)) _log?.LogInfo($"IVA: sound '{ev}' playing (id {id}).");
            if (id != 0u)
            {
                _playing.Add(id);
                if (_playing.Count > 64) _playing.RemoveAt(0);
            }
            return id;
        }

        // Thrusters: one loop while any thrust key is held (a short tap gives a puff).
        public void SetThrust(bool on)
        {
            if (on == _thrusting) return;
            _thrusting = on;
            Play(on ? ThrustStart : ThrustStop);
        }

        public void StartAmbience(string ev)
        {
            StopAmbience();
            if (string.IsNullOrEmpty(ev)) return;
            if (Play(ev) != 0u) _ambienceStop = ev + "_stop";
        }

        public void StopAmbience()
        {
            if (_ambienceStop == null) return;
            Play(_ambienceStop);
            _ambienceStop = null;
        }

        // Audition: stop the last one, play this one.
        public void PlayAudition(string ev)
        {
            if (_go == null) return;
            if (_auditionPlaying != 0u) AkSoundEngine.StopPlayingID(_auditionPlaying, 150);
            _auditionPlaying = Play(ev);
            _log?.LogInfo($"IVA: audition '{ev}' ({(_auditionPlaying != 0u ? "playing" : "no such event")}).");
        }

        public void End()
        {
            if (_go == null) return;
            try
            {
                if (_thrusting) Play(ThrustStop);
                StopAmbience();
                if (_borrowed)
                {
                    foreach (uint id in _playing) AkSoundEngine.StopPlayingID(id, 200);
                    SetVolume(1f);
                }
                else
                {
                    AkSoundEngine.StopAll(_id);
                    AkSoundEngine.UnregisterGameObj(_go);
                }
            }
            catch (Exception) { }
            if (!_borrowed) UnityEngine.Object.Destroy(_go);
            _playing.Clear();
            _go = null;
            _thrusting = false;
        }
    }
}
