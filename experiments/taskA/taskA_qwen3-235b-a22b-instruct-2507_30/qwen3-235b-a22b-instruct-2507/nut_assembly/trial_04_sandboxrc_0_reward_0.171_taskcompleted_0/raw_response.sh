import numpy as np
from scipy.spatial.transform import Rotation

# First, get the pose for grasping the extruded handle of the brown square nut
handle_position, handle_quaternion = sample_grasp_pose('extruded handle of the brown square nut')

# Approach and grasp the handle
goto_pose(handle_position, handle_quaternion, z_approach=0.1)  # approach from 10cm above
goto_pose(handle_position, handle_quaternion)  # move down to grasp pose
close_gripper()  # close gripper to grasp the nut

# Now get the center of the brown square nut (white hollow center) to determine insertion alignment
center_position, center_quaternion = get_object_pose('white hollow center of the brown square nut')

# Get the pose of the target peg on the brown square block for insertion
peg_position, peg_quaternion = get_object_pose('brown square block')

# Compute the fixed transform between the handle grasp pose and the nut's center
# This transform will be used to align the nut correctly during insertion
handle_to_center_transform = np.linalg.inv(Rotation.from_quat(handle_quaternion).as_matrix()) @ Rotation.from_quat(center_quaternion).as_matrix()

# We want to insert the nut so that its center aligns with the peg while maintaining orientation consistency
# Apply the same relative rotation from handle to center to the final insertion pose
insertion_rotation = Rotation.from_quat(peg_quaternion) * Rotation.from_matrix(handle_to_center_transform)
insertion_quaternion = insertion_rotation.as_quat()

# Adjust the insertion position: we need to offset the peg position by the vector from center to handle in the world frame
center_to_handle_vector = Rotation.from_quat(peg_quaternion).apply(
    Rotation.from_quat(center_quaternion).inv().apply(handle_position - center_position)
)
adjusted_insertion_position = peg_position + center_to_handle_vector

# Move above the insertion point
goto_pose(adjusted_insertion_position, insertion_quaternion, z_approach=0.1)

# Perform the insertion
goto_pose(adjusted_insertion_position, insertion_quaternion, z_approach=0.0)

# Optionally open gripper after insertion
open_gripper()

# Return to home position
goto_home_joint_position()