# Code block 0
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

# Rotation quaternion for 90 deg CCW around Z: [cos(45), 0, 0, sin(45)] -> [0.707, 0, 0, 0.707]
q_rotate_z_90 = np.array([0.707, 0, 0, 0.707])  # 90 deg CCW around Z

# Apply rotation to original approach quat
q_handover_orientation = q_rotate_z_90  # We'll manually set desired orientation
# Actually, composing rotations: we want to rotate the tool frame by 90 deg around Z
# The correct resulting quaternion when applying 90 deg Z-rotation to [0,1,0,0] is approximately [0.707, 0, 0, 0.707]? 
# Let’s compute: rotating vector (0,1,0) by 90 deg CCW around Z gives (-1,0,0) — not what we want.

# Wait: we want the *opening direction* (local Y of gripper) to align with the hammer's length.
# Originally: opening along Y_world → matched hammer along Y.
# Now we want opening along X_world? No — we want hammer along X_world, so gripper opening should also be along X_world.

# But our gripper can only open along certain axes based on mounting.
# From reference:
# - Arm0 gripper facing down opening along X-axis: [0, 0.707, 0.707, 0]
# - opening along Y-axis: [0, 1, 0, 0]

# So to have opening along X, we use [0, 0.707, 0.707, 0]

# So for handover, we want:
# - Hammer along X-axis, handle toward +X
# - Gripper opening along X (so fingers can slide along X)
# → Use q_handover = [0, 0.707, 0.707, 0] for Arm0

q_handover_for_Arm0 = np.array([0, 0.707, 0.707, 0])

# Also, during handover, the position must be at handover_pos with z in [0.15,0.20]
# Move Arm0 to handover position with proper orientation

# First go to handover position above with intermediate safe orientation?
# But we already have hammer lifted.

# Move to handover location with new orientation
goto_pose_arm0(handover_pos, q_handover_for_Arm0)

# Step 4: Prepare Arm1 to receive the hammer
# Arm1 needs to move to grasp the handle at handover location
# Since hammer handle is now pointing +X, and we want Arm1 to grasp the handle (near middle or base of handle),
# Arm1 should approach from the +Y side (front), with gripper opening along Y (to clamp along Y-axis)

# So Arm1 gripper should have orientation: opening along Y → use [0,0,1,0]
# And target position: same handover_pos, but we must approach from Y direction

# But note: the handover_pos is where the *middle* of the handle currently is.
# Since the handle length is 0.15–0.25m, and we're holding at center, the base of the handle is further +X by half-length.

# However, we don't know exact handle length. But since Arm1 is on the right, and handle points to +X (right),
# the base of the handle is even closer to Arm1.

# To grasp the handle (not the head), Arm1 should move to a point along the handle — ideally near the base.
# But we don't know base location. Instead, assume we can adjust.

# Since we are handing over at the center of the handle, and we want Arm1 to grasp the handle portion,
# Arm1 can grasp at the current center — that’s still part of the handle.

# So Arm1 goes to handover_pos with orientation [0,0,1,0], but approaches from +Y (front)

# Approach point: slightly in front of handover point along Y
approach_pos_arm1 = handover_pos + np.array([0, 0.1, 0])  # 10 cm in front

# Move Arm1 above (in terms of Y) the handover point
goto_pose_arm1(approach_pos_arm1, q_arm1_grasp)

# Then descend in Y-direction to grasp
goto_pose_arm1(handover_pos, q_arm1_grasp, z_approach=0.0)  # No z approach, but we are approaching along Y

# Close gripper to grasp the handle
close_gripper_arm1()

# Step 5: Arm0 releases after confirmation of grasp
# For safety, we assume close_gripper_arm1 secures the hammer
open_gripper_arm0()

# Step 6: Both arms retract carefully

# Retract Arm1 back along Y
retract_pos_arm1 = approach_pos_arm1
goto_pose_arm1(retract_pos_arm1, q_arm1_grasp)

# Retract Arm0 away from handover zone — move up first then backward
safe_lift_arm0 = handover_pos + np.array([0, 0, 0.1])
goto_pose_arm0(safe_lift_arm0, q_handover_for_Arm0)

# Then move to starting region
initial_retract_arm0 = np.array([0.44, 0.0, 0.4])
goto_pose_arm0(initial_retract_arm0, q_arm0_approach)