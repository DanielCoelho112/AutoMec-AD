#!/usr/bin/env python

import cv2
import numpy as np
import rospy
from std_msgs.msg import Int16

# PARAMETERS__________________________________________________________________

# Import Parameters
scale_import = 0.1  # The scale of the first image, related to the imported one.
N_red = 2  # Number of piramidizations to apply to each image.
factor_red = 0.8

# Font Parameters
subtitle_offset = -10
subtitle_2_offset = -10
font = cv2.FONT_HERSHEY_SIMPLEX
font_scale = 0.5
font_color = (0, 0, 255)
font_thickness = 2

# Line Parameters
line_thickness = 3

# Detection Parameters

scale_cap = 0.4
detection_threshold = 0.7

# Initial velocity
vel = 0

# ______________________________________________________________________________

# Images to import and Images Info
dict_images = {
    'pForward': {'title': 'Follow Straight Ahead', 'type': 'Panel', 'color': 'green', 'images': {}},
    'pStop': {'title': 'Stop', 'type': 'Panel', 'color': 'red', 'images': {}}
}

# Colors dictionary
dict_colors = {'red': (0, 0, 255), 'green': (0, 255, 0), 'blue': (255, 0, 0), 'yellow': (0, 255, 255)}

# Images Importation and Resizing
Counter_Nr_Images = 0
for name in dict_images.keys():

    # Key and Value for the Zero and Tilt Images
    images_key = '0'
    tilt1_key = '45'
    # tilt2_key = '-45'
    images_value = cv2.imread(name + '.png', cv2.IMREAD_GRAYSCALE)

    # Determination of required dimensions for the Zero Image
    width = int(images_value.shape[1] * scale_import)
    height = int(images_value.shape[0] * scale_import)
    dim = (width, height)

    # Resizing the Zero Image
    images_value = cv2.resize(images_value, dim)

    # Updating the dictionary with the Key and Value of the Zero Image
    dict_images[name]['images'][images_key] = images_value

    # Locate points of the signal which you want to transform
    pts1 = np.float32([[0, 0], [width, 0], [0, height], [width, height]])
    pts2 = np.float32([[0, 0], [width, 0], [width * 1 / 6, height], [width * 5 / 6, height]])
    # pts3 = np.float32([[0, height*1/6], [width, 0], [0, height*5/6], [width, height]])

    # Transform the original images into a tilted one
    matrix1 = cv2.getPerspectiveTransform(pts1, pts2)
    # matrix2 = cv2.getPerspectiveTransform(pts1, pts3)
    tilt1 = cv2.warpPerspective(images_value, matrix1, dim)
    # tilt2 = cv2.warpPerspective(images_value, matrix2, dim)

    # Updating the dictionary with the Key and Value of the tilted Image
    dict_images[name]['images'][tilt1_key] = tilt1
    # dict_images[name]['images'][tilt2_key] = tilt2

    Counter_Nr_Images += 2

    # Piramidization of the Zero and Tilt Image, creating smaller versions of it
    for n in range(N_red):
        # Defining the keys
        images_key = str(2 * n - 1)
        tilt1_keypyr = tilt1_key + "." + str(2 * n - 1)
        # tilt2_keypyr = tilt2_key + "." + str(2*n - 1)
        images_keyh = str(2 * n)
        tilt1_keypyrh = tilt1_key + "." + str(2 * n)
        # tilt2_keypyrh = tilt2_key + "." + str(2*n)

        # Creating another lair of piramidization, assuming dimensions stay the same between signals
        width = int(images_value.shape[1] * 3 / 4)
        height = int(images_value.shape[0] * 3 / 4)
        dim = (width, height)
        images_valueh = cv2.resize(images_value, dim)
        tilt1h = cv2.resize(tilt1, dim)
        # tilt2h = cv2.resize(tilt2, dim)

        # Pyramidization
        images_value = cv2.pyrDown(images_value)
        tilt1 = cv2.pyrDown(tilt1)
        # tilt2 = cv2.pyrDown(tilt2)

        # Updating the dictionary with the Key and Value
        dict_images[name]['images'][images_key] = images_value
        dict_images[name]['images'][tilt1_keypyr] = tilt1
        # dict_images[name]['images'][tilt2_keypyr] = tilt2
        dict_images[name]['images'][images_keyh] = images_valueh
        dict_images[name]['images'][tilt1_keypyrh] = tilt1h
        # dict_images[name]['images'][tilt2_keypyrh] = tilt2h
        Counter_Nr_Images += 6

