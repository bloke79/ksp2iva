// IVA for KSP2 Redux
// Started as a port of Mudkip909's "KSP2 Free IVA" (0.2.6, BepInEx/SpaceWarp 1); now ships its own
// modelled pod interiors (see CustomInterior.cs) with the real world visible through the windows.
//
// Press the toggle key (default C) in flight to sit inside your crew pod.
// Press the next-seat key (default N) while in IVA to move to the next seat, B for window views,
// U to unbuckle and float round the cabin (WASD, Shift/Ctrl up/down, Q/E roll; U again to sit back down).
// Mouse looks around, scroll wheel zooms. The numpad lines the interior up with the pod.
//
// Modes, tried in order:
//  1. Custom interior: a modelled interior shipped with the mod, placed inside the real pod.
//  2. Portrait camera: the original mod's behaviour, looking through a crew portrait camera.

using System;
using System.Collections.Generic;
using System.Linq;
using KSP.Game;
using KSP.Sim;
using KSP.Sim.impl;
using Redux.ExtraModTypes;
using SpaceWarp2.API.Configuration;
using SpaceWarp2.API.Input;
using UnityEngine;

namespace IVA
{
    // Run late so the camera pose is applied after the game's own camera code each frame.
    [DefaultExecutionOrder(30000)]
    public class IVAPlugin : KerbalMod
    {
        private const string FlightCameraName = "FlightCameraPhysics_Main";
        private const float IvaNearClip = 0.02f;

        // ---- Config ----
        private ConfigValue<KeyboardShortcut> _toggleKey;
        private ConfigValue<KeyboardShortcut> _nextSeatKey;
        private ConfigValue<KeyboardShortcut> _windowKey;
        private ConfigValue<KeyboardShortcut> _unbuckleKey;
        private ConfigValue<KeyboardShortcut> _doorKey;
        private ConfigValue<float> _floatSpeed;
        private ConfigValue<float> _walkSpeed;
        private string _toast;           // a short message on screen (e.g. "no floor to stand on")
        private float _toastUntil;
        private ConfigValue<bool> _soundOn;
        private ConfigValue<bool> _thrusterSound;
        private ConfigValue<float> _soundVolume;
        private ConfigValue<string> _ambience;
        private ConfigValue<bool> _audition;
        private ConfigValue<float> _windowFov;
        private ConfigValue<float> _glideTime;
        private ConfigValue<float> _mouseSensitivity;
        private ConfigValue<bool> _invertY;
        private ConfigValue<bool> _holdRightMouseToLook;
        private ConfigValue<float> _maxPitch;
        private ConfigValue<float> _defaultFov;
        private ConfigValue<float> _minFov;
        private ConfigValue<float> _maxFov;
        private ConfigValue<float> _zoomSpeed;
        private ConfigValue<bool> _invertZoom;
        private ConfigValue<bool> _hideOwnKerbal;

        private ConfigValue<bool> _useCustomInterior;
        private ConfigValue<string> _podNameFilter;
        private ConfigValue<bool> _anyPod;
        private ConfigValue<bool> _fitToPod;
        private ConfigValue<bool> _hideExterior;
        private ConfigValue<bool> _cabinAo;
        private ConfigValue<float> _cabinAoStrength;

        private ConfigValue<float> _offX, _offY, _offZ, _yaw, _scale;
        private ConfigValue<float> _eyeX, _eyeY, _eyeZ;
        private ConfigValue<bool> _numpadAlign;

        private ConfigValue<bool> _debugLog;
        private ConfigValue<bool> _poseDump;
        private bool _ready;

        // ---- State ----
        private enum Mode { None, CustomInterior, Portrait, Native }

        private Mode _mode = Mode.None;
        private Camera _flightCam;
        private int _seatIndex;

        // Custom interior
        private CustomInteriorSession _session;
        private VesselBehavior _vesselAtEntry;
        private bool _loading;
        private PodInfo _loadingFor;
        private readonly Dictionary<string, GameObject> _prefabCache = new Dictionary<string, GameObject>();
        private float _alignStep = 0.02f;

        // Portrait mode (original behaviour)
        private readonly List<Camera> _kerbalCams = new List<Camera>();
        private Camera _seatCam;
        private Transform _hiddenBody;
        private Vector3 _hiddenBodyScale;
        private static readonly Vector3 PortraitEyeLocalPosition = new Vector3(-0.001f, 0.625f, 0.1f);

        // Flight camera state saved on entry, restored on exit.
        private Transform _origParent;
        private Vector3 _origLocalPos;
        private Quaternion _origLocalRot;
        private float _origFov;
        private float _origNearClip;

        // Look state (degrees) and zoom (field of view).
        private float _yawLook;
        private float _pitch;
        private float _fov;

        // Window views: -1 = at the seat. Moves between poses glide from the pose captured at the switch (pod space).
        private int _viewIndex = -1;
        private float _blend = 1f;
        private Vector3 _fromPos;
        private Quaternion _fromRot = Quaternion.identity;
        private float _fromFov;
        private float _seatFov;

        private bool InIva => _mode != Mode.None;

        // Unbuckled: floating round the cabin (null while seated).
        private FreeMove _free;
        private Interact _interact;
        private readonly Dictionary<Doors.Door, int> _doorBoxes = new Dictionary<Doors.Door, int>();
        private bool _flightInputLocked;
        private GUIStyle _promptStyle;
        private GUIStyle _dotStyle;

        // Hatches of the current interior, and a move through one in progress (re-entering IVA in the next part).
        private List<Hatches.Hatch> _hatches = new List<Hatches.Hatch>();
        private bool _hasAirlock;
        private class Arrival { public PodInfo To; public PartBehavior From; public Vector3 FromWorld; public KSP.Game.KerbalInfo Kerbal; public float At; }
        private Arrival _arrival;
        private Hatches.Hatch _hatchGo;   // set when a hatch has finished opening; acted on in the next Update
        // EVA waits until IVA has fully let go of the camera (the game crashed when EVA started in the same frame).
        private class PendingEva { public PartBehavior Part; public VesselBehavior Vessel; public KSP.Game.KerbalInfo Kerbal; public float At; }
        private PendingEva _pendingEva;
        private Sounds _sounds;
        private Sounds.Source _soundSource = Sounds.Source.Camera;   // switched with \ while auditioning; kept for the game session
        private int _auditionIndex = -1;

        public override void OnInitialized()
        {
            BindConfig();
            Camera.onPreCull += OnCameraPreCull;
            _ready = true;
            SWLogger.LogInfo($"IVA loaded. Toggle: {_toggleKey.Value}, next seat: {_nextSeatKey.Value}, window view: {_windowKey.Value}. " +
                             $"Interiors: {string.Join(", ", InteriorCatalogue.All.Select(d => d.Name))}.");
        }

