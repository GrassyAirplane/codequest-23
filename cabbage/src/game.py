import random

import comms
from object_types import ObjectTypes

import sys
import math


class Game:
    """
    Stores all information about the game and manages the communication cycle.
    Available attributes after initialization will be:
    - tank_id: your tank id
    - objects: a dict of all objects on the map like {object-id: object-dict}.
    - width: the width of the map as a floating point number.
    - height: the height of the map as a floating point number.
    - current_turn_message: a copy of the message received this turn. It will be updated everytime `read_next_turn_data`
        is called and will be available to be used in `respond_to_turn` if needed.
    """
    def __init__(self):
        self.last_path_requested = None
        
        tank_id_message: dict = comms.read_message()
        self.tank_id = tank_id_message["message"]["your-tank-id"]
        
        self.enemy_tank_id = tank_id_message["message"]["enemy-tank-id"]

        self.current_turn_message = None

        # We will store all game objects here
        self.objects = {}

        next_init_message = comms.read_message()
        while next_init_message != comms.END_INIT_SIGNAL:
            # At this stage, there won't be any "events" in the message. So we only care about the object_info.
            object_info: dict = next_init_message["message"]["updated_objects"]

            # Store them in the objects dict
            self.objects.update(object_info)

            # Read the next message
            next_init_message = comms.read_message()

        # We are outside the loop, which means we must've received the END_INIT signal

        # Let's figure out the map size based on the given boundaries

        # Read all the objects and find the boundary objects
        boundaries = []

        #walls
        self.walls = []
        for game_object in self.objects.values():
            if game_object["type"] == ObjectTypes.BOUNDARY.value:
                boundaries.append(game_object)
            # If the game obj is wall
            if game_object["type"] == ObjectTypes.WALL.value:
                self.walls.append(game_object["position"])    

        # The biggest X and the biggest Y among all Xs and Ys of boundaries must be the top right corner of the map.

        # Let's find them. This might seem complicated, but you will learn about its details in the tech workshop.
        biggest_x, biggest_y = [
            max([max(map(lambda single_position: single_position[i], boundary["position"])) for boundary in boundaries])
            for i in range(2)
        ]

        self.width = biggest_x
        self.height = biggest_y

    def read_next_turn_data(self):
        """
        It's our turn! Read what the game has sent us and update the game info.
        :returns True if the game continues, False if the end game signal is received and the bot should be terminated
        """
        # Read and save the message
        self.current_turn_message = comms.read_message()

        if self.current_turn_message == comms.END_SIGNAL:
            return False

        # Delete the objects that have been deleted
        # NOTE: You might want to do some additional logic here. For example check if a powerup you were moving towards
        # is already deleted, etc.
        for deleted_object_id in self.current_turn_message["message"]["deleted_objects"]:
            try:
                del self.objects[deleted_object_id]
            except KeyError:
                pass

        # Update your records of the new and updated objects in the game
        # NOTE: you might want to do some additional logic here. For example check if a new bullet has been shot or a
        # new powerup is now spawned, etc.
        self.objects.update(self.current_turn_message["message"]["updated_objects"])

        return True
    
    def find_powerup(self):
        """
        Find existing powerups and return the closest one.
        """
        closest_powerup = None
        min_distance = float('inf')
        for game_object in self.objects.values():
            if game_object["type"] == ObjectTypes.POWERUP.value:
                # If in boudnary 
                if self.in_boundary(game_object["position"][0],  game_object["position"][1]):
                    object_x = game_object["position"][0]
                    object_y = game_object["position"][1]
                    self_x = self.objects[self.tank_id]["position"][0]
                    self_y = self.objects[self.tank_id]["position"][1]
                    distance = math.sqrt(abs(object_x - self_x) ** 2 + abs(object_y - self_y) ** 2)
                    if min_distance > distance:
                        min_distance = distance
                        closest_powerup = game_object["position"]
        return closest_powerup

    def find_distance(point_one, point_two):
        return math.sqrt(abs(point_one[0] - point_two[0]) ** 2 + abs(point_one[1] - point_two[1]) ** 2)
    
    def find_angle(self, mine, enemy):
        x1 = mine[0]
        y1 = mine[1]
        x2 = enemy[0]
        y2 = enemy[1]
        
        return math.atan2(y2 - y1, x2 - x1) * 180 / math.pi

    def check_clear(self, mine):
        # Only shoot if enemy is in view
        pass    

    def bouncing_shot(self):
        pass

    def are_points_on_line(self, x1, y1, x2, y2, epsilon=1e-6):
        # Step 1: Calculate the slope (m)
        if x2 - x1 != 0:
            m = (y2 - y1) / (x2 - x1)
        else:
            m = float('inf')  # Handle vertical lines (infinite slope)

        # Step 2: Calculate the y-intercept (b)
        b = y1 - m * x1

        # Step 3: Write the equation of the line
        def line_equation(x):
            return m * x + b

        # Step 4: Check if any points lie on the line
        for x, y in self.walls:
            if abs(y - line_equation(x)) < epsilon:
                return True

        return False

        # CREATED FUNCTIONS
    def in_boundary(self, x, y):
        for game_object in self.objects.values():
            if game_object["type"] == ObjectTypes.CLOSING_BOUNDARY.value:
                bounds = game_object

                x_bound_lower = bounds["position"][0][0]
                x_bound_upper = bounds["position"][2][0]
                y_bound_lower = bounds["position"][1][1]
                y_bound_upper = bounds["position"][3][1]

                       # Check for need to dodge   
                print("mine: " + str(x_bound_lower) + " upper" + str(x_bound_upper) + str(y_bound_lower) + " upper" + str(y_bound_upper), file=sys.stderr)

                if (x >= x_bound_lower and x <= x_bound_upper and y >= y_bound_lower and y <= y_bound_upper):
                    return True

        return False


    def respond_to_turn(self):
        """
        This is where you should write your bot code to process the data and respond to the game.
        """

        # Write your code here... For demonstration, this bot just shoots randomly every turn.

        # Enemy
        enemy_tank = self.objects[self.enemy_tank_id]
        enemy_tank_position = enemy_tank["position"]
        # Mine
        my_tank = self.objects[self.tank_id]
        my_tank_position = my_tank["position"]
        
        # Cleared Response
        my_response = {}
        
        # Moves towards Enemy
        # if self.last_path_requested is None or self.last_path_requested != enemy_tank_position:
        #     my_response = {"path": enemy_tank_position}
        #     self.last_path_requested = enemy_tank_position
        
        # Checking for powerup
        dest_x = self.width // 2
        dest_y = self.height // 2
        powerup = self.find_powerup()

        # Movement 
        if powerup is not None:
            dest_x = powerup[0]
            dest_y = powerup[1]
             # Updates Powerup Seeking
            my_response.update(
                {
                    "path": [dest_x, dest_y]
                }
            )

        else: 
            dest_x = enemy_tank_position[0]
            dest_y = enemy_tank_position[1]
            # Updates Seeking Enemy
            my_response.update(
                {
                    "path": [dest_x, dest_y]
                }
            )

        self.in_boundary(1,2)

        # Distance
        distance = abs(my_tank_position[0] - enemy_tank_position[0]) + abs(my_tank_position[1]) - abs(enemy_tank_position[1])

        if distance < 500 and not self.are_points_on_line(my_tank_position[0], my_tank_position[1], enemy_tank_position[0], enemy_tank_position[1]):
            # Updates the Response
            my_response.update({
                "shoot": self.find_angle(my_tank_position, enemy_tank_position),
            })

        # Final Post
        comms.post_message(my_response)



