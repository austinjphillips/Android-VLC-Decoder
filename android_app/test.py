import kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.uix.button import Button

class ImageSwitchApp(App):
    def __init__(self):
        super().__init__()
        self.button = None
        self.img = None

    def build(self):
        # Create a BoxLayout to hold the image
        layout = BoxLayout(orientation='vertical')

        # Create an Image widget and set the source to your PNG image
        self.img = Image(source='./images/init.png')

        # Create a Button widget
        self.button = Button(text='Switch Image')
        self.button.bind(on_press=self.switch_image)

        # Add the Image and Button widgets to the layout
        layout.add_widget(self.img)
        layout.add_widget(self.button)

        return layout

    def switch_image(self, instance):
        # Toggle between two image sources
        if self.img.source == './images/init.png':
            self.img.source = './images/preamble.png'
        else:
            self.img.source = './images/init.png'


app = ImageSwitchApp()
app.run()
