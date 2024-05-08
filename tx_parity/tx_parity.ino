
/*
  test_tx.ino: testing the VLC transmitter
  Course: CESE4110 Visible Light Communication & Sensing
*/

/*#######
 * Libraries
#######*/
#include <CRC8.h>
#include <DueFlashStorage.h>
//#include <avr/pgmspace.h>


/******************************* SETTINGS *******************************/
/************************************************************************/
/**************PLEASE ONLY TOUCH THESE WHEN USING THIS CODE!!*************/

const byte preamble = 0xDB; // preamble, needs to match the receiver side
const int initRoomNumber = 255; // not existing room number as the total room numbers is 212, see: 

const unsigned long period = 100000; // period defining the speed, needs to match the receiver side

/************************************************************************/

//different debug modes

// Set LED colour
int led_colour = 1;   // 0 = red, 1 = blue

#define DEBUG
//#define DEBUG2
//#define DEBUG3
//#define DEBUG4
//#define DEBUG5
//#define DEBUG6

//#define LEDFULLCOLOR

/*
 * The VLC transmitter is equipped with an RGB LED. 
 * The LED's three channels, R, G, B, can be controlled individually.
 * The R channel is connected to Pin 38 of the Arduino Due
 * The G channel is connected to Pin 42 of the Arduino Due
 * The B channel is connected to Pin 34 of the Arduino Due
 */

//global variables
CRC8 crc;
DueFlashStorage dueFlashStorage;

//hardware specific
const int ledR= 38; // GPIO for controlling R channel
const int ledG= 42; // GPIO for controlling G channel
const int ledB= 34; // GPIO for controlling B channel

/*
 * Brightness of each channel.
 * The range of the brightness is [0, 255].
 * *  0 represents the highest brightness
 * *  255 represents the lowest brightness
 */
int britnessR = 255; // Default: lowest brightness
int britnessG = 255; // Default: lowest brightness
int britnessB = 255; // Default: lowest brightness

//analog LED switch options
const int LEDoff = 130; //255;
const int LEDon = 120; //0;

//other
const byte testByte = 0b10011010;
boolean testBit = 0b1;

//int transmitmessage = 255;

byte frame[2] = {0};

// function to send a bit value according OOK + Manchester encoding
// 0 = rising edge & 1 = falling edge :: should lead to less noise https://www.instructables.com/Manchester-Code-Library-for-Arduino/
void sendBit( boolean b )
{
  #ifdef DEBUG3
    Serial.println( b );
  #endif
  
 // if( b > 1 )
 //   return;
    
  if( b )
  {
    #ifdef DEBUG2
      Serial.println( " Send bit HIGH" );
      Serial.println( b );
    #endif
    
    if (led_colour == 0) {
      analogWrite(ledR, LEDon);
      delayMicroseconds( (period) );
      analogWrite(ledR, LEDoff);
      delayMicroseconds( (period) );
    }
    
    if (led_colour == 1) {
      analogWrite(ledB, LEDon);
      delayMicroseconds( (period) );
      analogWrite(ledB, LEDoff);
      delayMicroseconds( (period) );
    }
  }
  else
  {
    #ifdef DEBUG2
      Serial.println( " Send bit LOW" );
      Serial.println( b );
    #endif
    
    if (led_colour == 0) {
      analogWrite(ledR, LEDoff);
      delayMicroseconds( (period) );
      analogWrite(ledR, LEDon);
      delayMicroseconds( (period) );
    }
    
    if (led_colour == 1) {
      analogWrite(ledB, LEDoff);
      delayMicroseconds( (period) );
      analogWrite(ledB, LEDon);
      delayMicroseconds( (period) );
    }
  }
}

// function to send a byte
void sendByte( byte b )
{
  #ifdef DEBUG3
    Serial.println( b, BIN );
  #endif
  
  //for( int i = 0; i < ( sizeof(b) * 8 ); i++ )
  for( int i = 8; i > 0; i-- )
  {
    boolean bit = bitRead(b, (i-1));
    
    #ifdef DEBUG4
      Serial.print( bit );
    #endif

    sendBit( bit );
  }
  
  #ifdef DEBUG4
    Serial.println( " " );
  #endif
}

bool calculateParityBit( byte dataByte ) 
{
  bool result = false;
  
  for (int i = 0; i < 8; i++)
    result ^= ( ( dataByte >> i ) & 1 );
    
  return result;
}

//function that sends the frame
void sendFrame( byte transframe[] /*, int messageLength*/ )
{

  //delay( 10 );
 
  #ifdef DEBUG
    Serial.println(" START TRANSMITTING THE FRAME: ");
    Serial.println(" ");
  #endif

  Serial.println(sizeof(transframe));

  // Send bytes of the frame
  for( int i = 0; i < 1; i++ )
  {
   #ifdef DEBUG
    Serial.print( "send byte: 0x" );
    Serial.print( transframe[ i ], HEX );
    Serial.print(" ");
    Serial.println(transframe[i], BIN);
   #endif

    sendByte( transframe[i] );
  }
}


