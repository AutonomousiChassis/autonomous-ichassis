'''
This is rpi-chassis.py. It is the primary program that runs the RPi Chassis.
The live navigation and object detection will reside within this program.
'''

# Our required libaries
import time 							# Used to sleep
from picarx import Picarx 				# Import our Picarx object
from picamera import PiCamera			# Import our Picamera object
from picamera.array import PiRGBArray  # Import the RGB array for picamera
import cv2								# Import opencv, used for object detection/image proccessing
import rpi_imu				# Import our IMU script
from rpi_gps import GPS								# Import our GPS script
# Import tflite, used for running an object-detection model
from tflite_support.task import core
from tflite_support.task import processor
from tflite_support.task import vision

#Making these easy to change so that its easier to test
num_objects = 3 #number of objects the camera will detect

# This is a helper function for object_detection. It reads in RPi Chassis object and a tuple.
# It will then update the tuple based on the ultrasonic sensors output
def ultrasonic_detect(rpi_chassis, object):
	#print("In ultrasonic detection")

	# Check if the ultrasonic sensor detects an object
	distance = rpi_chassis.ultrasonic.read()
	print("Ultrasonic distance: " + str(distance))

	# If the distance is less than 30, we have detected an object!
	if distance < 30:
		# Set our tuple that an object has been detected
		is_there = [True]
		there = ["unknown"]
		object = (is_there, there, there)

	return object


#This is a helper function to determine where an object is located 
def get_obj_location(boxLocation):
	local = ''
	#Getting the coordinates of the center of the box surrounding the object (automatically generated)
	x_origin = boxLocation.origin_x
	y_origin = boxLocation.origin_y
	x_len = boxLocation.width
	x_len = x_len / 2
	y_len = boxLocation.height
	y_len = y_len /2
	x = x_origin + x_len
	y = y_origin + y_len
	#Determining the location using the center of the object
	if x < 213:
		if y < 213:
			local = "Top Left"
		elif y < 426:
			local = "Center Left"
		else:
			local = "Bottom Left"
	elif x < 426:
		if y < 213:
			local = "Top Middle"
		elif y < 426:
			local = "True Middle"
		else:
			local = "Bottom Middle"
	else:
		if y < 213:
			local = "Top Right"
		elif y < 426:
			local = "Center Right"
		else:
			local = "Bottom Right"

	return local


# This is a helper function for object detection. It reads in the streamed image and a tuple.
# It will update the tuple based on the camera's input.
def camera_detect(img, object, detector):
	# Reduce the image size for reduced calculation & efficiency
	# Camera goes here
	rgb_image = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
	input = vision.TensorImage.create_from_array(rgb_image)
	dobject = detector.detect(input)
	#print("dobject: " + str(dobject))
	#object_detected = dobject.detections
	is_found = []
	obj_type = []
	locat = []
	if dobject.detections:
		for obj in dobject.detections:
			#object_detected = dobject.detections[0]
			obj_cat = obj.categories[0]
			obj_loc = obj.bounding_box
			#print("object_detected: " + str(object_detected))
			#print("obj_cat: " + str(obj_cat))
			#print("obj_loc: " + str(obj_loc))
			#Getting the object category
			is_found.append(True)
			obj_type.append(str(obj_cat.category_name))
		#print("obj_type: " + str(obj_type))
			locat.append(str(get_obj_location(obj_loc)))
		#print("locat: " + str(locat))
		object = (is_found, obj_type, locat)		
	return object


