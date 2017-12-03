# Imports
import RPi.GPIO as GPIO
import os
import time
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
from email.MIMEImage import MIMEImage
from email.MIMEBase import MIMEBase
from email import Encoders
import smtplib
import socket

# Hardware
buttonPin = 27
buttonLedPin = 17
numberOfShots = 4
led1 = 26
led2 = 19
led3 = 13
GPIO.setmode(GPIO.BCM)
GPIO.setup(buttonLedPin, GPIO.OUT)
GPIO.setup(led1, GPIO.OUT)
GPIO.setup(led2, GPIO.OUT)
GPIO.setup(led3, GPIO.OUT)
GPIO.setup(buttonPin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Config
pauseTime = 3
tileSize = '1000x664'
animationDelay = 150
photosPath = '/home/pi/photos/'
serverHost = 'user@server'
serverPort = '22'
serverFilePath = '/path/to/save/all/photos/to/'
serverSlideshowPath = '/path/to/save/tiles/to/'
gmail_username = 'user@gmail.com'
gmail_password = 'plaintextpasswordyay'

# Options
createTile = True
createGif = True
uploadToTumblr = False # createGif must be set to True
uploadToServer = True
removePhotosFromPi = True


# Function: Test Internet Connection
def connected():
    try:
        # see if we can resolve the host name
        host = socket.gethostbyname('www.google.com')
        # connect to the host
        s = socket.create_connection((host, 80), 2)
        return True
    except:
        pass
    return False


# Function: Ready Function (runs when script is started)
def ready():

    # Notify
    print("Waiting for Button Press")

    # Turn on LED
    GPIO.output(buttonLedPin, True)


# Function: Take Photos (runs on button press)
def takePhotos(session):

    # Turn off LED
    GPIO.output(buttonLedPin, False)

    # Set and Get Shot Number
    shotNumber = 1
    shotNumberStr = str(shotNumber)

    # While the shot number is x or less, keep taking photos
    while (shotNumber <= numberOfShots):

        # Set Capture Command
        capture = "gphoto2 --capture-image-and-download --quiet --filename "+photosPath+session+"-"+str(shotNumber)+".jpg"

        # Wait for Pause Time
        if (shotNumber == 1):
            time.sleep(pauseTime/2)
        else:
            time.sleep(pauseTime)

        # Countdown
        GPIO.output(led1, True)
        time.sleep(.5)
        GPIO.output(led1, False)
        time.sleep(.5)
        GPIO.output(led2, True)
        time.sleep(.5)
        GPIO.output(led2, False)
        time.sleep(.5)
        GPIO.output(led3, True)
        time.sleep(.5)
        GPIO.output(led3, False)
        time.sleep(.5)
        GPIO.output(led1, True)
        GPIO.output(led2, True)
        GPIO.output(led3, True)

        # Take Photo
        print("Taking Photo "+str(shotNumber))
        os.system(capture)

        # Turn LEDs off
        GPIO.output(led1, False)
        GPIO.output(led2, False)
        GPIO.output(led3, False)

        # Increase Number
        shotNumber += 1


# Function: Combine Photos into Grid
def tilePhotos(session):

    # Set Combine Command
    combine = "montage "+photosPath+session+"-[1-"+str(numberOfShots)+"].jpg -geometry "+tileSize+"+1+1 "+photosPath+session+"-tile.jpg"

    # Combine-arr, My Lord
    print("Creating Tiled Photo")
    os.system(combine)


# Function: Combine Photos into Animated Gif
def animatePhotos(session):

    # Set animate command
    animate = "convert -resize 875x -delay "+str(animationDelay)+" -loop 0 "+photosPath+session+"-[1-"+str(numberOfShots)+"].jpg "+photosPath+session+"-animated.gif"

    # Animate
    print("Creating Animated GIF")
    os.system(animate)


# Function: Upload to Tumblr
def tumblr(session):

    # Notify
    print("Uploading to Tumblr")

    # Check internet connection
    while connected():
    	try:

            # Start email stuff for Tumblr upload
            msg = MIMEMultipart()
            msg['Subject'] = 'Photo Booth '+session
            msg['From'] = 'amardell1990@gmail.com'
            msg['To'] = 'borzawh3vokdy@tumblr.com'

            file_path = os.path.join(photosPath+session+'-animated.gif')
            fp = open(file_path, 'rb')
            part = MIMEBase('image', 'gif')
            part.set_payload( fp.read() )
            Encoders.encode_base64(part)
            part.add_header('Content-Disposition', 'attachment; filename="%s"' % os.path.basename(file_path))
            fp.close()
            msg.attach(part)

            server = smtplib.SMTP('smtp.gmail.com:587')
            server.starttls()
            server.login(gmail_username, gmail_password)
            server.sendmail(msg['From'], msg['To'], msg.as_string())
            server.quit()

            break

    	except ValueError:

            print "No Internetz"


# Function: Upload Files to Home Server
def serverUpload(session):

    # Upload all of current session to server via SCP
    print("Uploading to Server")
    # Upload All
    os.system('scp -P '+serverPort+' '+photosPath+session+'-* '+serverHost+':'+serverFilePath)
    # Re-upload Tiled for Slideshow
    os.system('scp -P '+serverPort+' '+photosPath+session+'-tile.jpg '+serverHost+':'+serverSlideshowPath)


# Function: Remove Photos from Pi
def removePhotos(session):

    # Remove all photos with current session ID
    print("Removing Photos from Pi")
    os.system('rm '+photosPath+session+'-*')


# Ready
ready()

# Main Program
while True:

    # Wait for Button Press
    if (GPIO.input(buttonPin) == False):

        # Get Current Time
        currentTime = time.strftime('%y%m%d-%H%M%S') # '20151227-211345'

        # Take Photos
        takePhotos(currentTime)

        # Optional: Tile Photos
        if (createTile):
            tilePhotos(currentTime)

        # Optional: Create GIF
        if (createGif):
            animatePhotos(currentTime)

        # Optional: Upload to Tumblr
        if (uploadToTumblr):
            tumblr(currentTime)

        # Optional: Upload to Server
        if (uploadToServer):
            serverUpload(currentTime)

        # Optional: Remove Photos from Pi
        if (removePhotosFromPi):
            removePhotos(currentTime)

        # Ready
        ready()
