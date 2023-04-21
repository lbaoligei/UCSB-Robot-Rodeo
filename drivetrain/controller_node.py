import rclpy
import pygame
from time import sleep
from rclpy.node import Node
from sensor_msgs.msg import Joy

class ControllerNode(Node):
    def __init__(self):
        super().__init__('controller_node')
        self.publisher = self.create_publisher(Joy, 'controller_command_dt', 10)
        # self.publisher = self.create_publisher(Joy, 'controller_command_arm', 10)
        pygame.init()
        pygame.joystick.init()
        self.controller = pygame.joystick.Joystick(0)
        self.controller.init()
        self.buttons = {'x':0.,'o':0.,'t':0.,'s':0.,'L1':0.,'R1':0.,'L2':0.,'R2':0.,'share':0.,'options':0.,
           'axis1':0.,'axis2':0.,'axis3':0.,'axis4':0.,'Dpad up':0,'Dpad down':0, 'Dpad left':0,'Dpad right':0}

    def process_controller_input(self):
        while rclpy.ok():
            for event in pygame.event.get():
                if event.type == pygame.JOYAXISMOTION:
                    # taking in the controller's left joystick's info
                    left_stick_x = self.controller.get_axis(0)
                    left_stick_y = self.controller.get_axis(1)
                
                elif event.type == pygame.JOYBUTTONDOWN: 
                    # taking in the controller's L1 R1 info
                    for x,(key,val) in enumerate(self.buttons.items()):
                        if x < 10:
                            if self.controller.get_button(x):
                                self.buttons[key] = 1
                # if button is released 
                elif event.type == pygame.JOYBUTTONUP:                       # When Button released
#             print(event.dict,event.joy,event.button,'RELEASED')
                    for x,(key,val) in enumerate(self.buttons.items()):
                        if x < 10:
                            if event.button == x:
                                self.buttons[key] = 0
        
                # if directional buttons (Dpad) were pressed 
                elif event.type == pygame.JOYHATMOTION:
                    hat = controller.get_hat(event.hat)  	# return position for hat (x,y) for x,y in -1, 0, 1
                    for x,(key,val) in enumerate(self.buttons.items()):
                        if x == 14 or x == 15:
                            if hat[1] > 0:
                                self.buttons['Dpad up'] = hat[1]
                            else:
                                self.buttons['Dpad up'] = 0
                            if hat[1] < 0:
                                self.buttons['Dpad down'] = abs(hat[1])
                            else:
                                self.buttons['Dpad down'] = 0
                        if x == 16 or x == 17:
                            if hat[0] > 0:
                                self.buttons['Dpad right'] = hat[0]
                            else:
                                self.buttons['Dpad right'] = 0
                            if hat[0] < 0:
                                self.buttons['Dpad left'] = abs(hat[0])
                            else:
                                self.buttons['Dpad left'] = 0
                    # Create Joy message and populate axes values
                    joy_msg = Joy()
                    joy_msg.axes = [left_stick_x, left_stick_y]
                    joy_msg.buttons = [self.buttons[key] for key in ['Dpad up','Dpad down','Dpad left','Dpad right','x','o','t','s','l1', 'r1','l2','r2','share','option']]

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
