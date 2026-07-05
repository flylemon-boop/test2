import numpy as np

# Open both grippers initially
open_gripper_arm0()
open_gripper_arm1()

# Get hammer handle pose
hammer_pos, hammer_quat = get_hammer_pose()

# Define useful quaternions for orientation control
# Arm0 gripper facing down along X-axis (for grasping hammer handle)
q_arm0_grasp = np.array([0, 0.707, 0.707, 0])  # opening along X-axis
# Arm1 gripper facing down along Y-axis (to grasp handle properly after handover)
q_arm1_grasp = np.array([0, 0, 1, 0])  # opening along Y-axis

# Compute approach height to avoid table collision during motion
# We assume the table surface is near z=0, but we lift safely above it
safe_lift_height = 0.20  # meters

# --- ARM 0: Approach and grasp the hammer ---

# Move above the hammer with safe z_approach to prevent early contact
approach_offset = 0.1
goto_pose_arm0(hammer_pos, q_arm0_grasp, z_approach=approach_offset)

# Lower to grasp position (without extra z_approach since already approached)
goto_pose_arm0(hammer_pos, q_arm0_grasp)

# Close gripper to grasp the hammer
close_gripper_arm0()

# Lift hammer to safe height for transfer
lifted_hammer_pos = hammer_pos + np.array([0, 0, safe_lift_height])
goto_pose_arm0(lifted_hammer_pos, q_arm0_grasp)

# --- Plan handover location ---
# Handover should occur near midpoint between arms to minimize risk
# Initial rough arm positions (in robot0 frame)
arm0_x = 0.44
arm1_x = 1.18
mid_x = (arm0_x + arm1_x) / 2.0  # ~0.81 m

# Use current hammer y-position as base, adjust slightly if needed
handover_y = hammer_pos[1]  # keep same y as original hammer alignment
handover_z = 0.175  # within required 0.15-0.20 range

# Desired handover position in robot0 frame
handover_pos = np.array([mid_x, handover_y, handover_z])

# Ensure hammer is rotated so that Arm1 can grasp the handle correctly
# After rotation, the handle should point toward Arm1's gripper direction
# We want the handle oriented such that Arm1 (with gripper opening along Y) can grab along the handle length
# So rotate the hammer 90 degrees around Z so the handle now aligns with X-axis
# This requires a quaternion representing a 90-degree (π/2) rotation around Z-axis from upright pose
# Original grasp by Arm0 was along X, now we reorient so handle points along X but gripper opening for Arm1 will be along Y
# Actually, we need to consider: when rotating hammer 90 degrees, its head goes from -Y to -X or +X?
# Let’s rotate so that after handover, handle extends in +X direction (toward Arm1), head in -X

# Create a quaternion for 90-degree rotation around Z (from Y-aligned to X-aligned)
# Rotation of π/2 around Z: cos(π/4)=~0.707, sin(π/4)=~0.707 → [cos(θ/2), 0, 0, sin(θ/2)]
q_rotate_90z = np.array([np.cos(np.pi/4), 0, 0, np.sin(np.pi/4)])  # WXYZ

# Apply rotation to current hammer orientation (approximate desired final orientation)
# Since original quat may be unreliable, we instead define desired orientation directly
# After rotation, we want the hammer aligned along X-axis with handle toward +X
# And gripper of Arm0 must maintain orientation during move — we manually set desired quat
# For Arm0 to hold it during transfer: still use downward-facing gripper, now aligned to new pose
# But we keep Arm0's gripper fixed in orientation during transport? Or rotate?

# Instead: during handover, we want the hammer horizontal along X-axis
# So we set the orientation after rotation to have the hammer body along X
# We apply the 90-degree Z rotation to the original grasp orientation
q_handover = q_arm0_grasp.copy()  # start from original
# However, simply rotating the gripper orientation isn't trivial with quaternions
# Alternative: define expected orientation after 90-degree Z rotation of the tool frame
# If original was [0, 0.707, 0.707, 0] (gripper down, opening along X), 
# then after +90 deg Z rotation (CCW viewed from top), X becomes Y, Y becomes -X
# So opening direction becomes Y, hence new quaternion becomes [0, 1, 0, 0]? But that's opening along Y
# But Arm0 shouldn’t use that; better to keep stable.

# Instead, let's not rotate the hammer during Arm0's hold.
# Rather, Arm0 brings the hammer horizontally along Y to mid-zone, then rotates *during handover*?
# But handover requires precise coordination.

# Better strategy:
# Keep hammer aligned with Y-axis during transport — this avoids complex rotations mid-air
# Only reorient once at handover position using small motions.

# Revised plan:
# Arm0 moves hammer to handover position while keeping original orientation (along Y)
# Then, slowly rotates the hammer 90 degrees around Z so handle is now along X (pointing to Arm1)
# During this rotation, both robots coordinate grip.

# But first: move hammer to handover location without rotating
goto_pose_arm0(handover_pos, q_arm0_grasp)

