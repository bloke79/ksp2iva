// IVA Redux interior surface shader (built-in pipeline).
// Standard PBR lighting plus two things the cabins need:
//  - ambient occlusion baked into the mesh's vertex colours (red channel) by the Blender exporter, which grounds every
//    seam, recess and contact point;
//  - an "indirect light" level: a closed cabin gets little of the sky's ambient and reflected light, so that is scaled
//    down and the cabin lamp, the displays and the sun through the windows do the lighting.
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
        Tags { "RenderType"="Opaque" }
        LOD 300

        CGPROGRAM
        #pragma surface surf Standard fullforwardshadows
        #pragma target 3.0

        sampler2D _MainTex;
        sampler2D _BumpMap;
        sampler2D _EmissionMap;
        fixed4 _Color;
        half _BumpScale, _Metallic, _Glossiness, _AOStrength, _AODirect, _Indirect;
        half4 _EmissionColor;

        struct Input
        {
            float2 uv_MainTex;
            float4 color : COLOR;
        };

        void surf (Input IN, inout SurfaceOutputStandard o)
        {
            fixed4 c = tex2D(_MainTex, IN.uv_MainTex) * _Color;
            half ao = lerp(1.0h, saturate(IN.color.r), _AOStrength);
            o.Albedo = c.rgb * lerp(1.0h, ao, _AODirect);
            o.Normal = UnpackScaleNormal(tex2D(_BumpMap, IN.uv_MainTex), _BumpScale);
            o.Metallic = _Metallic;
            o.Smoothness = _Glossiness;
            o.Occlusion = ao * _Indirect;
            o.Emission = tex2D(_EmissionMap, IN.uv_MainTex).rgb * _EmissionColor.rgb;
            o.Alpha = 1;
        }
        ENDCG
    }
    FallBack "Diffuse"
}
