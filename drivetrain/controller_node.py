import rclpy
import pygame
from time import sleep
from rclpy.node import Node
from sensor_msgs.msg import Joy

class ControllerNode(Node):
    def __init__(self):
        super().__init__('controller_node')
        self.publisher = self.create_publisher(Joy, 'controller_command_dt', 10)
        pygame.init()
        pygame.joystick.init()
        self.controller = pygame.joystick.Joystick(0)
        self.controller.init()

    def process_controller_input(self):
        while rclpy.ok():
            for event in pygame.event.get():
                if event.type == pygame.JOYAXISMOTION:
                    # taking in the controller's left joystick's info
                    left_stick_x = self.controller.get_axis(0)
                    left_stick_y = self.controller.get_axis(1)
                    
                    # taking in the controller's L1 R1 info
                    l1 = self.controller.get_button(4)  # L1
                    r1 = self.controller.get_button(5)  # R1
                    

                    # Create Joy message and pack axes, buttons values into the package
                    joy_msg = Joy()
                    joy_msg.axes = [left_stick_x, -left_stick_y]	# flip y_axis so that up is positive, down is negative
                    joy_msg.buttons = [l1, r1]

                    # Publish the Joy message
                    self.publisher.publish(joy_msg)
            sleep(0.1)


def main(args=None):
    rclpy.init(args=args)
    controller_node = ControllerNode()
    print("controller_node is running ...")
    print("publishing left joystick to topic controller_command_dt")
    print("publishing L1 L2 to topic controller_command_dt")
    try:
        controller_node.process_controller_input()

    except KeyboardInterrupt:
        pass
    controller_node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
