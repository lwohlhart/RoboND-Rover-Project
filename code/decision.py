import numpy as np
import cv2   
from supporting_functions import rot_mat


# This is where you can build a decision tree for determining throttle, brake and steer 
# commands based on the output of the perception_step() function
def decision_step(Rover):

    # Implement conditionals to decide what to do given perception data
    # Here you're all set up with some basic functionality but you'll need to
    # improve on this decision tree to do a good job of navigating autonomously!
    if Rover.start_pos is None:
        Rover.start_pos = np.array([Rover.pos[0], Rover.pos[1]])

    if len(Rover.picked_rocks) >= 6:
        if np.linalg.norm(Rover.start_pos - np.array([Rover.pos[0], Rover.pos[1]])) < 5:
            Rover.mode = 'done'
            Rover.brake = Rover.brake_set
            Rover.throttle = 0
            Rover.steer = 0
            print ('you\'re at home baby')
            return Rover

    print ('decision - mode:{}'.format(Rover.mode))
    # If in a state where want to pickup a rock send pickup command    
    if Rover.near_sample:
        print("stop_rock")
        Rover.mode = 'stop'
        Rover.brake = Rover.brake_set
        Rover.throttle = 0
        if Rover.vel == 0 and not Rover.picking_up:
            Rover.picked_rocks.append(Rover.rocks.pop())
            Rover.send_pickup = True
            
        return Rover

    # wall crawl using left most nav angles
    nav_angles = np.sort(Rover.nav_angles)[-int(len(Rover.nav_angles)/2):] 
        
    
    # Example:
    # Check if we have vision data to make decisions with
    if nav_angles is not None:
        # Check for Rover.mode status
        if Rover.mode == 'forward': 
            if len(Rover.rock_angles) > 1:
                # print("approach_rock")
                Rover.throttle = Rover.throttle_set if Rover.vel < 0.5 else 0                
                Rover.brake = 0
                Rover.steer = np.clip(np.mean(Rover.rock_angles * 180/np.pi), -15, 15)             
            # Check the extent of navigable terrain
            elif len(nav_angles) >= Rover.stop_forward:  
                # If mode is forward, navigable terrain looks good 
                # and velocity is below max, then throttle                 
                Rover.throttle = Rover.throttle_set if Rover.vel < Rover.max_vel else 0                
                Rover.brake = 0
                # Set steering to average angle clipped to the range +/- 15
                Rover.steer = np.clip(np.mean(nav_angles * 180/np.pi), -15, 15)
            # If there's a lack of navigable terrain pixels then go to 'stop' mode
            elif len(nav_angles) < Rover.stop_forward:
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
                if len(nav_angles) < Rover.go_forward:
                    Rover.throttle = 0
                    # Release the brake to allow turning
                    Rover.brake = 0
                    # Turn range is +/- 15 degrees, when stopped the next line will induce 4-wheel turning
                    Rover.steer = -15 # Could be more clever here about which way to turn
                # If we're stopped but see sufficient navigable terrain in front then go!
                if len(nav_angles) >= Rover.go_forward:
                    # Set throttle back to stored value
                    Rover.throttle = Rover.throttle_set
                    # Release the brake
                    Rover.brake = 0
                    # Set steer to mean angle
                    Rover.steer = np.clip(np.mean(nav_angles * 180/np.pi), -15, 15)
                    Rover.mode = 'forward'
        ''' elif Rover.mode == 'approach_rock':
            p = Rover.rocks[0]
            # print('{} rocks at {}'.format(len(Rover.rocks), Rover.rocks))
            vec = p - Rover.pos
            rover_angle = Rover.yaw if Rover.yaw < 180 else Rover.yaw - 360
            #vec_trans = np.matmul(vec, rot_mat(-Rover.yaw/180*np.pi))
            
            angle_delta = np.arctan2(vec[1], vec[0])*180/np.pi - rover_angle
            dist = np.linalg.norm(vec)

            vec_trans = np.matmul(np.array([10,0]), rot_mat(angle_delta))
            cv2.line(Rover.vision_image, (160,160), (160+int(10*vec_trans[0]),160+int(10*vec_trans[1])) , (255,255,255))
            # print ('vec: {}, angle_delta {}, dist {}'.format(vec, angle_delta, dist))
            
            Rover.steer = np.clip(angle_delta, -15, 15) * np.clip(dist, 0.5, 1)
            if np.abs(angle_delta) > np.clip(dist,2,10) and Rover.vel > 0.2:
                Rover.brake = Rover.brake_set
                Rover.throttle = 0
            elif np.abs(angle_delta) < 2 and Rover.vel < Rover.max_vel:
                Rover.brake = 0
                Rover.throttle = Rover.throttle_set
            else: 
                Rover.brake = 0
                Rover.throttle = 0
            if Rover.near_sample:
                Rover.brake = Rover.brake_set
                Rover.throttle = 0 '''
    # Just to make the rover do something 
    # even if no modifications have been made to the code    
    else:
        Rover.throttle = Rover.throttle_set
        Rover.steer = 0
        Rover.brake = 0


    if Rover.mode == 'forward':
        if Rover.vel > 0.2:
            Rover.stuck_counter = 0
        elif Rover.throttle > 0:         
            Rover.stuck_counter += 1
        if Rover.stuck_counter > 100:
            Rover.mode = 'stuck'
        if Rover.steer > 0:
            Rover.left_counter += 1
        else:
            Rover.left_counter = 0     
        if Rover.left_counter > 360:   
            Rover.mode = 'break_circle'
    
    if Rover.mode == 'break_circle':
        Rover.steer = -15
        Rover.throttle = 0
        Rover.left_counter -= 10
        if Rover.left_counter <= 0:
            Rover.mode = 'stop'
        
        
    if Rover.mode == 'stuck':
        print('stuck: count {}'.format(Rover.stuck_counter))
        if Rover.stuck_counter > 75:
            Rover.steer = -15
            Rover.throttle = 0
            Rover.stuck_counter -= 1
        else:
            Rover.steer = 0
            Rover.throttle = - Rover.throttle_set
            Rover.stuck_counter -= 1            
            if Rover.stuck_counter < 50 and Rover.vel >= 0:
                # stuck while moving back try rotating instead
                Rover.throttle = 0
                Rover.steer = -15
        if Rover.stuck_counter <= 0:
            Rover.mode = 'stop'
            Rover.brake = Rover.brake_set
            Rover.stuck_counter = 0
    
    return Rover

