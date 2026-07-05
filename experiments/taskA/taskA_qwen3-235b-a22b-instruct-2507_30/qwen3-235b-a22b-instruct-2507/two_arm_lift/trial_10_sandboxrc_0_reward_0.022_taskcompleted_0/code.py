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

# Desired gripper orientations: sideways grasp with gripper y-axis aligned with world z-axis
# This means the gripper should face towards the center of the pot horizontally.
# For arm0 (on one side), we want the gripper x-axis pointing in the direction from handle0 to handle1
# And the gripper y-axis pointing up (aligned with world z)

# Compute approach direction (from each handle towards outside for pre-grasp)
approach_direction_0 = handle1_pos - handle0_pos
approach_direction_0 /= np.linalg.norm(approach_direction_0)
approach_direction_1 = -approach_direction_0  # opposite direction for arm1

# Define desired gripper orientation using rotation matrices
# We want: 
#   gripper_y_axis ≈ world_z_axis = [0, 0, 1]
#   gripper_x_axis ≈ approach_direction (horizontal, pointing outward)
# Then compute z_axis via cross product

world_z = np.array([0, 0, 1])

# For arm0:
gripper_x_0 = -approach_direction_0  # point gripper forward along approach
gripper_y_0 = world_z
gripper_z_0 = np.cross(gripper_x_0, gripper_y_0)
gripper_z_0 /= np.linalg.norm(gripper_z_0)
gripper_y_0 = np.cross(gripper_z_0, gripper_x_0)  # re-orthogonalize
R0 = np.column_stack((gripper_x_0, gripper_y_0, gripper_z_0))

# For arm1:
gripper_x_1 = -approach_direction_1
gripper_y_1 = world_z
gripper_z_1 = np.cross(gripper_x_1, gripper_y_1)
gripper_z_1 /= np.linalg.norm(gripper_z_1)
gripper_y_1 = np.cross(gripper_z_1, gripper_x_1)
R1 = np.column_stack((gripper_x_1, gripper_y_1, gripper_z_1))

# Convert rotation matrices to quaternions (WXYZ format)
def rot_to_quat(R):
    trace = np.trace(R)
    if trace > 0:
        s = 2.0 * np.sqrt(trace + 1)
        w = 0.25 * s
        x = (R[2,1] - R[1,2]) / s
        y = (R[0,2] - R[2,0]) / s
        z = (R[1,0] - R[0,1]) / s
    elif R[0,0] > R[1,1] and R[0,0] > R[2,2]:
        s = 2.0 * np.sqrt(1.0 + R[0,0] - R[1,1] - R[2,2])
        w = (R[2,1] - R[1,2]) / s
        x = 0.25 * s
        y = (R[0,1] + R[1,0]) / s
        z = (R[0,2] + R[2,0]) / s
    elif R[1,1] > R[2,2]:
        s = 2.0 * np.sqrt(1.0 + R[1,1] - R[0,0] - R[2,2])
        w = (R[0,2] - R[2,0]) / s
        x = (R[0,1] + R[1,0]) / s
        y = 0.25 * s
        z = (R[1,2] + R[2,1]) / s
    else:
        s = 2.0 * np.sqrt(1.0 + R[2,2] - R[0,0] - R[1,1])
        w = (R[1,0] - R[0,1]) / s
        x = (R[0,2] + R[2,0]) / s
        y = (R[1,2] + R[2,1]) / s
        z = 0.25 * s
    quat = np.array([w, x, y, z])
    return quat / np.linalg.norm(quat)

quat0 = rot_to_quat(R0)
quat1 = rot_to_quat(R1)

# Approach distance for grasping (in Z direction of gripper frame, but we'll use horizontal approach)
# Instead, use z_approach parameter to move back along approach direction before moving in
pre_approach_dist = 0.1  # 10 cm back along approach direction

pre_grasp_pos0 = handle0_pos + approach_direction_0 * pre_approach_dist
pre_grasp_pos1 = handle1_pos + approach_direction_1 * pre_approach_dist

# Move both arms to pre-grasp poses simultaneously
goto_pose_both(pre_grasp_pos0, quat0, pre_grasp_pos1, quat1)

# Open both grippers
open_gripper_arm0()
open_gripper_arm1()

# Now grasp the handles with a z_approach of 0.05m (move down 5cm vertically before final pose)
# Note: z_approach here is along world Z, so it will help make a gentle vertical descent into grasp
goto_pose_both(handle0_pos, quat0, handle1_pos, quat1, z_approach=0.05)

# Close both grippers to grasp the handles
close_gripper_arm0()
close_gripper_arm1()

# Now lift both arms up simultaneously to lift the pot
lift_height = 0.15  # lift up by 15 cm
final_pos0 = handle0_pos + np.array([0, 0, lift_height])
final_pos1 = handle1_pos + np.array([0, 0, lift_height])

goto_pose_both(final_pos0, quat0, final_pos1, quat1)