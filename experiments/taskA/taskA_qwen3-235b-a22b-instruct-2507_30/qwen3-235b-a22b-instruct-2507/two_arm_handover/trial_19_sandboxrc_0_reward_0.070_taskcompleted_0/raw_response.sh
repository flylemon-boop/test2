import numpy as np

# Open both grippers initially
open_gripper_arm0()
open_gripper_arm1()

# Get the current hammer pose (position of handle center)
hammer_pos, hammer_quat = get_hammer_pose()

# Table height is approximately the z-value of the hammer when it's lying flat
table_z = hammer_pos[2]

# Define safe z heights for lifting and handover
lift_z = table_z + 0.15  # Lift the hammer to ~15cm above table
handover_z = 0.175  # Midpoint between 0.15 and 0.20, within required bounds

# Compute approximate midpoint in x between the two arms for handover
# Based on initial positions: Arm0 ~0.44, Arm1 ~1.18 -> midpoint ~0.81
handover_x = 0.81

# Ensure handover occurs at a y where the table spans (use hammer's current y or average with arm y if needed)
handover_y = hammer_pos[1]  # Keep consistent with object alignment

# Define grasp approach height (a bit higher than table for safety)
grasp_z_approach = 0.05

# --- ARM 0: PICK UP THE HAMMER ---

# Step 1: Move Arm0 above the hammer handle with gripper aligned along Y-axis (to match hammer alignment)
gripper_down_Y = np.array([0, 1, 0, 0])  # For Arm0, opening along Y-axis
goto_pose_arm0(
    position=np.array([hammer_pos[0], hammer_pos[1], table_z + grasp_z_approach]),
    quaternion_wxyz=gripper_down_Y,
    z_approach=0.0
)

# Step 2: Approach down to grasp the hammer handle
goto_pose_arm0(
    position=np.array([hammer_pos[0], hammer_pos[1], hammer_pos[2]]),
    quaternion_wxyz=gripper_down_Y,
    z_approach=-grasp_z_approach
)

# Step 3: Close gripper to grasp hammer
close_gripper_arm0()

# Step 4: Lift hammer vertically to safe height
goto_pose_arm0(
    position=np.array([hammer_pos[0], hammer_pos[1], lift_z]),
    quaternion_wxyz=gripper_down_Y
)

# --- ARM 1: MOVE TO HANDOVER POSITION ---

# Arm1 needs to prepare to receive the hammer.
# Since hammer will be handed over near x=0.81, we move Arm1 there safely.

# First, lift to safe height before moving
goto_pose_arm1(
    position=np.array([hammer_pos[0], hammer_pos[1], lift_z]),
    quaternion_wxyz=np.array([0, 0, 1, 0]),  # Gripper facing down along Y-axis for Arm1
    z_approach=0.0
)

# Then move horizontally toward handover point (keep high to avoid collision)
goto_pose_arm1(
    position=np.array([handover_x, handover_y, lift_z]),
    quaternion_wxyz=np.array([0, 0, 1, 0])
)

# Now descend to handover height
goto_pose_arm1(
    position=np.array([handover_x, handover_y, handover_z]),
    quaternion_wxyz=np.array([0, 0, 1, 0])
)

# --- ARM 0: BRING HAMMER TO HANDOVER ZONE ---

# Rotate hammer to align with Arm1’s gripper direction (opening along Y-axis) — already oriented correctly
# Move Arm0 toward handover point at safe height first
goto_pose_arm0(
    position=np.array([handover_x, handover_y, lift_z]),
    quaternion_wxyz=gripper_down_Y
)

# Then lower to handover height (must stay within 0.15–0.20 m)
goto_pose_arm0(
    position=np.array([handover_x, handover_y, handover_z]),
    quaternion_wxyz=gripper_down_Y
)

# --- HANDOVER PHASE ---

# At this point, both arms are at the same position and height, holding opposite ends of the hammer.
# But only Arm0 has the hammer. Now Arm1 closes its gripper on the handle.

# To ensure Arm1 grasps the *handle*, not the head:
# The handle extends from center toward +Y. So Arm1 should grasp slightly behind center (+Y side).

# We adjust Arm1's final approach to close slightly behind the center of the handle
handle_grab_offset_y = 0.03  # Grasp 3cm behind center toward +Y (handle side)

goto_pose_arm1(
    position=np.array([handover_x, handover_y + handle_grab_offset_y, handover_z]),
    quaternion_wxyz=np.array([0, 0, 1, 0])
)

# Close Arm1 gripper to grasp the handle
close_gripper_arm1()

# Now Arm0 can release
open_gripper_arm0()

# Finally, Arm0 retracts slightly upward to complete handover cleanly
goto_pose_arm0(
    position=np.array([handover_x, handover_y, lift_z]),
    quaternion_wxyz=gripper_down_Y
)