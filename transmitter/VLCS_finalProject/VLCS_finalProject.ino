/*
  test_tx.ino: testing the VLC transmitter
  Course: CESE4110 Visible Light Communication & Sensing
*/

/*#######
 * Libraries
#######*/
#include <CRC8.h>
#include <RS-FEC.h>
#include <DueFlashStorage.h>
//#include <avr/pgmspace.h>

/******************************* SETTINGS *******************************/
/************************************************************************/
/**************PLEASE ONLY TOUCH THESE WHEN USING THIS CODE!!*************/

const byte preamble[3] = { 0x54, 0x55 }; // preamble, needs to match the receiver side
const int initRoomNumber = 255; // not existing room number as the total room numbers is 212, see: 

const unsigned long period = 33334; // period defining the speed, needs to match the receiver side

/************************************************************************/

//different debug modes

#define DEBUG
//#define DEBUG2
//#define DEBUG3
//#define DEBUG4
//#define DEBUG5
//#define DEBUG6

//#define LEDFULLCOLOR

const int msglen = sizeof( initRoomNumber ) - 2;
const uint8_t ECC_LENGTH = ceil( ( ( msglen + 2 ) / 2 ) );

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
RS::ReedSolomon<msglen, ECC_LENGTH> rs;

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

byte frame[ (2 + 1 + 1 ) ] = {0};

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
    
    analogWrite(ledR, LEDon);
    delayMicroseconds( (period) );
    analogWrite(ledR, LEDoff);
    delayMicroseconds( (period) );
  }
  else
  {
    #ifdef DEBUG2
      Serial.println( " Send bit LOW" );
      Serial.println( b );
    #endif
    
    analogWrite(ledR, LEDoff);
    delayMicroseconds( (period) );
    analogWrite(ledR, LEDon);
    delayMicroseconds( (period) );
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

//function that sends the frame
void sendFrame( byte transframe[] /*, int messageLength*/ )
{

  //delay( 10 );
 
  #ifdef DEBUG
    Serial.println(" START TRANSMITTING THE FRAME: ");
    Serial.println(" ");
     Serial.print("FRAME SIZE: ");
    Serial.println( ( sizeof( transframe ) + 2 ), HEX );
    Serial.println(" ");
  #endif
  
  // Send bytes of the frame
  for( int i = 0; i < ( sizeof( transframe ) + 2 ); i++ ) 
  //for( int i = 0; i < 6; i++ ) 
  {
   #ifdef DEBUG
    Serial.print( "send byte: 0x" );
    Serial.println( transframe[ i ], HEX );
   #endif

    sendByte( transframe[i] );
  }

  #ifdef DEBUG
    Serial.println(" \n TRANSMIT DONE \n\n");
  #endif

  delay(2000);
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

    for( int i = 0; i < sizeof( preamble )-1; i++ )
      Serial.print( preamble[i], HEX );

    Serial.println( "\n" );
  #endif

  // put the preamble in the frame
  for( int i = 0; i < sizeof( preamble ); i++ ) {
    frame[i] = preamble[i];
  }

  #ifdef DEBUG
    Serial.println( "DEFINE PAYLOAD LENGTH ");
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
    Serial.println( "\n" );
  #endif

  //put the room number in the frame
  frame[2] = (int) dueFlashStorage.read( 1 );
  //frame[4] = payLoadLength;

//  #ifdef DEBUG
//    Serial.println(" DEFINE PAYLOAD LENGTH ");
//    Serial.print(" Payload length: 1");
//    //Serial.println( frame.lentgh(), DEC );
//    Serial.println( " bytes \n" );
//  #endif
  
  //put the message length in the frame
  //frame[3] = 0;
  //frame[4] = payLoadLength;

  //put the room number in the frame
  //frame[2] = (int) pgm_read_word( &transmitmessage );
  //frame[4] = payLoadLength;

  #ifdef DEBUG
    Serial.println(" CALCULATE CRC ");
  #endif

  //put the message in the frame
  crc.restart();
  crc.add( ( int ) dueFlashStorage.read( 1 ) );

  //Serial.println( (int) crc.calc(), HEX);
  //Serial.println( calcCRC8((uint8_t)transmitmessage, 3), HEX );
  frame[3] = byte( (int) crc.calc() );

  //for( int i = 5; i < payLoadLength+5; i++ ) {
//    byte a = (payLoad.charAt(i-5));
//    frame[i] = a;
    // Add the byte to the CRC checksum
//    crc.add(a);

     
   #ifdef DEBUG
     Serial.print( "calculated CRC : 0x" );
     Serial.println( frame[3], HEX );
     Serial.println( "" );
   #endif
//  }
 
  #ifdef DEBUG
    Serial.print( "message and CRClength: " );
    Serial.print( ( sizeof( frame[2] + sizeof( frame[3] ) ) ) );
    Serial.println( "" );
    Serial.print( "ECC length: " );
    Serial.print( ECC_LENGTH );
    Serial.println( "" );
  #endif

  //calculate the CRC checksum
  //int checksum = crc.calc();

   // #ifdef DEBUG
   // Serial.print( "CRC checksum: " );
   // Serial.println(checksum, HEX);
   // Serial.println( "\n" );
 // #endif
  
  //byte checksumHigh = checksum >> 8;
  //byte checksumLow = checksum & 0xFF;

    //put the CRC checksum in the frame
  //frame[3] = (byte) 0x00;
  //frame[payLoadLength+6] = checksumLow;
  // frame[payLoadLength+4] = checksum;

  //sendBit(1);
  //sendBit(0);

  byte message_frame[2] = {0};
  //message_frame[0] = (byte) dueFlashStorage.read( 1 );
  //message_frame[1] = (byte) frame[3];

  memset( message_frame, 0, sizeof( message_frame ) );        // Clear the array
  for(uint i = 0; i < sizeof( message_frame ); i++) 
    message_frame[i] = frame[i+2]; // Fill with the message

  #ifdef DEBUG
    Serial.print( "message length: " );
    Serial.print(  sizeof( message_frame ) );
    Serial.println( "" );

    for( int i = 0; i < sizeof( message_frame ); i++ )
    {
      Serial.print( i );
      Serial.print( ": 0x" );
      Serial.println( message_frame[i], HEX );
    }
  #endif
  
  byte encoded[msglen + ECC_LENGTH];
  rs.Encode(message_frame, encoded);

  #ifdef DEBUG
    Serial.print( "Encoded message length: " );
    Serial.print(  sizeof( encoded ) );
    Serial.println( "" );

    for( int i = 0; i < sizeof( encoded ); i++ )
    {
      Serial.print( i );
      Serial.print( ": 0x" );
      Serial.println( encoded[i], HEX );
    }
      
  #endif

  //byte *new_frame = (byte*)calloc(6,sizeof(byte));
  byte new_frame[ ( sizeof( preamble ) + sizeof( encoded ) - 1 ) ] = { 0 };
  
  new_frame[0] = ( byte ) preamble[0];
  new_frame[1] = ( byte ) preamble[1];
  new_frame[2] = ( byte ) encoded[0];
  new_frame[3] = ( byte ) encoded[1];
  new_frame[4] = ( byte ) encoded[2];
  new_frame[5] = ( byte ) encoded[3];
  
  #ifdef DEBUG
    Serial.println( " TRANSMIT THE FRAME: " );

    for( int i = 0; i < sizeof( new_frame ); i++ )
    {
      Serial.print( i );
      Serial.print( ": 0x" );
      Serial.println( new_frame[i], HEX );
    }
  #endif

  #ifdef DEBUG
    Serial.print( "\n size of payload: " );
    Serial.println( sizeof( new_frame ), HEX );
    Serial.println( "" );
  #endif

  sendFrame( new_frame /*, sizeof( frame[2] )*/ );
  
//  sendFrame( frame, 1 );
  
}

/*
 * Some configurations
 */
void setup() 
{
  #ifdef DEBUG
    Serial.begin(115200); // Set the Baud rate to 115200 bits/s

    Serial.println( " \n\n _________________________VLC TRANSMITTER SIDE: _________________________ \n\n" );
  #endif
  
  while (Serial.available() > 0)
    Serial.read();

  pinMode(ledR, OUTPUT);
  analogWrite(ledR, LEDon);
  analogWrite(ledR, LEDoff);

  float tx_freq = 1.0 / (float(period) / 1000000.0);
  
  #ifdef DEBUG
    Serial.print("Tx Frequency: ");
    Serial.println(tx_freq);
  #endif
  
  #ifdef DEBUG
    Serial.print( "Message length: " );
    Serial.print(  msglen );
    Serial.println( "" );
  #endif 

  //transmitmessage PROGMEM = initRoomNumber;
  dueFlashStorage.write( 0, (uint8_t) initRoomNumber );
  
  delayMicroseconds(5000000);
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
