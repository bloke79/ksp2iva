// The IVA view as a camera shot for the game's camera manager (UniverseCameraManager.SetCameraShotOverride), the way
// Redux's own first-person camera works. The manager then places every render camera from it each frame: the physics
// camera, the scaled-space camera (planets, Mun, stars), clouds and reflections all agree with where you're looking.
// The pose is computed when the manager asks, so it never lags the pod.

using System;
using KSP.Sim;
using UnityEngine;

namespace IVA
{
    public delegate bool IvaPoseSource(out Vector3 position, out Quaternion rotation, out float fieldOfView);

    public sealed class IvaCameraShot : ICameraShot, ICameraNearClipProvider, ICameraShotProvider
    {
        private readonly IPhysicsSpaceProvider _space;
        private readonly IvaPoseSource _pose;
        private readonly float _nearClip;
        private Vector3 _lastPos;
        private Quaternion _lastRot = Quaternion.identity;
        private float _lastFov = 60f;

        public IvaCameraShot(IPhysicsSpaceProvider space, IvaPoseSource pose, float nearClip)
        {
            _space = space;
            _pose = pose;
            _nearClip = nearClip;
        }

        public ICameraShot Shot => this;

        private void Sample()
        {
            Vector3 p;
            Quaternion r;
            float f;
            if (_pose != null && _pose(out p, out r, out f))
            {
                _lastPos = p;
                _lastRot = r;
                _lastFov = f;
            }
        }

        public Position CameraPosition
        {
            get { Sample(); return _space.PhysicsToPosition(new Vector3d(_lastPos.x, _lastPos.y, _lastPos.z)); }
        }

        public Rotation CameraRotation
        {
            get { Sample(); return _space.PhysicsToRotation(new QuaternionD(_lastRot.x, _lastRot.y, _lastRot.z, _lastRot.w)); }
        }

        public Vector CameraForward
        {
            get { Sample(); Vector3 v = _lastRot * Vector3.forward; return _space.PhysicsToVector(new Vector3d(v.x, v.y, v.z)); }
        }

        public Vector CameraUp
        {
            get { Sample(); Vector3 v = _lastRot * Vector3.up; return _space.PhysicsToVector(new Vector3d(v.x, v.y, v.z)); }
        }

        public bool IsOrthographic => false;
        public double FieldOfView { get { Sample(); return _lastFov; } }
        public double OrthographicSize => 5.0;
        public float NearClipPlane => _nearClip;
    }
}
