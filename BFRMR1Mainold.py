#!/usr/bin/python

########################################################################
#
# A Python script for controlling the BFRMR1 mobile robot
#
#
# Author : Peter Neal
#
# Date : 30 July 2014
#
########################################################################

import BFRMR1tft
import RPi.GPIO as GPIO
import time
import BFRMR1serialport
import os

GPIO.setup(4, GPIO.IN) #Buttons
GPIO.setup(17, GPIO.IN)
GPIO.setup(21, GPIO.IN)
GPIO.setup(22, GPIO.IN)

# ScreenCounter
# 0: Main screen
# 1: View data screen
# 2: Manual control screen
# 3: Obstacle avoidance mode screen
# 4: Shutdown
#
#

# Data Packet from robot
#
# Byte  Description
# 0	Right Looking IR		
# 1	Centre IR
# 2	Left Looking IR
# 3	Head Pan Position
# 4	Head Tilt Position
# 5	Sonar Sensor
# 6	Left Encoder
# 7	Right Encoder


ScreenCounter = 0
pointercounter = 0

#################################################################################
#
# Robot control variables
#


SonarThreshold = 40
IRThreshold = 80
TurnCount = 0
AUTOSPEED = 5  #speed of robot during automatic operation


#Instructions
GETDATA = 0
ROBOTFORWARD = 1
ROBOTLEFT = 2
ROBOTRIGHT = 3
ROBOTREVERSE = 4
HEADMOVE = 5
#################################################################################
#
# TFT screen constants
#

STARTSCREEN = 0
VIEWDATASCREEN = 1

OBSTAVOIDSCREEN = 3
SHUTDOWNSCREEN = 4


def HeadMove(pan,tilt):
    BFRMR1serialport.sendserial([255,255,HEADMOVE,pan,tilt]) #send command to move head
    while True:
        a = BFRMR1serialport.getserial() #wait here until data is received to confirm command complete
        if a is not None:
            break    
    return a #return data packet

def RobotMove(direction,encodercount,speed):
    BFRMR1serialport.sendserial([255,255,direction,encodercount,speed]) #send command to move head
    while True:
        a = BFRMR1serialport.getserial() #wait here until data is received to confirm command complete
        if a is not None:
            break    
    return a #return data packet

def GetData():
    BFRMR1serialport.sendserial([255,255,GETDATA,0,0]) #send command to move head
    while True:
        a = BFRMR1serialport.getserial() #wait here until data is received to confirm command complete
        if a is not None:
            break    
    return a #return data packet

