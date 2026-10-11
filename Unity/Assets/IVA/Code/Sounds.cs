// Sounds inside the interior, played through the game's own Wwise events (so there's nothing of ours to ship or licence).
//
// Where they play from is switchable (the first two tests were silent although every event was accepted):
//   Camera   our own emitter at the camera, explicitly given the game's audio listener (Wwise only plays an emitter's
//            sounds to its listeners), with the part parameters set (k_part_attachment_status = 1 and so on)
//   Pod      the pod's own part-audio object (KSPPartAudioBase), set up by the game
//   Listener the listener's own game object (distance zero)
// Each event's first play logs its distance to the listener and, from Wwise callbacks, its duration and when it ended.

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

        public enum Source { Camera, Pod, Listener }
        public static readonly int SourceCount = 3;

        private readonly ILogger _log;
        private readonly Component _pod;
        private GameObject _own;          // our emitter (Camera source)
        private GameObject _go;           // where events go now
        private ulong _id;
        private Source _source;
        private float _volume = 1f;
        private readonly List<KeyValuePair<GameObject, uint>> _playing = new List<KeyValuePair<GameObject, uint>>();
        private readonly HashSet<string> _logged = new HashSet<string>();
        private readonly HashSet<string> _failed = new HashSet<string>();
        private readonly Dictionary<uint, KeyValuePair<string, float>> _timing = new Dictionary<uint, KeyValuePair<string, float>>();
        private bool _thrusting;
        private uint _auditionPlaying;
        private string _ambienceStop;

        public bool Valid => _go != null;
        public Source Current => _source;

        public static Sounds Create(Component pod, Source source, ILogger log)
        {
            var s = new Sounds(pod, log);
            try
            {
                s._own = new GameObject("IVA_Sounds");
                UnityEngine.Object.DontDestroyOnLoad(s._own);
                AkSoundEngine.RegisterGameObj(s._own, s._own.name);
                KSPBaseAudio.SetRTPCValue(KSPAudioParams.k_part_attachment_status, 1f, s._own);
                KSPBaseAudio.SetRTPCValue(KSPAudioParams.k_part_active_vessel_rtpc, 1f, s._own);
                // a pressurised cabin: sounds as at sea level, whatever the vessel's surroundings
                KSPBaseAudio.SetRTPCValue(KSPAudioParams.k_part_static_pressure_kPa_rtpc, 101.325f, s._own);
                KSPBaseAudio.SetRTPCValue(KSPAudioParams.k_part_atmos_density_rtpc, 1.225f, s._own);
                GameObject listener = ListenerObject();
                if (listener != null)
                {
                    AKRESULT r = AkSoundEngine.AddListener(s._own, listener);
                    log?.LogInfo($"IVA: sound listener '{listener.name}' (registered {AkSoundEngine.IsGameObjectRegistered(listener)}, default listener {listener.GetComponent<AkAudioListener>()?.isDefaultListener}); attaching it to our emitter: {r}.");
                }
                else log?.LogWarning("IVA: found no Wwise audio listener in the scene.");
                s.Use(source);
            }
            catch (Exception e)
            {
                log?.LogWarning("IVA: sounds unavailable: " + e.Message);
                s.End();
            }
            return s;
        }

        private Sounds(Component pod, ILogger log) { _pod = pod; _log = log; }

        // The game object carrying the Wwise listener (the listener manager sits on it or below it).
        private static GameObject ListenerObject()
        {
            GameObject m = KSPAudioListenerManager.GetListenerGameObject();
            if (m == null) return null;
            AkAudioListener l = m.GetComponentInParent<AkAudioListener>();
            return l != null ? l.gameObject : m;
        }

        public void Use(Source source)
        {
            _source = source;
            GameObject go = null;
            if (source == Source.Pod)
            {
                KSPPartAudioBase pa = _pod != null ? _pod.GetComponentInChildren<KSPPartAudioBase>(true) : null;
                go = pa != null ? pa.gameObject : null;
            }
            else if (source == Source.Listener) go = ListenerObject();
            if (go == null) { go = _own; _source = Source.Camera; }
            _go = go;
            _id = AkSoundEngine.GetAkGameObjectID(_go);
            _logged.Clear();
            _log?.LogInfo($"IVA: cabin sounds now play from {_source} ('{_go.name}', registered {AkSoundEngine.IsGameObjectRegistered(_go)}).");
            if (_source == Source.Camera) SetVolume(_volume);
        }

        public void Next() => Use((Source)(((int)_source + 1) % SourceCount));

        // 0..1, applied to our own emitter only (the pod's and the listener's objects carry the game's own sounds).
        public void SetVolume(float v)
        {
            _volume = Mathf.Clamp01(v);
            if (_own == null) return;
            try
            {
                GameObject listener = ListenerObject();
                ulong lid = listener != null ? AkSoundEngine.GetAkGameObjectID(listener) : AkSoundEngine.AK_INVALID_GAME_OBJECT;
                AKRESULT r = AkSoundEngine.SetGameObjectOutputBusVolume(AkSoundEngine.GetAkGameObjectID(_own), lid, _volume);
                if (r != AKRESULT.AK_Success) _log?.LogWarning($"IVA: setting the sound volume returned {r}.");
            }
            catch (Exception e) { _log?.LogWarning("IVA: couldn't set the sound volume: " + e.Message); }
        }

        public void Place(Transform at)
        {
            if (_own == null || at == null) return;
            _own.transform.SetPositionAndRotation(at.position, at.rotation);
            AkSoundEngine.SetObjectPosition(_own, _own.transform);
        }

        public uint Play(string ev)
        {
            if (_go == null || string.IsNullOrEmpty(ev)) return 0u;
            bool first = !_logged.Contains(ev);
            uint id = first
                ? KSPBaseAudio.PostEvent(ev, _go, (uint)(AkCallbackType.AK_EndOfEvent | AkCallbackType.AK_Duration), OnCallback, ev)
                : KSPBaseAudio.PostEvent(ev, _go);
            if (id == 0u)
            {
                if (_failed.Add(ev)) _log?.LogWarning($"IVA: sound event '{ev}' didn't play (not in the loaded banks?).");
                return 0u;
            }
            if (first)
            {
                _logged.Add(ev);
                GameObject listener = ListenerObject();
                float dist = listener != null ? Vector3.Distance(listener.transform.position, _go.transform.position) : -1f;
                _timing[id] = new KeyValuePair<string, float>(ev, Time.unscaledTime);
                _log?.LogInfo($"IVA: sound '{ev}' playing (id {id}) from {_source}, {dist:F2} m from the listener.");
            }
            _playing.Add(new KeyValuePair<GameObject, uint>(_go, id));
            if (_playing.Count > 64) _playing.RemoveAt(0);
            return id;
        }

        private void OnCallback(object cookie, AkCallbackType type, AkCallbackInfo info)
        {
            try
            {
                if (type == AkCallbackType.AK_Duration && info is AkDurationCallbackInfo d)
                    _log?.LogInfo($"IVA: sound '{cookie}': duration {d.fDuration:F2} s (estimated {d.fEstimatedDuration:F2} s), streaming {d.bStreaming}, media {d.mediaID}.");
                else if (type == AkCallbackType.AK_EndOfEvent && info is AkEventCallbackInfo e && _timing.TryGetValue(e.playingID, out var t))
                {
                    _log?.LogInfo($"IVA: sound '{t.Key}' ended after {Time.unscaledTime - t.Value:F2} s.");
                    _timing.Remove(e.playingID);
                }
            }
            catch (Exception) { }
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
            _logged.Remove(ev);   // log every audition play in full
            _auditionPlaying = Play(ev);
            _log?.LogInfo($"IVA: audition '{ev}' from {_source} ({(_auditionPlaying != 0u ? "playing" : "no such event")}).");
        }

        public void End()
        {
            try
            {
                if (_thrusting) Play(ThrustStop);
                StopAmbience();
                foreach (var kv in _playing) AkSoundEngine.StopPlayingID(kv.Value, 200);
                if (_own != null)
                {
                    AkSoundEngine.StopAll(AkSoundEngine.GetAkGameObjectID(_own));
                    AkSoundEngine.UnregisterGameObj(_own);
                    UnityEngine.Object.Destroy(_own);
                }
            }
            catch (Exception) { }
            _playing.Clear();
            _own = null;
            _go = null;
            _thrusting = false;
        }
    }
}
