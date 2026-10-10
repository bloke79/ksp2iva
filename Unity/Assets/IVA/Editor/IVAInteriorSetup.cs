// Unity editor menu: IVA > Set Up Interiors
//
// For every folder under Assets/IVA/Interiors that has a materials.json (written by the Blender
// export script), this:
//   1. marks normal-map textures as normal maps,
//   2. builds Standard-shader materials from the sheet (colour, metal, smoothness, textures, glow),
//   3. sets sensible import options on the model (no cameras, lights, animation or colliders),
//   4. makes a prefab with the materials applied and a cabin light,
//   5. registers the prefab in the IVA mod's addressable group under the address the mod loads.
//
// Safe to run again at any time; it updates what's already there.

using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.AddressableAssets;
using UnityEditor.AddressableAssets.Settings;
using UnityEngine;
using UnityEngine.Rendering;

namespace IVA.EditorTools
{
    public static class IVAInteriorSetup
    {
        private const string InteriorsRoot = "Assets/IVA/Interiors";
        private const string ModGroupName = "addressables_IVA_all";

        [Serializable]
        private class MatInfo
        {
            public string name;
            public float[] color;
            public float metallic;
            public float roughness;
            public float[] emission;
            public float emissionStrength;
            public string texture;
            public string normal;
            public float normalStrength = 1f;
            public float[] tiling;
            public bool emissionFromTexture;
        }

        [Serializable]
        private class Sheet
        {
            public string interior;
            public string address;
            public MatInfo[] materials;
            public float[] cabinLight;   // optional: x, y, z (Unity space, metres), range, intensity
            public float[] extraLights;  // optional: more lamps, 5 floats each as above (no shadows)
        }

        [MenuItem("IVA/Set Up Interiors")]
        public static void SetUpAll()
        {
            if (!AssetDatabase.IsValidFolder(InteriorsRoot))
            {
                EditorUtility.DisplayDialog("IVA", $"Couldn't find {InteriorsRoot}. Copy the Interiors folder from the IVA package into Assets/IVA first.", "OK");
                return;
            }

            var sheets = Directory.GetFiles(InteriorsRoot, "materials.json", SearchOption.AllDirectories)
                .Select(p => p.Replace('\\', '/')).ToList();
            if (sheets.Count == 0)
            {
                EditorUtility.DisplayDialog("IVA", "No interiors found (no materials.json under Assets/IVA/Interiors).", "OK");
                return;
            }

            var done = new List<string>();
            var problems = new List<string>();
            foreach (string sheetPath in sheets)
            {
                try
                {
                    string result = SetUpOne(sheetPath);
                    done.Add(result);
                }
                catch (Exception e)
                {
                    problems.Add($"{sheetPath}: {e.Message}");
                    Debug.LogException(e);
                }
            }

            AssetDatabase.SaveAssets();
            string msg = "Set up:\n" + string.Join("\n", done);
            if (problems.Count > 0) msg += "\n\nProblems:\n" + string.Join("\n", problems);
            msg += "\n\nNow run Assets/IVA/Pipelines/Build for Player.";
            Debug.Log("[IVA] " + msg);
            EditorUtility.DisplayDialog("IVA", msg, "OK");
        }