def clean_cam_objects(objects):
	# For every object in the objects list	
	for object in objects:
		obj_found, obj_type, obj_loc = object
		print("Object Type: + str(obj_type))
		
		# If it is not a person, remove
		if not obj_type == 'person':
			

def object_detection(rpi_chassis, img, detector):
	#print("In object-detection")

	# This is what our function will return
	# (True/False if object detected, Type of object, Location of Object)
	object = (False, "unknown", "unknown")

	# Update the object based on the ultrasonic sensor input
	object = ultrasonic_detect(rpi_chassis, object)

	# Check if the camera has detected an object
	object = camera_detect(img, object, detector)

	# Return the object information
	return object


# Note: The following 3 functions will likely be adjusted to include better accuracy/calibration
# Returns the (x,y,z) coordinates of the accelerometer
def get_accelerometer():
	return (IMU.readACCx(), IMU.readACCy(), IMU.readACCz())


# Returns the (x,y,z) coordinates of the gyrometer
def get_gyrometer():
	return (IMU.readGYRx(), IMU.readGYRy(), IMU.readGYRz())


# Returns the (x,y,z) coordinates of the magnetometer
def get_magnetometer():
	return (IMU.readMAGx(), IMU.readMAGy(), IMU.readMAGz())


# This is where the primary repeated navigation code will reside, for now it is a place holder
def navigation(objects, cur_coord, goal_coord):
	return "forward" or "left" or "right" or "backward" or "left_backward" or "right_backward"



# This is the main driver function
if __name__ == "__main__":
	print("Starting RPi-Chassis")
	start_time = time.time()
	# Initialize the PicarX object for our RPi Chassis
	rpi_chassis = Picarx()
	# Initilize the Picamera object
	rpi_camera = PiCamera()
	# Set the camera's resolution and framerate
	rpi_camera.resolution = (640,480) 	# Our camera can support other but at slower FPS
	rpi_camera.framerate = 90			# Our camera can support 90 fps
	# Create our rgb array for camera
	raw_capture = PiRGBArray(rpi_camera, size=rpi_camera.resolution)
	# Allow the camera to warm up
	time.sleep(2)
	print("Finished initializing")
	print("Elasped time: " + str(time.time()-start_time))
	# Our infinate loop for continuous object-detection and navigation
	# Get continuous input from our camera NOTE: This is also an infiniate loop!
	boption = core.BaseOptions(file_name='tf_lite_models/efficientdet_lite0.tflite', use_coral=True, num_threads=2)
	doption = processor.DetectionOptions(max_results=num_objects, score_threshold=0.6)
	options = vision.ObjectDetectorOptions(base_options=boption, detection_options=doption)
	detector = vision.ObjectDetector.create_from_options(options)
	#rpi_chassis.stop()
	for frame in rpi_camera.capture_continuous(raw_capture, format='bgr', use_video_port=True):
		print("\n\nBeginning of loop:")
		print("Elasped time: " + str(time.time()-start_time))
		# Convert our image into an array
		img = frame.array
		# Detect objects using the object detection function
		is_object, object_type, object_location = object_detection(rpi_chassis, img, detector)
		movement = navigation(object, 0, 0)
		# The current count
		count_obj = 0
		# If there is no object in frame we want the robot to move forward
		if is_object:
			# if there are any objects in detected we want it to stop print info on all detected
			rpi_chassis.stop()
			while count_obj < len(is_object):
				#rpi_chassis.stop()
				print("There is an object!")
				print("Type: " + object_type[count_obj])
				print("Location: " + object_location[count_obj])
				if "Right" in object_location[count_obj]:
					print("Move Left")
					#rpi_chassis.steer_left()
					#rpi_chassis.forward(5)
				elif "Left" in object_location[count_obj]:
					print("Move Right")
					#rpi_chassis.steer_right()
					#rpi_chassis.forward(5)
				else:
					print("Stopping")
					rpi_chassis.stop()
				count_obj += 1


		else:
			# Move forward
			print("Move forward")
			#rpi_chassis.forward(5)
			'''
			print("No object detected!")
			if movement == 'forward':
				rpi_chassis.steer_straight()
				rpi_chassis.forward(5)
			elif movement == 'left':
				# To turn left we steer left and move forward for 1.5 seconds
				rpi_chassis.steer_left()
				start_time = time.time()
				# Until we hit 1.5 seconds, move forward, while checking for objects
				while not ((time.time() - start_time) == 1.5):
					move(o)
			elif movement == 'right':
				rpi_chassis.steer_right()
				rpi_chassis.forward(5)
			elif movement == 'backward':
				rpi_chassis.backward(5)
			'''

		print("The number of objects detected was: " + str(count_obj))

		'''
		print("Elasped time: " + str(time.time()-start_time))
		# Get the coordinates from the gps
		latitude, longitude = GPS.get_coordinates()
		# Print the latitude and longitude
		print("Latitude: ", latitude)
		print("Longitude: ", longitude)

		print("Elasped time: " + str(time.time()-start_time))
		# Get the course and speed
		course, speed = GPS.get_course_speed()
		# Print the course and speed
		print("Course: ", course)
		print("Speed: ", speed)

		print("Elasped time: " + str(time.time()-start_time))
		cur_coord = (latitude, longitude)
		goal_coord = (0,0)

		'''
		print("Elasped time: " + str(time.time() - start_time))

		# Slow down output
		time.sleep(.5)
		# Show the image
		#cv2.imshow('RPi Camera', img)
		# Release image cache
		raw_capture.truncate(0)

		#k = cv2.waitKey(1) & 0xFF
		#if k == 27:
		#	break
