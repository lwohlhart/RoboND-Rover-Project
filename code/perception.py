import numpy as np
import cv2
import scipy.ndimage as ndimage

# Identify pixels above the threshold
# Threshold of RGB > 160 does a nice job of identifying ground pixels only
def color_thresh(img, rgb_thresh=(160, 160, 160), upper_rgb_thresh=None):
    # Create an array of zeros same xy size as img, but single channel
    color_select = np.zeros_like(img[:,:,0])
    # Require that each pixel be above all three threshold values in RGB
    # above_thresh will now contain a boolean array with "True"
    # where threshold was met
    above_thresh = (img[:,:,0] >= rgb_thresh[0]) \
                & (img[:,:,1] >= rgb_thresh[1]) \
                & (img[:,:,2] >= rgb_thresh[2])
    if upper_rgb_thresh:
        above_thresh = above_thresh \
                & (img[:,:,0] <= upper_rgb_thresh[0]) \
                & (img[:,:,1] <= upper_rgb_thresh[1]) \
                & (img[:,:,2] <= upper_rgb_thresh[2])
    # Index the array of zeros with the boolean array and set to 1
    color_select[above_thresh] = 1
    # Return the binary image
    return color_select

# Define a function to convert from image coords to rover coords
def rover_coords(binary_img):
    # Identify nonzero pixels
    ypos, xpos = binary_img.nonzero()
    # Calculate pixel positions with reference to the rover position being at the 
    # center bottom of the image.  
    x_pixel = -(ypos - binary_img.shape[0]).astype(np.float)
    y_pixel = -(xpos - binary_img.shape[1]/2 ).astype(np.float)
    return x_pixel, y_pixel


# Define a function to convert to radial coords in rover space
def to_polar_coords(x_pixel, y_pixel):
    # Convert (x_pixel, y_pixel) to (distance, angle) 
    # in polar coordinates in rover space
    # Calculate distance to each pixel
    dist = np.sqrt(x_pixel**2 + y_pixel**2)
    # Calculate angle away from vertical for each pixel
    angles = np.arctan2(y_pixel, x_pixel)
    return dist, angles

# Define a function to map rover space pixels to world space
def rotate_pix(xpix, ypix, yaw):
    # Convert yaw to radians
    yaw_rad = yaw * np.pi / 180
    xpix_rotated = (xpix * np.cos(yaw_rad)) - (ypix * np.sin(yaw_rad))

    ypix_rotated = (xpix * np.sin(yaw_rad)) + (ypix * np.cos(yaw_rad))
    # Return the result  
    return xpix_rotated, ypix_rotated

def translate_pix(xpix_rot, ypix_rot, xpos, ypos, scale): 
    # Apply a scaling and a translation
    xpix_translated = (xpix_rot / scale) + xpos
    ypix_translated = (ypix_rot / scale) + ypos
    # Return the result  
    return xpix_translated, ypix_translated


# Define a function to apply rotation and translation (and clipping)
# Once you define the two functions above this function should work
def pix_to_world(xpix, ypix, xpos, ypos, yaw, world_size, scale):
    # Apply rotation
    xpix_rot, ypix_rot = rotate_pix(xpix, ypix, yaw)
    # Apply translation
    xpix_tran, ypix_tran = translate_pix(xpix_rot, ypix_rot, xpos, ypos, scale)
    # Perform rotation, translation and clipping all at once
    x_pix_world = np.clip(np.int_(xpix_tran), 0, world_size - 1)
    y_pix_world = np.clip(np.int_(ypix_tran), 0, world_size - 1)
    # Return the result
    return x_pix_world, y_pix_world

# Define a function to perform a perspective transform
def perspect_transform(img, src, dst):
           
    M = cv2.getPerspectiveTransform(src, dst)
    warped = cv2.warpPerspective(img, M, (img.shape[1], img.shape[0]))# keep same size as input image
    
    return warped


