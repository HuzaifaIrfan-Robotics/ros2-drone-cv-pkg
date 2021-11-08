#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from functools import partial


import logging
import threading
import time


from example_interfaces.srv import Trigger








import os
import cv2
import numpy as np
import time
import mediapipe as mp




def drone_takeoff():

    global takeoff_drone

    takeoff_drone=1




def drone_land():

    global land_drone

    land_drone=1


class handDetector():
    def __init__(self, mode=False, maxHands=2, detectionConf=0.5, trackConf=0.5):
        self.mode = mode
        self.maxHands= maxHands
        self.detectionConf = detectionConf
        self.trackConf = trackConf

        self.mp_drawing = mp.solutions.drawing_utils
        #mp_drawing_styles = mp.solutions.drawing_styles
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(self.mode, self.maxHands, 1, self.detectionConf, self.trackConf)
        self.tipIds = [4,8,12,16,20]

    def findHands(self, image, draw=True):
        image.flags.writeable = False
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        self.results = self.hands.process(image)

        image.flags.writeable = True
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        if self.results.multi_hand_landmarks:
            for hand_landmarks in self.results.multi_hand_landmarks:
                if draw:
                    self.mp_drawing.draw_landmarks(
                        image,
                        hand_landmarks,
                        self.mp_hands.HAND_CONNECTIONS
                        #mp_drawing_styles.get_default_hand_landmarks_style(),
                        #mp_drawing_styles.get_default_hand_connections_style()
                    )
        return image
    
    def findPosition(self, image, handNo=0, draw=True):
        self.lmlist = []
        if self.results.multi_hand_landmarks:
            myHand = self.results.multi_hand_landmarks[handNo]
            for idx, lm in enumerate(myHand.landmark):
                h,w,c = image.shape
                cx, cy = int(lm.x*w), int(lm.y*h)
                self.lmlist.append([idx, cx, cy])
                if draw:
                    cv2.circle(image, (cx, cy), 10, (255,0,0), cv2.FILLED)

        return self.lmlist
    
    def fingersUp(self):


        fingers = []

        if len(self.lmlist):
            if self.lmlist[self.tipIds[0]][1] > self.lmlist[self.tipIds[1] - 1][1]:
                fingers.append(1)
            
            else:
                fingers.append(0)

            for id in range(1, 5):
                if self.lmlist[self.tipIds[id]][2] < self.lmlist[self.tipIds[id] - 2][2]:
                    fingers.append(1)
                
                else:
                    fingers.append(0)
        

        return fingers








takeoff_drone=0
land_drone=0

# ros2 service call /drone_land example_interfaces/srv/Trigger "{}"

class CvNode(Node):


    def __init__(self):
        super().__init__("CvNode_client")
        # self.call_add_two_ints_server(6, 7)
        # self.call_add_two_ints_server(3, 1)
        # self.call_add_two_ints_server(5, 2)

        global takeoff_drone
        global land_drone
        while True:

            # await asyncio.sleep(2)

            if takeoff_drone ==1:
                # await drone_takeoff()
                self.call_drone_takeoff_server()
                takeoff_drone=0
                land_drone=0

            else:

                if land_drone == 1:
                    # await drone_land()
                    self.call_drone_land_server()
                    land_drone=0

    def call_drone_takeoff_server(self):
        client = self.create_client(Trigger, "drone_takeoff")
        while not client.wait_for_service(1.0):
            self.get_logger().warn("Waiting for Server drone_takeoff...")

        request = Trigger.Request()
        future = client.call_async(request)
        future.add_done_callback(
            partial(self.callback_drone_takeoff))


    def call_drone_land_server(self):
        client = self.create_client(Trigger, "drone_land")
        while not client.wait_for_service(1.0):
            self.get_logger().warn("Waiting for Server drone_land...")

        request = Trigger.Request()
        future = client.call_async(request)
        future.add_done_callback(
            partial(self.callback_drone_land))



    def callback_drone_takeoff(self, future):
        try:
            response = future.result()
            self.get_logger().info('drone_takeoff')
        except Exception as e:
            self.get_logger().error("Service call failed %r" % (e,))

    def callback_drone_land(self, future):
        try:
            response = future.result()
            self.get_logger().info('drone_land')
        except Exception as e:
            self.get_logger().error("Service call failed %r" % (e,))

    # def __init__(self):
    #     super().__init__("Drone_Node_Server")
    #     self.server_ = self.create_service(
    #         Trigger, "drone_takeoff", self.callback_drone_takeoff)

    #     self.get_logger().info("Drone Takeoff server has been started.")

    #     self.server2 = self.create_service(
    #         Trigger, "drone_land", self.callback_drone_land)

    #     self.get_logger().info("Drone Land server has been started.")

    

    # def callback_drone_takeoff(self, request, response):
    #     global takeoff_drone
    #     response.success=True
    #     response.message = 'Drone Takeoff'
    #     self.get_logger().info('Drone Taking Off')
    #     takeoff_drone=1


    #     # loop = asyncio.get_event_loop()
    #     # loop.run_in_executor(None, drone_takeoff, '')
    #     # loop.create_task(drone_takeoff())



    #     return response

    # def callback_drone_land(self, request, response):
    #     global land_drone
    #     response.success=True
    #     response.message = 'Drone Land'
    #     self.get_logger().info('Drone Land')
    #     land_drone=1


    #     # loop.create_task(drone_land())
    #     # loop.run_in_executor(None, drone_land, '')

    #     return response