        private void BindConfig()
        {
            var cfg = SWConfiguration;

            _toggleKey = Bind(cfg, "Keys", "Toggle IVA", new KeyboardShortcut(KeyCode.C), "Enter or leave IVA view while in flight.");
            _nextSeatKey = Bind(cfg, "Keys", "Next seat", new KeyboardShortcut(KeyCode.N), "Move to the next seat while in IVA (V is the game's camera-mode key).");
            _windowKey = Bind(cfg, "Keys", "Window view", new KeyboardShortcut(KeyCode.B),
                "Lean up to the nearest window; press again for the next window, and after the last one, back to your seat.");
            _windowFov = Bind(cfg, "Zoom", "Window view field of view", 60f, "Field of view at a window.", new RangeConstraint<float>(20f, 120f));
            _glideTime = Bind(cfg, "Look", "Window glide time", 0.5f, "Seconds to move between the seat and a window (0 = instant).", new RangeConstraint<float>(0f, 3f));
            _unbuckleKey = Bind(cfg, "Keys", "Unbuckle", new KeyboardShortcut(KeyCode.U),
                "Leave the couch and float round the cabin (WASD move, Shift/Ctrl up/down, Q/E roll), or walk in a landed lander (WASD, Space jump, Ctrl crouch); press again to sit in the nearest couch.");
            _doorKey = Bind(cfg, "Keys", "Open door", new KeyboardShortcut(KeyCode.F),
                "While floating round the cabin: use what you're looking at (doors, lockers, drawers, curtains, lamps, screens, lights, the toilet; the vessel's controls are locked then, so F is free).");
            _floatSpeed = Bind(cfg, "Look", "Float speed", 1.2f, "Top speed when floating round the cabin (metres per second).", new RangeConstraint<float>(0.2f, 4f));
            _walkSpeed = Bind(cfg, "Look", "Walk speed", 0.9f, "Walking speed in a landed lander (metres per second).", new RangeConstraint<float>(0.3f, 3f));

            _soundOn = Bind(cfg, "Sound", "Interior sounds", true, "Sounds inside the cabin (thrusters, doors, buckles), using the game's own sound events.");
            _thrusterSound = Bind(cfg, "Sound", "Thruster sound", true, "While floating, moving plays the EVA jetpack's thruster sound.");
            _soundVolume = Bind(cfg, "Sound", "Volume", 0.6f, "Volume of the cabin sounds (0 to 1).", new RangeConstraint<float>(0f, 1f));
            _ambience = Bind(cfg, "Sound", "Cabin ambience", "",
                "A looping sound event to play quietly while in a cabin (its stop event is the same name plus _stop). Blank = none.");
            _audition = Bind(cfg, "Sound", "Audition keys", false,
                "Testing aid: in IVA, [ and ] step through the game sounds that might suit the cabin's switches, lockers and doors, showing each name.");

            _mouseSensitivity = Bind(cfg, "Look", "Mouse sensitivity", 2.0f,
                "Degrees of rotation per unit of mouse movement.", new RangeConstraint<float>(0.1f, 10f));
            _invertY = Bind(cfg, "Look", "Invert vertical look", false, "Push the mouse forward to look down.");
            _holdRightMouseToLook = Bind(cfg, "Look", "Hold right mouse button to look", false,
                "If on, the view only turns while the right mouse button is held, leaving the cursor free for the UI.");
            _maxPitch = Bind(cfg, "Look", "Max look up/down angle", 85f,
                "How far up or down you can look, in degrees.", new RangeConstraint<float>(10f, 89f));

            _defaultFov = Bind(cfg, "Zoom", "Starting field of view", 75f, "Field of view when you enter IVA.", new RangeConstraint<float>(20f, 120f));
            _minFov = Bind(cfg, "Zoom", "Minimum field of view", 30f, "Most zoomed in.", new RangeConstraint<float>(10f, 90f));
            _maxFov = Bind(cfg, "Zoom", "Maximum field of view", 110f, "Most zoomed out.", new RangeConstraint<float>(60f, 150f));
            _zoomSpeed = Bind(cfg, "Zoom", "Zoom speed", 5f, "Field of view change per scroll-wheel notch.", new RangeConstraint<float>(0.5f, 30f));
            _invertZoom = Bind(cfg, "Zoom", "Invert scroll zoom", false, "By default scrolling up zooms in.");

            _backAfterBoarding = Bind(cfg, "General", "Back into IVA after boarding", true,
                "After an EVA started from a hatch, boarding again returns to IVA in that kerbal's seat.");
            _hideOwnKerbal = Bind(cfg, "General", "Hide own kerbal", true,
                "Hide the head of the kerbal you're looking out of (custom interiors; the portrait view hides the whole body).");

            _useCustomInterior = Bind(cfg, "Interior", "Use custom interiors", true,
                "Use the modelled interiors shipped with this mod. Turn off for the original portrait-camera view.");
            _podNameFilter = Bind(cfg, "Interior", "Pod name filter", "",
                "Blank picks the pod automatically (3-seat pods first). Otherwise part of the pod's name, as listed in the log.");
            _anyPod = Bind(cfg, "Interior", "Use for pods without their own interior", false,
                "Use the Mk1-3 interior in crewed pods that don't have a matching interior yet.");
            _fitToPod = Bind(cfg, "Interior", "Fit to pod", true,
                "Measure the pod and size the interior to match.");
            _hideExterior = Bind(cfg, "Interior", "Hide pod exterior in IVA", false,
                "Turn on if parts of the pod's outer model show inside the cabin. The cabin then gets direct sunlight with no shadows.");

            _cabinAo = Bind(cfg, "Interior", "Ambient occlusion", true,
                "Darken corners, seams and gaps inside the cabin (the game's own post-processing). Turn off if it looks wrong or costs too much.");
            _cabinAoStrength = Bind(cfg, "Interior", "Ambient occlusion strength", 1.0f,
                "How dark the ambient occlusion gets.", new RangeConstraint<float>(0f, 2f));

            var off = new RangeConstraint<float>(-3f, 3f);
            _offX = Bind(cfg, "Alignment", "Offset X", 0f, "Shifts the interior inside the pod (metres). Set with the numpad in IVA.", off);
            _offY = Bind(cfg, "Alignment", "Offset Y", 0f, "Up/down shift (metres).", off);
            _offZ = Bind(cfg, "Alignment", "Offset Z", 0f, "Forward/back shift (metres).", off);
            _yaw = Bind(cfg, "Alignment", "Yaw", 0f, "Turns the interior round the pod axis (degrees), to line its windows up with the pod's.", new RangeConstraint<float>(-180f, 180f));
            _scale = Bind(cfg, "Alignment", "Scale", 1f, "Extra size adjustment on top of the automatic fit.", new RangeConstraint<float>(0.5f, 2f));
            _eyeX = Bind(cfg, "Alignment", "Eye X", 0f, "Eye position relative to the seat's eye point (metres).", off);
            _eyeY = Bind(cfg, "Alignment", "Eye Y", 0f, "Eye height relative to the seat's eye point (metres).", off);
            _eyeZ = Bind(cfg, "Alignment", "Eye Z", 0f, "Eye forward/back relative to the seat's eye point (metres).", off);
            _numpadAlign = Bind(cfg, "Alignment", "Numpad alignment keys", true,
                "In IVA: numpad 8/2 4/6 9/3 move, 7/1 turn, * and / scale, hold Shift to move the eye instead, +/- step size, 5 save, 0 reset.");
            _debugLog = Bind(cfg, "Debug", "Debug logging", true, "Log key presses and the camera report. Errors, warnings and mode switches are always logged.");
            _poseDump = Bind(cfg, "Debug", "Pose dump", true, "Write the crew poses to IVA-pose/*.obj on entering a pod, for building new interiors.");
        }

        private static ConfigValue<T> Bind<T>(IConfigFile cfg, string section, string key, T defaultValue,
            string description, IValueConstraint constraint = null)
        {
            return new ConfigValue<T>(cfg.Bind(section, key, defaultValue, description, constraint));
        }

        private PlacementSettings Placement() => new PlacementSettings
        {
            FitToPod = _fitToPod.Value,
            Offset = new Vector3(_offX.Value, _offY.Value, _offZ.Value),
            Yaw = _yaw.Value,
            ExtraScale = _scale.Value,
        };

        private Vector3 EyeOffset() => new Vector3(_eyeX.Value, _eyeY.Value, _eyeZ.Value);

        // ------------------------------------------------------------------
        // Frame loop
        // ------------------------------------------------------------------

        private void Update()
        {
            if (!_ready) return;
            bool inFlight = IsInFlight();
            // before the returns below, so nothing can stall a fade or a boarding watch
            TickHatchFade();
            TickBoarding();

            // Brief state changes (saves, autosaves, the pause menu) mustn't throw you out of IVA: only leave once the
            // game has been out of flight view for a moment, or straight away if the pod/vessel itself is gone.
            if (InIva)
            {
                bool valid = StillValid();
                _notFlightFor = inFlight ? 0f : _notFlightFor + Time.unscaledDeltaTime;
                if (!valid || _notFlightFor > LeaveAfterSeconds)
                {
                    SWLogger.LogInfo($"IVA: leaving IVA ({(!valid ? "the pod or vessel changed" : "game state " + StateName())}).");
                    ExitIva();
                    return;
                }
                if (!inFlight) return;   // hold the view, ignore input until the state comes back
            }
            CheckCameraAfterExit();
            if (!inFlight) { _loading = false; return; }
            if (_pendingEva != null && !InIva && Time.unscaledTime >= _pendingEva.At) StartPendingEva();
            if (_arrival != null && !InIva && !_loading)
            {
                if (Time.unscaledTime > _arrival.At + 10f) { SWLogger.LogWarning("IVA: gave up entering the next part."); _arrival = null; }
                else if (Time.unscaledTime >= _arrival.At && _arrival.To?.Pod != null) { _exitCheckAt = -1f; EnterIva(_arrival.To); }
            }

            if (_toggleKey.Value.Down)
            {
                if (InIva) ExitIva();
                else if (_loading) { _loading = false; _loadingFor = null; SWLogger.LogInfo("IVA: cancelled loading the interior."); }
                else EnterIva();
                return;
            }

            if (!InIva) return;
            if (_mode == Mode.CustomInterior) KeepCameraGuard();
            if (_mode == Mode.CustomInterior && _unbuckleKey.Value.Down)
            {
                if (_free != null) Buckle();
                else Unbuckle();
            }
            if (_nextSeatKey.Value.Down)
            {
                if (_debugLog.Value) SWLogger.LogInfo($"IVA: next-seat key ({_nextSeatKey.Value}) pressed in mode {_mode}.");
                if (_free != null) Buckle();   // back into the nearest couch first
                else NextSeat();
            }
            else if (Input.GetKeyDown(KeyCode.V) && _nextSeatKey.Value.Main != KeyCode.V)
                if (_debugLog.Value) SWLogger.LogInfo("IVA: V pressed (V is the game's camera-mode key; next seat is " + _nextSeatKey.Value + ").");
            if (_mode == Mode.CustomInterior && _windowKey.Value.Down)
            {
                if (_free != null) Buckle();
                NextWindow();
            }
            if (_audition.Value && _sounds != null)
            {
                if (Input.GetKeyDown(KeyCode.Backslash))
                {
                    _sounds.SetThrust(false);
                    _sounds.Next();
                    _soundSource = _sounds.Current;
                    if (_auditionIndex >= 0) _sounds.PlayAudition(Sounds.Audition[_auditionIndex]);
                }
                int step = Input.GetKeyDown(KeyCode.RightBracket) ? 1 : Input.GetKeyDown(KeyCode.LeftBracket) ? -1 : 0;
                if (step != 0)
                {
                    int n = Sounds.Audition.Length;
                    _auditionIndex = ((_auditionIndex < 0 && step < 0 ? 0 : _auditionIndex + step) % n + n) % n;
                    _sounds.PlayAudition(Sounds.Audition[_auditionIndex]);
                }
            }
            if (_hatchGo != null) { Hatches.Hatch g = _hatchGo; _hatchGo = null; BeginHatchFade(g); return; }
            if (_free != null && _doorKey.Value.Down && (_interact == null || !_interact.HatchBusy)) UseTarget();
            if (_free != null) MoveFree();
            if (_blend < 1f) _blend = _glideTime.Value <= 0f ? 1f : Mathf.Min(1f, _blend + Time.unscaledDeltaTime / _glideTime.Value);
            if (_mode == Mode.CustomInterior && _numpadAlign.Value) HandleAlignmentKeys();
            ReadLookInput();
        }