fade = np.rot90((np.tile(np.linspace(1,0,160),(320,1))))**2
# Apply the above functions in succession and update the Rover state accordingly
def perception_step(Rover):
    # Perform perception steps to update Rover()
    # TODO: 
    # NOTE: camera image is coming to you in Rover.im
    # 1) Define source and destination points for perspective transform
    dst_size = 5 
    bottom_offset = 6
    source = np.float32([[14, 140], [301 ,140],[200, 96], [118, 96]])

    # source pitch correction 
    pitch_correction = Rover.pitch if Rover.pitch < 180 else Rover.pitch - 360
    source = (source - np.array([0.0, 2 * pitch_correction])).astype(np.float32)
    #source = np.float32([[1, 150], [319 ,150],[204, 100], [116, 100]])
    destination = np.float32([[-dst_size, -bottom_offset],
                              [dst_size, -bottom_offset],
                              [dst_size, -2*dst_size - bottom_offset], 
                              [-dst_size, -2*dst_size - bottom_offset],
                             ]) + np.float32([Rover.img.shape[0], Rover.img.shape[1]/2])
    world_scale = 20
    world_size = 200
    # 2) Apply perspective transform
    warped = perspect_transform(Rover.img, source, destination)
    
    # 3) Apply color threshold to identify navigable terrain/obstacles/rock samples
    navigable = ndimage.binary_closing(color_thresh(warped)).astype(int)
    obstacle = (1 - navigable) & perspect_transform(np.ones_like(warped[:,:,0]), source, destination)
    rock = color_thresh(warped, (100, 100, 0), (255, 255, 50))

    # fade_warped = perspect_transform(fade, source, destination)
    # navigable = navigable * fade
    # obstacle = obstacle * fade
    #rock = ndimage.binary_opening(rock).astype(int)

    # 4) Update Rover.vision_image (this will be displayed on left side of screen)
        # Example: Rover.vision_image[:,:,0] = obstacle color-thresholded binary image
        #          Rover.vision_image[:,:,1] = rock_sample color-thresholded binary image
        #          Rover.vision_image[:,:,2] = navigable terrain color-thresholded binary image
        
    Rover.vision_image[:,:,0] = 255 * obstacle
    Rover.vision_image[:,:,1] = 255 * rock
    Rover.vision_image[:,:,2] = 255 * navigable


    # 5) Convert map image pixel values to rover-centric coords
    # 6) Convert rover-centric pixel values to world coordinates
    navigable_x, navigable_y = rover_coords(navigable)
    obstacle_x, obstacle_y = rover_coords(obstacle)
    rock_x, rock_y = rover_coords(rock)

    obstacle_update =  np.clip(1 - to_polar_coords(obstacle_x, obstacle_y)[0]/100, 0, 1)
    navigable_update = np.clip(1 - to_polar_coords(navigable_x, navigable_y)[0]/227, 0, 1)
    
    # Rover.vision_image[:,:,0] = 0
    # Rover.vision_image[:,:,2] = 0
    # Rover.vision_image[obstacle_y, obstacle_x, 0] = obstacle_update
    # Rover.vision_image[navigable_y, navigable_x, 2] = navigable_update

    navigable_x_world, navigable_y_world = pix_to_world(navigable_x, navigable_y, Rover.pos[0], Rover.pos[1], Rover.yaw, world_size, world_scale)
    obstacle_x_world, obstacle_y_world = pix_to_world(obstacle_x, obstacle_y, Rover.pos[0], Rover.pos[1], Rover.yaw, world_size, world_scale)    
    rock_x_world, rock_y_world = pix_to_world(rock_x, rock_y, Rover.pos[0], Rover.pos[1], Rover.yaw, world_size, world_scale)

    # 7) Update Rover worldmap (to be displayed on right side of screen)
        # Example: Rover.worldmap[obstacle_y_world, obstacle_x_world, 0] += 1
        #          Rover.worldmap[rock_y_world, rock_x_world, 1] += 1
        #          Rover.worldmap[navigable_y_world, navigable_x_world, 2] += 1
    
    if (Rover.roll < 5 or Rover.roll > 355) and not Rover.picking_up: # and (Rover.pitch < 2 or Rover.pitch > 358) 
        # Rover.occupancy[obstacle_y_world, obstacle_x_world] -= 1 #obstacle[obstacle_x.astype(np.int), obstacle_y.astype(np.int)]
        # Rover.occupancy[navigable_y_world, navigable_x_world] += 10 #navigable[navigable_x.astype(np.int), navigable_y.astype(np.int)]        
        # Rover.occupancy[obstacle_y_world, obstacle_x_world] = np.clip(Rover.occupancy[obstacle_y_world, obstacle_x_world] - obstacle_update, -10, 10)
        # Rover.occupancy[navigable_y_world, navigable_x_world] = np.clip(Rover.occupancy[navigable_y_world, navigable_x_world] + 10*navigable_update, -10, 10)
        Rover.occupancy[obstacle_y_world, obstacle_x_world] -= obstacle_update
        Rover.occupancy[navigable_y_world, navigable_x_world] += 10*navigable_update
        Rover.occupancy = np.clip(Rover.occupancy, -10, 10)
        Rover.worldmap[:, :, 0] = (Rover.occupancy < 0) * 255
        Rover.worldmap[:, :, 2] = (Rover.occupancy > 0) * 255
        # Rover.worldmap[navigable_y_world, navigable_x_world, 2] = 255
        # Rover.worldmap[navigable_y_world, navigable_x_world, 0] = 0

        if rock_x_world.any() and rock_y_world.any():        
            rock_pos = np.float32([np.mean(rock_x_world), np.mean(rock_y_world)])
            Rover.spot_rock(rock_pos)
            Rover.worldmap[int(rock_pos[1]), int(rock_pos[0]), 1] = 255            
    else:
        print('not mapping roll = {}, pitch = {}'.format(Rover.roll, Rover.pitch))
    


    # 8) Convert rover-centric pixel positions to polar coordinates
    rover_centric_pixel_distances, rover_centric_angles = to_polar_coords(navigable_x, navigable_y)    
    #if rock_x.any() and rock_y.any():
    #    rover_centric_pixel_distances, rover_centric_angles = to_polar_coords(rock_x, rock_y)    
    # Update Rover pixel distances and angles
        # Rover.nav_dists = rover_centric_pixel_distances
        # Rover.nav_angles = rover_centric_angles
    Rover.nav_dists = rover_centric_pixel_distances
    Rover.nav_angles = rover_centric_angles
             
    return Rover