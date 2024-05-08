import cv2
import matplotlib.pyplot as plt
import numpy as np
import cv2 as cv
from imutils import contours
import imutils
import requests
import crc8


sig_lst = []
found_first_transition = False

# *** LOAD CAMERA ***
# Change the port number, e.g. (4747), to what DroidCam says
url = "http://127.0.0.1:4747"
# Load camera using OpenCV, may need to adjust the camera number (0)
cap = cv2.VideoCapture(0)

# Check if the webcam is opened correctly
if not cap.isOpened():
    raise IOError("Cannot open webcam")

bitstream = ''
msg_bitstream = ''
msg_decoded = ''
message = []
msg_length = 4
preamble = '1010011010011010'
read_message = False
message_received = False
received_parity = 0
n_bit = 0
msg = ''
crc_rx = ''

sync_1 = '11110'
sync_2 = '0001'
sync_3 = '000000000011'

rx_synchronized = False
skip = 0

sig_prev = 0
sig_curr = 0

count = 0
circ_perc = 0
while True:

    avg = 0
    # Read frame from camera
    ret, frame = cap.read()
    # Read FPS from camera
    fps = cap.get(cv2.CAP_PROP_FPS)
    # Read timestamp from camera
    timestamp = cap.get(cv2.CAP_PROP_POS_MSEC)
    # Resize image and flip
    frame = imutils.resize(frame, width=640, height=480)
    frame = cv2.flip(frame, 1)
    frame = cv2.flip(frame, 0)


    # *** LED CONTOUR DETECTION ***
    # We can detect the contour of the LED by filtering out the red band around the LED
    hsv_image = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    # We can detect the contour of the LED by filtering out the red band around the LED
    lower_red = np.array([100, 150, 250], np.uint8)
    upper_red = np.array([110, 255, 255], np.uint8)
    red_mask = cv2.inRange(hsv_image, lower_red, upper_red)

    # *** LED CENTRE EXTRACTION
    # Filter out bright objects of image (LED, but also light sources)
    centre_mask = cv2.inRange(frame, np.array([225, 225, 225]), np.array([255, 255, 255]))
    bgr_threshed = centre_mask

    # Blur the image with a gaussian filter to remove any noise, and also to soften the image
    # Dilate the pixels of the image to repair the red circle border around the LED
    # thresh = cv2.erode(red_mask, None, iterations=1)
    # thresh = cv2.erode(red_mask, None, iterations=1)
    thresh = cv2.dilate(red_mask, None, iterations=10)

    contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
    # cv2.drawContours(frame, contours, -1, (0, 255, 0), 3)

    # cnt = contours[0]
    # ellipse = cv2.fitEllipse(cnt)
    # cv2.ellipse(frame, ellipse, (0, 0, 255), 3)

    # Find the LED contour parameters
    circles = cv2.HoughCircles(thresh, cv2.HOUGH_GRADIENT_ALT, dp=1.5, minDist=5, param1=10, param2=0, minRadius=5, maxRadius=0)

    # print(circles)

    # If the LED contour is present, extract the circle parameters: midpoint and radius
    if circles is not None:
        x, y, radius = circles[0][0]

        cv2.circle(frame, (int(x), int(y)), int(radius), (0, 255, 0), 2)

        x1 = max(0, int(x - radius))
        x2 = min(int(x + radius), 640)
        y1 = max(0, int(y - radius))
        y2 = min(int(y + radius), 480)

        cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)

        # Create a square mask with the same shape as bgr_threshed
        square_mask = np.zeros(bgr_threshed.shape, dtype=np.uint8)

        # Draw a filled white rectangle on the square mask
        cv2.rectangle(square_mask, (x1, y1), (x2, y2), 255, thickness=-1)

        # Apply the square mask to bgr_threshed to extract the pixels within the square
        values = cv2.bitwise_and(bgr_threshed, square_mask)
        cropped_values = values[y1:y2, x1:x2]
        # pts = np.array([[[x1, y1], [x1, y2], [x2, y1], [x2, y2]]], dtype=np.int32)
        # cv2.fillPoly(square_mask, [[[x1, y1]], [[x2, y2]]], (255, 255, 255))
        # values = cv2.bitwise_and(bgr_threshed, square_mask)
        #
        cv2.imshow("LED Centre", values)
        cv2.imshow("Zoomed Centre", cropped_values)

        avg = np.mean(cropped_values)

        circ_perc += 1



    # Plot image processing steps
    # From left to right: original frame - LED contour detection - LED centre detection
    images = np.hstack((frame, cv2.cvtColor(thresh, cv2.COLOR_GRAY2BGR), cv2.cvtColor(bgr_threshed, cv2.COLOR_GRAY2BGR)))
    cv2.imshow("Images", images)

    # if avg > 0:
    #     print("1")
    # else:
    #     print("0")

    # print(circles)

    # if not found_first_transition and sig == 1:
    #     sig_lst.append(sig)
    #     found_first_transition = True
    #
    # if found_first_transition:
    #     sig_lst.append(sig)
    #
    # if len(sig_lst) == 64:
    #     break

    c = cv2.waitKey(1)
    if c == 27:
        break

    print(avg)

    count += 1
    # print(circ_perc / count * 100)
    if avg > 5:
        sig = 1
    else:
        sig = 0

    sig_curr = sig

    if read_message:
        if len(msg_decoded) < 8:
            if skip == 0:
                if [sig_prev, sig_curr] == [1, 0]:
                    msg_bitstream += f"{sig_prev}{sig_curr}"
                    msg += '1'
                    msg_decoded += '1'
                    skip = 5
                elif [sig_prev, sig_curr] == [0, 1]:
                    msg_bitstream += f"{sig_prev}{sig_curr}"
                    msg += '0'
                    msg_decoded += '0'
                    skip = 5
                else:
                    skip = 0
        elif len(msg_decoded) < 16:
            if skip == 0:
                if [sig_prev, sig_curr] == [1, 0]:
                    msg_bitstream += f"{sig_prev}{sig_curr}"
                    crc_rx += '1'
                    msg_decoded += '1'
                    skip = 5
                elif [sig_prev, sig_curr] == [0, 1]:
                    msg_bitstream += f"{sig_prev}{sig_curr}"
                    crc_rx += '0'
                    msg_decoded += '0'
                    skip = 5
                else:
                    skip = 0
        else:
            message_received = True
    else:
        bitstream += f"{sig}"

    if message_received:

        print(f"Checking Checksum: {crc_rx}...")
        msg_encode = msg.encode('utf-16')[:1]
        calc_crc = crc8.crc8()
        calc_crc.update(msg_encode)
        crc_calc = int(calc_crc.hexdigest(), 16)
        crc_rx_int = int(crc_rx, 2)
        print(int(calc_crc.hexdigest(), 16))
        print(crc_rx)
        print(int(crc_rx))
        print(int(crc_rx, 2))
        print(hex(int(crc_rx, 2)))

        if crc_calc == crc_rx_int:
            print(f"Correct Checksum! Decoding message...")
            # msg_string = decode_message(message)
            print(f"Message received: {msg}")
        else:
            print(f"Incorrect Checksum! Trying again...")

        bitstream = ''
        message = []

        calc_crc.reset()

    if sync_3 in bitstream:
        rx_synchronized = True
        bitstream = ''
        msg_bitstream = ''
        msg_decoded = ''
        skip = 1

    if not read_message and rx_synchronized and skip == 0:
        if [sig_prev, sig_curr] == [1, 0]:
            msg_bitstream += f"{sig_prev}{sig_curr}"
            msg_decoded += '1'
            skip = 4
        elif [sig_prev, sig_curr] == [0, 1]:
            msg_bitstream += f"{sig_prev}{sig_curr}"
            msg_decoded += '0'
            skip = 4
        else:
            skip = 0
    else:
        if skip > 0:
            skip -= 1

    if preamble in msg_bitstream:
        print(f"Detected Preamble: {preamble}...")
        idx = bitstream.find(preamble)
        read_message = True
        msg_bitstream = ''
        msg_decoded = ''

    sig_prev = sig_curr
    print(f"Sig: {sig}")
    print(f"Bitsream: {bitstream}")
    print(f"Msg Bitstream: {msg_bitstream}")
    print(f"Decoded: {msg_decoded}")
    print(f"Message: {msg}")
    print(f"Checksum: {crc_rx}")
    print(f"Skip: {skip}")
    print("====================================================")


