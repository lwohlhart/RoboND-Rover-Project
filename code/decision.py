import numpy as np
import cv2   


# This is where you can build a decision tree for determining throttle, brake and steer 
# commands based on the output of the perception_step() function
def decision_step(Rover):

    # Implement conditionals to decide what to do given perception data
    # Here you're all set up with some basic functionality but you'll need to
    # improve on this decision tree to do a good job of navigating autonomously!

        
    ''' if len(Rover.path_plan) == 0:
        theta = Rover.yaw/180 * np.pi + np.pi/8
        M = np.array([[np.cos(theta), -np.sin(theta)], 
                      [np.sin(theta),  np.cos(theta)]])
        p = Rover.pos + np.matmul(M, np.array([2, 0]))        
        thresh = (1 * (Rover.occupancy > 0)).astype(np.uint8)
        im2, contours, hierarchy = cv2.findContours(thresh,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
        cnt_img = np.zeros((200,200,3))
        cv2.drawContours(cnt_img, contours, -1, (255,0,0), 1)
        cv2.line(cnt_img, (int(Rover.pos[0]), int(Rover.pos[1])), (int(p[0]), int(p[1])), (0,255,0), 1)
        #cv2.polylines(cnt_img,[np.array([Rover.pos, p])],True,(0,255,255))
        intersections_x, intersections_y = cv2.inRange(cnt_img, (200,200,0), (255,255,0)).nonzero()
        Rover.worldmap[:,:,1] = cnt_img[:,:,0]#cv2.inRange(cnt_img, (200,200,0), (255,255,0))
        Rover.worldmap[:,:,1] = 0
        cv2.drawContours(Rover.worldmap, contours, -1, (0,255,0), 1)     
        print("contours {}".format(contours))   

        if intersections_x.any():
            intersection_pos = np.mean(np.hstack([intersections_x, intersections_y]), axis=1)
            print("intersection at {}".format(intersection_pos))                       
            print(contours)
        print ('add point {}'.format(p))
        Rover.path_plan.append(p)
    
    if len(Rover.path_plan) > 0:
        if len(Rover.rocks) > 0:
            p = Rover.rocks[0]
        else:
            p = Rover.path_plan[0]
        vec = p - Rover.pos
        rover_angle = Rover.yaw if Rover.yaw < 180 else Rover.yaw - 360
        angle_delta = np.arctan2(vec[1], vec[0]) - rover_angle/180*np.pi
        dist = np.linalg.norm(vec)
        print ('vec: {}, angle_delta {}, dist {}'.format(vec, angle_delta, dist))
        if np.abs(angle_delta) > 0:
            Rover.steer = np.clip(angle_delta*10, -15, 15)
        if np.abs(angle_delta) > 10*np.pi/180 and Rover.vel > 0.2:
            Rover.brake = Rover.brake_set
            Rover.throttle = 0
        elif np.abs(angle_delta) < 2*np.pi/180 and Rover.vel < Rover.max_vel:
            Rover.brake = 0
            Rover.throttle = Rover.throttle_set
        else: 
            Rover.brake = 0
            Rover.throttle = 0
        if dist < 0.1:
            Rover.path_plan.pop() '''
    if len(Rover.rocks) > 0:
        Rover.mode = 'approach_rock'
                 
    # Example:
    # Check if we have vision data to make decisions with
    if Rover.nav_angles is not None:
        # Check for Rover.mode status
        if Rover.mode == 'forward': 
            # Check the extent of navigable terrain
            if len(Rover.nav_angles) >= Rover.stop_forward:  
                # If mode is forward, navigable terrain looks good 
                # and velocity is below max, then throttle 
                if Rover.vel < Rover.max_vel:
                    # Set throttle value to throttle setting
                    Rover.throttle = Rover.throttle_set
                else: # Else coast
                    Rover.throttle = 0
                Rover.brake = 0
                # Set steering to average angle clipped to the range +/- 15
                Rover.steer = np.clip(np.mean(Rover.nav_angles * 180/np.pi), -15, 15)
            # If there's a lack of navigable terrain pixels then go to 'stop' mode
            elif len(Rover.nav_angles) < Rover.stop_forward:
                    # Set mode to "stop" and hit the brakes!
                    Rover.throttle = 0
                    # Set brake to stored brake value
                    Rover.brake = Rover.brake_set
                    Rover.steer = 0
                    Rover.mode = 'stop'

        # If we're already in "stop" mode then make different decisions
        elif Rover.mode == 'stop':
            # If we're in stop mode but still moving keep braking
            if Rover.vel > 0.2:
                Rover.throttle = 0
                Rover.brake = Rover.brake_set
                Rover.steer = 0
            # If we're not moving (vel < 0.2) then do something else
            elif Rover.vel <= 0.2:
                # Now we're stopped and we have vision data to see if there's a path forward
                if len(Rover.nav_angles) < Rover.go_forward:
                    Rover.throttle = 0
                    # Release the brake to allow turning
                    Rover.brake = 0
                    # Turn range is +/- 15 degrees, when stopped the next line will induce 4-wheel turning
                    Rover.steer = -15 # Could be more clever here about which way to turn
                # If we're stopped but see sufficient navigable terrain in front then go!
                if len(Rover.nav_angles) >= Rover.go_forward:
                    # Set throttle back to stored value
                    Rover.throttle = Rover.throttle_set
                    # Release the brake
                    Rover.brake = 0
                    # Set steer to mean angle
                    Rover.steer = np.clip(np.mean(Rover.nav_angles * 180/np.pi), -15, 15)
                    Rover.mode = 'forward'
        elif Rover.mode == 'approach_rock':
        
            p = Rover.rocks[0]
            
            vec = p - Rover.pos
            rover_angle = Rover.yaw if Rover.yaw < 180 else Rover.yaw - 360
            angle_delta = np.arctan2(vec[1], vec[0]) - rover_angle/180*np.pi
            dist = np.linalg.norm(vec)
            print ('vec: {}, angle_delta {}, dist {}'.format(vec, angle_delta, dist))
            if np.abs(angle_delta) > 0:
                Rover.steer = np.clip(angle_delta*10, -15, 15)
            if np.abs(angle_delta) > 10*np.pi/180 and Rover.vel > 0.2:
                Rover.brake = Rover.brake_set
                Rover.throttle = 0
            elif np.abs(angle_delta) < 2*np.pi/180 and Rover.vel < Rover.max_vel:
                Rover.brake = 0
                Rover.throttle = Rover.throttle_set
            else: 
                Rover.brake = 0
                Rover.throttle = 0
            if dist < 0.1:
                Rover.path_plan.pop()

            rock_vector = Rover.rocks[0] - Rover.pos
            rock_yaw = np.arctan2(rock_vector[1], rock_vector[0]) - Rover.yaw
            rock_distance = np.linalg.norm(rock_vector)
            if np.abs(rock_yaw) > 10 or rock_distance < Rover.vel:
                if Rover.vel > 0.2:
                    Rover.brake = Rover.brake_set
                else:
                    Rover.brake = 0
                Rover.throttle = 0
            else:
                Rover.brake = 0
                Rover.throttle = Rover.throttle_set
            Rover.steer = rock_yaw
    # Just to make the rover do something 
    # even if no modifications have been made to the code    
    else:
        Rover.throttle = Rover.throttle_set
        Rover.steer = 0
        Rover.brake = 0
        
    # If in a state where want to pickup a rock send pickup command
    if Rover.near_sample and Rover.vel == 0 and not Rover.picking_up:
        Rover.send_pickup = True
        Rover.rocks.pop()

        Rover.mode = 'forward'
    
    return Rover

