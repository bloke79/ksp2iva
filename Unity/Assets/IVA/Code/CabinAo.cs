// Screen-space ambient occlusion while inside a custom interior: darkens corners, panel seams and the gaps behind and
// under things, which a single cabin lamp and flat ambient light can't. Uses the game's own post-processing stack
// (PPv2): a temporary global volume on the flight camera's volume layer, removed again on leaving IVA.
using System;
using UnityEngine;
using UnityEngine.Rendering.PostProcessing;
using ILogger = ReduxLib.Logging.ILogger;

namespace IVA
{
    public static class CabinAo
    {
        private static PostProcessVolume _volume;

        public static bool Active => _volume != null;

        public static void Begin(Camera flightCam, float strength, ILogger log)
        {
            End();
            try
            {
                PostProcessLayer layer = flightCam != null ? flightCam.GetComponent<PostProcessLayer>() : null;
                if (layer == null)
                    foreach (Camera c in Camera.allCameras)   // the post-processing may sit on another flight camera
                    {
                        var l = c != null ? c.GetComponent<PostProcessLayer>() : null;
                        if (l != null && l.enabled) { layer = l; break; }
                    }
                if (layer == null) { log.LogInfo("IVA: no post-processing layer on the flight cameras; ambient occlusion stays off."); return; }
                int bits = layer.volumeLayer.value, lyr = -1;
                for (int i = 0; i < 32; i++) if ((bits & (1 << i)) != 0) { lyr = i; break; }
                if (lyr < 0) { log.LogInfo("IVA: the post-processing layer reads no volume layers; ambient occlusion stays off."); return; }

                var ao = ScriptableObject.CreateInstance<AmbientOcclusion>();
                ao.enabled.Override(true);
                ao.mode.Override(AmbientOcclusionMode.ScalableAmbientObscurance);
                ao.intensity.Override(Mathf.Clamp(strength, 0f, 2f));
                ao.radius.Override(0.25f);              // cabin scale: switches, seams, the gap behind a locker
                ao.quality.Override(AmbientOcclusionQuality.Medium);
                ao.color.Override(Color.black);
                ao.ambientOnly.Override(false);
                _volume = PostProcessManager.instance.QuickVolume(lyr, 100f, ao);
                _volume.name = "IVA_CabinAO";
                log.LogInfo($"IVA: ambient occlusion on (camera {layer.name}, volume layer {LayerMask.LayerToName(lyr)}, strength {strength:F2}).");
            }
            catch (Exception e)
            {
                log.LogWarning("IVA: couldn't turn on ambient occlusion: " + e.Message);
                End();
            }
        }

        public static void End()
        {
            if (_volume == null) return;
            try { RuntimeUtilities.DestroyVolume(_volume, true, true); }
            catch (Exception) { if (_volume != null) UnityEngine.Object.Destroy(_volume.gameObject); }
            _volume = null;
        }
    }
}
