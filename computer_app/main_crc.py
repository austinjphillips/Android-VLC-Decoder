from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.camera import Camera
from kivy.uix.image import Image
from kivy.clock import Clock
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.popup import Popup
import cv2
from kivy.graphics.texture import Texture
import numpy as np
import crc8
import re
import urllib.request
import datetime
from pytz import timezone
import icalendar
import json



class CameraWithImagesApp(App):

    def __init__(self):
        super().__init__()
        self.raw_bitstream = ''
        self.manchester_bitstream = ''
        self.decoded_bitstream = ''

        self.received_message = ''
        self.received_crc = ''

        self.room_msg = ''

        self.bool_bitstream_cleared = False
        self.bool_rx_synchronized = False
        self.bool_signal_detected = False
        self.bool_preamble_detected = False
        self.bool_read_message = False
        self.bool_message_received = False
        self.correct_room = False

        self.preamble = '1010011010011010'
        self.sync_bits = '0000000011'
        self.clear_bits = '000000000'

        self.skip = 0
        self.sig_curr = 0
        self.sig_prev = 0
        self.BER = 0
        self.miss_count = 0
        self.miss_rate = 0
        self.msg_count = 0

        self.led_colour = 0

        self.init_image = './images/init.png'
        self.signal_image = './images/signal.png'
        self.preamble_image = './images/preamble.png'
        self.receiving_image = './images/receiving.png'
        self.crc_correct_image = './images/crc_correct.png'
        self.crc_incorrect_image = './images/crc_incorrect.png'
        self.received_image = './images/received.png'

        self.popup = None

        self.debug = False
        self.debug1 = False

    def build(self):
        # Set the desired size for the camera feed and images
        self.width, self.height = 640, 480

        # Create a BoxLayout to hold the camera feed and images
        layout = BoxLayout(orientation='vertical', width=480)

        button_layout = BoxLayout(orientation='horizontal', size_hint=(1, None), height=50)
        red_button = Button(text='Red LED', size_hint=(0.5, 1))
        red_button.bind(on_press=self.set_red_led)
        blue_button = Button(text='Blue LED', size_hint=(0.5, 1))
        blue_button.bind(on_press=self.set_blue_led)

        # Create a Camera widget
        self.camera_frame = Image(size_hint=(1, None), height=250)

        # Create an Image widget to display the camera feed
        self.progress_image = Image(source='./images/init.png', allow_stretch=True, size_hint=(1, None), height=250)

        # Add the Camera and Camera Image widgets to the layout
        button_layout.add_widget(red_button)
        button_layout.add_widget(blue_button)
        layout.add_widget(button_layout)
        layout.add_widget(self.camera_frame)
        layout.add_widget(self.progress_image)

        # Schedule the image update function
        Clock.schedule_interval(self.update_frame, 1.0 / 30)

        self.capture = cv2.VideoCapture(0)


        return layout

    def set_red_led(self, instance):
        self.led_colour = 0

    def set_blue_led(self, instance):
        self.led_colour = 1

    def update_frame(self, dt):
        # Capture a frame from the camera
        ret, frame = self.capture.read()

        if ret:
            self.receive_message(frame)
            # Convert the frame from BGR to RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Create a Kivy Texture from the frame
            texture = Texture.create(size=(self.width, self.height), colorfmt='rgb')
            texture.blit_buffer(frame_rgb.tostring(), colorfmt='rgb', bufferfmt='ubyte')

            # Assign the Texture to the Image widget for display
            self.camera_frame.texture = texture

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
            self.skip = 4
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
            self.skip = 4
        elif [self.sig_prev, self.sig_curr] == [0, 1]:
            self.manchester_bitstream += f"{self.sig_prev}{self.sig_curr}"
            self.received_crc += '0'
            self.decoded_bitstream += '0'
            print("CRC is setting")
            self.skip = 5
        else:
            self.skip = 0

    def display_room_info(self):
        print(self.received_message)
        x = int(self.received_message, 2)

        url = "https://esviewer.tudelft.nl/space/" + str(x) + "/"

        if self.debug1:
            print(x)
            print("url: " + url + "\n\n")

        with urllib.request.urlopen(url) as f:
            html_code = f.read().decode('utf-8')

        # Define a regular expression pattern to match the title tag
        title_pattern_hall = r'<title>(.*?)</title>'
        pattern_building = r'<font size="5">(.*?)</font>'

        pattern_hall = re.compile(title_pattern_hall)
        pattern_building = re.compile(pattern_building)

        # Use re.search to find the title within the HTML code
        hall = re.search(pattern_hall, html_code)
        building = re.search(pattern_building, html_code)

        customMessage = ''

        if hall and building:
            # Extract the title content from the match object
            hall = hall.group(1)
            building = building.group(1)

            if self.debug1:
                print("Hall:", hall)
                print("Building:", building)

            ttURL = 'https://slechtvalk.tudelft.nl/timetable.ics'
            rooms = self.fetch_allowed_rooms( ttURL )

            for room in rooms:
                if hall in room:
                    self.correct_room = True

            if self.correct_room:
                self.room_msg = "You're in the correct room :)"

                number = 1
                customMessage = self.fetch_custom_message( number )

                if self.debug1:
                    print( f"custom message: {customMessage}" )
            else:
                self.room_msg = "You're in the wrong room :("

            self.correct_room = False
            popup_msg = f"Building: {building}, Hall: {hall} \n\n You are in the correct room :) \n\n {customMessage} \n"
            self.show_popup(popup_msg)
        else:
            if self.debug1:
                print("Building and Hall not found in the HTML code")
            popup_msg = "Building and Hall not found"
            self.show_popup(popup_msg)



    def fetch_custom_message( self, number ):
        if self.debug1:
            print( f"fetching message for number: {number}" )
        message = ''

        messageURL = "https://slechtvalk.tudelft.nl/roommessages.json"

        if self.debug1:
            print(f"path to messages: {messageURL} \n\n")

        with urllib.request.urlopen( messageURL ) as f:
            messages = f.read().decode( 'utf-8' )

        decoded = json.loads( messages )

        if self.debug1:
            print( f"messages: {messages}" )
            print( f"message 1: {decoded['1']}" )
            print( f"message 2: {decoded['2']}" )
            print( f"message 3: {decoded['3']}" )

        message = decoded[ str(number) ]

        return message

    def fetch_allowed_rooms( self, timetableURL ):
        if self.debug1:
            print( "path to ics file: " +  timetableURL + "\n\n" )
        allowedRooms = []

        currTime = datetime.datetime.now( timezone('UTC') )
        if self.debug1:
            print( "Now it is: " )
            print( currTime )
            print( "\n\n" )

        with urllib.request.urlopen( timetableURL ) as f:
            calendar = icalendar.Calendar.from_ical(f.read())

            for event in calendar.walk('VEVENT'):
                start_time = event['DTSTART'].dt.astimezone( timezone('UTC') )
                end_time = event['DTEND'].dt.astimezone( timezone('UTC') )
                #start_time_utc = start_time.dt.astimezone(timezone('UTC'))
                #print( event.get( "SUMMARY" ) )
                #print( end_time )
                #print( start_time )
                #print( end_time )
                #print( event.get("SUMMARY") + " " + event.get("LOCATION") + " " + event.get( "STATUS" ) )
                #print( "\n\n" )

                timeToEvent = start_time - currTime
                #print( "time to event: " )
                #print( timeToEvent )
                #print( "\n\n" )

                timeToEnd = end_time - currTime

                if ( ( ( ( timeToEnd.total_seconds() ) / 60 ) > 0 ) and ( ( ( timeToEvent.total_seconds() ) / 60 ) < 3000 ) and event.get( "STATUS" ) == "CONFIRMED" ): #and timeToEvent.minutes < 30:
                    allowedRooms.append( event.get("LOCATION") )
                    #print( "course of interest at location: " )
                    #print( event.get("LOCATION") )
                    #print( "\n\n" )

        if self.debug1:
            print( "locations of interest: \n\n" )

            for room in allowedRooms:
                print( room + "\n" )

        return allowedRooms


    def show_popup(self, content_text):
        popup_content = BoxLayout(orientation='vertical')
        message_label = Label(text=content_text)
        dismiss_button = Button(text='Dismiss')
        popup_content.add_widget(message_label)
        popup_content.add_widget(dismiss_button)

        self.popup = Popup(title='Popup Title', content=popup_content, size_hint=(None, None), size=(700, 400))
        dismiss_button.bind(on_release=self.dismiss_popup)
        self.popup.open()

    def dismiss_popup(self, instance):
        self.popup.dismiss()


    def receive_message(self, frame):
        avg = 0
        # *** LED CONTOUR DETECTION ***
        # We can detect the contour of the LED by filtering out the red band around the LED
        hsv_image = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        # We can detect the contour of the LED by filtering out the red band around the LED

        # === RED MASK ===
        lower_red = np.array([0, 0, 200], np.uint8)
        upper_red = np.array([60, 60, 255], np.uint8)
        red_mask = cv2.inRange(frame, lower_red, upper_red)

        lower_red = np.array([160, 90, 200], np.uint8)
        upper_red = np.array([180, 255, 255], np.uint8)
        red_mask = cv2.inRange(hsv_image, lower_red, upper_red)

        # === BLUE MASK ===
        lower_blue = np.array([100, 90, 150], np.uint8)
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

        if avg > 20:
            sig = 1
        else:
            sig = 0

        self.sig_curr = sig

        if not self.bool_bitstream_cleared and self.clear_bits in self.raw_bitstream:
            self.bool_bitstream_cleared = True
            self.bool_rx_synchronized = False
            self.bool_signal_detected = False
            self.bool_preamble_detected = False
            self.bool_read_message = False
            self.bool_message_received = False


        if self.bool_bitstream_cleared and self.sync_bits in self.raw_bitstream:

            self.bool_bitstream_cleared = False
            self.progress_image.source = self.signal_image
            self.bool_rx_synchronized = True
            self.raw_bitstream = ''
            self.manchester_bitstream = ''
            self.decoded_bitstream = ''
            self.received_crc = ''
            self.received_message = ''
            self.skip = 0

        if self.bool_read_message:
            if len(self.decoded_bitstream) < 8:
                if self.skip == 0:
                    self.decode_message()
            elif len(self.decoded_bitstream) < 16:
                if self.skip == 0:
                    self.decode_crc()
            else:
                self.bool_message_received = True

        if self.bool_message_received:

            msg_encode = bytes.fromhex(f"{hex(int(self.received_message, 2))[2:]}")
            calc_crc = crc8.crc8()
            calc_crc.update(msg_encode)
            calculated_crc = int(calc_crc.hexdigest(), 16)
            received_crc_int = int(self.received_crc, 2)

            if calculated_crc == received_crc_int:
                if self.debug:
                    print(f"Correct Checksum! Decoding message...")
                self.progress_image.source = self.received_image
                # msg_string = decode_message(message)
                if self.debug:
                    print(f"Message received: {self.received_message}")
                self.display_room_info()
            else:
                if self.debug:
                    print(f"Incorrect Checksum! Trying again...")
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

        if self.preamble in self.manchester_bitstream:
            self.progress_image.source = self.receiving_image
            if self.debug:
                print(f"Detected Preamble: {self.preamble}...")

            self.bool_read_message = True
            self.manchester_bitstream = ''
            self.decoded_bitstream = ''

        self.raw_bitstream += f"{sig}"

        self.sig_prev = self.sig_curr

        if self.debug:
            print("")
            print(f"Sig: {sig}")
            print(f"Bitstream: {self.raw_bitstream}")
            print(f"Msg Bitstream: {self.manchester_bitstream}")
            print(f"Decoded: {self.decoded_bitstream}")
            print(f"Message: {self.received_message}")
            print(f"Checksum: {self.received_crc}")
            print(f"Skip: {self.skip}")
            print(f"Miss Rate: {self.miss_rate}")
            print(f"BER: {self.BER}")
            print("====================================================")


app = CameraWithImagesApp()
app.run()