        private void LateUpdate()
        {
            if (!InIva) return;
            if (_mode == Mode.CustomInterior && _session != null && _session.Live != null && _vesselAtEntry != null)
            {
                try { _session.Live.Update(Game, _vesselAtEntry.Model, _session.PodTransform, Time.deltaTime); }
                catch (Exception e) { SWLogger.LogError("IVA: live instruments failed and are now off: " + e.Message); _session.DisableLive(); }
            }
            if (_interact != null)
            {
                _interact.Update(Time.unscaledDeltaTime);
                if (_free != null)
                    foreach (var kv in _doorBoxes) _free.SetDoorSolid(kv.Value, kv.Key.Open < 0.3f);
            }
            ApplyPose();
            if (_sounds != null && _flightCam != null) _sounds.Place(_flightCam.transform);
        }

        // Applied again just before the flight camera renders, in case anything moved it after LateUpdate.
        private void OnCameraPreCull(Camera cam)
        {
            if (InIva && cam == _flightCam) ApplyPose();
            else if (InIva && _mode == Mode.CustomInterior && _shot == null && cam != null && cam == _scaledCam) SyncScaledCamera();   // it renders first
        }

        // The IVA camera pose in world (physics) space: seat eye or window view, the player's look, and any glide.
        private bool ComputeIvaPose(out Vector3 posW, out Quaternion rotW, out float fov)
        {
            posW = Vector3.zero;
            rotW = Quaternion.identity;
            fov = _fov;
            if (_mode != Mode.CustomInterior || _session == null || _session.PodTransform == null) return false;
            Vector3 pos;
            Quaternion rot;
            if (_free != null)
            {
                posW = _session.PodTransform.TransformPoint(_free.Pos);
                rotW = _session.PodTransform.rotation * _free.Rot;
                return true;
            }
            if (!_session.TryGetPose(_seatIndex, _viewIndex, EyeOffset(), out pos, out rot)) return false;
            rot *= Quaternion.Euler(_pitch, _yawLook, 0f);
            if (_blend < 1f)
            {
                float k = Mathf.SmoothStep(0f, 1f, _blend);
                pos = Vector3.Lerp(_fromPos, pos, k);
                rot = Quaternion.Slerp(_fromRot, rot, k);
                fov = Mathf.Lerp(_fromFov, _fov, k);
            }
            Transform pod = _session.PodTransform;
            posW = pod.TransformPoint(pos);
            rotW = pod.rotation * rot;
            return true;
        }

        // Preferred: hand the game's camera manager our shot, so it places all its cameras itself.
        private IvaCameraShot _shot;

        private bool TryStartShotOverride()
        {
            try
            {
                UniverseCameraManager cm = Game?.CameraManager;
                var space = Game?.UniverseView?.PhysicsSpace;
                if (cm == null || space == null) return false;
                if (cm.IsFirstPersonCameraActive) cm.ExitFirstPersonCamera(false);   // Redux's own first-person view
                // undo any offset an earlier transform-driven IVA left on the camera under its mount
                _flightCam.transform.localPosition = _origLocalPos;
                _flightCam.transform.localRotation = _origLocalRot;
                _shot = new IvaCameraShot(space, ComputeIvaPose, IvaNearClip);
                cm.SetCameraShotOverride(CameraID.Flight, _shot);
                cm.RefreshCameraShot(CameraID.Flight);
                SWLogger.LogInfo("IVA: driving the game's flight camera with the IVA view (camera shot override).");
                return true;
            }
            catch (Exception e)
            {
                SWLogger.LogWarning("IVA: couldn't hand the view to the game's camera manager (" + e.Message + "); moving the camera directly instead.");
                _shot = null;
                return false;
            }
        }

        // The game's camera rig keeps updating under our shot and raycasts terrain for collisions; in some camera modes
        // (cycled with V) that raycast crashes natively (TerrainHeightSampler via BasicCameraRigSolution.DoesCameraCollide).
        // While in IVA, hold the rig in Auto mode with its input off, and put things back afterwards.
        private CameraMode _modeBeforeIva = CameraMode.Auto;
        private bool _inputWasEnabled = true, _guarding;

        private void StartCameraGuard()
        {
            try
            {
                UniverseCameraManager cm = Game?.CameraManager;
                if (cm == null) return;
                _modeBeforeIva = cm.GetFlightCameraMode();
                _inputWasEnabled = cm.InputEnabled;
                if (_modeBeforeIva != CameraMode.Auto) cm.SelectFlightCameraMode(CameraMode.Auto, false);
                cm.DisableInput();
                _guarding = true;
                SWLogger.LogInfo($"IVA: holding the game camera in Auto mode with its input off (was {_modeBeforeIva}).");
            }
            catch (Exception e) { SWLogger.LogWarning("IVA: couldn't hold the game camera: " + e.Message); }
        }

        private void KeepCameraGuard()
        {
            if (!_guarding) return;
            try
            {
                UniverseCameraManager cm = Game?.CameraManager;
                if (cm == null) return;
                if (cm.GetFlightCameraMode() != CameraMode.Auto)
                {
                    cm.SelectFlightCameraMode(CameraMode.Auto, false);
                    SWLogger.LogInfo("IVA: the game camera mode changed during IVA (V?); put it back to Auto.");
                }
                if (cm.InputEnabled) cm.DisableInput();
            }
            catch (Exception) { }
        }

        private void StopCameraGuard()
        {
            if (!_guarding) return;
            _guarding = false;
            try
            {
                UniverseCameraManager cm = Game?.CameraManager;
                if (cm == null) return;
                if (_inputWasEnabled) cm.EnableInput();
                if (_modeBeforeIva != CameraMode.Auto) cm.SelectFlightCameraMode(_modeBeforeIva, false);
            }
            catch (Exception e) { SWLogger.LogWarning("IVA: restoring the game camera failed: " + e.Message); }
        }

        private void StopShotOverride()
        {
            if (_shot == null) return;
            try
            {
                UniverseCameraManager cm = Game?.CameraManager;
                if (cm != null && cm.GetCameraShotIncludeOverride(CameraID.Flight) == _shot)
                {
                    cm.ClearCameraShotOverride(CameraID.Flight);
                    cm.RefreshCameraShot(CameraID.Flight);
                }
            }
            catch (Exception e) { SWLogger.LogWarning("IVA: clearing the camera shot override failed: " + e.Message); }
            _shot = null;
        }

        private void ApplyPose()
        {
            if (_flightCam == null || _mode == Mode.Native) return;   // Redux's first-person camera drives itself
            Quaternion look = Quaternion.Euler(_pitch, _yawLook, 0f);

            if (_mode == Mode.CustomInterior)
            {
                if (_session == null) return;
                _session.ApplyPlacement(Placement());
                _session.UpdateMovedCrew();
                if (_shot != null)
                {
                    // the game has placed the cameras from our shot; only keep the close-up clip and the close-vessel
                    // camera off (the game clamps the main camera's near clip to 0.2 m and turns that camera on)
                    _flightCam.nearClipPlane = IvaNearClip;
                    SuppressCloseVesselCamera();
                    return;
                }
                Vector3 pos;
                Quaternion rot;
                float fov;
                if (!ComputeIvaPose(out pos, out rot, out fov)) return;
                _flightCam.transform.SetPositionAndRotation(pos, rot);
                _flightCam.fieldOfView = fov;
                _flightCam.nearClipPlane = IvaNearClip;
                SyncCompanions(fov, IvaNearClip);
                SyncScaledCamera();
                return;
            }

            Transform t = _flightCam.transform;
            t.localPosition = PortraitEyeLocalPosition;
            t.localRotation = look;
            _flightCam.fieldOfView = _fov;
            _flightCam.nearClipPlane = IvaNearClip;
        }

        private void OnDestroy()
        {
            Camera.onPreCull -= OnCameraPreCull;
            if (InIva) ExitIva();
        }

        private const float LeaveAfterSeconds = 1.5f;
        private float _notFlightFor;
        private float _exitCheckAt = -1f;

        private string StateName()
        {
            try { return Game.GlobalGameState.GetState().ToString(); } catch (Exception) { return "unknown"; }
        }

        // After leaving IVA the game's camera rig should take the camera back out of the pod. If it's still inside the
        // pod half a second later, put it back to where it was before IVA again and say so in the log.
        private void CheckCameraAfterExit()
        {
            if (_exitCheckAt < 0f || Time.unscaledTime < _exitCheckAt) return;
            _exitCheckAt = -1f;
            if (_flightCam == null || _exitPod == null) return;
            float d = Vector3.Distance(_flightCam.transform.position, _exitPod.position);
            if (d > 3f) return;
            SWLogger.LogWarning($"IVA: the camera was still {d:F1} m from the pod after leaving IVA; restoring it again.");
            Transform t = _flightCam.transform;
            t.SetParent(_origParentAtExit, false);
            t.localPosition = _exitLocalPos;
            t.localRotation = _exitLocalRot;
        }

