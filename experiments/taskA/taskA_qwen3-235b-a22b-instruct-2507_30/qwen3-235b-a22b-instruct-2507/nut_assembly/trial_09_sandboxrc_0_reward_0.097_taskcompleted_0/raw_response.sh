import numpy as np
from scipy.spatial.transform import Rotation

# First, get the pose of the extruded handle of the brown square nut for grasping
handle_position, handle_quaternion = sample_grasp_pose('extruded handle of the brown square nut')

# Open the gripper before attempting grasp
open_gripper()

# Approach the handle with a safe z offset to avoid collision
goto_pose(handle_position, handle_quaternion, z_approach=0.1)

# Move down to the actual grasp pose without z offset (performs insertion in Z)
goto_pose(handle_position, handle_quaternion)

# Close the gripper to grasp the nut
close_gripper()

# Now, get the pose of the white hollow center of the brown square nut to understand its orientation relative to the handle
nut_center_position, nut_center_quaternion = get_object_pose('white hollow center of the brown square nut')

# We need to compute the fixed transform from the handle grasp pose to the nut's center,
# so we can align the nut correctly when inserting onto the peg.

# Compute transformation from handle to nut center in object frame
# Create transformation matrices
handle_to_world = np.eye(4)
handle_to_world[:3, 3] = handle_position
handle_to_world[:3, :3] = Rotation.from_quat(handle_quaternion).as_matrix()

center_to_world = np.eye(4)
center_to_world[:3, 3] = nut_center_position
center_to_world[:3, :3] = Rotation.from_quat(nut_center_quaternion).as_matrix()

# Compute the relative transform from handle to nut center (in world frame)
world_to_handle = np.linalg.inv(handle_to_world)
handle_to_center = world_to_handle @ center_to_world

# This handle_to_center is constant and encodes how the nut is positioned relative to the handle grasp

# Now get the target insertion location: the peg on the brown square block
peg_position, peg_quaternion = get_object_pose('brown square block')

# The goal is to place the nut center at the peg position with correct alignment
# So we want: target_center_position = peg_position, target_center_quaternion = peg_quaternion

# Now compute desired handle pose using the inverse of the fixed handle_to_center transform
target_center_to_world = np.eye(4)
target_center_to_world[:3, 3] = peg_position
target_center_to_world[:3, :3] = Rotation.from_quat(peg_quaternion).as_matrix()

# Apply reverse transform: handle = center * (center_to_handle)
target_handle_to_world = target_center_to_world @ np.linalg.inv(handle_to_center)

target_handle_position = target_handle_to_world[:3, 3]
target_handle_quaternion_wxyz = Rotation.from_matrix(target_handle_to_world[:3, :3]).as_quat()

# Before inserting, lift slightly to clear any obstacles (optional safety move)
lift_position = handle_position + np.array([0, 0, 0.1])
goto_pose(lift_position, handle_quaternion)

# Now approach the insertion point with z_approach for precision
goto_pose(target_handle_position, target_handle_quaternion_wxyz, z_approach=0.1)

# Perform final insertion by moving down
goto_pose(target_handle_position, target_handle_quaternion_wxyz)

# Optionally open gripper after insertion
open_gripper()

# Return to home joint configuration
goto_home_joint_position()