//function that builds the frame to send
void buildFrame( int payLoad )
{
  #ifdef DEBUG
    Serial.println(" BUILD THE FRAME \n");
  #endif

  //length of the messsage to send
  //int payLoadLength = payLoad.length();

  //preamble
  #ifdef DEBUG
    Serial.println(" DEFINE PREAMBLE ");

    Serial.print( "Preamble: 0x" );

    Serial.print(preamble, HEX);

    Serial.println( "\n" );
  #endif

  // put the preamble in the frame
  frame[0] = preamble;

  #ifdef DEBUG
    Serial.println(" DEFINE PAYLOAD LENGTH ");
    Serial.print(" Payload length: 1");
    //Serial.println( frame.lentgh(), DEC );
    Serial.println( " bytes \n" );
  #endif
  
  //put the message length in the frame
  //frame[3] = 0;
  //frame[4] = payLoadLength;

  #ifdef DEBUG
    Serial.println(" DEFINE PAYLOAD ");
    Serial.print( "Room number: " );
    Serial.println( dueFlashStorage.read( 1 ) );
    Serial.println(dueFlashStorage.read( 1 ), BIN);
    Serial.println("\n");
  #endif

  //put the room number in the frame
  frame[0] = (int) dueFlashStorage.read( 1 );

  bool parity = calculateParityBit(frame[0]);

  Serial.println(parity);

  #ifdef DEBUG
    Serial.println(" CALCULATE CRC ");
  #endif

  //put the message in the frame
  crc.restart();
  crc.add( ( int ) dueFlashStorage.read( 1 ) );

  frame[2] = byte( (int) crc.calc() );

     
  //  #ifdef DEBUG
  //    Serial.print( "calculated CRC : 0x" );
  //    Serial.println( frame[2], HEX );
  //    Serial.println( "" );
  //  #endif

  #ifdef DEBUG
    Serial.println( " TRANSMIT THE FRAME: " );

    for( int i = 0; i < sizeof( frame ); i++ )
    {
      Serial.print( i );
      Serial.print( ": " );
      Serial.println( frame[i], HEX );
    }
  #endif

  // #ifdef DEBUG
  //   Serial.print( "\n size of payload: " );
  //   Serial.println( sizeof( frame[2] ), HEX );
  //   Serial.println( "" );
  // #endif


  sendBit(1);
  sendByte(dueFlashStorage.read( 1 ));
  sendBit(parity);

  #ifdef DEBUG
    Serial.println(" \n TRANSMIT DONE \n\n");
  #endif

  if (led_colour == 0) {
    analogWrite(ledR, LEDoff);
  }
  if (led_colour == 1) {
    analogWrite(ledB, LEDoff);
  }
  delayMicroseconds(4*period);
  
//  sendFrame( frame, 1 );
  
}

/*
 * Some configurations
 */
void setup() 
{
  #ifdef DEBUG
    Serial.begin(115200); // Set the Baud rate to 115200 bits/s

    Serial.println( " _________________________VLC TRANSMITTER SIDE: _________________________ \n\n" );
  #endif
  
  while (Serial.available() > 0)
    Serial.read();

  // pinMode(ledR, OUTPUT);
  pinMode(ledB, OUTPUT);
  analogWrite(ledB, LEDon);
  // analogWrite(ledR, LEDon);
  analogWrite(ledB, LEDoff);
  // analogWrite(ledR, LEDoff);

  float tx_freq = 1.0 / (float(period) / 1000000.0);
  
  Serial.print("Tx Frequency: ");
  Serial.println(tx_freq);

  //transmitmessage PROGMEM = initRoomNumber;
  dueFlashStorage.write( 0, (uint8_t) initRoomNumber );
  
  delayMicroseconds(500000);

}

/*
 * The Main function
 */
void loop() {
  /*
   * In this simple test, only the R channel is used to transmit data.
   * The R channel is turned ON and OFF alternatively to transmit 1 and 0. 
   * The TX frequency is set to 10 Hz, i.e., sending a symbol every 100 ms
   */
   while ( Serial.available() > 0 ) 
   {
      int message = dueFlashStorage.read( 0 );

      #ifdef DEBUG
        if( message != 255 )
          Serial.println( "ERROR IN MEMORY READ!" );
      #endif
      
      while( Serial.available() )
      {
        message = Serial.parseInt();
        String str = Serial.readStringUntil( '\n' );
      }

      // room numbers fall between 0 and 213
      if( message > 0 && message < 213 ) 
      {

       //transmitmessage PROGMEM = (int) message;
       dueFlashStorage.write( 1, (uint8_t) message );
       
       #ifdef DEBUG
        Serial.print( "New message provided: " );
        Serial.println( dueFlashStorage.read( 1 ) );
      #endif
      }
      else
      {
       #ifdef DEBUG
        Serial.print( "Invalid Room Number, please provide a valid one!, input: " );
        Serial.println( message );
      #endif
      }
   }

  #ifdef DEBUG
    Serial.println(" ---- PREPARE FRAME ---- ");
    //Serial.print(" preamble: " );
    //Serial.println( message );
    Serial.println(" ");
    Serial.print(" Message to transmit: " );
    //Serial.println(  transmitmessage );
    Serial.println( dueFlashStorage.read( 1 ) );
    Serial.println( " \n " );
  #endif

  // build the frame to send, include the message
  buildFrame( dueFlashStorage.read( 1 ) );
/*
  #ifdef DEBUG
    Serial.println(" ---- END SENDING FRAME ---- ");
    Serial.println(" \n\n ");
  #endif

  // do other stuff
  #ifdef LEDFULLCOLOR
    analogWrite(ledG, britnessG);
    britnessG = (britnessG == 0 ? 255 : 0);

    analogWrite(ledB, britnessB);
    britnessB = (britnessB == 0 ? 255 : 0);
  #endif
*/
  //delay(Period); // TX frequency:  1s/400ms = 2.5 Hz
}