# import math
# import random
# import sys

# import comms
# from object_types import ObjectTypes


# class Game:
#     """
#     Stores all information about the game and manages the communication cycle.
#     Available attributes after initialization will be:
#     - tank_id: your tank id
#     - objects: a dict of all objects on the map like {object-id: object-dict}.
#     - width: the width of the map as a floating point number.
#     - height: the height of the map as a floating point number.
#     - current_turn_message: a copy of the message received this turn. It will be updated everytime `read_next_turn_data`
#         is called and will be available to be used in `respond_to_turn` if needed.
#     """
#     def __init__(self):
#         tank_id_message: dict = comms.read_message()

#         # Tanks ID
#         self.tank_id = tank_id_message["message"]["your-tank-id"]
#         self.enemy_tank_id = tank_id_message["message"]["enemy-tank-id"]

#         self.current_turn_message = None

#         # We will store all game objects here
#         self.objects = {}

#         next_init_message = comms.read_message()
#         while next_init_message != comms.END_INIT_SIGNAL:
#             # At this stage, there won't be any "events" in the message. So we only care about the object_info.
#             object_info: dict = next_init_message["message"]["updated_objects"]

#             # Store them in the objects dict
#             self.objects.update(object_info)

#             # Read the next message
#             next_init_message = comms.read_message()

