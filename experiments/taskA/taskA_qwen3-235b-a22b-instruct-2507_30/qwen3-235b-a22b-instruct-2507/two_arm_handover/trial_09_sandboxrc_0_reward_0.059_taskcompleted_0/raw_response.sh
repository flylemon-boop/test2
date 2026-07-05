import numpy as np

# Open both grippers initially
open_gripper_arm0()
open_gripper_arm1()

# Get the current hammer pose (middle of the handle)
hammer_pos, _ = get_hammer_pose()

# Define key quaternions for orientation control
# Arm0 will approach the hammer with gripper opening along Y-axis (facing down)
q_arm0_approach = np.array([0, 1, 0, 0])  # [0, 1, 0, 0] for Y-axis opening, facing down
# For handover, we want Arm1 to grasp the handle — so gripper should open along Y-axis, facing down
q_arm1_grasp = np.array([0, 0, 1, 0])  # [0, 0, 1, 0] for Arm1, opening along Y-axis

# Step 1: Arm0 moves above the hammer for safe approach
z_offset = 0.1  # 10 cm above hammer for safe descent
approach_pos_arm0 = hammer_pos + np.array([0, 0, z_offset])

# Move Arm0 above the hammer with z_approach to ensure vertical descent
goto_pose_arm0(approach_pos_arm0, q_arm0_approach, z_approach=0.0)

# Descend vertically to grasp the hammer handle
goto_pose_arm0(hammer_pos, q_arm0_approach, z_approach=-z_offset)

# Close gripper to grasp the hammer
close_gripper_arm0()

# Step 2: Lift the hammer to a safe height
lift_height = 0.15  # Ensure hammer is lifted to at least 0.15m above table
lifted_pos_arm0 = hammer_pos + np.array([0, 0, lift_height])
goto_pose_arm0(lifted_pos_arm0, q_arm0_approach)

# Step 3: Plan handover location near midpoint between initial arm positions
# Approximate midpoint in X between Arm0 and Arm1 (in robot0's frame)
mid_x = (0.44 + 1.18) / 2
handover_x = mid_x
handover_y = 0.0  # Keep around y=0 to avoid table gap
handover_z = 0.17  # Within required 0.15-0.20 range

# Target handover position (Arm0 will bring hammer here)
handover_pos = np.array([handover_x, handover_y, handover_z])

# But we must rotate the hammer so that Arm1 can grasp the handle properly.
# Currently, hammer lies along Y-axis (handle +Y, head -Y). 
# After Arm0 picks it up from the middle, to hand over to Arm1:
# We want the handle to be oriented toward Arm1's side (+X direction), so we rotate the hammer 90 degrees.

# So when handing over, the hammer should be rotated so its handle points toward +X
# This means the gripper of Arm0 must rotate accordingly during handover.
# Desired orientation: hammer aligned along X-axis, handle toward +X → gripper opening should be along Z or Y?
# But grippers open along local Y or X depending on setup.

# Since Arm1 uses [0,0,1,0] for Y-axis opening (gripper jaws move along Y), to grasp the handle,
# the handle must be aligned along Y-axis again? But wait: if hammer is handed over with handle along X,
# then Arm1 cannot grasp unless it approaches along X.

# Reconsider: 
# - Initial: hammer along Y (handle +Y, head -Y)
# - Arm0 grasps middle — so now it holds center, can reorient.
# - To hand over safely, we want Arm1 to grasp the *handle* (not head). So Arm1 must approach from the head side (-Y relative to handle).
# But due to physical layout (Arms on left/right), best way is to rotate hammer 90 degrees so handle points to right (+X).

# So final orientation: hammer along X-axis, handle toward +X (toward Arm1), head toward -X (toward Arm0)
# Then Arm1 can approach along Y-axis to grasp the handle (since its gripper opens along Y locally).

# Therefore, during handover, the hammer should be oriented with handle along +X.
# So the gripper holding it (Arm0) must have its opening direction compatible.

# How to orient Arm0's gripper to hold hammer along X-axis?
# Initially, it approached along Y (gripper opening along Y) to grab handle along Y.
# Now we need to rotate the object so it lies along X.
# We can rotate the wrist: rotating by 90 degrees around Z-axis changes Y-aligned to X-aligned.

# Rotation quaternion for 90 deg CCW around Z: [cos(45), 0, 0, sin(45)] = [0.707, 0, 0, 0.707]
q_rotate_z_90 = np.array([np.cos(np.pi/4), 0, 0, np.sin(np.pi/4)])  # 90 deg around Z

# Apply this rotation to the original approach quaternion
# Multiply quaternions: new_q = q_rotate_z_90 * q_arm0_approach
def quat_multiply(q1, q2):
    w1, x1, y1, z1 = q1
    w2, x2, y2, z2 = q2
    w = w1*w2 - x1*x2 - y1*y2 - z1*z2
    x = w1*x2 + x1*w2 + y1*z2 - z1*y2
    y = w1*y2 + y1*w2 + z1*x2 - x1*z2
    z = w1*z2 + z1*w2 + x1*y2 - y1*x2
    return np.array([w, x, y, z])

q_handover = quat_multiply(q_rotate_z_90, q_arm0_approach)
q_handover = q_handover / np.linalg.norm(q_handover)

# Now move Arm0 to handover position with rotated orientation
goto_pose_arm0(handover_pos, q_handover)

# Step 4: Arm1 moves to grasp the handle at handover position
# Arm1 needs to approach the handle part of the hammer.
# Since hammer is centered at handover_pos, and handle is now pointing toward +X (length ~0.15–0.25m),
# the actual handle end is approximately: handover_pos + [0.15, 0, 0] (but we don't know exact length)

# Instead, Arm1 should go to the handover position but offset along -Y to approach perpendicular to the handle
# Wait: after rotation, hammer is aligned along X-axis, so to grasp the handle, Arm1 should approach along Y-axis.

# But which side? The handle is at +X side, so Arm1 should be at +X side already.
# Actually, since Arm1 is on the right (high X), and hammer handle now points to right (+X), 
# Arm1 can approach along Y-axis to grasp the handle at the center.

# However, Arm0 is still holding the center. So we need Arm1 to grasp the handle portion — which extends from center to +X.
# So target grasp point for Arm1 is slightly shifted in +X from handover center.

# Estimate handle length: since handle was originally toward +Y, and Arm0 picked from center,
# half the handle length is unknown. But we can assume average handle length 0.2m → half is 0.1m.

# So the handle extends ~0.1m in +X from center.
# Let Arm1 aim for the center of the handle, which is now located at handover_pos + [0.1, 0, 0]
handle_center_pos = handover_pos + np.array([0.1, 0, 0])

# But Arm1 must approach from a safe direction. Best to approach vertically from above.
# Use z_approach to descend onto the handle.

# First, move Arm1 above the target handle position
approach_pos_arm1 = handle_center_pos + np.array([0, 0, z_offset])
goto_pose_arm1(approach_pos_arm1, q_arm1_grasp, z_approach=0.0)

# Then descend to grasp
goto_pose_arm1(handle_center_pos, q_arm1_grasp, z_approach=-z_offset)

# Close gripper to grasp the handle
close_gripper_arm1()

# Step 5: Arm0 releases the hammer
open_gripper_arm0()

# Optional: lift Arm0 away
safe_retreat_arm0 = handover_pos + np.array([0, 0, 0.1])
goto_pose_arm0(safe_retreat_arm0, q_handover)

# Success condition met: handover occurred at z=0.17 which is within [0.15, 0.20]