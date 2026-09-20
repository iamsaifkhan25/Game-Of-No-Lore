using Unity.Cinemachine;
using UnityEngine;

public sealed class CameraZone : MonoBehaviour
{
    [SerializeField] private CinemachineCamera cinemachineCamera;

    private void OnTriggerEnter(Collider other)
    {
        if (other.GetComponent<CharacterController>() != null)
            cinemachineCamera.enabled = true;
    }

    private void OnTriggerExit(Collider other)
    {
        if (other.GetComponent<CharacterController>() != null)
            cinemachineCamera.enabled = false;
    }
}
