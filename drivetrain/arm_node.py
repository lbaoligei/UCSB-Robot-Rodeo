import rclpy
import RPi.GPIO as GPIO
import xarm 
import math 
import pygame 
from time import sleep
from os import environ
from os import system
from rclpy.node import Node
from sensor_msgs.msg import Joy

#need to fix main and init

class ArmNode(Node):
    def __init__(self):
        # Initialize the Node with the name 'ps4_arm_node'
        super().__init__('arm_node')
        # Create a subscription to the 'controller_command_arm' topic with the Joy message type
        self.subscription = self.create_subscription(Joy, 'controller_command_dt', self.joy_callback, 10)
        self.subscription
        
        self.intial_parameters()
        
        
    def joy_callback(self, msg):

        ## Two default positions:
        # set initial servo position: (number of servo, angle_desired, time span (ms))
        self.JSbutton = {}
        for i in range(len(self.buttonkeys)): 
            self.JSbutton[self.buttonkeys[i]] =msg.buttons[i]
        
        self.angleList_current = [self.angle1,self.angle2,self.angle3,self.angle4,self.angle5]
        if self.JSbutton['share'] == 1 and self.JSbutton['options'] == 0:
            self.SetAngleList(5, self.angleList_current,self.angleList_init, 1000)
        # set the arm motors to climing position
        elif self.JSbutton['options'] == 1 and self.JSbutton['share']==0:
            self.SetAngleList(5,self.angleList_current, self.angleList_climing, 1000)

        ## set the gripper and waist motion through motors 1,2
        # Incremental step values for joystick and button presses
        inc1 = 3.0
        inc2 = 3.0
        # 't' - gripper open, 'x' - gripper close, 'o' - waist turn clockwise, 
        # 's' - waist turn conter-clockwise
        if self.JSbutton['t'] == 1:  # triangular
            self.angle1 = self.SetAngle(1,self.angle1,inc1,0,60)
        if self.JSbutton['x'] == 1:  # 'x'
            self.angle1 = self.SetAngle(1,self.angle1,-inc1,0,60)
        if self.JSbutton['o'] == 1:  # circle
            self.angle2 = self.SetAngle(2,self.angle2,inc2)
        if self.JSbutton['s'] == 1:  # square
            self.angle2 = self.SetAngle(2,self.angle2,-inc2)


        ## set the arm position through motors 3,4,5
        self.oldy = self.y; self.oldz = self.z
        if self.JSbutton[self.butYpos] == 1 or self.JSbutton[self.butYneg] == 1 or self.JSbutton[self.butZpos] == 1 or self.JSbutton[self.butZneg] == 1:
            # calculate the new theta angles and y z positions
            self.theta1,self.theta2,self.theta3,self.y,self.z = self.SetNewCoord(self.JSbutton[self.butYpos],self.JSbutton[self.butYneg], self.JSbutton[self.butZpos],self.JSbutton[self.butZneg],self.y, self.z)

            ## check whether the calculated value can be reached
            # whether the range of motion is satisfied based on the length of two linkages
            if 11**2 < self.y**2+self.z**2 < 26.2**2 and self.y > 0:
                # whether the desired angles are within the range
                if self.minang5 < self.theta1 < self.maxang5 and self.minang4 < self.theta2 < self.maxang4 and self.minang3 < self.theta3 < self.maxang3:
                    self.arm.setPosition(3,self.theta3,self.waitTime, wait=True)
                    self.arm.setPosition(4,self.theta2,self.waitTime, wait=True)
                    self.arm.setPosition(5,self.theta1,self.waitTime, wait=True)
                    self.oldtheta1 = self.theta1; self.oldtheta2 = self.theta2; self.oldtheta3 = self.theta3
                else:
                    self.y = self.oldy
                    self.z = self.oldz
                    print('oldy ', self.oldy, 'oldz ',self.oldz,self.angle3, self.angle4, self.angle5)
                    print('Out of workspace angle')
            else:
                self.arm.setPosition(3,self.oldtheta3,self.waitTime, wait=True)
                self.arm.setPosition(4,self.oldtheta2,self.waitTime, wait=True)
                self.arm.setPosition(5,self.oldtheta1,self.waitTime, wait=True)
                self.y = self.oldy
                self.z = self.oldz
                print('oldy ', self.oldy, 'oldz ',self.oldz,self.angle3, self.angle4, self.angle5)
                print('Out of workspace coordinate')

        ## shutdown shortcut
        if self.JSbutton['L1'] == 1 and self.JSbutton['L2'] == 1 and self.JSbutton['R1'] == 1 and self.JSbutton['R2'] == 1 and self.shutdown_started == False:
            self.shutdown_started = True
            system('shutdown now -h')
        sleep(0.01)
    
    def SetNewCoord(self,button1,button2,button3,button4,y,z):


	# set increment for the z,y coordinates
        increment = 0.35       
        print(button1,button2,button3,button4)
        
        # Change y,z position based on the button info
        if button1 == 1 and button2 == 0 and button3 == 0 and button4 == 0:
            if self.l1**2 < (y+increment)**2 + z**2 < (self.l1+self.l2)**2 and y > 0:
                y+=increment
            else:
                pass
        elif button1 == 0 and button2 == 1 and button3 == 0 and button4 == 0:
            if self.l1**2 < (y-increment)**2 + z**2 < (self.l1+self.l2)**2 and y > 0:
                y-=increment
            else:
                pass
        elif button1 == 0 and button2 == 0 and button3 == 1 and button4 == 0:
            if self.l1**2 < (y)**2 + (z+increment)**2 < (self.l1+self.l2)**2:
                z+=increment
            else:
                pass
        elif button1 == 0 and button2 == 0 and button3 == 0 and button4 == 1:
            if self.l1**2 < (y)**2 + (z-increment)**2 < (self.l1+self.l2)**2:
                z-=increment
            else:
                pass

        # calculate the angle change for all motors
        if -1 <= (self.l1**2+self.l2**2-y**2-z**2)/(2*self.l1*self.l2) <= 1:
            gamma = math.acos((self.l1**2+self.l2**2-y**2-z**2)/(2*self.l1*self.l2))
            if -1 <= (self.l2*math.sin(gamma))/math.sqrt(y**2+z**2) <= 1:
                theta2 = math.pi-gamma
                delta = math.asin((self.l2*math.sin(gamma))/math.sqrt(y**2+z**2))
                theta1 = math.pi/2-math.atan(z/y)-delta
                theta1 = theta1*180.0/math.pi
                theta2 = theta2*180.0/math.pi
                theta3 = theta1 + theta2 - 90.0 + 12 # 12 is offset for theta 3
            else:
                theta1 = self.angle5; theta2 = self.angle4; theta3 = self.angle3
                return
        else:
            theta1 = self.angle5; theta2 = self.angle4; theta3 = self.angle3
            return
        return theta1, theta2, theta3, y, z


    def SetAngle(self,numservo,angle,increment,minangle=-100.0,maxangle=100.0):

        angle += increment
        print(angle)
        if angle >= maxangle:
            angle = maxangle
        elif angle <= minangle:
            angle = minangle
        self.arm.setPosition(numservo,round(float(angle),2),self.waitTime, wait=True)
        return round(float(angle),2) 	
    
    def intial_parameters(self):
        # order of keys in controller_node.py
        self.buttonkeys = ['Dpad up','Dpad down','Dpad left','Dpad right','x','o','t','s','L1', 'R1','L2','R2','share','options']
        
        #set up button mappings for directional buttons, PS4 controller
        self.butYpos = 'Dpad up'
        self.butYneg = 'Dpad down'
        self.butZpos = 'Dpad left'
        self.butZneg = 'Dpad right'

        # Min and max angle values for each joint
        self.xarmmin = -125.0
        self.xarmmax = 125.0
        self.minang1 = -11
        self.maxang1 = 32
        self.minang2 = self.xarmmin
        self.maxang2 = self.xarmmax
        self.minang3 = self.xarmmin
        self.maxang3 = self.xarmmax
        self.minang4 = self.xarmmin
        self.maxang4 = self.xarmmax
        self.minang5 = -78.0
        self.maxang5 = 91.0

        # initialization values for the robot arm 
        self.oldtheta3 = -20.0
        self.oldtheta2 = 100.0
        self.oldtheta1 = -45.0
        # prepare new theta value in 'for' loop
        self.theta1 = 0.0
        self.theta2 = 0.0
        self.theta3 = 0.0
        self.y = 3
        self.z = 15

        # Lengths of links in the arm 
        self.l1 = 11
        self.l2 = 15.2

        # time to wait between commands 
        self.waitTime = 1
        self.shutdown_started = False
	
        # Initialize xArm and servos 
        self.arm = xarm.Controller('USB')
        self.servo1 = xarm.Servo(1,0.0)
        self.servo2 = xarm.Servo(2,0.0)
        self.servo3 = xarm.Servo(3,0.0)
        self.servo4 = xarm.Servo(4,0.0)
        self.servo5 = xarm.Servo(5,0.0)
        self.servo6 = xarm.Servo(6,0.0)
        sleep(1)

        # Initialize angles for each joint
        # Notice: In xarm, the position paramter may be an int to 
        # indicate a unit position (0 to 1000)
        # or a float to indicate an angle in degrees (-125.0 to 125.0).
        self.angle1 = 0.0
        self.angle2 = 0.0
        self.angle3 = -21.0
        self.angle4 = 118.0
        self.angle4 = 75.0
        self.angle5 = -62.0
	
        # set the initial arm position:
        self.angleList_init = [self.angle1, self.angle2, self.angle3, self.angle4, self.angle5]
        for i in range(5):
            self.arm.setPosition(5-i, self.angleList_init[5-i-1], 800, wait=True)
        # set the climbing angles
        self.angleList_climing = [0.0,0.0,0.0,50.0,0.0]

    def SetAngleList(self,numrange, angleList_i, angleList_f,timespan):

        #start_time = time.time()
    
        for i in range(numrange):
            print(i,angleList_i[i], angleList_f[i])
            angle_diff = abs(angleList_i[i] - angleList_f[i])
            if angle_diff > 0.01:      # only set position if there's a difference greater than 0.001 radians
                self.arm.setPosition(i+1, round(float(angleList_f[i]),2), timespan, wait=True)
    
        #end_time = time.time()
        #print("Time passed: %f"%(end_time - start_time))



def main(args=None):
    rclpy.init(args=args)
    arm_node = ArmNode()

    # Register the on_shutdown function to be called when the node is shut down
    print("arm_node is running ...")

    # Spin the node to keep it running and processing callbacks
    rclpy.spin(arm_node)
    rclpy._shutdown(arm_node.on_shutdown)    # not sure if this is correct
    # Clean up the node after spinning
    arm_node.destroy_node()
    # Shutdown rclpy
    rclpy.shutdown()

if __name__ == '__main__':
    main()
