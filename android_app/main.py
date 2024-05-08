from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.button import Button
from kivy.graphics.texture import Texture
from kivy.uix.camera import Camera
from kivy.uix.image import Image
from kivy.network.urlrequest import UrlRequest
from kivy.clock import Clock
from kivy.uix.label import Label
from kivy.lang import Builder
from jnius import autoclass
import numpy as np
import cv2
from kivy.properties import ObjectProperty
import crc8
from android.permissions import request_permissions, Permission
from threading import Thread
import re


CameraInfo = autoclass('android.hardware.Camera$CameraInfo')
CAMERA_INDEX = {'front': CameraInfo.CAMERA_FACING_FRONT, 'back': CameraInfo.CAMERA_FACING_BACK}
Builder.load_file("myapplayout.kv")


class AndroidCamera(Camera):
    resolution = (640, 480)
    index = CAMERA_INDEX['front']
    counter = 0

    progress_image = ObjectProperty(None)

    raw_bitstream = ''
    manchester_bitstream = ''
    decoded_bitstream = ''

    received_message = ''
    received_crc = ''

    room_msg = ''

    bool_bitstream_cleared = False
    bool_rx_synchronized = False
    bool_signal_detected = False
    bool_preamble_detected = False
    bool_read_message = False
    bool_message_received = False
    correct_room = False

    preamble = '10'
    sync_bits = '0000000011'
    clear_bits = '000000000'

    skip = 0
    sig_curr = 0
    sig_prev = 0
    BER = 0
    miss_count = 0
    miss_rate = 0
    msg_count = 0

    led_colour = 1
    encoding = 0

    init_image = './images/init.png'
    signal_image = './images/signal.png'
    preamble_image = './images/preamble.png'
    receiving_image = './images/receiving.png'
    crc_correct_image = './images/crc_correct.png'
    crc_incorrect_image = './images/crc_incorrect.png'
    received_image = './images/received.png'

    popup = None
    popup_msg = 'Default'

    def on_tex(self, *l):
        if self._camera._buffer is None:
            return None

        super(AndroidCamera, self).on_tex(*l)
        self.texture = Texture.create(size=np.flip(self.resolution), colorfmt='rgb')
        frame = self.frame_from_buf()
        self.frame_to_screen(frame)


    def frame_from_buf(self):
        w, h = self.resolution
        frame = np.frombuffer(self._camera._buffer.tostring(), 'uint8').reshape((h + h // 2, w))
        frame_bgr = cv2.cvtColor(frame, 93)
        if self.index:
            return np.flip(np.rot90(frame_bgr, 1), 1)
        else:
            return np.rot90(frame_bgr, 3)

    def frame_to_screen(self, frame):
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # val = image_processing(frame_rgb)
        self.receive_message(frame_rgb)
        cv2.putText(frame_rgb, self.raw_bitstream, (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
        cv2.putText(frame_rgb, self.manchester_bitstream, (20, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
        cv2.putText(frame_rgb, self.received_message, (20, 150), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
        self.counter += 1
        flipped = np.flip(frame_rgb, 0)
        buf = flipped.tobytes()
        self.texture.blit_buffer(buf, colorfmt='rgb', bufferfmt='ubyte')

    def decode_preamble(self):
        if [self.sig_prev, self.sig_curr] == [1, 0]:
            self.manchester_bitstream += f"{self.sig_prev}{self.sig_curr}"
            self.decoded_bitstream += '1'
            self.skip = 4
        elif [self.sig_prev, self.sig_curr] == [0, 1]:
            self.manchester_bitstream += f"{self.sig_prev}{self.sig_curr}"
            self.decoded_bitstream += '0'
            self.skip = 5
        else:
            self.skip = 0

    def decode_message(self):
        if [self.sig_prev, self.sig_curr] == [1, 0]:
            self.manchester_bitstream += f"{self.sig_prev}{self.sig_curr}"
            self.received_message += '1'
            self.decoded_bitstream += '1'
            self.skip = 5
        elif [self.sig_prev, self.sig_curr] == [0, 1]:
            self.manchester_bitstream += f"{self.sig_prev}{self.sig_curr}"
            self.received_message += '0'
            self.decoded_bitstream += '0'
            self.skip = 5
        else:
            self.skip = 0

    def decode_crc(self):
        if [self.sig_prev, self.sig_curr] == [1, 0]:
            self.manchester_bitstream += f"{self.sig_prev}{self.sig_curr}"
            self.received_crc += '1'
            self.decoded_bitstream += '1'
            self.skip = 5
        elif [self.sig_prev, self.sig_curr] == [0, 1]:
            self.manchester_bitstream += f"{self.sig_prev}{self.sig_curr}"
            self.received_crc += '0'
            self.decoded_bitstream += '0'
            self.skip = 5
        else:
            self.skip = 0

    def display_room_info(self):
        Thread(target=self.fetch_room_info).start()

    def on_request_success(self, request, result):
        # This is called when the request succeeded
        html_code = result

        # Define a regular expression pattern to match the title tag
        title_pattern_hall = r'<title>(.*?)</title>'
        pattern_building = r'<font size="5">(.*?)</font>'

        pattern_hall = re.compile(title_pattern_hall)
        pattern_building = re.compile(pattern_building)

        # Use re.search to find the title within the HTML code
        hall = re.search(pattern_hall, html_code)
        building = re.search(pattern_building, html_code)

        if hall and building:
            # Extract the title content from the match object
            hall = hall.group(1)
            print("Hall:", hall)
            building = building.group(1)
            print("Building:", building)

            self.popup_msg = f"Building: {building}, Hall: {hall}"
            self.show_popup()

        else:
            print("Building and Hall not found in the HTML code")
            self.popup_msg = f"{int(self.received_message, 2)}"
            self.show_popup()

    def on_request_failure(self, request, result):
        # This is called if the server returns a status code other than 200-299
        print("Request failed with result:", result)

    def on_request_error(self, request, error):
        # This is called if an error occurs while the request is being performed
        print("Request errored with error:", error)

    def fetch_room_info(self):
        x = int(self.received_message, 2)

        url = "https://esviewer.tudelft.nl/space/" + str(x) + "/"

        print("url: " + url + "\n\n")

        if 0 < x < 213:
            UrlRequest(url, on_success=self.on_request_success, on_failure=self.on_request_failure,
                       on_error=self.on_request_error)


    def show_popup(self):
        popup_content = BoxLayout(orientation='vertical')
        message_label = Label(text=self.popup_msg)
        dismiss_button = Button(text='Dismiss')
        popup_content.add_widget(message_label)
        popup_content.add_widget(dismiss_button)

        self.popup = Popup(title='Building and Room Info', content=popup_content, size_hint=(None, None), size=(1000, 1000))
        dismiss_button.bind(on_release=self.close_popup)
        self.popup.open()

    def close_popup(self, button):
        self.popup.dismiss()

    def receive_message(self, frame):

        avg = 0
        # *** LED CONTOUR DETECTION ***
        # We can detect the contour of the LED by filtering out the red band around the LED
        hsv_image = cv2.cvtColor(frame, cv2.COLOR_RGB2HSV)
        # We can detect the contour of the LED by filtering out the red band around the LED

        # === RED MASK ===
        # lower_red = np.array([0, 0, 200], np.uint8)
        # upper_red = np.array([60, 60, 255], np.uint8)
        # red_mask = cv2.inRange(frame, lower_red, upper_red)

        lower_red = np.array([160, 100, 200], np.uint8)
        upper_red = np.array([180, 255, 255], np.uint8)
        red_mask = cv2.inRange(hsv_image, lower_red, upper_red)

        # === BLUE MASK ===
        lower_blue = np.array([100, 100, 150], np.uint8)
        upper_blue = np.array([110, 255, 255], np.uint8)
        blue_mask = cv2.inRange(hsv_image, lower_blue, upper_blue)

        # *** LED CENTRE EXTRACTION
        # Filter out bright objects of image (LED, but also light sources)
        centre_mask = cv2.inRange(frame, np.array([225, 225, 225]), np.array([255, 255, 255]))
        bgr_threshed = centre_mask

        # Blur the image with a gaussian filter to remove any noise, and also to soften the image
        # Dilate the pixels of the image to repair the red circle border around the LED
        # thresh = cv2.erode(red_mask, None, iterations=1)
        # thresh = cv2.erode(red_mask, None, iterations=1)
        if self.led_colour == 0:
            mask = red_mask
        elif self.led_colour == 1:
            mask = blue_mask

        thresh = cv2.dilate(mask, None, iterations=10)

        # Find the LED contour parameters
        circles = cv2.HoughCircles(thresh, cv2.HOUGH_GRADIENT_ALT, dp=1.5, minDist=5, param1=10, param2=0, minRadius=5,
                                   maxRadius=0)

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

            avg = np.mean(cropped_values)

        if avg > 5:
            if not self.bool_signal_detected:
                self.bool_signal_detected = True
                self.progress_image.source = self.signal_image
            sig = 1
        else:
            sig = 0

        self.sig_curr = sig

        if not self.bool_bitstream_cleared and self.clear_bits in self.raw_bitstream:
            self.bool_bitstream_cleared = True
            self.bool_rx_synchronized = False
            self.bool_preamble_detected = False
            self.bool_read_message = False
            self.bool_message_received = False

            self.manchester_bitstream = ''
            self.decoded_bitstream = ''
            self.received_crc = ''
            self.received_message = ''

        if self.bool_bitstream_cleared and self.sync_bits in self.raw_bitstream:
            self.bool_bitstream_cleared = False
            self.progress_image.source = self.preamble_image
            self.bool_rx_synchronized = True
            self.raw_bitstream = '11'
            self.manchester_bitstream = ''
            self.decoded_bitstream = ''
            self.received_crc = ''
            self.received_message = ''
            self.skip = 0

        if self.bool_read_message:
            if self.encoding == 0:
                if len(self.decoded_bitstream) < 8:
                    if self.skip == 0:
                        self.decode_message()
                elif len(self.decoded_bitstream) < 16:
                    if self.skip == 0:
                        self.decode_crc()
                else:
                    self.bool_message_received = True

            elif self.encoding == 1:
                if len(self.decoded_bitstream) < 8:
                    if self.skip == 0:
                        self.decode_message()
                elif len(self.decoded_bitstream) < 9:
                    if self.skip == 0:
                        self.decode_crc()
                else:
                    self.bool_message_received = True

        if self.bool_message_received:

            if self.encoding == 0:
                msg_encode = bytes.fromhex(f"{hex(int(self.received_message, 2))[2:]}")
                calc_crc = crc8.crc8()
                calc_crc.update(msg_encode)
                calculated_crc = int(calc_crc.hexdigest(), 16)
                received_crc_int = int(self.received_crc, 2)

                if calculated_crc == received_crc_int:
                    self.progress_image.source = self.received_image
                    self.display_room_info()
                else:
                    self.progress_image.source = self.crc_incorrect_image

            elif self.encoding == 1:
                received_parity = int(self.received_crc, 2)
                calc_parity = self.received_message.count('1') % 2

                if calc_parity == received_parity:
                    self.progress_image.source = self.received_image
                    self.display_room_info()
                else:
                    self.progress_image.source = self.crc_incorrect_image

            self.raw_bitstream = ''
            self.manchester_bitstream = ''
            self.decoded_bitstream = ''
            self.received_message = ''
            self.received_crc = ''

            self.bool_rx_synchronized = False
            self.bool_signal_detected = False
            self.bool_preamble_detected = False
            self.bool_read_message = False
            self.bool_message_received = False

        if not self.bool_read_message and self.bool_rx_synchronized and self.skip == 0:
            self.decode_preamble()
        else:
            if self.skip > 0:
                self.skip -= 1

        if not self.bool_read_message and self.preamble in self.manchester_bitstream:
            self.progress_image.source = self.receiving_image
            self.bool_read_message = True
            self.raw_bitstream = ''
            self.manchester_bitstream = ''
            self.decoded_bitstream = ''

        self.raw_bitstream += f"{sig}"

        self.sig_prev = self.sig_curr

    def set_led_color(self, color):
        self.led_colour = color

    def set_encoding(self, encode):
        self.encoding = encode


class ProgressImage(Image):
    pass

class MyLayout(BoxLayout):
    pass

class MyApp(App):

    def build(self):
        request_permissions([
            Permission.CAMERA,
            Permission.WRITE_EXTERNAL_STORAGE,
            Permission.READ_EXTERNAL_STORAGE,
            Permission.INTERNET,
        ])
        return MyLayout()


if __name__ == '__main__':
    MyApp().run()
