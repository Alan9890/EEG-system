#include <ESP8266WiFi.h>
#include <WiFiUdp.h>
#include <SPI.h>
#include <Servo.h>

//Default register settings (some can be changed by the GUI):
//==============
//Channel config:
byte CHANNEL_SELECT = 0;
byte GAIN = 0b110;
/* 
Gain bits:
//========
0b000 = 6
0b001 = 1
0b010 = 2
0b011 = 3
0b100 = 4
0b101 = 8
0b110 = 12
 */
 
byte SOURCE = 0b000;
/*
000 = Normal electrode input
001 = Input shorted (for offset or noise measurements)
010 = Used in conjunction with RLD_MEAS bit for RLD measurements. See the Right Leg Drive (RLD) DC Bias Circuit subsection of the ECG-Specific Functions section of the ADS1298 datasheet for more details.
011 = MVDD for supply measurement
100 = Temperature sensor
101 = Test signal
110 = RLD_DRP (positive electrode is the RLD driver)
111 = RLD_DRN (negative electrode is the RLD driver)
*/

//config 1:
#define HR 1 // 0 = low power, 1 = high resolution
#define DAISY_EN 1 // 0 = daisy chain, 1 = multiple feedback
#define CLK_EN 0  //0 = external clock output disabled, 1 = enabled
byte DR = 0b101; 
/*Data rates:
000: HR Mode: 32 kSPS, LP Mode: 16 kSPS
001: HR Mode: 16 kSPS, LP Mode: 8 kSPS
010: HR Mode: 8 kSPS, LP Mode: 4 kSPS
011: HR Mode: 4 kSPS, LP Mode: 2 kSPS
100: HR Mode: 2 kSPS, LP Mode: 1 kSPS
101: HR Mode: 1 kSPS, LP Mode: 500 SPS
110: HR Mode: 500 SPS, LP Mode: 250 SPS
111: Reserved (do not use)
*/

//config 2:
#define WCT_CHOP 0      //variable chopping frequency
#define INT_TEST 1      //internal test signal source
#define TEST_AMP 0      //1mv ref signal
#define TEST_FREQ 0     //pulsed at f_clk/s^21

//config 3:
#define PD_REFBUFF 1    //enabled
#define VREF_4V 0       //use 2.4v reference
#define RLD_MEAS 0      //open
#define RLDREF_INT 1    //internally generated
#define PD_RLD 1        //powered down
#define RLD_LOFF_SENS 0 //enabled
#define RLD_STAT 0      //status bit - read only

//config 4:
#define RESP_FREQ 0b00
#define SINGLE_SHOT 0
#define WCT_TO_RLD 0
#define PD_LOFF_COMP 0 //enable comparator

//LOFF:
#define COMP_TH 0b011   //Comparator threshold
#define VLEAD_OFF_EN 0  //Current source mode
#define ILEAD_OFF 0b11  //Lead-ff detect current: 24nA
#define FLEAD_OFF 0b01  //AC mode

//pin assignments for NodeMCU:
int DRDY = D1;          //ADS1198 data ready, active low
int CS = D4;
int PDWN_RESET = D2;
/*
    MOSI = GPIO13 = D7
    MISO = GPIO12 = D6
    SCLK = GPIO14 = D5
*/

//opcodes:
int WAKEUP = 0x02;
int STANDBY = 0x04;
int RESET = 0x06;
int START = 0x08; 
int STOP = 0x0A;
int RDATAC = 0x10;
int SDATAC = 0x11;
int RDATA = 0x12;

//register map:
int ID = 0x0;
int CONFIG1 = 0x01;
int CONFIG2 = 0x02;
int CONFIG3 = 0x03;
int LOFF = 0x04;
int CHSET[8] = {0x05, 0x06, 0x07, 0x08, 0x09, 0x0A, 0X0B, 0x0C};
int RLD_SENSP = 0x0D;
int RLD_SENSN = 0x0E;
int LOFF_SENSP = 0x0F;
int LOFF_SENSN = 0x10;
int LOFF_FLIP = 0x11;
int LOFF_STATP = 0x12;
int LOFF_STATN = 0x13;
int GPIO = 0x14;
int PACE = 0x15;
int CONFIG4 = 0x17;
int WCT1 = 0x18;
int WCT2 = 0x19;