        private Transform _exitPod, _origParentAtExit;
        private Vector3 _exitLocalPos;
        private Quaternion _exitLocalRot;

        private bool IsInFlight()
        {
            try
            {
                return Game != null && Game.GlobalGameState != null
                       && Game.GlobalGameState.GetState() == GameState.FlightView;
            }
            catch (Exception) { return false; }
        }

        private bool StillValid()
        {
            if (_flightCam == null) return false;
            if (_mode == Mode.Portrait) return _seatCam != null;
            if (_mode == Mode.Native)
            {
                try { return Game?.CameraManager != null && Game.CameraManager.IsFirstPersonCameraActive; } catch (Exception) { return false; }
            }
            if (_mode == Mode.CustomInterior)
            {
                if (_session == null || !_session.IsValid) return false;
                VesselBehavior now = PodLocator.ActiveVessel(Game);
                return now != null && now == _vesselAtEntry;
            }
            return false;
        }

        private void ReadLookInput()
        {
            bool look = !_holdRightMouseToLook.Value || Input.GetMouseButton(1);
            if (look)
            {
                // Mouse axes are already a per-frame delta, so no Time.deltaTime: frame-rate independent
                // and still works while paused.
                float sens = _mouseSensitivity.Value;
                float mx = Input.GetAxis("Mouse X") * sens;
                float my = Input.GetAxis("Mouse Y") * sens;
                if (_invertY.Value) my = -my;
                if (_free != null) _free.Turn(mx, -my, 0f);   // floating: no horizon, turn about the view's own axes
                else
                {
                    _yawLook = Mathf.Repeat(_yawLook + mx + 180f, 360f) - 180f;
                    float maxPitch = _maxPitch.Value;
                    _pitch = Mathf.Clamp(_pitch - my, -maxPitch, maxPitch);
                }
            }

            float scroll = Input.mouseScrollDelta.y;
            if (Mathf.Abs(scroll) > 0.001f)
            {
                if (_invertZoom.Value) scroll = -scroll;
                _fov -= scroll * _zoomSpeed.Value; // scroll up narrows the view (zooms in)
            }
            _fov = Mathf.Clamp(_fov, MinFov(), MaxFov());
        }

        private float MinFov() => Mathf.Min(_minFov.Value, _maxFov.Value);
        private float MaxFov() => Mathf.Max(_minFov.Value, _maxFov.Value);

        // ------------------------------------------------------------------
        // Alignment tool
        // ------------------------------------------------------------------

        private void HandleAlignmentKeys()
        {
            bool eye = Input.GetKey(KeyCode.LeftShift) || Input.GetKey(KeyCode.RightShift);
            float step = _alignStep;
            bool changed = false;

            if (Input.GetKeyDown(KeyCode.KeypadPlus)) { _alignStep = Mathf.Min(0.5f, _alignStep * 2f); SWLogger.LogInfo($"IVA align: step {_alignStep:F3} m"); }
            if (Input.GetKeyDown(KeyCode.KeypadMinus)) { _alignStep = Mathf.Max(0.005f, _alignStep * 0.5f); SWLogger.LogInfo($"IVA align: step {_alignStep:F3} m"); }

            ConfigValue<float> x = eye ? _eyeX : _offX, y = eye ? _eyeY : _offY, z = eye ? _eyeZ : _offZ;
            if (Input.GetKeyDown(KeyCode.Keypad8)) { z.Value += step; changed = true; }
            if (Input.GetKeyDown(KeyCode.Keypad2)) { z.Value -= step; changed = true; }
            if (Input.GetKeyDown(KeyCode.Keypad6)) { x.Value += step; changed = true; }
            if (Input.GetKeyDown(KeyCode.Keypad4)) { x.Value -= step; changed = true; }
            if (Input.GetKeyDown(KeyCode.Keypad9)) { y.Value += step; changed = true; }
            if (Input.GetKeyDown(KeyCode.Keypad3)) { y.Value -= step; changed = true; }
            if (!eye && Input.GetKeyDown(KeyCode.Keypad7)) { _yaw.Value = WrapAngle(_yaw.Value - step * 250f); changed = true; }
            if (!eye && Input.GetKeyDown(KeyCode.Keypad1)) { _yaw.Value = WrapAngle(_yaw.Value + step * 250f); changed = true; }
            if (!eye && Input.GetKeyDown(KeyCode.KeypadMultiply)) { _scale.Value = Mathf.Clamp(_scale.Value * (1f + step), 0.5f, 2f); changed = true; }
            if (!eye && Input.GetKeyDown(KeyCode.KeypadDivide)) { _scale.Value = Mathf.Clamp(_scale.Value / (1f + step), 0.5f, 2f); changed = true; }

            if (Input.GetKeyDown(KeyCode.Keypad0))
            {
                if (eye) { _eyeX.Value = 0f; _eyeY.Value = 0f; _eyeZ.Value = 0f; }
                else { _offX.Value = 0f; _offY.Value = 0f; _offZ.Value = 0f; _yaw.Value = 0f; _scale.Value = 1f; }
                changed = true;
            }

            if (changed)
                SWLogger.LogInfo($"IVA align: offset ({_offX.Value:F3}, {_offY.Value:F3}, {_offZ.Value:F3}) yaw {_yaw.Value:F1} scale {_scale.Value:F3}, " +
                                 $"eye ({_eyeX.Value:F3}, {_eyeY.Value:F3}, {_eyeZ.Value:F3})");

            if (Input.GetKeyDown(KeyCode.Keypad5))
            {
                try { SWConfiguration.Save(); SWLogger.LogInfo("IVA align: saved to config."); }
                catch (Exception e) { SWLogger.LogWarning("IVA align: couldn't save config: " + e.Message); }
            }
        }

        private static float WrapAngle(float a) => Mathf.Repeat(a + 180f, 360f) - 180f;

        // ------------------------------------------------------------------
        // Entering, leaving and switching seats
        // ------------------------------------------------------------------

        private void EnterIva() => EnterIva(null);

        private void EnterIva(PodInfo forced)
        {
            if (!FindFlightCamera()) return;

            if (_useCustomInterior.Value)
            {
                PodInfo pod = forced ?? PodLocator.FindPod(Game, (_podNameFilter.Value ?? "").Trim(), SWLogger);
                if (pod != null)
                {
                    InteriorDesign design = InteriorCatalogue.ForPod(pod.Name, pod.Seats, _anyPod.Value);
                    if (design != null)
                    {
                        StartLoad(pod, design);
                        return; // finishes in OnInteriorLoaded
                    }
                    SWLogger.LogInfo($"IVA: no interior for {pod.Name} yet (turn on 'Use for pods without their own interior' to borrow one).");
                    if (_poseDump.Value) CustomInteriorSession.CapturePoses(pod, SWLogger);
                }
            }

            EnterPortraitMode();
        }

        private void StartLoad(PodInfo pod, InteriorDesign design)
        {
            GameObject cached;
            if (_prefabCache.TryGetValue(design.Address, out cached) && cached != null)
            {
                FinishLoad(pod, design, cached);
                return;
            }

            _loading = true;
            _loadingFor = pod;
            SWLogger.LogInfo($"IVA: loading interior '{design.Address}'...");
            try
            {
                Assets.Load<GameObject>(design.Address, prefab => OnInteriorLoaded(pod, design, prefab), false);
            }
            catch (Exception e)
            {
                _loading = false;
                SWLogger.LogWarning($"IVA: couldn't start loading '{design.Address}': {e.Message}");
                EnterPortraitMode();
            }
        }

        private void OnInteriorLoaded(PodInfo pod, InteriorDesign design, GameObject prefab)
        {
            if (!_loading || _loadingFor != pod) return; // cancelled or superseded
            _loading = false;
            _loadingFor = null;

            if (prefab == null)
            {
                SWLogger.LogWarning($"IVA: couldn't load '{design.Address}'. Was 'IVA > Set Up Interiors' run before building the mod?");
                EnterPortraitMode();
                return;
            }
            _prefabCache[design.Address] = prefab;

            // The player may have left flight or switched vessel while it loaded.
            if (!IsInFlight() || pod.Pod == null || PodLocator.ActiveVessel(Game) == null) return;
            FinishLoad(pod, design, prefab);
        }