#         # We are outside the loop, which means we must've received the END_INIT signal

#         # Let's figure out the map size based on the given boundaries

#         # Read all the objects and find the boundary objects
#         boundaries = []
#         for game_object in self.objects.values():
#             if game_object["type"] == ObjectTypes.BOUNDARY.value:
#                 boundaries.append(game_object)

#         # The biggest X and the biggest Y among all Xs and Ys of boundaries must be the top right corner of the map.

#         # Let's find them. This might seem complicated, but you will learn about its details in the tech workshop.
#         biggest_x, biggest_y = [
#             max([max(map(lambda single_position: single_position[i], boundary["position"])) for boundary in boundaries])
#             for i in range(2)
#         ]

#         self.width = biggest_x
#         self.height = biggest_y

#     def read_next_turn_data(self):
#         """
#         It's our turn! Read what the game has sent us and update the game info.
#         :returns True if the game continues, False if the end game signal is received and the bot should be terminated
#         """
#         # Read and save the message
#         self.current_turn_message = comms.read_message()

#         if self.current_turn_message == comms.END_SIGNAL:
#             return False

#         # Delete the objects that have been deleted
#         # NOTE: You might want to do some additional logic here. For example check if a powerup you were moving towards
#         # is already deleted, etc.
#         for deleted_object_id in self.current_turn_message["message"]["deleted_objects"]:
#             try:
#                 del self.objects[deleted_object_id]
#             except KeyError:
#                 pass

#         # Update your records of the new and updated objects in the game
#         # NOTE: you might want to do some additional logic here. For example check if a new bullet has been shot or a
#         # new powerup is now spawned, etc.
#         self.objects.update(self.current_turn_message["message"]["updated_objects"])

#         return True

#     def calculate_angle(self, mine, enemy):
#         x1 = mine[0]
#         x2 = mine[1]
#         y1 = enemy[0]
#         y2 = enemy[1]
#         return math.atan2(y2 - y1, x2 - x1) * 100 / math.pi
    
#     def calculate_distance(self, mine, enemy): 
#         return abs(mine[0] - enemy[0]) + abs(mine[1] - abs(enemy[1]) )


#     def respond_to_turn(self):
#         # Find your tank's position
#         my_tank_position = self.objects[self.tank_id]["position"]
#         enemey_tank_position =  self.objects[self.enemy_tank_id]["position"]

#         # Print
#         print("mine" + str(my_tank_position) + "enemy" + str(enemey_tank_position), file=sys.stderr)

#         # Move towards the middle
#         comms.post_message({
#             "shoot": self.calculate_angle(my_tank_position, enemey_tank_position)
#         })

#         # my_response = {}
#         # print("mine: " + self.objects[self.tank_id], file=sys.stderr)
#         # comms.post_message(my_response)
        



