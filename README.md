# Android VLC Decoder App

## Austin Phillips, Eric Kooij

This repo presents the development of an Android app for decoding Visible Light Communication (VLC) signals transmitted by an LED, allowing users to receive and display encoded messages. Developed for educational environments, the app enables real-time retrieval of lecture hall information via the Android app on a smartphone.

The LED transmitter sends a dataframe, including the room number that has been programmed into it. Then, the receiver (the smartphone), receives the dataframe and decodes it, checking with the student's timetable to determine which they have entered the right lecture hall for their lecture.

## Methodology

### Transmitter
The transmitter is built upon an Arduino Due with the CESE4110 VLCS course shield on top:

<img src="https://github.com/austinjphillips/android-vlc-decoder/blob/main/images/VLC-board.png" width=50% height=50%>

Since the dataframe must be received while passing under the transmitter, the dataframe format was kept as short as possible to minimize the transmission time. The standard format uses only three bytes that are placed in the dataframe as follows:

| 1st byte | 2nd byte | 3rd byte |
| --- | --- | --- |
| preamble | room number | CRC |

To shrink the dataframe further, some experiments were conducted using a parity check instead of a CRC. This resulting dataframe contains only two bytes and a single bit for the parity check, resulting in the following format:

| 1st byte | 2nd byte | Last bit |
| --- | --- | --- |
| preamble | room number | parity |

The dataframe is encoded by the Manchester encoding method and then sent by the binary transmission method. The transmitter sends the dataframe continuously to receivers passing by. The room number to be transmitted can be reconfigured on the fly by the UART communication channel, and its value is stored in the board's memory such that power losses will not require human action to recover the functionality.

### Receiver
The receiver obtains the dataframe from the smartphone's camera, making use of its global shutter. Then, depending on whether a red or blue LED is used for transmission, a specific image mask is applied to the frame to allow only the contour of the LED itself to pass through. With the LED isolated, a circle contour detection function provided by OpenCV’s toolbox is used to find the LED and mark it with a bounding box for visualization purposes. The light intensity values from this bounding box are then measured in order to be able to obtain the transmitted signal.

Apart from the image processing task, the receiver follows a standard procedure for the data reception: preamble detection, Manchester decoding, CRC checking, and message decoding. As mentioned previously, the received message will then be checked with the timetable if received successfully and a popup will be displayed to indicate whether the person has entered the right room or not. These steps have all been visualized in the custom android app for a better user experience.

![VLCS Android App Layout](https://github.com/austinjphillips/android-vlc-decoder/blob/main/images/app-layout.png?raw=true)

## Evaluation

### Setup
To test the Android app, the LED transmitter and the smartphone camera are set up in a bright office. The smartphone is positioned with the front display facing upwards, as this would mimic the position that someone would hold their phone as they walk through a door.

<img src="https://github.com/austinjphillips/android-vlc-decoder/blob/main/images/test-setup.png" width=40% height=40%>

The transmitter is hand-held to simulate hand jitter, and is rotated and tilted to test reliability. The data rates and error data are measured to assess how the system performs within these conditions, and is used to improve the system.

| Implementation | Range [cm] | Data Rate [Hz] / Goodput [bps] | Bit Error Rate [%] |
| --- | --- | --- | --- |
| CRC Checksum | 40 (bright), 65 (dark) | 10 (1/3 FPS) / 1.667 | 1.25 (1 incorrect bit over 10 transmissions) |
| Parity Bit | 40 (bright), 65 (dark) | 10 (1/3 FPS) / 2.353 | 7.5 (6 incorrect bits over 10 transmissions) |

### Effect of Rotations
The system is marginally affected by rotation and angling of the smartphone, since the receiver makes use of a robust object detection algorithm. Angling the smartphone of up to 25 degrees with respect to the transmitter can be achieved before the link becomes unreliable. Slow movement and rotations have little effect. Hence, the link is reliable even with normal hand jitter.

### Effect of Ambient Light
It is difficult to optimize the parameters of the contour masks for both dark and bright conditions, as the smartphone automatically adjusts its exposure. For bright conditions you would like to pass as much blue light from the LED since the exposure is shorter. However, for dark conditions you would like to limit how much blue light is passed through, as the exposure is longer. So a compromise must be made and the ideal performance cannot be achieved for different lighting conditions.

### Flicker
Since the transmitter operates at 10 Hz (⅓ camera FPS), flicker is observable to the eye. 

## Discussion
Creating and debugging the Android app contributed to a significant portion of the work for this project. There was little documentation on how to operate OpenCV on Android, which resulted in lots of debugging before the app stopped crashing. For example, it was determined that you cannot perform image processing in OpenCV’s default BGR image format, but rather needed to do so in RGB format, otherwise the app would crash. Furthermore, accessing the URLs for the building/hall and calendar information, as well as displaying the popup, was intuitive on the computer, but this implementation did not translate smoothly into the Android app.
Aside from the app development, determining a reliable and feasible method to detect the LED was also difficult. Many LED detection implementations would be too computationally intensive to operate on a smartphone, given real-time retrieval of the lecture hall information. Hence, many hours were spent on this.

Within the project scope, a working concept was developed in relatively short time. However, future work can build upon making the link more reliable, receiving at higher distances, and achieve better data rates. This can be done by implementing e.g. Hamming code into the message, to allow for 1 or multiple bit flips to occur and the message to still be received properly. Furthermore, different LED colors should be investigated to determine their suitability for different lighting conditions - a blue LED was more reliable for a brighter environment.

This setup can also be applied to other use cases as well: on a moving drone, tracking aircraft in the night sky (blinking lights on wings). These new applications could be researched further. 