while True:

    #Read all of the buttons
    buttonstate0 = GPIO.input(4)
    buttonstate1 = GPIO.input(17)
    buttonstate2 = GPIO.input(21)
    buttonstate3 = GPIO.input(22)
    #print buttonstate0, buttonstate1, buttonstate2, buttonstate3

    if ScreenCounter is STARTSCREEN: #on main screen
        if buttonstate0 is 0:
            time.sleep(0.2) #debounce switch
            if pointercounter > 0: 
                pointercounter -= 1
                BFRMR1tft.EditStartScreen(pointercounter)
      
        if buttonstate1 is 0:
            time.sleep(0.2) #debounce switch
            if pointercounter < 3: 
                pointercounter += 1
                BFRMR1tft.EditStartScreen(pointercounter)

        if buttonstate2 is 0:
            time.sleep(0.2) #debounce switch
            if pointercounter is 0:
                ScreenCounter = VIEWDATASCREEN
                BFRMR1tft.ViewDataScreen()
            if pointercounter is 2:
                ScreenCounter = OBSTAVOIDSCREEN
                BFRMR1tft.ObsAvoidScreen()
            if pointercounter is 3:
                ScreenCounter = SHUTDOWNSCREEN
                buttonstate2 = 1 #reset buttonstate2 so shutdown is not called straight away
                BFRMR1tft.ShutdownScreen()


    if ScreenCounter is VIEWDATASCREEN: #on view data screen
        if SendFirstPacket is 0: #send a packet of data once to trigger return of data from arduino
            a = GetData()
            BFRMR1tft.EditViewDataScreen(a[5],a[2],a[1],a[0],a[6],a[7])
            

        if buttonstate3 is 0:
            time.sleep(0.2) #debounce switch
            ScreenCounter = STARTSCREEN
            BFRMR1tft.StartScreen()
            BFRMR1tft.EditStartScreen(pointercounter)

    #####################################################################################
    #
    # Obstacle avoidance routine

    if ScreenCounter is 3: #on obstacle avoid screen
        
        if SendFirstPacket is 0: #send a packet of data once to trigger return of data from arduino
            senddata()
            SendFirstPacket = 1
        #time.sleep(0.1)        
        a = BFRMR1serialport.getserial()

        if a is not None: #if some data has been received
            LeftEncoderTotal = LeftEncoderTotal + a[6]
            RightEncoderTotal = RightEncoderTotal + a[7]

            if ObstAvoidCounter is 0 or ObstAvoidCounter is 1 or ObstAvoidCounter is 2:
                if a[0] > IRThreshold:             #if object detected to the right
                    LeftWheelSpeed = 20 #stop the wheels
                    RightWheelSpeed = 20
                    LeftEncoderTotal = 0 #reset wheel encoder counts ready to turn
                    RightEncoderTotal = 0
                    TurnCount = 50
                    BFRMR1tft.EditObsAvoidScreen('Object to right - IR')                  
                    ObstAvoidCounter = 3    #trigger turn

            if ObstAvoidCounter is 0 or ObstAvoidCounter is 1 or ObstAvoidCounter is 2:
                if a[1] > IRThreshold:             #if object detected at the centre
                    LeftWheelSpeed = 20 #stop the wheels
                    RightWheelSpeed = 20
                    LeftEncoderTotal = 0 #reset wheel encoder counts ready to turn
                    RightEncoderTotal = 0
                    TurnCount = 50
                    BFRMR1tft.EditObsAvoidScreen('Object at centre - IR')  
                    ObstAvoidCounter = 5    #trigger turn

            if ObstAvoidCounter is 0 or ObstAvoidCounter is 1 or ObstAvoidCounter is 2:
                if a[2] > IRThreshold:             #if object detected to the left
                    LeftWheelSpeed = 20 #stop the wheels
                    RightWheelSpeed = 20
                    LeftEncoderTotal = 0 #reset wheel encoder counts ready to turn
                    RightEncoderTotal = 0
                    TurnCount = 50
                    BFRMR1tft.EditObsAvoidScreen('Object to left - IR') 
                    ObstAvoidCounter = 4   #trigger turn
                

            if ObstAvoidCounter is 0:          #look to the right
                HeadPanPos = 40          #go to first sweep position
                HeadTiltPos = 128
                if a[3] > 45 and a[3] < 60:        #if at first position
                    if a[5] < SonarThreshold: #object detected to the right by either sonar sensor or IR sensor
                        LeftWheelSpeed = 20 #stop the wheels
                        RightWheelSpeed = 20
                        LeftEncoderTotal = 0 #reset wheel encoder counts ready to turn
                        RightEncoderTotal = 0
                        TurnCount = 50
                        BFRMR1tft.EditObsAvoidScreen('Object to right - Sonar') 
                        ObstAvoidCounter = 3

                    else:
                        LeftWheelSpeed = 20 + AutoSpeed     #start wheels
                        RightWheelSpeed = 20 + AutoSpeed
                        ObstAvoidCounter = 1       #increment counter
                        BFRMR1tft.EditObsAvoidScreen('Clear - Moving forward') 

                        
            elif ObstAvoidCounter is 1:        #look to the left
                HeadPanPos = 220          #go to second head position
                HeadTiltPos = 128  
                if a[3] > 100 and a[3] < 110:        #if at second position
                    if a[5] < SonarThreshold:
                        LeftWheelSpeed = 20 #stop the wheels
                        RightWheelSpeed = 20
                        LeftEncoderTotal = 0 #reset wheel encoder counts ready to turn
                        RightEncoderTotal = 0
                        TurnCount = 50
                        BFRMR1tft.EditObsAvoidScreen('Object to left - Sonar')
                        ObstAvoidCounter = 4

                    else:
                        LeftWheelSpeed = 20 + AutoSpeed     #start wheels
                        RightWheelSpeed = 20 + AutoSpeed
                        ObstAvoidCounter = 2       #increment counter
                        BFRMR1tft.EditObsAvoidScreen('Clear - Moving forward')

            elif ObstAvoidCounter is 2:      #look forward with sonar sensor
                HeadPanPos = 128          #go to third head position
                HeadTiltPos = 128
                if a[3] > 77 and a[3] < 90:      #if at third position
                    if a[5] < SonarThreshold:
                        LeftWheelSpeed = 20 #stop the wheels
                        RightWheelSpeed = 20
                        LeftEncoderTotal = 0 #reset wheel encoder counts ready to turn
                        RightEncoderTotal = 0
                        TurnCount = 50
                        BFRMR1tft.EditObsAvoidScreen('Object to centre - Sonar')
                        ObstAvoidCounter = 5

                    else:
                        LeftWheelSpeed = 20 + AutoSpeed     #start wheels
                        RightWheelSpeed = 20 + AutoSpeed
                        ObstAvoidCounter = 0       #Back to the start
                        BFRMR1tft.EditObsAvoidScreen('Clear - Moving forward')


            #Obstavoidcounter is 3 - start wheels turning so that robot turns left. 
            #When left wheel encoder count has hit it limit, stop the wheel.
            #Same for the right wheel. When both wheels have stopped, set counter to 0 to resume exploring
            elif ObstAvoidCounter is 3:
                LeftWheelSpeed = 20 - AutoSpeed     #start wheels
                RightWheelSpeed = 20 + AutoSpeed
                if LeftEncoderTotal > TurnCount:
                    LeftWheelSpeed = 20 #stop the left wheel
                if RightEncoderTotal > TurnCount:
                    RightWheelSpeed = 20 #stop the right wheel
                if LeftWheelSpeed is 20 and RightWheelSpeed is 20: #Both wheels have stopped
                    ObstAvoidCounter = 0
                  
            #Obstavoidcounter is 4 - start wheels turning so that robot turns right. 
            #When left wheel encoder count has hit it limit, stop the wheel.
            #Same for the right wheel. When both wheels have stopped, set counter to 0 to resume exploring
            elif ObstAvoidCounter is 4:
                LeftWheelSpeed = 20 + AutoSpeed     #start wheels
                RightWheelSpeed = 20 - AutoSpeed
                if LeftEncoderTotal > TurnCount:
                    LeftWheelSpeed = 20 #stop the left wheel
                if RightEncoderTotal > TurnCount:
                    RightWheelSpeed = 20 #stop the right wheel
                if LeftWheelSpeed is 20 and RightWheelSpeed is 20: #Both wheels have stopped
                    ObstAvoidCounter = 0

            #Obstavoidcounter is 5 - Start wheels so that robot reverses. When left wheel encoder count has hit it limit, stop the wheel.
            #Same for the right wheel. When both wheels have stopped, set counter to 4 to turn left approximately 180 degrees
            elif ObstAvoidCounter is 5:
                LeftWheelSpeed = 20 - AutoSpeed     #start wheels
                RightWheelSpeed = 20 - AutoSpeed
                if LeftEncoderTotal > TurnCount:
                    LeftWheelSpeed = 20 #stop the left wheel
                if RightEncoderTotal > TurnCount:
                    RightWheelSpeed = 20 #stop the right wheel
                if LeftWheelSpeed is 20 and RightWheelSpeed is 20: #Both wheels have stopped
                    LeftEncoderTotal = 0 #reset wheel encoder counts ready to turn
                    RighEncoderTotal = 0
                    TurnCount = 70
                    ObstAvoidCounter = 4

            time.sleep(0.05) # delay a bit to slow down data transfer
            senddata()

        if buttonstate3 is 0:
            time.sleep(0.2) #debounce switch
            ScreenCounter = 0
            LeftWheelSpeed = 20 #stop the wheels
            RightWheelSpeed = 20
            senddata()
            SendFirstPacket = 0
            BFRMR1tft.StartScreen()
            BFRMR1tft.EditStartScreen(pointercounter)

    #####################################################################################
    #
    # Shutdown routine

    if ScreenCounter is SHUTDWONSCREEN: #on shutdown screen

        if buttonstate3 is 0: #back button has been pressed, return to main screen
            time.sleep(0.2) #debounce switch
            ScreenCounter = STARTSCREEN
            BFRMR1tft.StartScreen()
            BFRMR1tft.EditStartScreen(pointercounter)

        if buttonstate2 is 0: #enter button pressed, time to shutdown
            time.sleep(0.2) #debounce switch
            BFRMR1tft.ShuttingDown()
            os.system("sudo shutdown -h now")



