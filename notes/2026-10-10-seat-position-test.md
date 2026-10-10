# Log: seat-position-test (2026-10-10)

Source: `C:\Users\mattl\AppData\LocalLow\Intercept Games\Kerbal Space Program 2\Player.log` (modified 10/10/2026 19:45:55)

## Observations

- 

## Log lines

```
   226: [System] IVA: Loading plumes from files completed in 0.0001s.
   227: [System] IVA: loading soundbanks completed in 0.0001s.
   327: [IVA] IVA loaded. Toggle: C, next seat: V. Interiors: Mk1-3, Mk1.
   624: Exception: Reentering the Update method is not allowed.  This can happen when calling WaitForCompletion on an operation while inside of a callback.
   631: UnityEngine.StackTraceUtility:ExtractStringFromExceptionInternal(Object, String&, String&)
   648: UnityEngine.ResourceManagement.AsyncOperations.AsyncOperationBase`1:Complete(GameObject, Boolean, Exception, Boolean)
   649: UnityEngine.ResourceManagement.AsyncOperations.ProviderOperation`1:ProviderCompleted(Object, Boolean, Exception)
   650: UnityEngine.ResourceManagement.ResourceProviders.ProvideHandle:Complete(Object, Boolean, Exception)
   655: UnityEngine.ResourceManagement.AsyncOperations.AsyncOperationBase`1:Complete(IList`1, Boolean, Exception, Boolean)
   669: NullReferenceException: Object reference not set to an instance of an object
   674: UnityEngine.StackTraceUtility:ExtractStringFromExceptionInternal(Object, String&, String&)
   778: [IVA] IVA: crewed parts on vessel: pod_1v_conical_crew (seats 1)
   779: [IVA] IVA: loading interior 'IVA/Interior_pod_1v_conical_crew'...
   780: [IVA] IVA: placed the Mk1 interior in pod_1v_conical_crew. Pod measured from mesh colliders: base radius 0.73 m, height 1.39 m (from -0.66 to 0.73). Fit scale (1.16, 1.45). 1 seat(s).
   781: [IVA] IVA: the pod's own window meshes: pod_1v_m1_conical_crew at 92 deg, height 0.12. The interior's front windows face 0 deg; set Alignment > Yaw to the pod's forward window angle if they differ.
   782: [IVA] Entered IVA (Mk1 interior), seat 1 of 1.
   791: [IVA] Left IVA.
   792: [IVA] IVA: crewed parts on vessel: pod_1v_conical_crew (seats 1)
   793: [IVA] IVA: placed the Mk1 interior in pod_1v_conical_crew. Pod measured from mesh colliders: base radius 0.73 m, height 1.39 m (from -0.66 to 0.73). Fit scale (1.16, 1.45). 1 seat(s).
   794: [IVA] IVA: the pod's own window meshes: pod_1v_m1_conical_crew at 92 deg, height 0.12. The interior's front windows face 0 deg; set Alignment > Yaw to the pod's forward window angle if they differ.
   795: [IVA] Entered IVA (Mk1 interior), seat 1 of 1.
   796: [IVA] Left IVA.
```