        private void FinishLoad(PodInfo pod, InteriorDesign design, GameObject prefab)
        {
            CustomInteriorSession session = null;
            try { session = CustomInteriorSession.Create(pod, design, prefab, Placement(), SWLogger, dumpPoses: _poseDump.Value); }
            catch (Exception e) { SWLogger.LogError("IVA: failed to place the interior: " + e); }

            if (session == null || !session.IsValid)
            {
                if (session != null) session.End();
                SWLogger.LogWarning("IVA: the interior has no seat points (IVA_Seat*), so falling back to the portrait view.");
                EnterPortraitMode();
                return;
            }

            SaveFlightCamera();
            ResetView();
            _session = session;
            _interact = null;
            if (_session.Root != null)
            {
                try { _interact = Interact.Build(_session.Root.gameObject, _session.PodTransform, SWLogger); }
                catch (Exception e) { SWLogger.LogError("IVA: couldn't set up the cabin's interactive parts: " + e); }
            }
            _vesselAtEntry = PodLocator.ActiveVessel(Game);
            _seatIndex = 0;
            _mode = Mode.CustomInterior;
            if (_hideExterior.Value || design.HideExterior) _session.HidePodExterior();
            FindCompanionsAndReport();
            StartCameraGuard();
            TryStartShotOverride();
            ApplyPose();
            if (_cabinAo.Value) CabinAo.Begin(_flightCam, _cabinAoStrength.Value, SWLogger);
            _session.ShowSeat(_seatIndex, _hideOwnKerbal.Value, SWLogger);
            if (_soundOn.Value)
            {
                _sounds = Sounds.Create(_session.Pod, _soundSource, SWLogger);
                if (_sounds.Valid)
                {
                    _sounds.SetVolume(_soundVolume.Value);
                    if (_flightCam != null) _sounds.Place(_flightCam.transform);
                    _sounds.StartAmbience(_ambience.Value);
                }
                else _sounds = null;
            }
            if (_interact != null) _interact.Sounds = _sounds;
            SetUpHatches(pod);
            SWLogger.LogInfo($"Entered IVA ({design.Name} interior), seat 1 of {session.SeatCount}" +
                             (session.UsesGameEyes ? ", at the game's kerbal eye point." : ", at the interior's seat point."));
            if (_arrival != null && _arrival.To != null && _arrival.To.Pod == pod.Pod) Arrive();
        }

        // Pods without an interior of ours: hand over to Redux's own first-person camera. The old portrait-camera view
        // moved the flight camera to the crew portrait booth, and the game's camera rig then crashed in its terrain
        // raycast (native crash in TerrainHeightSampler from BasicCameraRigSolution.DoesCameraCollide).
        private void EnterPortraitMode()
        {
            try
            {
                UniverseCameraManager cm = Game?.CameraManager;
                if (cm != null && cm.SelectNextFirstPersonCameraTarget())
                {
                    _mode = Mode.Native;
                    SWLogger.LogInfo("Entered IVA (Redux first-person camera; no interior for this pod yet).");
                    return;
                }
            }
            catch (Exception e) { SWLogger.LogWarning("IVA: Redux first-person camera unavailable: " + e.Message); }
            SWLogger.LogInfo("IVA: no interior for this pod and no first-person camera available; staying in the normal view.");
        }

        private void EnterLegacyPortraitMode()
        {
            if (!FindKerbalCams()) return;
            SaveFlightCamera();
            ResetView();
            if (_seatIndex >= _kerbalCams.Count) _seatIndex = 0;
            _seatCam = _kerbalCams[_seatIndex];
            _mode = Mode.Portrait;
            AttachToPortraitSeat();
            SWLogger.LogInfo($"Entered IVA (portrait camera), seat {_seatIndex + 1} of {_kerbalCams.Count}.");
        }

        // Starts a glide from wherever the camera is now (including where the player was looking).
        private void BeginGlide()
        {
            if (_session == null || _session.PodTransform == null || _flightCam == null) { _blend = 1f; return; }
            Transform pod = _session.PodTransform;
            _fromPos = pod.InverseTransformPoint(_flightCam.transform.position);
            _fromRot = Quaternion.Inverse(pod.rotation) * _flightCam.transform.rotation;
            _fromFov = _flightCam.fieldOfView;
            _blend = 0f;
            _yawLook = 0f;
            _pitch = 0f;
        }

        // Seat -> nearest window -> next nearest ... -> back to the seat.
        private void NextWindow()
        {
            if (_session == null || _session.Views.Count == 0)
            {
                SWLogger.LogInfo("IVA: this interior has no window views.");
                return;
            }
            Vector3 eye;
            Quaternion r;
            if (!_session.TryGetPose(_seatIndex, -1, EyeOffset(), out eye, out r)) return;
            Transform pod = _session.PodTransform;
            List<int> order = Enumerable.Range(0, _session.Views.Count)
                .OrderBy(i => (pod.InverseTransformPoint(_session.Views[i].Key.position) - eye).sqrMagnitude).ToList();
            int at = order.IndexOf(_viewIndex);
            int next = at + 1 < order.Count ? order[at + 1] : -1;
            BeginGlide();
            if (_viewIndex < 0) _seatFov = _fov;
            _viewIndex = next;
            _fov = next >= 0 ? Mathf.Clamp(_windowFov.Value, MinFov(), MaxFov()) : _seatFov;
            SWLogger.LogInfo(next >= 0 ? $"IVA: window view {_session.ViewNames[next]}." : "IVA: back to the seat.");
        }

        private void ResetView()
        {
            _viewIndex = -1;
            _blend = 1f;
            _yawLook = 0f;
            _pitch = 0f;
            _fov = Mathf.Clamp(_defaultFov.Value, MinFov(), MaxFov());
        }

        // Cameras that move with the flight camera (children, or siblings sitting on it). If the game draws some layers
        // with a second camera, it must get our field of view, near clip and pose too, or what it draws won't line up.
        private class Companion { public Camera Cam; public bool Child; public float Fov, Near; public Vector3 LocalPos; public Quaternion LocalRot; }
        private readonly List<Companion> _companions = new List<Companion>();

        private static string Layers(int mask)
        {
            var names = new List<string>();
            for (int i = 0; i < 32; i++)
                if ((mask & (1 << i)) != 0) { string n = LayerMask.LayerToName(i); names.Add(string.IsNullOrEmpty(n) ? i.ToString() : $"{i}:{n}"); }
            return names.Count == 32 ? "everything" : string.Join(",", names);
        }

        private void FindCompanionsAndReport()
        {
            _companions.Clear();
            Transform ft = _flightCam.transform;
            var lines = new List<string>();
            foreach (Camera c in FindObjectsByType<Camera>())
            {
                if (c == null || !c.enabled || !c.gameObject.activeInHierarchy) continue;
                bool child = c != _flightCam && c.transform.IsChildOf(ft);
                bool onIt = c != _flightCam && !child && Vector3.Distance(c.transform.position, ft.position) < 0.05f;
                string role = c == _flightCam ? "FLIGHT" : child ? "child" : onIt ? "co-located" : "other";
                lines.Add($"{role} '{c.name}' depth {c.depth} clear {c.clearFlags} near {c.nearClipPlane:F2} far {c.farClipPlane:F0} fov {c.fieldOfView:F0} layers [{Layers(c.cullingMask)}]");
                if (child || onIt)
                    _companions.Add(new Companion { Cam = c, Child = child, Fov = c.fieldOfView, Near = c.nearClipPlane, LocalPos = c.transform.localPosition, LocalRot = c.transform.localRotation });
            }
            if (_debugLog.Value) SWLogger.LogInfo("IVA: cameras: " + string.Join(" | ", lines));
            if (_session != null && _session.PodTransform != null)
            {
                Vector3 c0 = _session.PodTransform.position;
                var byLayer = FindObjectsByType<Renderer>()
                    .Where(r => r != null && r.enabled && Vector3.Distance(r.bounds.center, c0) < 4f)
                    .GroupBy(r => r.gameObject.layer)
                    .Select(g => $"{g.Key}:{LayerMask.LayerToName(g.Key)} x{g.Count()} ({string.Join(", ", g.Take(6).Select(r => r.name))})");
                SWLogger.LogInfo("IVA: renderers within 4 m of the pod by layer: " + string.Join(" | ", byLayer));
            }
        }

        // The game's "Close Vessel" camera: in camera modes that want a near clip under 0.2 m it moves every vessel part
        // onto the characters layer for one frame and draws them after clearing depth, i.e. on top of everything the
        // main camera drew - straight through our interior. In IVA the main camera already draws parts and kerbals with
        // proper depth, so keep that camera and its layer swap off (the game turns them back on as it needs after IVA).
        private const string CloseVesselCameraName = "[PhysicsSpace] FlightCamera Close Vessel";
        private bool _closeVesselLogged;

        private void SuppressCloseVesselCamera()
        {
            if (_flightCam == null) return;
            Transform t = _flightCam.transform.Find(CloseVesselCameraName);
            if (t == null) return;
            Camera c = t.GetComponent<Camera>();
            bool was = c != null && c.enabled;
            if (c != null) c.enabled = false;
            foreach (MonoBehaviour mb in t.GetComponents<MonoBehaviour>())
                if (mb != null && mb.enabled && mb.GetType().Name == "CloseVesselLayerScope") mb.enabled = false;   // OnDisable restores the layers
            if (was && !_closeVesselLogged)
            {
                _closeVesselLogged = true;
                SWLogger.LogInfo("IVA: switched off the game's close-vessel camera (it draws parts over the interior in some camera modes).");
            }
        }

        // The distant world (planets, Mun, stars) is drawn first by the scaled-space camera. The game turns it from the
        // same simulation rotation as the main camera, converted into scaled space. Do the same with the IVA view, or the
        // sky stays put while the cabin turns round it (the Mun showing in several windows).
        private const string ScaledCameraName = "FlightCameraScaled_Main";
        private Camera _scaledCam;
        private Quaternion _scaledLocalRot;
        private bool _scaledSaved, _scaledFailed;

