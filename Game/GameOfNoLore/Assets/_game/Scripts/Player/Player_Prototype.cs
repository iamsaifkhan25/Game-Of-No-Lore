using UnityEngine;
using UnityEngine.InputSystem;

[RequireComponent(typeof(CharacterController))]
[RequireComponent(typeof(PlayerInput))]
public class PrototypePlayerController : MonoBehaviour
{
    [SerializeField] private Transform movementCamera;
    [SerializeField] private float movementSpeed = 3f;
    [SerializeField] private float rotationSpeed = 10f;
    [SerializeField] private float gravity = -20f;

    private CharacterController characterController;
    private PlayerInput playerInput;
    private InputAction moveAction;
    private float verticalVelocity;

    private void Awake()
    {
        characterController = GetComponent<CharacterController>();
        playerInput = GetComponent<PlayerInput>();
        moveAction = playerInput.actions.FindAction("Move");

        if (movementCamera == null)
        {
            Camera mainCamera = Camera.main;
            if (mainCamera != null)
            {
                movementCamera = mainCamera.transform;
            }
        }
    }

    private void Update()
    {
        Vector2 moveInput = moveAction != null
            ? moveAction.ReadValue<Vector2>()
            : Vector2.zero;

        Vector3 moveDirection = Vector3.zero;

        if (movementCamera != null)
        {
            Vector3 cameraForward = Vector3.ProjectOnPlane(movementCamera.forward, Vector3.up).normalized;
            Vector3 cameraRight = Vector3.ProjectOnPlane(movementCamera.right, Vector3.up).normalized;

            moveDirection = Vector3.ClampMagnitude(
                cameraForward * moveInput.y + cameraRight * moveInput.x,
                1f);
        }

        if (moveDirection.sqrMagnitude > 0.0001f)
        {
            Quaternion targetRotation = Quaternion.LookRotation(moveDirection, Vector3.up);
            transform.rotation = Quaternion.Slerp(
                transform.rotation,
                targetRotation,
                rotationSpeed * Time.deltaTime);
        }

        if (characterController.isGrounded && verticalVelocity < 0f)
        {
            verticalVelocity = -2f;
        }
        else
        {
            verticalVelocity += gravity * Time.deltaTime;
        }

        Vector3 velocity = moveDirection * movementSpeed;
        velocity.y = verticalVelocity;
        characterController.Move(velocity * Time.deltaTime);
    }
}
