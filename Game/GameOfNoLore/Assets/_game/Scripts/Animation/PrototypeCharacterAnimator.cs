using UnityEngine;

public sealed class PrototypeCharacterAnimator : MonoBehaviour
{
    [SerializeField] private Animator animator;

    private CharacterController characterController;
    private int moveSpeedHash;

    private void Awake()
    {
        characterController = GetComponentInParent<CharacterController>();
        moveSpeedHash = Animator.StringToHash("MoveSpeed");
    }

    private void Update()
    {
        if (animator == null || characterController == null)
            return;

        Vector3 velocity = characterController.velocity;
        velocity.y = 0f;
        animator.SetFloat(moveSpeedHash, velocity.magnitude);
    }
}
