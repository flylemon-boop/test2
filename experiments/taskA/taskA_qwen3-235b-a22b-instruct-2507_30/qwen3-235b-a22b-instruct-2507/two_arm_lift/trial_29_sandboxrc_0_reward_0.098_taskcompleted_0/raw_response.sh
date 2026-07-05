import numpy as np

# First, slightly lift both arms to avoid occlusion
pos0, quat0 = get_arm0_gripper_pose()
pos1, quat1 = get_arm1_gripper_pose()

lift_height = 0.1  # Lift 10 cm up
pos0_lifted = pos0.copy()
pos0_lifted[2] += lift_height
pos1_lifted = pos1.copy()
pos1_lifted[2] += lift_height

goto_pose_both(pos0_lifted, quat0, pos1_lifted, quat1, z_approach=0.0)

# Get handle positions from vision
handle0_pos = get_handle0_pos()
handle1_pos = get_handle1_pos()

# Define sideways grasp orientation: y-axis of gripper aligned with world z-axis
# This means the gripper will approach horizontally, not top-down
# Desired rotation: align gripper forward (usually -Z) toward the handle, and gripper Y with world Z
# Target quaternion for sideways grasp (gripper frame): X right, Y up (world Z), Z forward
# Representing this as WXYZ quaternion: approximately [0.707, 0.707, 0, 0] for 90 deg around X axis

sideways_quat_wxyz = np.array([0.707, 0.707, 0.0, 0.0])  # Rotate 90 degrees around X to align Y with Z

# Approach distance in Z (horizontal approach, so we use lateral offset)
approach_offset = 0.05  # 5 cm approach distance

# For Arm 0: approach handle 0 from the side
approach_dir0 = np.array([-1, 0, 0])  # Assuming handle 0 is on the negative X side
target_approach0 = handle0_pos + approach_dir0 * approach_offset
goto_pose_arm0(target_approach0, sideways_quat_wxyz, z_approach=0.0)
goto_pose_arm0(handle0_pos, sideways_quat_wxyz, z_approach=0.0)  # Move to grasp
close_gripper_arm0()

# For Arm 1: approach handle 1 from the opposite side
approach_dir1 = np.array([1, 0, 0])  # Opposite direction for handle 1
target_approach1 = handle1_pos + approach_dir1 * approach_offset
goto_pose_arm1(target_approach1, sideways_quat_wxyz, z_approach=0.0)
goto_pose_arm1(handle1_pos, sideways_quat_wxyz, z_approach=0.0)  # Move to grasp
close_gripper_arm1()

# Now both arms have grasped the handles. Lift the pot together to same height.
lift_amount = 0.1  # Lift pot by 10 cm
lifted_handle0_pos = handle0_pos.copy()
lifted_handle0_pos[2] += lift_amount
lifted_handle1_pos = handle1_pos.copy()
lifted_handle1_pos[2] += lift_amount

goto_pose_both(lifted_handle0_pos, sideways_quat_wxyz, lifted_handle1_pos, sideways_quat_wxyz, z_approach=0.0)