# Now rotate the hammer gradually around Z by 90 degrees so the handle points toward Arm1 (+X direction)
# New orientation: after rotating the entire hammer 90 deg CCW around Z, its local X becomes global Y, etc.
# The gripper of Arm0 must now change orientation accordingly
# Original q_arm0_grasp: [0, 0.707, 0.707, 0] → down, opening along X
# After +90 deg Z rotation: opening direction becomes +Y → new quat: [0, 1, 0, 0]

q_after_rotation = np.array([0, 1, 0, 0])  # Arm0 gripper now opening along Y

# Perform rotation in steps to avoid large IK jumps
steps = 5
for i in range(1, steps + 1):
    ratio = i / steps
    # Interpolate quaternion
    q_step = slerp(q_arm0_grasp, q_after_rotation, ratio)
    goto_pose_arm0(handover_pos, q_step)

# Update current orientation
current_orientation = q_after_rotation

# Now the hammer is rotated: handle pointing +X, head -X
# Arm1 needs to approach from +X side to grasp the handle (middle of handle is at handover_pos)

# But Arm1 must now move to grasp the same point — however, Arm1's gripper opens along Y by default
# To grasp a handle along X, it needs gripper opening along X → requires different orientation

# Wait — correction: our earlier definition said:
# "Arm1 gripper facing down opening along Y-axis: [0, 0, 1, 0]"
# That means the fingers open/close along Y. To grasp an object aligned along X, we need fingers to open along X.

# So Arm1 needs a gripper orientation where fingers open along X
# That corresponds to: similar to Arm0's initial grasp: [0, 0.707, 0.707, 0] but transformed?

# But Arm1’s frame is mirrored. We cannot directly reuse Arm0's quaternions.
# Instead, think geometrically.

# In robot0 frame:
# We want Arm1's gripper to face down and open along X-axis (so fingers move in X direction)
# That would be the same rotational orientation as Arm0's initial grasp: [0, 0.707, 0.707, 0]

# So Arm1 should use q_arm1_target = [0, 0.707, 0.707, 0] to open along X

q_arm1_approach = np.array([0, 0.707, 0.707, 0])

# Before handover, Arm1 approaches the handover position from the +X side?
# But handover_pos.x is ~0.81, and Arm1 starts at x=1.18 → so Arm1 is on the +X side already
# So Arm1 should come from further +X to grasp the handle near handover_pos

# Compute Arm1 approach position: offset in +X from handover point
approach_distance = 0.1
arm1_approach_pos = handover_pos + np.array([approach_distance, 0, 0])

# Arm1 moves to approach position above the handover point (to avoid collision)
arm1_safe_z = handover_z + 0.1
goto_pose_arm1(np.array([arm1_approach_pos[0], arm1_approach_pos[1], arm1_safe_z]), q_arm1_approach)

# Lower to approach level
goto_pose_arm1(arm1_approach_pos, q_arm1_approach)

# Now move slowly toward handover position to make contact with hammer handle
# Step forward in small increments along -X
step_size = 0.02
for dx in np.arange(approach_distance, 0, -step_size):
    target_x = handover_pos[0] + dx - step_size
    pos = np.array([target_x, handover_pos[1], handover_pos[2]])
    goto_pose_arm1(pos, q_arm1_approach)

    # Break if needed? Not really possible to sense — just complete full move
# Final small step to exactly handover position
goto_pose_arm1(handover_pos, q_arm1_approach)

# Now Arm1 is at the same point — but both grippers are trying to hold the same object
# We must ensure that Arm1 closes first before Arm0 opens

# Close Arm1 gripper to grasp the hammer
close_gripper_arm1()

# Now Arm0 can release
open_gripper_arm0()

# Arm0 retracts slightly to avoid interference
retract_offset = 0.05
retract_pos = handover_pos + np.array([retract_offset, 0, 0])
goto_pose_arm0(retract_pos, current_orientation)

# Final check: Arm1 holds the hammer at correct z-height
# Already at handover_z ∈ [0.15, 0.20], so valid

# Task complete


# Helper function for spherical linear interpolation of quaternions
def slerp(q1, q2, t):
    # Normalize input quaternions
    q1 = q1 / np.linalg.norm(q1)
    q2 = q2 / np.linalg.norm(q2)
    # Compute dot product
    dot = np.dot(q1, q2)
    # Ensure shortest path
    if dot < 0.0:
        q2 = -q2
        dot = -dot
    # If quaternions are very close, just interpolate linearly
    if dot > 0.9995:
        return q1 + t * (q2 - q1)
    # Spherical interpolation
    theta_0 = np.arccos(dot)
    sin_theta_0 = np.sin(theta_0)
    theta = theta_0 * t
    sin_theta = np.sin(theta)
    s0 = (np.cos(theta) - dot * sin_theta / sin_theta_0)
    s1 = sin_theta / sin_theta_0
    return (s0 * q1) + (s1 * q2)