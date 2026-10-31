// IVA Redux interior surface shader (URP; the game moved from the built-in pipeline to URP in 26w43).
// Standard PBR lighting plus two things the cabins need:
//  - ambient occlusion baked into the mesh's vertex colours (red channel) by the Blender exporter, which grounds every
//    seam, recess and contact point;
//  - an "indirect light" level: a closed cabin gets little of the sky's ambient and reflected light, so that is scaled
//    down and the cabin lamp, the displays and the sun through the windows do the lighting.
// Same name and properties as the built-in version, so existing materials carry over.
Shader "IVA/Interior"
{
    Properties
    {
        _Color ("Colour", Color) = (1,1,1,1)
        _MainTex ("Albedo", 2D) = "white" {}
        _BumpMap ("Normal map", 2D) = "bump" {}
        _BumpScale ("Normal strength", Float) = 1.0
        _Metallic ("Metallic", Range(0,1)) = 0.0
        _Glossiness ("Smoothness", Range(0,1)) = 0.5
        [HDR] _EmissionColor ("Emission", Color) = (0,0,0,1)
        _EmissionMap ("Emission map", 2D) = "white" {}
        _AOStrength ("Baked AO strength", Range(0,1)) = 1.0
        _AODirect ("Baked AO on direct light", Range(0,1)) = 0.45
        _Indirect ("Indirect light", Range(0,1)) = 0.25
    }
    SubShader
    {
        Tags { "RenderType"="Opaque" "RenderPipeline"="UniversalPipeline" "Queue"="Geometry" }
        LOD 300

        Pass
        {
            Name "ForwardLit"
            Tags { "LightMode"="UniversalForwardOnly" }

            HLSLPROGRAM
            #pragma target 3.5
            #pragma vertex vert
            #pragma fragment frag

            #pragma multi_compile _ _MAIN_LIGHT_SHADOWS _MAIN_LIGHT_SHADOWS_CASCADE _MAIN_LIGHT_SHADOWS_SCREEN
            #pragma multi_compile _ _ADDITIONAL_LIGHTS_VERTEX _ADDITIONAL_LIGHTS
            #pragma multi_compile _ _CLUSTER_LIGHT_LOOP
            #pragma multi_compile_fragment _ _ADDITIONAL_LIGHT_SHADOWS
            #pragma multi_compile_fragment _ _SHADOWS_SOFT
            #pragma multi_compile_fragment _ _REFLECTION_PROBE_BLENDING
            #pragma multi_compile_fragment _ _REFLECTION_PROBE_BOX_PROJECTION
            #pragma multi_compile_fragment _ _LIGHT_COOKIES
            #pragma multi_compile_fog

            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"

            TEXTURE2D(_MainTex);     SAMPLER(sampler_MainTex);
            TEXTURE2D(_BumpMap);     SAMPLER(sampler_BumpMap);
            TEXTURE2D(_EmissionMap); SAMPLER(sampler_EmissionMap);

            CBUFFER_START(UnityPerMaterial)
                half4 _Color;
                float4 _MainTex_ST;
                half _BumpScale;
                half _Metallic;
                half _Glossiness;
                half4 _EmissionColor;
                half _AOStrength;
                half _AODirect;
                half _Indirect;
            CBUFFER_END

            struct Attributes
            {
                float4 positionOS : POSITION;
                float3 normalOS   : NORMAL;
                float4 tangentOS  : TANGENT;
                float2 uv         : TEXCOORD0;
                half4  color      : COLOR;
            };

            struct Varyings
            {
                float4 positionCS : SV_POSITION;
                float2 uv         : TEXCOORD0;
                float3 positionWS : TEXCOORD1;
                half3  normalWS   : TEXCOORD2;
                half4  tangentWS  : TEXCOORD3;
                half4  color      : TEXCOORD4;
                half   fogFactor  : TEXCOORD5;
            };

            Varyings vert (Attributes IN)
            {
                Varyings OUT;
                VertexPositionInputs pos = GetVertexPositionInputs(IN.positionOS.xyz);
                VertexNormalInputs nrm = GetVertexNormalInputs(IN.normalOS, IN.tangentOS);
                OUT.positionCS = pos.positionCS;
                OUT.positionWS = pos.positionWS;
                OUT.uv = TRANSFORM_TEX(IN.uv, _MainTex);
                OUT.normalWS = nrm.normalWS;
                real sign = IN.tangentOS.w * GetOddNegativeScale();
                OUT.tangentWS = half4(nrm.tangentWS, sign);
                OUT.color = IN.color;
                OUT.fogFactor = ComputeFogFactor(pos.positionCS.z);
                return OUT;
            }

            half4 frag (Varyings IN) : SV_Target
            {
                half4 c = SAMPLE_TEXTURE2D(_MainTex, sampler_MainTex, IN.uv) * _Color;
                half ao = lerp(1.0h, saturate(IN.color.r), _AOStrength);

                half3 nTS = UnpackNormalScale(SAMPLE_TEXTURE2D(_BumpMap, sampler_BumpMap, IN.uv), _BumpScale);
                half3 bitangent = cross(IN.normalWS, IN.tangentWS.xyz) * IN.tangentWS.w;
                half3 normalWS = normalize(mul(nTS, half3x3(IN.tangentWS.xyz, bitangent, IN.normalWS)));

                SurfaceData s = (SurfaceData)0;
                s.albedo = c.rgb * lerp(1.0h, ao, _AODirect);
                s.metallic = _Metallic;
                s.smoothness = _Glossiness;
                s.occlusion = ao * _Indirect;
                s.emission = SAMPLE_TEXTURE2D(_EmissionMap, sampler_EmissionMap, IN.uv).rgb * _EmissionColor.rgb;
                s.alpha = 1;
                s.normalTS = nTS;

                InputData d = (InputData)0;
                d.positionWS = IN.positionWS;
                d.positionCS = IN.positionCS;
                d.normalWS = normalWS;
                d.viewDirectionWS = GetWorldSpaceNormalizeViewDir(IN.positionWS);
                d.shadowCoord = TransformWorldToShadowCoord(IN.positionWS);
                d.fogCoord = InitializeInputDataFog(float4(IN.positionWS, 1.0), IN.fogFactor);
                d.bakedGI = SampleSH(normalWS);
                d.normalizedScreenSpaceUV = GetNormalizedScreenSpaceUV(IN.positionCS);
                d.shadowMask = half4(1, 1, 1, 1);

                half4 col = UniversalFragmentPBR(d, s);
                col.rgb = MixFog(col.rgb, d.fogCoord);
                col.a = 1;
                return col;
            }
            ENDHLSL
        }

        UsePass "Universal Render Pipeline/Lit/ShadowCaster"
        UsePass "Universal Render Pipeline/Lit/DepthOnly"
        UsePass "Universal Render Pipeline/Lit/DepthNormals"
    }
}