        private void SyncScaledCamera()
        {
            if (_scaledFailed || _flightCam == null) return;
            try
            {
                if (_scaledCam == null)
                {
                    _scaledCam = FindObjectsByType<Camera>().FirstOrDefault(c => c != null && c.name == ScaledCameraName);
                    if (_scaledCam == null) return;
                }
                if (!_scaledSaved) { _scaledLocalRot = _scaledCam.transform.localRotation; _scaledSaved = true; }
                var uv = Game?.UniverseView;
                if (uv == null || uv.PhysicsSpace == null || uv.ScaledSpace == null) return;
                Quaternion q = _flightCam.transform.rotation;
                var sim = uv.PhysicsSpace.PhysicsToRotation(new QuaternionD(q.x, q.y, q.z, q.w));
                QuaternionD s = uv.ScaledSpace.RotationToScaled(sim);
                _scaledCam.transform.rotation = new Quaternion((float)s.x, (float)s.y, (float)s.z, (float)s.w);
                _scaledCam.fieldOfView = _flightCam.fieldOfView;
            }
            catch (Exception e)
            {
                _scaledFailed = true;
                SWLogger.LogError("IVA: couldn't turn the scaled-space camera with the view: " + e.Message);
            }
        }

        private void RestoreScaledCamera()
        {
            if (_scaledCam != null && _scaledSaved) _scaledCam.transform.localRotation = _scaledLocalRot;
            _scaledSaved = false;
        }

        private void SyncCompanions(float fov, float near)
        {
            SuppressCloseVesselCamera();
            foreach (Companion c in _companions)
            {
                if (c.Cam == null || c.Cam.name == CloseVesselCameraName) continue;
                c.Cam.fieldOfView = fov;
                c.Cam.nearClipPlane = near;
                if (!c.Child) c.Cam.transform.SetPositionAndRotation(_flightCam.transform.position, _flightCam.transform.rotation);
            }
        }

        private void RestoreCompanions()
        {
            _closeVesselLogged = false;
            foreach (Companion c in _companions)
            {
                if (c.Cam == null) continue;
                c.Cam.fieldOfView = c.Fov;
                c.Cam.nearClipPlane = c.Near;
                if (!c.Child) { c.Cam.transform.localPosition = c.LocalPos; c.Cam.transform.localRotation = c.LocalRot; }
            }
            _companions.Clear();
        }

        private void SaveFlightCamera()
        {
            Transform t = _flightCam.transform;
            _origParent = t.parent;
            _origLocalPos = t.localPosition;
            _origLocalRot = t.localRotation;
            _origFov = _flightCam.fieldOfView;
            _origNearClip = _flightCam.nearClipPlane;
        }

        private void ExitIva()
        {
            CabinAo.End();
            _free = null;
            _interact?.Reset();
            _interact = null;
            _doorBoxes.Clear();
            _sounds?.End();
            _sounds = null;
            LockFlightInput(false);
            _loading = false;
            _loadingFor = null;
            ShowPortraitBody();

            StopShotOverride();
            StopCameraGuard();
            RestoreCompanions();
            RestoreScaledCamera();
            _exitPod = _session != null ? _session.PodTransform : null;
            if (_session != null)
            {
                _session.End();
                _session = null;
            }

            if (_mode == Mode.Native)
            {
                try { if (Game?.CameraManager != null && Game.CameraManager.IsFirstPersonCameraActive) Game.CameraManager.ExitFirstPersonCamera(true); }
                catch (Exception e) { SWLogger.LogWarning("IVA: leaving the first-person camera failed: " + e.Message); }
            }
            else if (_flightCam != null && _mode != Mode.None)
            {
                _origParentAtExit = _origParent;
                _exitLocalPos = _origLocalPos;
                _exitLocalRot = _origLocalRot;
                _exitCheckAt = Time.unscaledTime + 0.5f;
                Transform t = _flightCam.transform;
                // If the original parent was destroyed (vessel change), leave the camera unparented
                // and let the game's camera code pick it up again.
                t.SetParent(_origParent != null ? _origParent : null, false);
                t.localPosition = _origLocalPos;
                t.localRotation = _origLocalRot;
                _flightCam.fieldOfView = _origFov > 0f ? _origFov : 60f;
                _flightCam.nearClipPlane = _origNearClip > 0f ? _origNearClip : 0.3f;
            }

            bool was = InIva;
            _mode = Mode.None;
            _seatCam = null;
            _vesselAtEntry = null;
            _origParent = null;
            if (was) SWLogger.LogInfo("Left IVA.");
        }

        // ------------------------------------------------------------------
        // Unbuckled: floating round the cabin
        // ------------------------------------------------------------------

        private void Unbuckle()
        {
            if (_session == null || _session.Root == null || _session.PodTransform == null) return;
            FreeMove f = FreeMove.Build(_session.Root, _session.PodTransform, SWLogger);
            if (!f.Valid) return;
            bool heavy = FeltGravity(out Vector3 upPod, out float g, out string why);
            int floor = heavy ? f.FloorFor(upPod) : -1;
            SWLogger.LogInfo($"IVA: gravity {why}; {(heavy ? floor >= 0 ? $"walking on floor {floor}" : "no floor faces up" : "floating")}.");
            if (heavy && floor < 0)
            {
                Toast("No floor to stand on here");
                return;
            }
            if (!ComputeIvaPose(out Vector3 posW, out Quaternion rotW, out float _)) return;
            Transform pod = _session.PodTransform;
            f.Begin(pod.InverseTransformPoint(posW), Quaternion.Inverse(pod.rotation) * rotW);
            if (_viewIndex >= 0) _fov = _seatFov;
            _viewIndex = -1;
            _blend = 1f;
            _yawLook = 0f;
            _pitch = 0f;
            _free = f;
            if (heavy) f.SetWalking(true, upPod, g);
            _doorBoxes.Clear();
            if (_interact?.Doors != null)
                foreach (Doors.Door d in _interact.Doors.All)
                    if (d.IsRoomDoor && !d.Name.StartsWith("DoorHatch", StringComparison.Ordinal))
                    {
                        _doorBoxes[d] = f.AddDoor(d.CentrePod, d.EdgePod * 0.5f, d.AxisPod.normalized * d.HalfHeight, d.OutPod * 0.02f);
                    }
            _session.HideWholeKerbal(_seatIndex);   // you've left the couch
            LockFlightInput(true);                  // WASD, Shift and Ctrl move you, not the vessel
            _sounds?.Play(Sounds.Unbuckle);
            SWLogger.LogInfo($"IVA: unbuckled from seat {_seatIndex + 1}.");
        }

        private void Buckle()
        {
            if (_free == null || _session == null) return;
            int best = _seatIndex;
            float bestD = float.MaxValue;
            for (int i = 0; i < _session.SeatCount; i++)
            {
                if (!_session.TryGetPose(i, -1, EyeOffset(), out Vector3 eye, out Quaternion _)) continue;
                float d = (eye - _free.Pos).sqrMagnitude;
                if (d < bestD) { bestD = d; best = i; }
            }
            BeginGlide();   // from where you are now
            _free = null;
            _sounds?.SetThrust(false);
            _sounds?.Play(Sounds.Buckle);
            _seatIndex = best;
            _viewIndex = -1;
            _session.ShowSeat(_seatIndex, _hideOwnKerbal.Value, SWLogger);
            LockFlightInput(false);
            SWLogger.LogInfo($"IVA: buckled into seat {_seatIndex + 1}.");
        }

        // Gravity you'd feel standing in the pod: only when landed, splashed or on the pad (in flight you float, thrust or
        // not). up: pod space, opposite to the pull. why: for the log.
        private bool FeltGravity(out Vector3 up, out float g, out string why)
        {
            up = Vector3.up;
            g = 0f;
            why = "unknown";
            try
            {
                VesselComponent v = _vesselAtEntry != null ? _vesselAtEntry.Model : null;
                var space = Game?.UniverseView?.PhysicsSpace;
                if (v == null || space == null || _session?.PodTransform == null) { why = "no vessel"; return false; }
                bool landed = v.LandedOrSplashed || v.Situation == VesselSituations.PreLaunch;
                Vector3 gW = (Vector3)space.VectorToPhysics(v.gravityForPos);
                g = gW.magnitude;
                if (g > 1e-4f) up = _session.PodTransform.InverseTransformDirection(-gW).normalized;
                why = $"{g:F2} m/s2 ({g / 9.81f:F3} g), up (pod) {up.ToString("F2")}, {v.Situation}{(landed ? ", landed" : "")}";
                return landed && g > 0.3f;
            }
            catch (Exception e) { why = "error: " + e.Message; return false; }
        }

        private void Toast(string text, float secs = 3f)
        {
            _toast = text;
            _toastUntil = Time.unscaledTime + secs;
            SWLogger.LogInfo("IVA: " + text + ".");
        }

        private void MoveFree()
        {
            float dt = Time.timeScale > 0f ? Time.unscaledDeltaTime : 0f;   // hold still while paused
            float K(KeyCode k) => Input.GetKey(k) ? 1f : 0f;
            bool heavy = FeltGravity(out Vector3 upPod, out float g, out string why) && _free.FloorFor(upPod) >= 0;
            if (heavy != _free.Walking)
            {
                _free.SetWalking(heavy, upPod, g);
                SWLogger.LogInfo($"IVA: {(heavy ? "walking" : "floating")} now (gravity {why}).");
            }
            if (_free.Walking)
            {
                _free.SetWalking(true, upPod, g);   // follow slow changes (the vessel settling)
                var walk = new Vector2(K(KeyCode.D) - K(KeyCode.A), K(KeyCode.W) - K(KeyCode.S));
                if (walk.sqrMagnitude > 1f) walk.Normalize();
                _free.StepWalk(walk, Input.GetKeyDown(KeyCode.Space), Input.GetKey(KeyCode.LeftControl), dt, _walkSpeed.Value);
                _sounds?.SetThrust(false);
                return;
            }
            var move = new Vector3(K(KeyCode.D) - K(KeyCode.A), K(KeyCode.LeftShift) - K(KeyCode.LeftControl), K(KeyCode.W) - K(KeyCode.S));
            if (move.sqrMagnitude > 1f) move.Normalize();
            float roll = K(KeyCode.Q) - K(KeyCode.E);
            _free.Turn(0f, 0f, roll * 70f * dt);
            float top = _floatSpeed.Value;
            _free.Step(move, dt, top * 2.5f, top, 2.5f);
            _sounds?.SetThrust(_thrusterSound.Value && dt > 0f && (move.sqrMagnitude > 0f || roll != 0f));
        }

