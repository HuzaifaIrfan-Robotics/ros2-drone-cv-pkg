#!/usr/bin/env python3
import rclpy
from rclpy.node import Node


import logging
import threading
import time


from example_interfaces.srv import Trigger





import asyncio
from mavsdk import System



takeoff_drone=0
land_drone=0

# loop =asyncio.get_event_loop()
drone = System() 

async def connect_drone(drone):

    await drone.connect(system_address="udp://:14540")
    


async def drone_wait(drone):

    

    print("Waiting for drone to connect...")
    async for state in drone.core.connection_state():
        if state.is_connected:
            print(f"Drone discovered!")
            break

    print("Waiting for drone to have a global position estimate...")
    async for health in drone.telemetry.health():
        if health.is_global_position_ok:
            print("Global position estimate ok")
            break


    print("Fetching amsl altitude at home location....")
    async for terrain_info in drone.telemetry.home():
        Drone_Position=terrain_info
        absolute_altitude = Drone_Position.absolute_altitude_m
        
        break




async def drone_takeoff():

    print("-- Taking off")
    await drone.action.arm()
    await drone.action.takeoff()

    await asyncio.sleep(5)


async def drone_land():

    print("-- Landing")
    await drone.action.land()
    await asyncio.sleep(5)



# ros2 service call /drone_land example_interfaces/srv/Trigger "{}"

class DroneNode(Node):

    def __init__(self):
        super().__init__("Drone_Node_Server")
        self.server_ = self.create_service(
            Trigger, "drone_takeoff", self.callback_drone_takeoff)

        self.get_logger().info("Drone Takeoff server has been started.")

        self.server2 = self.create_service(
            Trigger, "drone_land", self.callback_drone_land)

        self.get_logger().info("Drone Land server has been started.")

    

    def callback_drone_takeoff(self, request, response):
        global takeoff_drone
        response.success=True
        response.message = 'Drone Takeoff'
        self.get_logger().info('Drone Taking Off')
        takeoff_drone=1


        # loop = asyncio.get_event_loop()
        # loop.run_in_executor(None, drone_takeoff, '')
        # loop.create_task(drone_takeoff())



        return response

    def callback_drone_land(self, request, response):
        global land_drone
        response.success=True
        response.message = 'Drone Land'
        self.get_logger().info('Drone Land')
        land_drone=1


        # loop.create_task(drone_land())
        # loop.run_in_executor(None, drone_land, '')

        return response


def ros_thread(args=None):




    rclpy.init(args=args)
    node = DroneNode()
    rclpy.spin(node)
    rclpy.shutdown()



async def drone_run(loop):
    global land_drone
    global takeoff_drone

    loop.create_task(connect_drone(drone))

    absolute_altitude=0

    await asyncio.sleep(2)

    loop.create_task(drone_wait(drone))


    while True:

        await asyncio.sleep(2)

        if takeoff_drone ==1:
            await drone_takeoff()
            takeoff_drone=0
            land_drone=0

        else:

            if land_drone == 1:
                await drone_land()
                land_drone=0








def drone_thread():

    loop = asyncio.new_event_loop()

    asyncio.set_event_loop(loop)
    loop.run_until_complete(drone_run(loop))

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
    x = threading.Thread(target=drone_thread)
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
