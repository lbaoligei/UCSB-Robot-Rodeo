import rclpy
import RPi.GPIO as GPIO
from rclpy.node import Node
from sensor_msgs.msg import Joy
import time
import threading

class TailNode(Node):
    def __init__(self):
        super().__init__('tail_node')
        self.subscription = self.create_subscription(Joy, 'controller_command_dt', self.joy_callback, 10)
        self.subscription

        # Set GPIO pin assignments for tail motor
        self.tail_motor_pwm = 9
        self.tail_motor_dir = 11

        # Initialize RPi.GPIO and set GPIO pins as output
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.tail_motor_pwm, GPIO.OUT)
        GPIO.setup(self.tail_motor_dir, GPIO.OUT)

        # Initialize PWM
        self.tail_motor = GPIO.PWM(self.tail_motor_pwm, 100)
        self.tail_motor.start(0)
        self.subroutine_thread = None
        self.exit_subroutines = False
    
    def move_tail(self, duration, speed, direction):
        tail_speed = speed if direction == 1 else -speed
        self.set_motor_speed(self.tail_motor, self.tail_motor_dir, tail_speed)
        
        start_time = time.time()
        while time.time() - start_time < duration:
            if self.exit_subroutines:
                break
            time.sleep(0.1)

        self.set_motor_speed(self.tail_motor, self.tail_motor_dir, 0)

    def joy_callback(self, msg):
        l1 = msg.buttons[0]  # L1 button
        r1 = msg.buttons[1]  # R1 button

        if msg.buttons[4] == 1:
            self.exit_subroutines = True
        else:
            self.exit_subroutines = False
        
        if msg.buttons[2] == 1: 
            tail_duration = 3  # Duration in seconds
            tail_speed_percentage = 50  # Speed percentage
            direction = 1  # Use "up" or "down"
            self.subroutine_thread = threading.Thread(target=self.move_tail, args=(tail_duration, tail_speed_percentage, direction))
            self.subroutine_thread.start()
        
        if msg.buttons[3] == 1: 
            tail_duration = 3  # Duration in seconds
            tail_speed_percentage = 50  # Speed percentage
            direction = -1  # Use "up" or "down"
            self.subroutine_thread = threading.Thread(target=self.move_tail, args=(tail_duration, tail_speed_percentage, direction))
            self.subroutine_thread.start()
    
        # SET THIS PART TO CHANGE MOTOR SPEED!!
        tail_speed_perc = 50   # between -100 to 100

        if l1:
            # Control the tail's direction when L1 is pressed
            self.set_motor_speed(self.tail_motor, self.tail_motor_dir, tail_speed_perc)
        elif r1:
            # Control the tail's direction when R1 is pressed
            self.set_motor_speed(self.tail_motor, self.tail_motor_dir, -tail_speed_perc)
        else:
            self.set_motor_speed(self.tail_motor, self.tail_motor_dir, 0)

    def set_motor_speed(self, motor, dir_pin, speed):
        # Determine the direction of the motor based on the sign of the speed
        direction = 1 if speed >= 0 else 0
        # Get the absolute value of the speed
        speed = abs(speed)

        # Set the direction GPIO pin
        GPIO.output(dir_pin, direction)
        # Set the motor PWM duty cycle to control the speed
        motor.ChangeDutyCycle(speed)

    def on_shutdown(self):
        # stop the motor
        self.set_motor_speed(self.tail_motor, self.tail_motor_dir, 0)
        # Clean up GPIO settings
        GPIO.cleanup()


def main(args=None):
    rclpy.init(args=args)
    tail_node = TailNode()
    print("tail_node is running ...")

    try:
        rclpy.spin(tail_node)
    except KeyboardInterrupt:
        pass

    rclpy._shutdown(tail_node.on_shutdown())
    tail_node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