//wifi variables:
WiFiUDP Udp;
#define localUdpPort 4210  // local port to listen on
char incomingPacket[255];  // buffer for incoming packets

//Variables:
uint8_t  CHH[8], CHM[8], CHL[8]; //recieved A2D bits  
uint32_t STATUS1, Peak_time;
double CHV[8], CHV_S[8], CHV_DC[8], CH_Peak, CH_Threshold = 1; //calculated voltage values

char buffNew[10];
char buff[2048];

uint16_t i;
uint16_t count;
byte sendPacket[1350];

IPAddress remote;
Servo myservo;


void setup() {
myservo.attach(D8);  
ESP8266_config();
ADS1298_config();
WifiConfig();
Serial.println("Waiting for start signal");
}

void loop() {  

  checkUDP();
    
  if (!digitalRead(DRDY)) //if DRDY pulled low
  { 
     
    for (i = 0 ; i < 9 ; i++) 
    {
      //Clock out each byte - 3x status bytes, plus 3x channel 1 bytes
      sendPacket[count] = SPI.transfer(0);
      count++;      
      sendPacket[count] = SPI.transfer(0);
      count++;      
      sendPacket[count] = SPI.transfer(0);
      count++;      
    }

    //send
    if (count >= 1350) //packet size = 9*3*[number of samples for each channel]
    //note: count limit must be a multiple of packet size
    { 
      //broadcast over UDP
      Udp.beginPacket(remote, localUdpPort);
      Udp.write(sendPacket,sizeof(sendPacket));
      Udp.endPacket();

      //clear buffer and count
      count = 0;
    }
    
//    //IF USING SERVO MOTOR DIRECTLY FROM ESP8266:
//    //highpass filter:
//    CHV_DC[CHANNEL_SELECT] = CHV_DC[CHANNEL_SELECT]*0.9 + CHV[CHANNEL_SELECT]*0.1;
//    CHV_S[CHANNEL_SELECT] = CHV[CHANNEL_SELECT] - CHV_DC[CHANNEL_SELECT];
//    
//    //Rectifying and peak detection
//    if (abs(CHV_S[CHANNEL_SELECT]) > CH_Peak) //if new peak is detected
//    {
//      CH_Peak = abs(CHV_S[CHANNEL_SELECT]);   //peak take new value
//      Peak_time = micros();                   //start timing from when peak was detected
//    }
//    else
//      if (micros() - Peak_time > 100)         //if below peak, wait 100ms then slow(ish) decay
//        CH_Peak *= 0.95;
//
//    //Threshold system with hysteresis (AKA schmidt trigger, or double-threshold  to prevent chatter)
//    if (CH_Peak > CH_Threshold) //if thrshold exceeded, activate motor and reduce threshold to 10%
//    {
//      myservo.write(180);
//      CH_Threshold = 0.1;
//    }
//    else        //if lower threshold is not exceeded, move motor back to start and raise threshold again
//    {
//      myservo.write(0);
//      CH_Threshold = 1;
//    }
  }
}

