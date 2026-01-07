import os
import cv2
import glob
import time
from emailing import send_email
from threading import Thread

# setting up the camera.
video = cv2.VideoCapture(0)    # 0 - main camera, and 1 could be secondary camera USB one and else.
time.sleep(1)         # giving the camera time to load, to avoid black frames.


first_frame = None
status_list = []
count = 1

# This is the code to remove all images after use from the folder.
def clean_folder():
    print("Clean folder function started")
    images = glob.glob("images/*.png")
    for image in images:
        os.remove(image)
    print("Clean folder function finished")

while True:

    status = 0
    check, frame = video.read()

    grey_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)  # converting to grey scale for better handling for now.

    grey_frame_gaussian = cv2.GaussianBlur(grey_frame, (21, 21), 0) # blurring a little for lighter handling.

    if first_frame is None:
        first_frame = grey_frame_gaussian

    delta_frame = cv2.absdiff(first_frame, grey_frame_gaussian)    # takes the first frame, and then shows the difference, if something in the live frame changes.

    thresh_frame = cv2.threshold(delta_frame, 60, 255, cv2.THRESH_BINARY)[1]   # trying to modify delta frame, first_frame = black < 65 pix, and anything over that pitch white 255.
    dil_frame = cv2.dilate(thresh_frame, None, iterations=2)    # the more iteration, the more processing.
    # cv2.imshow('My Video', dil_frame)

    contours, check = cv2.findContours(dil_frame, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)   # detect the contours

    for contour in contours:
        if cv2.contourArea(contour) > 25000:
            continue
        x, y, w, h = cv2.boundingRect(contour)      # extracting the corners of the rectangle detector.
        rectangle = cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 3)

        if rectangle.any():
            status = 1
            cv2.imwrite(f"images/{count}.png", frame)  # creating the image to be emailed.
            count = count + 1

            # calling all images, so we specify to find the middle one of the pile.
            all_images = glob.glob("images/*.png")
            index = int(len(all_images)/2)
            image_with_object = all_images[index]



    status_list.append(status)
    status_list = status_list[-2:]

    if status_list[0] == 1 and status_list[1] == 0:

        # creating the thread, parallel task, working on sending and else in the background.
        email_thread = Thread(target=send_email, args=(image_with_object, ))
        email_thread.daemon = True

        email_thread.start()

        # Thread to clean folder
        clean_thread = Thread(target=clean_folder)
        clean_thread.daemon = True


        clean_thread.start()    # want to clean the folder once the user has clicked q

    cv2.imshow("Video", frame)

    key = cv2.waitKey(1)
    if key == ord('q'):
        break

video.release()

