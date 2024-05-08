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
image_address = "./Hello_Austin/frame105.jpg"

# test the image address
# print(image_address)

# read the image
image = cv2.imread(image_address)

# convert BGR to RGB, we won't use this in any of the processes, just to test image loading
rgb_image = cv2.cvtColor(image , cv2.COLOR_BGR2RGB)

gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

# blur the image with a gussian filter to remove any noise, and also to soften the image
blurred = cv2.GaussianBlur(gray, (5, 5), 5)

# plot images in a nice array. We have to define the colormap for imshow to get a black and white image, as the default
# color map shows colors between yellow (pixel = 255) and black (pixel = 0)
fig , ax = plot_imshow_in_array([rgb_image , gray , blurred] , \
                                max_image_in_row = 4 , \
                                plots_kwargs_list = [{} , {'cmap':'gray', 'vmin':0, 'vmax':255} , {'cmap':'gray', 'vmin':0, 'vmax':255}] )

# use this command to place enough spacing between the borders of images and the numbers
fig.tight_layout()

thresh = cv2.threshold(blurred, 240, 255, cv2.THRESH_BINARY)[1]
plt.imshow(thresh)
plt.show()

# perform a series of erosions and dilations to remove
# any small blobs of noise from the thresholded image
thresh = cv2.erode(thresh, None, iterations=2)
thresh = cv2.dilate(thresh, None, iterations=4)

plt.imshow(thresh)
plt.show()

MAX_GREY_VALUE = 255
MAX_ALLOWED_PIXEL_IN_REGION = 3000
MIN_ALLOWED_PIXEL_IN_REGION = 300

contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

# find out regions and label them
labels = measure.label(thresh, connectivity=2, background=0)

# The list holding all contiguous masks that will be found
individual_masks = []

# loop over the unique components
for label in np.unique(labels):
    # if this is the background (dark) label, ignore it
    if label == 0:
        continue

    # otherwise, construct the label mask and count the number of pixels
    labelMask = np.zeros(thresh.shape, dtype="uint8")
    labelMask[labels == label] = MAX_GREY_VALUE
    numPixels = cv2.countNonZero(labelMask)

    # this condition filters "very" small regions
    if MAX_ALLOWED_PIXEL_IN_REGION > numPixels > MIN_ALLOWED_PIXEL_IN_REGION:
        plt.figure()
        individual_masks.append(labelMask)

plot_imshow_in_array(matrices_to_show=individual_masks, max_image_in_row=4)

circles_ratio_lst = []
## make a copy of the individual_mask to avoid them from being overwritten
individual_masks_cp = [mask.copy() for mask in individual_masks]

for idx, current_mask in enumerate(individual_masks_cp):
    cnts = cv2.findContours(current_mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = imutils.grab_contours(cnts)
    #     cnts = contours.sort_contours(cnts)[0]

    ## create a mask to hold the values of the enclosing circle, we also fill inside the cirlce.
    filled_circle = np.zeros(current_mask.shape)

    ## find the coordinates of the center and the radius of the circle
    ((cX, cY), radius) = cv2.minEnclosingCircle(cnts[0])

    ## fill the mask values surrounded by the circle
    cv2.circle(filled_circle, (int(cX), int(cY)), int(radius), (255, 255, 255), -1)

    ## count the number of pixels in the circle
    circle_area = cv2.countNonZero(filled_circle)

    ## count the number of non-zero pixels in the original region
    mask_non_zero_area = cv2.countNonZero(individual_masks[idx])

    ## plot the circle and the region, and show the filled ratio in each circle
    plot_imshow_in_array([filled_circle, individual_masks[idx]], max_image_in_row=4)
    circles_ratio_lst.append(mask_non_zero_area / circle_area)

    plt.title("circles' filled ratio = {:.2}".format(mask_non_zero_area / circle_area))

    plt.show()

if max(circles_ratio_lst) > 0.85:
    max_idx = max(enumerate(circles_ratio_lst), key=lambda x: x[1])[0]

    plt.imshow(individual_masks[max_idx])
    plt.show()

    avg = np.mean(individual_masks[max_idx])
    print(avg)
else:
    avg = 0