char checkUDP(void)
{
  incomingPacket[0] = 'z';
  int packetSize = Udp.parsePacket();
  if (packetSize)
  {
    // receive incoming UDP packets
    Serial.printf("Received %d bytes from %s, port %d\n", packetSize, remote.toString().c_str(), localUdpPort);
    remote = Udp.remoteIP();
    int len = Udp.read(incomingPacket, UDP_TX_PACKET_MAX_SIZE);
    if (len > 0)
      incomingPacket[len] = 0;

    if (incomingPacket[0] == 'a')
    {
      Serial.println("Start instruction received.");
      SPI.transfer(START); //Activate conversion
      SPI.transfer(RDATAC); //Activate continuous data mode
      Udp.beginPacket(remote, localUdpPort);
      Udp.write('A');
      Udp.endPacket();
    }
    
    if (incomingPacket[0] == 'b')
    {
      Serial.println("Stop instruction received.");
      SPI.transfer(STOP); //Activate conversion
      Udp.beginPacket(remote, localUdpPort);
      Udp.write('B');
      Udp.endPacket();
    }
    
    if (incomingPacket[0] == 'c')
    {
      Serial.println("Reset instruction received.");
      Udp.beginPacket(remote, localUdpPort);
      Udp.write('C');
      Udp.endPacket();

      delay(1000);
      ESP.restart();
    }

    if (incomingPacket[0] == 'd')
    {
      Serial.println("Select electrodes instruction received.");
      SPI.transfer(STOP); //Activate conversion
      delay(5);
      SOURCE = 0b000;
      for (i = 0; i < 8 ; i++)
        WREG(CHSET[i], (GAIN << 4) + SOURCE);
      SPI.transfer(START); //Activate conversion
      Udp.beginPacket(remote, localUdpPort);
      Udp.write('D');
      Udp.endPacket();
    }
    
    if (incomingPacket[0] == 'e')
    {
      Serial.println("Select test signal instruction received.");
      SPI.transfer(STOP); //Activate conversion
      delay(5);
      SOURCE = 0b101;
      for (i = 0; i < 8 ; i++)
        WREG(CHSET[i], (GAIN << 4) + SOURCE);
      SPI.transfer(START); //Activate conversion
      Udp.beginPacket(remote, localUdpPort);
      Udp.write('E');
      Udp.endPacket();
    }

    if (incomingPacket[0] == 'f')
    {
      Serial.println("Select internal short instruction received.");
      SPI.transfer(STOP); //Activate conversion
      delay(5);
      SOURCE = 0b001;
       for (i = 0; i < 8 ; i++)
        WREG(CHSET[i], (GAIN << 4) + SOURCE);
      SPI.transfer(START); //Activate conversion
      Udp.beginPacket(remote, localUdpPort);
      Udp.write('F');
      Udp.endPacket();
    }  

    if (incomingPacket[0] == 'g')
    {
      Serial.println("Select 1x Gain instruction received.");
      SPI.transfer(STOP); //Activate conversion
      delay(5);
      GAIN = 0b001;
      for (i = 0; i < 8 ; i++)
        WREG(CHSET[i], (GAIN << 4) + SOURCE);
      SPI.transfer(START); //Activate conversion
      Udp.beginPacket(remote, localUdpPort);
      Udp.write('G');
      Udp.endPacket();
    }  

    if (incomingPacket[0] == 'h')
    {
      Serial.println("Select 2x Gain instruction received.");
      SPI.transfer(STOP); //Activate conversion
      delay(5);
      GAIN = 0b010;
      for (i = 0; i < 8 ; i++)
        WREG(CHSET[i], (GAIN << 4) + SOURCE);
      SPI.transfer(START); //Activate conversion
      Udp.beginPacket(remote, localUdpPort);
      Udp.write('H');
      Udp.endPacket();
    }  
    
    if (incomingPacket[0] == 'i')
    {
      Serial.println("Select 4x Gain instruction received.");
      SPI.transfer(STOP); //Activate conversion
      delay(5);
      GAIN = 0b100;
      for (i = 0; i < 8 ; i++)
        WREG(CHSET[i], (GAIN << 4) + SOURCE);
      SPI.transfer(START); //Activate conversion
      Udp.beginPacket(remote, localUdpPort);
      Udp.write('I');
      Udp.endPacket();
    }  
    
    if (incomingPacket[0] == 'j')
    {
      Serial.println("Select 6x Gain instruction received.");
      SPI.transfer(STOP); //Activate conversion
      delay(5);
      GAIN = 0b000;
      for (i = 0; i < 8 ; i++)
        WREG(CHSET[i], (GAIN << 4) + SOURCE);
      SPI.transfer(START); //Activate conversion
      Udp.beginPacket(remote, localUdpPort);
      Udp.write('J');
      Udp.endPacket();
    }  
    
    if (incomingPacket[0] == 'k')
    {
      Serial.println("Select 12x Gain instruction received.");
      SPI.transfer(STOP); //Activate conversion
      delay(5);
      GAIN = 0b110;
      for (i = 0; i < 8 ; i++)
        WREG(CHSET[i], (GAIN << 4) + SOURCE);
      SPI.transfer(START); //Activate conversion
      Udp.beginPacket(remote, localUdpPort);
      Udp.write('K');
      Udp.endPacket();
    }  

    if (incomingPacket[0] == 'l')
    {
      Serial.println("Select sampling rate of 500sps instruction received.");
      SPI.transfer(STOP); //Activate conversion
      delay(5);
      DR = 0b110;
      WREG(CONFIG1, (HR<<7) + (DAISY_EN<<6) + (CLK_EN<<5) + DR);
      SPI.transfer(START); //Activate conversion
      Udp.beginPacket(remote, localUdpPort);
      Udp.write('L');
      Udp.endPacket();
    } 

    if (incomingPacket[0] == 'm')
    {
      Serial.println("Select sampling rate of 1000sps instruction received.");
      SPI.transfer(STOP); //Activate conversion
      delay(5);
      DR = 0b101;
      WREG(CONFIG1, (HR<<7) + (DAISY_EN<<6) + (CLK_EN<<5) + DR);
      SPI.transfer(START); //Activate conversion
      Udp.beginPacket(remote, localUdpPort);
      Udp.write('M');
      Udp.endPacket();
    }

    if (incomingPacket[0] == 'n')
    {
      Serial.println("Select sampling rate of 2000sps instruction received.");
      SPI.transfer(STOP); //Activate conversion
      delay(5);
      DR = 0b100;
      WREG(CONFIG1, (HR<<7) + (DAISY_EN<<6) + (CLK_EN<<5) + DR);
      SPI.transfer(START); //Activate conversion
      Udp.beginPacket(remote, localUdpPort);
      Udp.write('N');
      Udp.endPacket();
    }  

    if (incomingPacket[0] == 'o')
    {
      Serial.println("Select sampling rate of 4000sps instruction received.");
      SPI.transfer(STOP); //Activate conversion
      delay(5);
      DR = 0b011;
      WREG(CONFIG1, (HR<<7) + (DAISY_EN<<6) + (CLK_EN<<5) + DR);
      SPI.transfer(START); //Activate conversion
      Udp.beginPacket(remote, localUdpPort);
      Udp.write('O');
      Udp.endPacket();
    }
    if (incomingPacket[0] == 'p')
    {
      Serial.println("Select sampling rate of 1000sps instruction received.");
      SPI.transfer(STOP); //Activate conversion
      delay(5);
      DR = 0b010;
      WREG(CONFIG1, (HR<<7) + (DAISY_EN<<6) + (CLK_EN<<5) + DR);
      SPI.transfer(START); //Activate conversion
      Udp.beginPacket(remote, localUdpPort);
      Udp.write('P');
      Udp.endPacket();
    }
  }
  return incomingPacket[0];
}