# Number of Images Created
print("Number of images: " + str(Counter_Nr_Images))

for name in dict_images.keys():
    for key in dict_images[name]['images']:
        dict_images[name]['images'][key] = cv2.GaussianBlur(dict_images[name]['images'][key], (3, 3), 0)
        #cv2.imshow(name + ' ' + key, dict_images[name]['images'][key])

# VIDEO CAPTURE AND PROCESSING

# Start of video capture
cap = cv2.VideoCapture(0)

while True:

    # Reading and resizing one frame
    _, def_frame = cap.read()
    width_frame = def_frame.shape[1]
    height_frame = def_frame.shape[0]
    default_dim = (width_frame, height_frame)
    reduced_dim = (int(width_frame * scale_cap), int(height_frame * scale_cap))
    frame = cv2.resize(def_frame, reduced_dim)

    # Converting to a grayscale frame
    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    res = 0
    loc = 0
    max_res = 0
    max_loc = 0
    max_name = ''
    max_key = ''

    # For each image:
    for name in dict_images.keys():
        for key in dict_images[name]['images']:

            matrix_res = cv2.matchTemplate(gray_frame, dict_images[name]['images'][key], cv2.TM_CCOEFF_NORMED)
            res = np.max(matrix_res)
            loc = np.where(matrix_res == res)

            if res > max_res:
                max_res = res
                max_loc = loc

                max_name = name
                max_key = key

    max_width = int(dict_images[max_name]['images'][max_key].shape[1] / scale_cap)
    max_height = int(dict_images[max_name]['images'][max_key].shape[0] / scale_cap)
    max_dim = (max_width, max_height)

    if max_res > detection_threshold:

        for pt in zip(*max_loc[::-1]):
            pt = tuple(int(pti / scale_cap) for pti in pt)
            cv2.rectangle(def_frame, pt, (pt[0] + max_width, pt[1] + max_height),
                          dict_colors.get(dict_images[max_name]['color']), line_thickness)
            text = 'Detected: ' + max_name + ' ' + max_key + ' > ' + dict_images[max_name]['type'] + ': ' + \
                   dict_images[max_name]['title']
            # print(text)

            origin = (pt[0], pt[1] + subtitle_offset)
            origin_2 = (0, height_frame + subtitle_2_offset)
            # Using cv2.putText() method
            subtitle = cv2.putText(def_frame, str(max_name) + '_' + str(max_key) + ' ' + str(round(max_res, 2)), origin,
                                   font, font_scale, font_color, font_thickness, cv2.LINE_AA)
            subtitle_2 = cv2.putText(def_frame, text, origin_2, font, font_scale, font_color, font_thickness,
                                     cv2.LINE_AA)

        # Defining and publishing the velocity of the car in regards to the signal seen
        if max_name == "pForward":
            vel = 1
        elif max_name == "pStop":
            vel = 0

    # Defining the publisher and publishing the velocity
    pub = rospy.Publisher('pub_vel', Int16, queue_size=10)
    rospy.init_node('signal_velocity', anonymous=True)
    rospy.loginfo(vel)
    pub.publish(vel)

    # Show the frame
    '''frame = cv2.resize(frame, default_dim)'''
    #cv2.imshow("Working Frame", frame)
    cv2.imshow("Frame", def_frame)
    key = cv2.waitKey(1)

    if key == 27:  # Press "ESC"
        break  # End While cycle
cap.release()  # Stops Video Capture
cv2.destroyAllWindows()  # Closes all windows
