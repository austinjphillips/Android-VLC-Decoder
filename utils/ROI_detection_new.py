from imutils import contours
from skimage import measure
import numpy as np
import argparse
import imutils
import cv2
import matplotlib.pyplot as plt
import os


def plot_imshow_in_array(matrices_to_show: list, max_image_in_row: int = 4, plots_kwargs_list: list = []):
    """
        Plots the image list in an array of row * col , where max(col) = max_image_in_row, and the
        number of rows is calculated accordingly.
        @param matrices_to_show a list of matrices to be plotted using plt.imshow
        @param max_image_in_row maximum number of plots in one row
        @param plots_kwargs_list list of dictionaries of parameters of each plot

    """
    # total number of plots
    plot_count = len(matrices_to_show)

    assert len(plots_kwargs_list) == 0 or len(plots_kwargs_list) == len(matrices_to_show), """ plots_kwargs_list should be either an empty 
                                                                                    list or should have the same number of members
                                                                                    as matrices_to_show """

    # number of rows
    nrow = plot_count // max_image_in_row + (1 if (plot_count % max_image_in_row > 0) else 0)

    # number of columns
    ncol = max_image_in_row if plot_count >= max_image_in_row else plot_count

    # plotting using imshow
    fig, ax = plt.subplots(nrow, ncol, figsize=(12, 6))
    for i in range(plot_count):

        # select the subplot
        plt.subplot(nrow, ncol, i + 1)

        # format the argument dictionary of the imshow function
        if (len(plots_kwargs_list) == 0):
            config_dict = {}
        else:
            config_dict = plots_kwargs_list[i]

        # pass the image as well as extra arguments to the imshow function
        plt.imshow(matrices_to_show[i], **config_dict)

    return fig, ax


# address of the image to be processed
image_address = "./15Hz_75cm/frame92.jpg"

# read the image
image = cv2.imread(image_address)

# convert BGR to RGB, we won't use this in any of the processes, just to test image loading
rgb_image = cv2.cvtColor(image , cv2.COLOR_BGR2RGB)

hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

lower_red = np.array([150, 120, 100])
upper_red = np.array([200, 255, 255])
mask1 = cv2.inRange(hsv, lower_red, upper_red)

# join my masks
mask = mask1

# apply the mask to the original image
output_img = image.copy()
output_img[np.where(mask == 0)] = 0

gray = cv2.cvtColor(output_img, cv2.COLOR_HSV2BGR)
gray = cv2.cvtColor(gray, cv2.COLOR_BGR2GRAY)

# blur the image with a gussian filter to remove any noise, and also to soften the image
blurred = cv2.GaussianBlur(gray, (5, 5), 10)

# plot images in a nice array. We have to define the colormap for imshow to get a black and white image, as the default
# color map shows colors between yellow (pixel = 255) and black (pixel = 0)
fig , ax = plot_imshow_in_array([rgb_image , gray , blurred] , \
                                max_image_in_row = 4 , \
                                plots_kwargs_list = [{} , {'cmap':'gray', 'vmin':0, 'vmax':255} , {'cmap':'gray', 'vmin':0, 'vmax':255}] )

# use this command to place enough spacing between the borders of images and the numbers
fig.tight_layout()

thresh = cv2.threshold(blurred, 160, 255, cv2.THRESH_BINARY)[1]
plt.imshow(thresh)
plt.show()

# perform a series of erosions and dilations to remove
# any small blobs of noise from the thresholded image

plt.imshow(thresh)
plt.show()

circles_ratio_lst = []


cnts = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
cnts = imutils.grab_contours(cnts)
cv2.drawContours(thresh, cnts, -1, (255, 255, 255), thickness=cv2.FILLED)

if cv2.countNonZero(thresh) > 300:

    # create a mask to hold the values of the enclosing circle, we also fill inside the cirlce.
    filled_circle = np.zeros(thresh.shape)

    # find the coordinates of the center and the radius of the circle
    ((cX, cY), radius) = cv2.minEnclosingCircle(cnts[0])

    # fill the mask values surrounded by the circle
    cv2.circle(filled_circle, (int(cX), int(cY)), int(radius), (255, 255, 255), -1)

    # count the number of pixels in the circle
    circle_area = cv2.countNonZero(filled_circle)

    # count the number of non-zero pixels in the original region
    mask_non_zero_area = cv2.countNonZero(thresh)

    # plot the circle and the region, and show the filled ratio in each circle
    plot_imshow_in_array([filled_circle, thresh], max_image_in_row=4)
    circles_ratio_lst.append(mask_non_zero_area / circle_area)

    plt.title("circles' filled ratio = {:.2}".format(mask_non_zero_area / circle_area))

    plt.show()

if max(circles_ratio_lst) > 0.8:
    max_idx = max(enumerate(circles_ratio_lst), key=lambda x: x[1])[0]

    avg = np.mean(thresh)
    print(avg)
else:
    avg = 0