def ros_thread(args=None):




    rclpy.init(args=args)
    node = CvNode()
    rclpy.spin(node)
    rclpy.shutdown()













def cv_thread():




    index_finger_tip_y=0
    ptime = 0
    ctime = 0
    detector = handDetector()
    cap = cv2.VideoCapture(0)
    #vid_cod = cv2.VideoWriter_fourcc(*'XVID')
    #output = cv2.VideoWriter(r"D:\OpenCV\HandTrackingProject\hands.mp4", vid_cod, 20.0, (640,480))
    while cap.isOpened():
        ret, image = cap.read()
        if not ret:
            print("No Video detected")
            break
        image = cv2.flip(image, 1)
        image = detector.findHands(image)
        lmlist = detector.findPosition(image)
        if len(lmlist):
            if lmlist[8][2]>50 and lmlist[8][2]<450:
                if index_finger_tip_y>50 and index_finger_tip_y<450:


                

                    if lmlist[8][2]-index_finger_tip_y > 120:
                        print('Finger Down')
                        drone_land()
                    elif index_finger_tip_y - lmlist[8][2] > 120:
                        print('Finger Up')
                        drone_takeoff()
                  





            index_finger_tip_y=lmlist[8][2]

        else:
            index_finger_tip_y=0


        # print(detector.fingersUp())
        ctime = time.time()
        fps = 1/(ctime-ptime)
        ptime = ctime

        cv2.putText(image, str(int(fps)), (10, 70), cv2.FONT_HERSHEY_PLAIN, 3, (255,0,255), 2)

        cv2.imshow("Image", image)
        #output.write(image)
        if cv2.waitKey(5) == ord('q'):
            break            

    cap.release()
    #output.release()
    cv2.destroyAllWindows()


    
    # loop = asyncio.new_event_loop()

    # asyncio.set_event_loop(loop)
    # loop.run_until_complete(cv_thread(loop))



     # Start the main function
    # asyncio.ensure_future(drone_run())

    # # Runs the event loop until the program is canceled with e.g. CTRL-C
    # asyncio.get_event_loop().run_forever()


# def thread_function(name):
#     logging.info("Thread %s: starting", name)
#     time.sleep(2)
#     logging.info("Thread %s: finishing", name)


def main(args=None):


    logging.info("Main    : before creating thread")
    x = threading.Thread(target=cv_thread)
    logging.info("Main    : before running thread")
    x.start()

    y= threading.Thread(target=ros_thread)
    y.start()
    

        
    logging.info("Main    : wait for the thread to finish")
    # x.join()
    logging.info("Main    : all done")




# if __name__ == "__main__":

if __name__ == "__main__":
    main()