        private static string SetUpOne(string sheetPath)
        {
            string dir = Path.GetDirectoryName(sheetPath).Replace('\\', '/');
            var sheet = JsonUtility.FromJson<Sheet>(File.ReadAllText(sheetPath));
            if (sheet == null || string.IsNullOrEmpty(sheet.interior))
                throw new Exception("materials.json is missing the interior name.");

            // 1. Textures
            string texDir = dir + "/Textures";
            foreach (MatInfo m in sheet.materials)
            {
                if (!string.IsNullOrEmpty(m.normal)) SetTextureType(TexPath(texDir, m.normal), normalMap: true);
                if (!string.IsNullOrEmpty(m.texture)) SetTextureType(TexPath(texDir, m.texture), normalMap: false);
            }

            // 2. Materials
            string matDir = dir + "/Materials";
            if (!AssetDatabase.IsValidFolder(matDir)) AssetDatabase.CreateFolder(dir, "Materials");
            var materials = new Dictionary<string, Material>();
            // IVA/Interior: Standard lighting plus baked vertex AO and a dimmed indirect level (Assets/IVA/Shaders).
            Shader standard = Shader.Find("IVA/Interior") ?? Shader.Find("Standard");
            if (standard == null) throw new Exception("Neither IVA/Interior nor the Standard shader is available in this project.");
            foreach (MatInfo m in sheet.materials)
            {
                string path = $"{matDir}/{m.name}.mat";
                var mat = AssetDatabase.LoadAssetAtPath<Material>(path);
                if (mat == null)
                {
                    mat = new Material(standard) { name = m.name };
                    AssetDatabase.CreateAsset(mat, path);
                }
                mat.shader = standard;
                Configure(mat, m, texDir);
                EditorUtility.SetDirty(mat);
                materials[m.name] = mat;
            }

            // 3. Model import settings
            string modelPath = $"{dir}/{sheet.interior}.fbx";
            var importer = AssetImporter.GetAtPath(modelPath) as ModelImporter;
            if (importer == null) throw new Exception($"Couldn't find the model {modelPath}.");
            importer.globalScale = 1f;
            importer.useFileScale = true;
            importer.importCameras = false;
            importer.importLights = false;
            importer.importAnimation = false;
            importer.animationType = ModelImporterAnimationType.None;
            importer.addCollider = false;
            importer.isReadable = false;
            importer.materialImportMode = ModelImporterMaterialImportMode.None;
            importer.importNormals = ModelImporterNormals.Import;
            importer.SaveAndReimport();

            // 4. Prefab
            var model = AssetDatabase.LoadAssetAtPath<GameObject>(modelPath);
            var inst = (GameObject)UnityEngine.Object.Instantiate(model);
            inst.name = sheet.interior;
            int missing = 0;
            foreach (var r in inst.GetComponentsInChildren<MeshRenderer>(true))
            {
                // Meshes are named Mesh_<Material>, materials IVA_<Material>. Moving parts are Mesh_<Material>__Live_<name>.
                string baseName = r.gameObject.name;
                int live = baseName.IndexOf("__", StringComparison.Ordinal);
                if (live > 0) baseName = baseName.Substring(0, live);
                string key = "IVA_" + StripSuffix(baseName).Replace("Mesh_", "");
                Material mat;
                if (materials.TryGetValue(key, out mat)) r.sharedMaterial = mat;
                else missing++;
                r.shadowCastingMode = ShadowCastingMode.On;
                r.receiveShadows = true;
            }

            var lightGo = new GameObject("IVA_CabinLight");
            lightGo.transform.SetParent(inst.transform, false);
            float[] cl = sheet.cabinLight != null && sheet.cabinLight.Length >= 5 ? sheet.cabinLight : new[] { 0f, 1.55f, 0f, 2.6f, 1.0f };
            lightGo.transform.localPosition = new Vector3(cl[0], cl[1], cl[2]);
            var light = lightGo.AddComponent<Light>();
            light.type = LightType.Point;
            light.range = cl[3];
            light.intensity = Mathf.Clamp(cl[4] * 1.6f, 0.6f, 1.4f);   // the cabin lamp now carries the lighting (see IndirectLight)
            light.color = new Color(1f, 0.93f, 0.82f);
            // soft shadows from the cabin lamp give the modules, switches and housings their depth
            light.shadows = LightShadows.Soft;
            light.shadowStrength = 0.85f;
            light.shadowBias = 0.02f;
            light.shadowNormalBias = 0.2f;
            light.shadowNearPlane = 0.05f;

            // Our own reflection probe: without it the shiny parts reflect the game's probes, i.e. the bright sky outside,
            // and the whole cabin reads as white. Box-sized to the model, it wins over the game's probes inside it.
            Cubemap env = CabinReflection();
            if (env != null)
            {
                Bounds bb = new Bounds(Vector3.zero, Vector3.zero);
                bool any = false;
                foreach (var r in inst.GetComponentsInChildren<MeshRenderer>(true))
                {
                    if (!any) { bb = r.bounds; any = true; } else bb.Encapsulate(r.bounds);
                    r.reflectionProbeUsage = ReflectionProbeUsage.BlendProbes;
                }
                var probeGo = new GameObject("IVA_CabinReflection");
                probeGo.transform.SetParent(inst.transform, false);
                probeGo.transform.localPosition = inst.transform.InverseTransformPoint(bb.center);
                var probe = probeGo.AddComponent<ReflectionProbe>();
                probe.mode = ReflectionProbeMode.Custom;
                probe.customBakedTexture = env;
                probe.size = bb.size + Vector3.one * 0.2f;
                probe.importance = 100;
                probe.boxProjection = false;
                probe.intensity = 1f;
            }

            if (sheet.extraLights != null)
                for (int i = 0; i + 4 < sheet.extraLights.Length; i += 5)
                {
                    var go = new GameObject($"IVA_DeckLight{i / 5}");
                    go.transform.SetParent(inst.transform, false);
                    go.transform.localPosition = new Vector3(sheet.extraLights[i], sheet.extraLights[i + 1], sheet.extraLights[i + 2]);
                    var l = go.AddComponent<Light>();
                    l.type = LightType.Point;
                    l.range = sheet.extraLights[i + 3];
                    l.intensity = Mathf.Clamp(sheet.extraLights[i + 4] * 1.6f, 0.4f, 1.4f);
                    l.color = new Color(1f, 0.9f, 0.76f);
                    l.shadows = LightShadows.None;
                }

            string prefabPath = $"{dir}/{sheet.interior}.prefab";
            PrefabUtility.SaveAsPrefabAsset(inst, prefabPath);
            UnityEngine.Object.DestroyImmediate(inst);

            // 5. Addressable entry in the mod's own group (the only groups the mod build packs)
            var settings = AddressableAssetSettingsDefaultObject.Settings;
            if (settings == null) throw new Exception("Addressables aren't set up in this project. Create the IVA mod with Modding > Create New Mod first.");
            AddressableAssetGroup group = settings.FindGroup(ModGroupName);
            if (group == null) throw new Exception($"Couldn't find the addressable group '{ModGroupName}'. Was the mod created with the ID 'IVA'?");
            string guid = AssetDatabase.AssetPathToGUID(prefabPath);
            AddressableAssetEntry entry = settings.CreateOrMoveEntry(guid, group, false, false);
            entry.address = sheet.address;
            settings.SetDirty(AddressableAssetSettings.ModificationEvent.EntryMoved, entry, true);

            string note = missing > 0 ? $" ({missing} meshes without a matching material)" : "";
            return $"{sheet.interior}: {materials.Count} materials, prefab and address '{sheet.address}'{note}";
        }

