// IVA for KSP2 Redux
// Started as a port of Mudkip909's "KSP2 Free IVA" (0.2.6, BepInEx/SpaceWarp 1); now ships its own
// modelled pod interiors (see CustomInterior.cs) with the real world visible through the windows.
//
// Press the toggle key (default C) in flight to sit inside your crew pod.
// Press the next-seat key (default V) while in IVA to move to the next seat.
// Mouse looks around, scroll wheel zooms. The numpad lines the interior up with the pod.
//
// Modes, tried in order:
//  1. Custom interior: a modelled interior shipped with the mod, placed inside the real pod.
//  2. Portrait camera: the original mod's behaviour, looking through a crew portrait camera.

using System;
using System.Collections.Generic;
using System.Linq;
using KSP.Game;
using KSP.Sim.impl;
using Redux.ExtraModTypes;
using ReduxLib.Configuration;
using ReduxLib.Input;
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

        private ConfigValue<float> _offX, _offY, _offZ, _yaw, _scale;
        private ConfigValue<float> _eyeX, _eyeY, _eyeZ;
        private ConfigValue<bool> _numpadAlign;

        private bool _ready;

        // ---- State ----
        private enum Mode { None, CustomInterior, Portrait }

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

        private bool InIva => _mode != Mode.None;

        public override void OnInitialized()
        {
            BindConfig();
            Camera.onPreCull += OnCameraPreCull;
            _ready = true;
            SWLogger.LogInfo($"IVA loaded. Toggle: {_toggleKey.Value}, next seat: {_nextSeatKey.Value}. " +
                             $"Interiors: {string.Join(", ", InteriorCatalogue.All.Select(d => d.Name))}.");
        }

        private void BindConfig()
        {
            var cfg = SWConfiguration;

            _toggleKey = Bind(cfg, "Keys", "Toggle IVA", new KeyboardShortcut(KeyCode.C), "Enter or leave IVA view while in flight.");
            _nextSeatKey = Bind(cfg, "Keys", "Next seat", new KeyboardShortcut(KeyCode.V), "Move to the next seat while in IVA.");

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

            _hideOwnKerbal = Bind(cfg, "General", "Hide own kerbal", true,
                "Portrait-camera view only: hide the kerbal you're looking through.");

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

            if (InIva && (!inFlight || !StillValid()))
            {
                ExitIva(); // scene change, map view, vessel switch, EVA, pod destroyed
                return;
            }
            if (!inFlight) { _loading = false; return; }

            if (_toggleKey.Value.Down)
            {
                if (InIva) ExitIva();
                else if (_loading) { _loading = false; _loadingFor = null; SWLogger.LogInfo("IVA: cancelled loading the interior."); }
                else EnterIva();
                return;
            }

            if (!InIva) return;
            if (_nextSeatKey.Value.Down) NextSeat();
            if (_mode == Mode.CustomInterior && _numpadAlign.Value) HandleAlignmentKeys();
            ReadLookInput();
        }

        private void LateUpdate()
        {
            if (InIva) ApplyPose();
        }

        // Applied again just before the flight camera renders, in case anything moved it after LateUpdate.
        private void OnCameraPreCull(Camera cam)
        {
            if (InIva && cam == _flightCam) ApplyPose();
        }

        private void ApplyPose()
        {
            if (_flightCam == null) return;
            Quaternion look = Quaternion.Euler(_pitch, _yawLook, 0f);

            if (_mode == Mode.CustomInterior)
            {
                if (_session == null) return;
                _session.ApplyPlacement(Placement());
                _session.ApplyCamera(_flightCam, _seatIndex, look, EyeOffset(), _fov, IvaNearClip);
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
                _yawLook = Mathf.Repeat(_yawLook + mx + 180f, 360f) - 180f;
                float maxPitch = _maxPitch.Value;
                _pitch = Mathf.Clamp(_pitch - my, -maxPitch, maxPitch);
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

        private void EnterIva()
        {
            if (!FindFlightCamera()) return;

            if (_useCustomInterior.Value)
            {
                PodInfo pod = PodLocator.FindPod(Game, (_podNameFilter.Value ?? "").Trim(), SWLogger);
                if (pod != null)
                {
                    InteriorDesign design = InteriorCatalogue.ForPod(pod.Seats, _anyPod.Value);
                    if (design != null)
                    {
                        StartLoad(pod, design);
                        return; // finishes in OnInteriorLoaded
                    }
                    SWLogger.LogInfo($"IVA: no interior for a {pod.Seats}-seat pod yet (turn on 'Use for pods without their own interior' to use the Mk1-3 one).");
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
            try { session = CustomInteriorSession.Create(pod, design, prefab, Placement(), SWLogger); }
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
            _vesselAtEntry = PodLocator.ActiveVessel(Game);
            _seatIndex = 0;
            _mode = Mode.CustomInterior;
            if (_hideExterior.Value) _session.HidePodExterior();
            ApplyPose();
            SWLogger.LogInfo($"Entered IVA ({design.Name} interior), seat 1 of {session.Seats.Count}.");
        }

        private void EnterPortraitMode()
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

        private void ResetView()
        {
            _yawLook = 0f;
            _pitch = 0f;
            _fov = Mathf.Clamp(_defaultFov.Value, MinFov(), MaxFov());
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
            _loading = false;
            _loadingFor = null;
            ShowPortraitBody();

            if (_session != null)
            {
                _session.End();
                _session = null;
            }

            if (_flightCam != null && _mode != Mode.None)
            {
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

        private void NextSeat()
        {
            if (_mode == Mode.CustomInterior)
            {
                if (_session.Seats.Count < 2) return;
                _seatIndex = (_seatIndex + 1) % _session.Seats.Count;
                _yawLook = 0f;
                _pitch = 0f;
                ApplyPose();
                SWLogger.LogInfo($"Switched to seat {_seatIndex + 1} of {_session.Seats.Count}.");
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
