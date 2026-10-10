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
    private Vector3 movementForward;
    private Vector3 movementRight;
    private bool hasMovementReference;
    private bool isTurningInPlace;

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

        if (moveInput != Vector2.zero)
        {
            if (!hasMovementReference && movementCamera != null)
            {
                movementForward = Vector3.ProjectOnPlane(movementCamera.forward, Vector3.up).normalized;
                movementRight = Vector3.Cross(Vector3.up, movementForward).normalized;
                hasMovementReference = movementForward.sqrMagnitude > 0.0001f;
            }

            if (hasMovementReference)
            {
                moveDirection = Vector3.ClampMagnitude(
                    movementForward * moveInput.y + movementRight * moveInput.x,
                    1f);
            }
        }
        else
        {
            hasMovementReference = false;
            isTurningInPlace = false;
        }

        if (moveDirection.sqrMagnitude > 0.0001f)
        {
            Vector3 facingDirection = Vector3.ProjectOnPlane(transform.forward, Vector3.up).normalized;
            if (Vector3.Angle(facingDirection, moveDirection) >= 70f)
            {
                isTurningInPlace = true;
            }

            Quaternion targetRotation = Quaternion.LookRotation(moveDirection, Vector3.up);
            transform.rotation = Quaternion.Slerp(
                transform.rotation,
                targetRotation,
                rotationSpeed * Time.deltaTime);

            facingDirection = Vector3.ProjectOnPlane(transform.forward, Vector3.up).normalized;
            if (Vector3.Angle(facingDirection, moveDirection) <= 30f)
            {
                isTurningInPlace = false;
            }

            moveDirection = isTurningInPlace
                ? Vector3.zero
                : facingDirection * moveDirection.magnitude;
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