        private void LockFlightInput(bool on)
        {
            if (on == _flightInputLocked) return;
            try
            {
                Game?.InputManager?.SetInputLock(on ? KSP.Input.InputLocks.FlightInputDisabled : KSP.Input.InputLocks.FlightInputEnabled);
                _flightInputLocked = on;
            }
            catch (Exception e) { SWLogger.LogWarning($"IVA: couldn't {(on ? "lock" : "unlock")} the flight controls: {e.Message}"); }
        }

        private Interact.Target Aimed() => _free != null && _interact != null ? _interact.Pick(_free.Pos, _free.Rot * Vector3.forward) : null;

        private void UseTarget()
        {
            Interact.Target t = Aimed();
            if (t == null) return;
            SWLogger.LogInfo($"IVA: {t.Prompt()} ({t.Name}).");
            t.Use();
        }

        private void OnGUI()
        {
            if (_promptStyle == null) _promptStyle = new GUIStyle(GUI.skin.label) { alignment = TextAnchor.MiddleCenter, fontSize = 18 };
            if (_audition.Value && _sounds != null)
                GUI.Label(new Rect(0f, Screen.height * 0.08f, Screen.width, 30f),
                          (_auditionIndex >= 0 ? $"[ / ]  sound {_auditionIndex + 1} of {Sounds.Audition.Length}: {Sounds.Audition[_auditionIndex]}" : "[ / ]  play a sound") +
                          $"     \\  source: {_sounds.Current}", _promptStyle);
            _fade.Draw();
            if (_toast != null && Time.unscaledTime < _toastUntil)
                GUI.Label(new Rect(0f, Screen.height * 0.55f, Screen.width, 30f), _toast, _promptStyle);
            if (_free == null) return;
            // a small dot where you're looking
            GUI.Label(new Rect(Screen.width / 2f - 10f, Screen.height / 2f - 15f, 20f, 30f), "\u00b7", _dotStyle ?? (_dotStyle = new GUIStyle(_promptStyle) { fontSize = 28 }));
            string text = null;
            Interact.Target t = Aimed();
            if (t != null) text = $"{_doorKey.Value}: {t.Prompt()}";
            if (text != null) GUI.Label(new Rect(0f, Screen.height * 0.62f, Screen.width, 30f), text, _promptStyle);
        }

        // ------------------------------------------------------------------
        // Hatches: into the next module, or out on EVA
        // ------------------------------------------------------------------

        private KSP.Game.KerbalInfo Me()
        {
            if (_session == null || _seatIndex < 0 || _seatIndex >= _session.EyeKerbals.Count) return null;
            return _session.EyeKerbals[_seatIndex]?.ThisKerbalInfo;
        }

        private void SetUpHatches(PodInfo pod)
        {
            _hatches = new List<Hatches.Hatch>();
            if (_session?.Root == null || _interact == null) return;
            try
            {
                _hatches = Hatches.Find(_session.Root, pod, Game, _anyPod.Value);
                _hasAirlock = Hatches.HasAirlock(_session.Pod);
            }
            catch (Exception e) { SWLogger.LogWarning("IVA: couldn't work out the hatches: " + e.Message); return; }
            bool hasSide = _hatches.Any(h => h.Name == "Side");
            foreach (Hatches.Hatch hatch in _hatches)
            {
                Hatches.Hatch h = hatch;
                bool eva = h.Outside && _hasAirlock && (h.Name == "Side" || !hasSide);
                _interact.Targets.Add(new Interact.Target
                {
                    Kind = "Hatch", Name = h.Name, Pod = h.Pod,
                    Prompt = () => !h.Outside ? (Hatches.FreeSeat(Game, h.Beyond.Pod) < 0 && Me() != null ? $"{h.Beyond.Name} is full" : $"go through to the {h.Beyond.Name}")
                                 : eva ? "go outside (EVA)" : "nothing on the other side of this hatch",
                    Use = () => UseHatch(h, eva),
                });
            }
            SWLogger.LogInfo("IVA: hatches: " + string.Join(", ", _hatches.Select(h => h.Name + (h.Outside ? (h.Name == "Side" || !hasSide) && _hasAirlock ? " (EVA)" : " (nothing beyond)" : " -> " + h.Beyond.Name))));
        }

        private void UseHatch(Hatches.Hatch h, bool eva)
        {
            KSP.Game.KerbalInfo me = Me();
            if (!h.Outside)
            {
                if (me != null && Hatches.FreeSeat(Game, h.Beyond.Pod) < 0) { SWLogger.LogInfo($"IVA: {h.Beyond.Name} is full."); return; }
                if (_interact != null) _interact.OpenHatch(h.Name, () => _hatchGo = h);   // wheel, lid, then through
                else _hatchGo = h;
                return;
            }
            if (!eva) return;
            if (me == null) { SWLogger.LogInfo("IVA: no kerbal of yours here to send outside."); return; }
            var pending = new PendingEva { Part = _session.Pod, Vessel = PodLocator.ActiveVessel(Game), Kerbal = me, At = Time.unscaledTime + 1.0f };
            ExitIva();
            _pendingEva = pending;
            SWLogger.LogInfo("IVA: leaving IVA; EVA in a moment.");
        }

        // The same call as the crew portrait's EVA button, once the normal flight camera is back.
        private void StartPendingEva()
        {
            PendingEva e = _pendingEva;
            _pendingEva = null;
            if (e.Part == null || e.Part.Model == null || PodLocator.ActiveVessel(Game) != e.Vessel)
            { SWLogger.LogInfo("IVA: EVA cancelled (the pod or vessel changed)."); return; }
            try
            {
                var vc = Game.ViewController;
                if (vc != null && (vc.TimeWarp.IsWarping || vc.IsPaused)) { SWLogger.LogInfo("IVA: EVA cancelled (time warp or paused)."); return; }
            }
            catch (Exception) { }
            if (KSP.EVAUtils.GetFirstLadderOrAirlockPhysicsSpacePosRot(e.Part, true, out Vector3 at, out Quaternion _))
                SWLogger.LogInfo($"IVA: EVA spawn point {e.Part.transform.InverseTransformPoint(at):F2} (pod space).");
            bool started = Hatches.StartEva(e.Part, e.Kerbal, SWLogger);
            if (started && _backAfterBoarding.Value) { ForgetBoarding(); _boardWatch = e.Kerbal; }
        }

        private readonly ScreenFade _fade = new ScreenFade();
        private Hatches.Hatch _fadeHatch;
        private bool _fadeHold;
        private ConfigValue<bool> _backAfterBoarding;
        private KSP.Game.KerbalInfo _boardWatch;
        private KSP.Game.KerbalInfo _boardSeatFor;
        private bool _boardSawEva;
        private float _boardReadyAt = -1f;
        private float _boardMissingFor;
        private float _boardNotFlightFor;

        private void BeginHatchFade(Hatches.Hatch h)
        {
            if (h.Beyond?.Pod == null || _fadeHatch != null || _fadeHold || _fade.Alpha > 0f) return;
            _fadeHatch = h;
            _fade.FadeOut();
        }

        private void TickHatchFade()
        {
            try
            {
                _fade.Tick();
                if (_fadeHatch != null)
                {
                    if (!InIva || !IsInFlight()) { _fadeHatch = null; _fade.FadeIn(); return; }
                    if (!_fade.IsBlack) return;
                    Hatches.Hatch h = _fadeHatch;
                    _fadeHatch = null;
                    _fadeHold = true;
                    GoThrough(h);
                    return;
                }
                if (_fadeHold && (!_fade.IsBlack || (_arrival == null && !_loading)))
                {
                    _fadeHold = false;
                    _fade.FadeIn();
                }
            }
            catch (Exception e)
            {
                _fadeHatch = null;
                _fadeHold = false;
                _fade.FadeIn();
                SWLogger.LogError("IVA: hatch fade failed: " + e);
            }
        }

        private void ForgetBoarding()
        {
            _boardWatch = null;
            _boardSawEva = false;
            _boardReadyAt = -1f;
            _boardMissingFor = 0f;
            _boardNotFlightFor = 0f;
        }

        private PodInfo BoardedPod()
        {
            var roster = Hatches.Roster(Game);
            if (roster == null || !roster.TryGetKerbalByID(_boardWatch.Id, out KSP.Game.KerbalInfo info) || info == null) return null;
            foreach (PodInfo p in PodLocator.FindAll(Game, _anyPod.Value))
                if (p.Pod != null && p.Pod.Model != null && p.Pod.Model.GlobalId == info.Location.SimObjectId) return p;
            return null;
        }

