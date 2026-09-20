using UnityEngine;
using UnityEngine.InputSystem;

public sealed class PrototypeGateInteraction : MonoBehaviour
{
    [SerializeField] private Transform gatePivot;
    [SerializeField] private float openAngle = 90f;
    [SerializeField] private float rotationSpeed = 180f;

    private Quaternion closedRotation;
    private Quaternion openRotation;
    private PlayerInput playerInput;
    private InputAction interactAction;
    private bool playerInside;
    private bool isOpen;

    private void Awake()
    {
        closedRotation = gatePivot.localRotation;
        openRotation = closedRotation * Quaternion.Euler(0f, openAngle, 0f);
    }

    private void Update()
    {
        if (playerInside && interactAction != null && interactAction.WasPressedThisFrame())
        {
            isOpen = !isOpen;
        }

        Quaternion targetRotation = isOpen ? openRotation : closedRotation;
        gatePivot.localRotation = Quaternion.RotateTowards(
            gatePivot.localRotation,
            targetRotation,
            rotationSpeed * Time.deltaTime);
    }

    private void OnTriggerEnter(Collider other)
    {
        CharacterController characterController = other.GetComponent<CharacterController>();
        if (characterController == null)
        {
            return;
        }

        PlayerInput enteringPlayer = characterController.GetComponent<PlayerInput>();
        if (enteringPlayer == null)
        {
            return;
        }

        playerInput = enteringPlayer;
        interactAction = playerInput.actions.FindAction("Interact");
        playerInside = true;
    }

    private void OnTriggerExit(Collider other)
    {
        CharacterController characterController = other.GetComponent<CharacterController>();
        if (characterController == null || playerInput == null ||
            characterController.gameObject != playerInput.gameObject)
        {
            return;
        }

        playerInside = false;
        interactAction = null;
        playerInput = null;
    }
}
