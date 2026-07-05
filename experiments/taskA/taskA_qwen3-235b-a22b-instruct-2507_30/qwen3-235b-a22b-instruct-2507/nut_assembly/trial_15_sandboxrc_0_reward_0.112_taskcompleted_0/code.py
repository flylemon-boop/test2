# Code block 0
import numpy as np
from scipy.spatial.transform import Rotation

# First, open the gripper to prepare for grasping
open_gripper()

# Get the grasp pose for the extruded handle of the brown square nut
handle_position, handle_quaternion_wxyz = sample_grasp_pose('extruded handle of the brown square nut')

# Approach the handle from above to avoid collision
goto_pose(handle_position, handle_quaternion_wxyz, z_approach=0.1)

# Move down to the actual grasp pose
goto_pose(handle_position, handle_quaternion_wxyz)

# Close the gripper to grasp the nut
close_gripper()

# Now, get the pose of the white hollow center of the brown square nut to understand its orientation
center_position, center_quaternion_wxyz = get_object_pose('white hollow center of the brown square nut')

# Compute the fixed transform from the center to the handle (this defines how the nut is oriented when held)
# This transform will be used to ensure proper alignment during insertion
handle_to_center_translation = center_position - handle_position
center_to_handle_rotation = Rotation.from_quat(handle_quaternion_wxyz).inv() * Rotation.from_quat(center_quaternion_wxyz)

# Get the pose of the target location: the peg on the brown square block where the nut should be inserted
target_center_position, target_center_quaternion_wxyz = get_object_pose('brown square block')

# Compute desired handle position and orientation for insertion
# We want the center of the nut to align with the block's center, so we reverse the earlier transform
desired_handle_position = target_center_position - center_to_handle_rotation.apply(handle_to_center_translation)
desired_rotation = Rotation.from_quat(target_center_quaternion_wxyz) * center_to_handle_rotation.inv()
desired_handle_quaternion_wxyz = desired_rotation.as_quat()

# Now move above the target insertion point
goto_pose(desired_handle_position, desired_handle_quaternion_wxyz, z_approach=0.1)

# Insert the nut by moving down precisely
goto_pose(desired_handle_position, desired_handle_quaternion_wxyz, z_approach=0.0)

# Optionally open gripper to release
open_gripper()

# Return arm to home position
goto_home_joint_position()