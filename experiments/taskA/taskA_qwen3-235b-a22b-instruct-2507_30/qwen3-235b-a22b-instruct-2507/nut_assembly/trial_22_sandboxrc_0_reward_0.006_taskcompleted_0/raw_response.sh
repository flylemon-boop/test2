import numpy as np
from scipy.spatial.transform import Rotation

# First, get the grasp pose for the extruded handle of the brown square nut
handle_position, handle_quaternion_wxyz = sample_grasp_pose('extruded handle of the brown square nut')

# Approach from 5cm above to ensure safe approach
goto_pose(handle_position, handle_quaternion_wxyz, z_approach=0.05)
# Move down to actual grasp pose
goto_pose(handle_position, handle_quaternion_wxyz)

# Close the gripper to grasp the nut
close_gripper()

# Now, get the center of the brown square nut (white hollow center) to compute relative transform
center_position, _ = get_object_pose('white hollow center of the brown square nut')

# Compute the fixed offset between handle grasp pose and nut center in the object's local frame
# This offset will be used later to align the nut center with the peg during insertion
offset_handle_to_center = center_position - handle_position

# Get the target insertion pose: we want to insert the nut onto the brown square block
# Assuming the 'brown square block' has a peg where the nut should be inserted
block_center_position, block_quaternion_wxyz = get_object_pose('brown square block')

# Desired final position of the nut center should match the block center
desired_nut_center_position = block_center_position

# To achieve this, we need to move the handle such that the center aligns with the block
# So, desired handle position = desired_nut_center_position - offset_handle_to_center
desired_handle_position = desired_nut_center_position - offset_handle_to_center

# We keep the same orientation as the original handle grasp for consistent alignment
# Move above the target insertion point first
goto_pose(desired_handle_position, handle_quaternion_wxyz, z_approach=0.05)

# Perform the insertion by moving down
goto_pose(desired_handle_position, handle_quaternion_wxyz, z_approach=0.0)

# Optionally open gripper to release
open_gripper()

# Return to home joint configuration
goto_home_joint_position()