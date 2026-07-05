import numpy as np

# First, slightly lift both arms to avoid occluding the pot and handles
pos0, quat0 = get_arm0_gripper_pose()
pos1, quat1 = get_arm1_gripper_pose()

# Lift both arms up by 0.1 meters in Z to clear any potential obstruction
lift_offset = np.array([0, 0, 0.1])
goto_pose_both(pos0 + lift_offset, quat0, pos1 + lift_offset, quat1)

# Get the current positions of handle 0 and handle 1
handle0_pos = get_handle0_pos()
handle1_pos = get_handle1_pos()

# Define desired gripper orientation: sideways grasp with gripper y-axis aligned to world z-axis
# This means the gripper will approach from the side, not top-down.
# Target rotation: We want the gripper's y-axis (which is forward when closing) to point upward (world z)
# A suitable quaternion for this is a 90-degree rotation around the x-axis from default [0,0,1,0] (top-down)
# Rotating [0,0,1,0] by 90 deg around x gives: w=cos(45)=~0.707, x=sin(45)=~0.707 -> [0.707, 0.707, 0, 0]
side_grasp_quat = np.array([0.707, 0.707, 0, 0])  # WXYZ format

# Prepare approach: we'll use a z_approach of 0.05m (approach from 5cm above target)
z_approach = 0.05

# Open both grippers before grasping
open_gripper_arm0()
open_gripper_arm1()

# Move both arms to approach poses above the handles
goto_pose_both(
    position0=handle0_pos + np.array([0, 0, z_approach]),
    quaternion_wxyz0=side_grasp_quat,
    position1=handle1_pos + np.array([0, 0, z_approach]),
    quaternion_wxyz1=side_grasp_quat,
    z_approach=0.0  # Already accounted for approach height
)

# Now descend to the actual handle positions
goto_pose_both(
    position0=handle0_pos,
    quaternion_wxyz0=side_grasp_quat,
    position1=handle1_pos,
    quaternion_wxyz1=side_grasp_quat,
    z_approach=0.0
)

# Close both grippers to grasp the handles
close_gripper_arm0()
close_gripper_arm1()

# Lift both arms simultaneously to raise the pot
lift_height = 0.1  # Lift 10 cm up
final_pos0 = handle0_pos + np.array([0, 0, lift_height])
final_pos1 = handle1_pos + np.array([0, 0, lift_height])

goto_pose_both(
    position0=final_pos0,
    quaternion_wxyz0=side_grasp_quat,
    position1=final_pos1,
    quaternion_wxyz1=side_grasp_quat
)