        private static Cubemap CabinReflection()
        {
            string path = InteriorsRoot + "/Shared/Textures/cabin_reflection.png";
            var ti = AssetImporter.GetAtPath(path) as TextureImporter;
            if (ti == null) { Debug.LogWarning("[IVA] cabin_reflection.png missing; interiors keep the game's reflections."); return null; }
            if (ti.textureShape != TextureImporterShape.TextureCube)
            {
                ti.textureShape = TextureImporterShape.TextureCube;
                ti.generateCubemap = TextureImporterGenerateCubemap.Cylindrical;
                ti.mipmapEnabled = true;
                ti.SaveAndReimport();
            }
            return AssetDatabase.LoadAssetAtPath<Cubemap>(path);
        }

        private static string StripSuffix(string name)
        {
            // Unity may add " (1)" style suffixes; Blender may add ".001".
            int i = name.IndexOf(" (", StringComparison.Ordinal);
            if (i > 0) name = name.Substring(0, i);
            i = name.IndexOf('.');
            if (i > 0) name = name.Substring(0, i);
            return name;
        }

        private static void SetTextureType(string path, bool normalMap)
        {
            var ti = AssetImporter.GetAtPath(path) as TextureImporter;
            if (ti == null)
            {
                Debug.LogWarning($"[IVA] Texture not found: {path}");
                return;
            }
            TextureImporterType wanted = normalMap ? TextureImporterType.NormalMap : TextureImporterType.Default;
            if (ti.textureType == wanted && ti.mipmapEnabled) return;
            ti.textureType = wanted;
            ti.mipmapEnabled = true;
            ti.wrapMode = TextureWrapMode.Repeat;
            ti.anisoLevel = 4;
            ti.SaveAndReimport();
        }

        // Textures shared by every interior live in Interiors/Shared/Textures; an interior's own Textures folder
        // only holds what differs (e.g. its name plate) and wins when both have the file.
        private static string TexPath(string texDir, string file)
        {
            string own = texDir + "/" + file;
            return File.Exists(own) ? own : InteriorsRoot + "/Shared/Textures/" + file;
        }