void ESP8266_config(void)
{
//Serial config:
Serial.begin(250000);
Serial.println();
Serial.println("________________________________________________________________");

//pin modes
pinMode(CS, OUTPUT);
pinMode(DRDY, INPUT);
pinMode(PDWN_RESET, OUTPUT);

//SPI config:
SPI.begin();
SPI.beginTransaction(SPISettings(1000000,MSBFIRST, SPI_MODE1));
SPI.setBitOrder(MSBFIRST);
SPI.setDataMode(SPI_MODE1); //sets clock polaroty and phase 
}

void ADS1298_config(void)
{
  //initialize ADS1298:
  digitalWrite(PDWN_RESET, LOW);
  delay(200);
  digitalWrite(PDWN_RESET, HIGH);
  digitalWrite(CS, LOW);        //Since only using one device (not daisy-chained), hold CS low permanently 
  delay(1000);                   //wait for oscillator to wake up
  SPI.transfer(RESET);
  delay(100);
  SPI.transfer(WAKEUP);
  delay(1);
  SPI.transfer(SDATAC);
  delay(1);
  
  Serial.print("Testing device communication...");
  
  //check comms:
  if (RREG(ID) != 0x92) //check device ID
  {
    Serial.println();
    Serial.println();
    Serial.println("Communication error, check wiring and power");
    Serial.print("Expected device ID 0x92, received 0x");
    Serial.print(RREG(ID), HEX);
    Serial.println(".");
    ESP.restart();
  }
  else
    Serial.println("Success. Communication with ADS1298 estabished");
  
  Serial.println("Writing config registers:");
  Serial.print("Config 1: "); Serial.println((HR<<7) + (DAISY_EN<<6) + (CLK_EN<<5) + DR, BIN);
  Serial.print("Config 2: "); Serial.println((WCT_CHOP<<5) + (INT_TEST<<4) + (TEST_AMP<<2) +(TEST_FREQ), BIN);
  Serial.print("Config 3: "); Serial.println((PD_REFBUFF<<7) + (VREF_4V<<5) + (RLD_MEAS<<4) + (RLDREF_INT<<3) + (PD_RLD<<2) + (RLD_LOFF_SENS<<1) + (RLD_STAT), BIN);
  
  uint8_t test1 = WREG(CONFIG3, (PD_REFBUFF<<7) + (1<<6) + (VREF_4V<<5)+(RLD_MEAS<<4) + (RLDREF_INT<<3) + (PD_RLD<<2) + (RLD_LOFF_SENS<<1) + (RLD_STAT));
  delay(10); //delay recommended by datasheet
  uint8_t test2 = WREG(CONFIG1, (HR<<7) + (DAISY_EN<<6) + (CLK_EN<<5) + DR);
  uint8_t test3 = WREG(CONFIG2, (WCT_CHOP<<5) + (INT_TEST<<4) + (TEST_AMP<<2) +(TEST_FREQ));
  
  //channel configs:
  for (i = 0; i < 8; i++)
    WREG(CHSET[i], (GAIN << 4) + SOURCE);
  
  //select which channel(s) to power up, and modes:
  
  //always use CH1 for RLD
  WREG(RLD_SENSN, 0b1); //select this channel for RLD input
  WREG(RLD_SENSP, 0b1); //select this channel for RLD input
  
  if (test1 && test2 && test3)
    Serial.println("Successful");
  else
  {
    Serial.println("Communication failure. registers not written");
    while(1);
  }
}

