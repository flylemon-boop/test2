# Code block 0
import numpy as np

# First, slightly lift both arms to avoid occluding the pot and handles
initial_pose0 = get_arm0_gripper_pose()
initial_pose1 = get_arm1_gripper_pose()

# Lift both arms up by 10 cm initially
lift_offset = np.array([0.0, 0.0, 0.1])
lifted_pos0 = initial_pose0[0] + lift_offset
lifted_pos1 = initial_pose1[0] + lift_offset

goto_pose_both(lifted_pos0, initial_pose0[1], lifted_pos1, initial_pose1[1])

# Get current handle positions using vision
handle0_pos = get_handle0_pos()
handle1_pos = get_handle1_pos()

# Define sideways grasp orientation: gripper y-axis aligned with world z-axis
# This means the gripper will approach horizontally, not from top
# Target quaternion for sideways grasp (gripper frame): x forward, y down, z left -> we want gripper y along world z
# Target rotation: rotate 90 degrees around x-axis from canonical [0,0,1,0] -> becomes [0.707, 0, 0, 0.707] (w,x,y,z)
sideways_quat = np.array([np.sqrt(2)/2, np.sqrt(2)/2, 0, 0])  # 90 deg around x-axis

# Prepare approach: come from 5 cm above the handle height for precision
approach_z = 0.05

# Open both grippers before grasping
open_gripper_arm0()
open_gripper_arm1()

# Move both arms to approach poses above the handles
goto_pose_both(
    handle0_pos + np.array([0, 0, approach_z]), sideways_quat,
    handle1_pos + np.array([0, 0, approach_z]), sideways_quat,
    z_approach=approach_z
)

# Now move down precisely to grasp poses at handle level
goto_pose_both(
    handle0_pos, sideways_quat,
    handle1_pos, sideways_quat,
    z_approach=0.0
)

# Close both grippers to grasp the handles
close_gripper_arm0()
close_gripper_arm1()

# Slightly lift both arms simultaneously to lift the pot
lift_height = 0.1  # Lift by 10 cm
final_pos0 = handle0_pos + np.array([0, 0, lift_height])
final_pos1 = handle1_pos + np.array([0, 0, lift_height])

goto_pose_both(final_pos0, sideways_quat, final_pos1, sideways_quat)