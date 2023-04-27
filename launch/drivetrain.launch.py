from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    ld = LaunchDescription()

    controller_node = Node(
        package="drivetrain",
        executable="controller_node",
        name="controller_node"
    )

    drivetrain_node = Node( 
        package="drivetrain",
        executable="drivetrain_node",
        name="drivetrain_node"
    )

    tail_node = Node(
        package="drivetrain",
        executable="tail_node",
        name="tail_node"
    )

    ld.add_action(controller_node)
    ld.add_action(drivetrain_node)
    ld.add_action(tail_node)

    return ld