        // Polled from TickBoarding: the session only exists once the interior has loaded.
        private void PutInBoardedSeat()
        {
            if (_loading) return;
            KSP.Game.KerbalInfo k = _boardSeatFor;
            _boardSeatFor = null;
            if (!InIva || _session == null) return;
            for (int i = 0; i < _session.EyeKerbals.Count; i++)
            {
                var seat = _session.EyeKerbals[i]?.ThisKerbalInfo;
                if (seat != null && seat.Id == k.Id)
                {
                    _seatIndex = i;
                    _session.ShowSeat(i, _hideOwnKerbal.Value, SWLogger);
                    break;
                }
            }
        }

        private void TickBoarding()
        {
            if (_boardWatch == null && _boardSeatFor == null) return;
            try
            {
                if (_boardSeatFor != null) { PutInBoardedSeat(); return; }
                if (_toggleKey.Value.Down) { ForgetBoarding(); return; }
                if (!IsInFlight())
                {
                    _boardNotFlightFor += Time.unscaledDeltaTime;
                    if (_boardNotFlightFor > LeaveAfterSeconds) ForgetBoarding();
                    return;
                }
                _boardNotFlightFor = 0f;
                if (InIva || _loading) return;
                KSP.Sim.impl.VesselComponent v = Game.ViewController?.GetActiveSimVessel(true);
                if (v == null) return;
                if (v.IsKerbalEVA) { _boardSawEva = true; _boardReadyAt = -1f; _boardMissingFor = 0f; return; }
                if (!_boardSawEva) return;
                PodInfo pod = BoardedPod();
                if (pod == null)
                {
                    // the 1 s lets Location catch up with the vessel change
                    _boardReadyAt = -1f;
                    _boardMissingFor += Time.unscaledDeltaTime;
                    if (_boardMissingFor > 1f) ForgetBoarding();
                    return;
                }
                _boardMissingFor = 0f;
                if (_boardReadyAt < 0f) { _boardReadyAt = Time.unscaledTime + 2f; return; }
                if (Time.unscaledTime < _boardReadyAt) return;
                KSP.Game.KerbalInfo k = _boardWatch;
                SWLogger.LogInfo($"IVA: boarded, back into IVA ({PodLocator.PartName(pod.Pod)}).");
                ForgetBoarding();
                _boardSeatFor = k;
                EnterIva(pod);
            }
            catch (Exception e)
            {
                ForgetBoarding();
                _boardSeatFor = null;
                SWLogger.LogError("IVA: boarding watch failed: " + e);
            }
        }

        private void GoThrough(Hatches.Hatch h)
        {
            if (_session == null || h.Beyond?.Pod == null) return;
            KSP.Game.KerbalInfo me = Me();
            if (me != null && !Hatches.Transfer(Game, me, h.Beyond.Pod, SWLogger)) return;
            var a = new Arrival { To = h.Beyond, From = _session.Pod, FromWorld = _session.PodTransform.position, Kerbal = me, At = Time.unscaledTime + 0.3f };
            ExitIva();
            _arrival = a;
        }

        // Just through the hatch from the part you came from: floating inside it, facing into the cabin.
        private void Arrive()
        {
            Arrival a = _arrival;
            _arrival = null;
            if (_session == null) return;
            for (int i = 0; i < _session.EyeKerbals.Count; i++)
                if (a.Kerbal != null && _session.EyeKerbals[i]?.ThisKerbalInfo == a.Kerbal) { _seatIndex = i; _session.ShowSeat(i, _hideOwnKerbal.Value, SWLogger); break; }
            Unbuckle();
            if (_free == null || _hatches.Count == 0) return;
            Transform pod = _session.PodTransform;
            // the hatch that faces the part you came from (side hatches only if there's nothing else). The part's position
            // is read now: a world position saved before the move is stale by the time the next interior has loaded (in
            // orbit the vessel travels hundreds of metres), and then picked the hatch facing the direction of travel.
            Vector3 fromNow = a.From != null ? a.From.transform.position : a.FromWorld;
            Vector3 toFrom = fromNow - pod.position;
            Hatches.Hatch h = _hatches.OrderBy(x => (x.Name == "Side" ? 1000f : 0f) + Vector3.Angle(Hatches.Facing(x.Name, pod.TransformPoint(x.Pod), pod), toFrom)).First();
            Vector3 dir = (_free.Middle - h.Pod).normalized;
            Vector3 up = Vector3.ProjectOnPlane(Vector3.forward, dir);
            if (up.sqrMagnitude < 0.01f) up = Vector3.ProjectOnPlane(Vector3.up, dir);
            _free.Begin(h.Pod + dir * 0.35f, Quaternion.LookRotation(dir, up.normalized));
            _sounds?.Play(Sounds.HatchClose);
            SWLogger.LogInfo($"IVA: came through the {h.Name} hatch (from {(a.From != null ? PodLocator.PartName(a.From) : "?")}).");
        }

        private void NextSeat()
        {
            if (_mode == Mode.Native)
            {
                try { Game?.CameraManager?.SelectNextFirstPersonCameraTarget(); } catch (Exception) { }
                return;
            }
            if (_mode == Mode.CustomInterior)
            {
                // after the last seat, on to the next crewed part with an interior (command pod, cabins, labs...)
                if (_seatIndex >= _session.SeatCount - 1)
                {
                    List<PodInfo> parts = PodLocator.FindAll(Game, _anyPod.Value);
                    if (parts.Count > 1)
                    {
                        int at = parts.FindIndex(p => p.Pod == _session.Pod);
                        PodInfo next = parts[(at + 1) % parts.Count];
                        SWLogger.LogInfo($"IVA: next part: {next.Name}.");
                        ExitIva();
                        EnterIva(next);
                        return;
                    }
                }
                if (_session.SeatCount < 2) { SWLogger.LogInfo($"IVA: only {_session.SeatCount} seat(s) here."); return; }
                BeginGlide();
                if (_viewIndex >= 0) _fov = _seatFov;
                _viewIndex = -1;
                _seatIndex = (_seatIndex + 1) % _session.SeatCount;
                _session.ShowSeat(_seatIndex, _hideOwnKerbal.Value, SWLogger);
                SWLogger.LogInfo($"Switched to seat {_seatIndex + 1} of {_session.SeatCount}.");
                return;
            }

            if (!FindKerbalCams()) { ExitIva(); return; }
            if (_kerbalCams.Count < 2) return;
            ShowPortraitBody();
            _seatIndex = (_kerbalCams.IndexOf(_seatCam) + 1) % _kerbalCams.Count;
            _seatCam = _kerbalCams[_seatIndex];
            _yawLook = 0f;
            _pitch = 0f;
            AttachToPortraitSeat();
            SWLogger.LogInfo($"Switched to seat {_seatIndex + 1} of {_kerbalCams.Count}.");
        }

        // ---- Portrait mode (original behaviour) ----

        private void AttachToPortraitSeat()
        {
            Transform head = _seatCam.transform.parent != null ? _seatCam.transform.parent : _seatCam.transform;
            _flightCam.transform.SetParent(head, false);
            ApplyPose();
            if (!_hideOwnKerbal.Value) return;

            Transform bone = PodLocator.FindChildRecursive(head, PodLocator.KerbalBodyBoneName);
            if (bone == null || bone.parent == null)
            {
                SWLogger.LogWarning($"Couldn't find '{PodLocator.KerbalBodyBoneName}' under the kerbal camera, so the body stays visible.");
                return;
            }
            // Scaling to zero rather than SetActive(false): the original author found deactivating it caused problems.
            _hiddenBody = bone.parent;
            _hiddenBodyScale = _hiddenBody.localScale;
            _hiddenBody.localScale = Vector3.zero;
        }

        private void ShowPortraitBody()
        {
            if (_hiddenBody != null) _hiddenBody.localScale = _hiddenBodyScale;
            _hiddenBody = null;
        }

        // ------------------------------------------------------------------
        // Finding cameras
        // ------------------------------------------------------------------

        private bool FindFlightCamera()
        {
            if (_flightCam != null) return true;
            Camera[] cameras = FindObjectsByType<Camera>();
            _flightCam = cameras.FirstOrDefault(c => c != null && c.name == FlightCameraName);
            if (_flightCam == null)
            {
                SWLogger.LogWarning($"IVA: couldn't find the flight camera '{FlightCameraName}'. Cameras in scene: {CameraNames(cameras)}");
                return false;
            }
            return true;
        }

        private bool FindKerbalCams()
        {
            _kerbalCams.Clear();
            Camera[] cameras = FindObjectsByType<Camera>();
            foreach (Camera c in cameras)
                if (c != null && c.name == PodLocator.KerbalCameraName) _kerbalCams.Add(c);

            if (_kerbalCams.Count == 0)
            {
                foreach (var kc in FindObjectsByType<KSP.UI.Flight.KerbalCamera>())
                {
                    Camera c = kc != null ? kc.GetComponent<Camera>() : null;
                    if (c != null && !_kerbalCams.Contains(c)) _kerbalCams.Add(c);
                }
            }

            _kerbalCams.Sort((a, b) => string.CompareOrdinal(PodLocator.HierarchyPath(a.transform, null), PodLocator.HierarchyPath(b.transform, null)));
            if (_kerbalCams.Count == 0)
            {
                SWLogger.LogInfo($"IVA: no crew cameras found (uncrewed vessel?). Cameras in scene: {CameraNames(cameras)}");
                return false;
            }
            return true;
        }

        private static string CameraNames(IEnumerable<Camera> cameras)
        {
            return string.Join(", ", cameras.Where(c => c != null).Select(c => c.name).Distinct());
        }
    }
}
