from machine import Pin
import time


IN1 = Pin(4, Pin.OUT)
IN2 = Pin(3, Pin.OUT)
IN3 = Pin(2, Pin.OUT)
IN4 = Pin(1, Pin.OUT)

current_direction = 1

# definer stepsekvensen for motoren
seq_clockwise = [
    (1, 0, 0, 0),
    (1, 1, 0, 0),
    (0, 1, 0, 0),
    (0, 1, 1, 0),
    (0, 0, 1, 0),
    (0, 0, 1, 1),
    (0, 0, 0, 1),
    (1, 0, 0, 1)
]

seq_counterclockwise = [
    (1, 0, 0, 1),
    (0, 0, 0, 1),
    (0, 0, 1, 1),
    (0, 0, 1, 0),
    (0, 1, 1, 0),
    (0, 1, 0, 0),
    (1, 1, 0, 0),
    (1, 0, 0, 0)
]

def rotate_half():
	global current_direction
	
	half_revolution_steps = 100
	
	if current_direction == 1:
	
		step_motor(half_revolution_steps, 0.001, seq_clockwise)
		current_direction = -1
	
	else:
		step_motor(half_revolution_steps, 0.001, seq_counterclockwise)
		current_direction = 1

def step_motor(steps, delay=0.0002, sequence=None):
    for _ in range(steps):
        for s in sequence:
            IN1.value(s[0])
            IN2.value(s[1])
            IN3.value(s[2])
            IN4.value(s[3])
            time.sleep(delay)

if __name__=="__main__":

	while True:
		rotate_half()
		time.sleep(1)