cap.release()
cv2.destroyAllWindows()

print(sig_lst)


# *** EXTRA OLD CODE ***
# hsv_new = cv2.cvtColor(frame, cv2.COLOR_BGR)


#
# cv2.imshow('Mask 1', mask1)
#

#
# cv2.imshow('hsv', bgr_threshed)
#
# # print(hsv[211, 395])
#
# lower_red = np.array([10, 10, 250], np.uint8)
# upper_red = np.array([15, 15, 255], np.uint8)
# mask0 = cv2.inRange(hsv, lower_red, upper_red)
#
# frame_threshed_lower = cv2.inRange(hsv, lower_red, upper_red)
#
# cv2.imshow('Output Mask0', frame_threshed_lower)
#
# bgr_threshed += frame_threshed_lower
#
# frame_threshed_upper = cv2.inRange(frame, lower_red, upper_red)
# cv2.imshow('Output Mask1', frame_threshed_upper)
#
#
# combined = bgr_threshed
#
# first_imgs = np.hstack((cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR), cv2.cvtColor(frame_threshed_lower, cv2.COLOR_GRAY2BGR), cv2.cvtColor(frame_threshed_upper, cv2.COLOR_GRAY2BGR), cv2.cvtColor(combined, cv2.COLOR_GRAY2BGR)))
#
# cv2.imshow('Images', first_imgs)
#
# mask = mask0 + mask1
#
# output_img = frame.copy()
# output_img[np.where(mask == 0)] = 0
#
# bgr = cv2.cvtColor(output_img, cv2.COLOR_HSV2BGR)
#
# gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)


# thresh = cv2.threshold(mask1, 0, 255, cv2.THRESH_BINARY)[1]
# thresh = cv2.erode(thresh, None, iterations=2)


# cnts1 = cv2.findContours(mask1, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
# cnts1 = imutils.grab_contours(cnts1)
# mask1 = cv2.drawContours(mask1, cnts1, -1, (255, 255, 255), thickness=cv2.FILLED)
# cv2.imshow('Contours Mask 1', mask1)
#
# cnts = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
# cnts = imutils.grab_contours(cnts)
# filled = thresh.copy()
# filled = cv2.drawContours(filled, cnts, -1, (255, 255, 255), thickness=cv2.FILLED)