        private static Color FromLinear(float[] c, float a = 1f)
        {
            if (c == null || c.Length < 3) return Color.white;
            return new Color(c[0], c[1], c[2], a).gamma; // Blender stores linear colours; Unity materials take sRGB
        }

        // Inside a closed cabin almost none of the sky's ambient light gets in. The Standard shader scales ambient and
        // reflected light by its occlusion map, so every interior material gets a flat dark one: the cabin is then lit by
        // the cabin lamp, its own glowing displays and the sun through the windows, not the daylight outside.
        private const float IndirectLight = 0.22f;
        private static Texture2D _dim;

        private static Texture2D DimOcclusion()
        {
            if (_dim != null) return _dim;
            string path = InteriorsRoot + "/Shared/Textures/indirect_dim.png";
            if (!File.Exists(path))
            {
                var t = new Texture2D(4, 4, TextureFormat.RGB24, false, true);
                byte v = (byte)Mathf.RoundToInt(IndirectLight * 255f);
                var px = new Color32[16];
                for (int i = 0; i < 16; i++) px[i] = new Color32(v, v, v, 255);
                t.SetPixels32(px);
                File.WriteAllBytes(path, t.EncodeToPNG());
                AssetDatabase.ImportAsset(path);
            }
            var ti = AssetImporter.GetAtPath(path) as TextureImporter;
            if (ti != null && (ti.sRGBTexture || ti.mipmapEnabled))
            {
                ti.sRGBTexture = false;      // the value is a light factor, not a colour
                ti.mipmapEnabled = false;
                ti.SaveAndReimport();
            }
            _dim = AssetDatabase.LoadAssetAtPath<Texture2D>(path);
            return _dim;
        }

        private static void Configure(Material mat, MatInfo m, string texDir)
        {
            if (mat.shader.name == "IVA/Interior")
            {
                mat.SetFloat("_Indirect", IndirectLight);
                mat.SetFloat("_AOStrength", 1f);
                mat.SetFloat("_AODirect", m.emissionStrength > 0f ? 0f : 0.45f);   // screens and lamps aren't shaded
            }
            else
            {
                mat.SetTexture("_OcclusionMap", DimOcclusion());
                mat.SetFloat("_OcclusionStrength", 1f);
            }
            mat.SetColor("_Color", string.IsNullOrEmpty(m.texture) ? FromLinear(m.color) : Color.white);
            mat.SetFloat("_Metallic", Mathf.Clamp01(m.metallic));
            mat.SetFloat("_Glossiness", Mathf.Clamp01(1f - m.roughness));

            Vector2 tiling = m.tiling != null && m.tiling.Length >= 2 ? new Vector2(m.tiling[0], m.tiling[1]) : Vector2.one;
            Texture2D main = string.IsNullOrEmpty(m.texture) ? null : AssetDatabase.LoadAssetAtPath<Texture2D>(TexPath(texDir, m.texture));
            mat.SetTexture("_MainTex", main);
            mat.SetTextureScale("_MainTex", tiling);

            Texture2D normal = string.IsNullOrEmpty(m.normal) ? null : AssetDatabase.LoadAssetAtPath<Texture2D>(TexPath(texDir, m.normal));
            mat.SetTexture("_BumpMap", normal);
            mat.SetFloat("_BumpScale", m.normalStrength);
            if (normal != null) mat.EnableKeyword("_NORMALMAP"); else mat.DisableKeyword("_NORMALMAP");

            if (m.emissionStrength > 0f)
            {
                mat.EnableKeyword("_EMISSION");
                mat.globalIlluminationFlags = MaterialGlobalIlluminationFlags.None;
                // Blender strengths (up to 6 for lamps) bloom badly in the game's post-processing: scale them down
                float k = Mathf.Clamp(m.emissionStrength * 0.25f, 0.2f, 1.2f);
                if (m.emissionFromTexture && main != null)
                {
                    mat.SetTexture("_EmissionMap", main);
                    mat.SetColor("_EmissionColor", Color.white * k);
                }
                else
                {
                    mat.SetTexture("_EmissionMap", null);
                    mat.SetColor("_EmissionColor", FromLinear(m.emission) * k);
                }
            }
            else
            {
                mat.DisableKeyword("_EMISSION");
                mat.SetColor("_EmissionColor", Color.black);
            }
        }
    }
}