byte WifiConfig(void)
{
Serial.print("Setting up access point...");
const char *ssid = "Biosignals";
const char *password = "password";
WiFiClient client;
client.setNoDelay(1);
WiFi.mode(WIFI_AP);
WiFi.softAP(ssid, password);
Udp.begin(localUdpPort);
Serial.printf("Success. Now listening at IP %s, UDP port %d\n", WiFi.softAPIP().toString().c_str(), localUdpPort);
}

int WREG(int Reg, int data)
{
  SPI.transfer(0b01000000 + Reg);//read ID register
  delay(1);
  SPI.transfer(0);//number of registers to write -1
  delay(1);
  SPI.transfer(data); //transfer data
  delay(1);
  
  //check write:
  if (RREG(Reg) == data)
    return 1;
  else
    return 0;
}

int RREG(int Reg)
{
  SPI.transfer(0b00100000 + Reg);//read ID register
  delay(1);
  SPI.transfer(0);//number of registers to read -1
  delay(1);
  
  int data = SPI.transfer(0);//number of registers to read -1
  delay(1);
  
  return data;
}

double codes2volts(uint32_t CH)
{
  if (CH <= 0x7FFFFF)
    return float(CH)/0x7FFFFF*2400;
  else
    return (float(CH)/0x7FFFFF - 2)*2400;
}
