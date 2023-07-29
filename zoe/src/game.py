import random
import math
import sys

import comms
from object_types import ObjectTypes


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
        for game_object in self.objects.values():
            if game_object["type"] == ObjectTypes.BOUNDARY.value:
                boundaries.append(game_object)

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
                object_x = game_object["position"][0]
                object_y = game_object["position"][1]
                self_x = self.objects[self.tank_id]["position"][0]
                self_y = self.objects[self.tank_id]["position"][1]
                distance = math.sqrt(abs(object_x - self_x) ** 2 + abs(object_y - self_y) ** 2)
                if min_distance > distance:
                    min_distance = distance
                    closest_powerup = game_object["position"]
        return closest_powerup

    def find_enemy_tank(self):
        for game_key, game_object in self.objects.items():
            if game_object["type"] == ObjectTypes.TANK.value and game_key != self.tank_id:
                return game_object["position"]
        return None

    def calculate_angle(self, mine, enemy):
            # angle_radians = math.degrees(math.atan(abs(mine[0] - enemy[0]) / abs(mine[1] - enemy[1])))
            # return -1 * (360 - angle_radians - 90)
            # mineX = mine[0]
            # mineY = mine[1]
            # enemyX = enemy[0]
            # enemyY = enemy[1]

            # dotProduct = mineX * enemyX + mineY * enemyY 
            # length = math.sqrt(mineX * mineX + mineY * mineY) * math.sqrt(enemyX * enemyX + enemyY * enemyY)
            # cosTheta = dotProduct / length
            # theta = math.acos(cosTheta)

            # return math.degrees(theta)
            # # return angleBetweenTwoPoints(0, 0, myVelocityX, myVelocityY)
            # angle = (math.atan2(enemy[1] - mine[1], enemy[0] - mine[0]) * 100 )/ math.pi
            angle = self.angleBetweenTwoPoints(mine[0], mine[1], enemy[0], enemy[1])
            return angle - 90
    
    def angleBetweenTwoPoints(self, x1, y1, x2, y2): 
        rateOfChange = (y2 - y1)/(x2 - x1)
        theta = math.atan(rateOfChange)
        return math.degrees(theta)
    
    # def angleRadBetweenTwoPoints(x1, y1, x2, y2):  
    #     dotProduct = x1 * x2 + y1 * y2 
    #     length = math.sqrt(x1 * x1 + y1 * y1) * math.sqrt(y1 * y1 + y2 * y2)
    #     cosTheta = dotProduct / length
    #     return math.acos(cosTheta)
    
    def respond_to_turn(self):
        """
        This is where you should write your bot code to process the data and respond to the game.
        """

        # Locate (and move towards) Power Up
        my_tank_position = self.objects[self.tank_id]["position"]
        enemey_tank_position =  self.objects[self.enemy_tank_id]["position"]

        print("mine: " + str(my_tank_position) + "enemyL " + str(enemey_tank_position) , file=sys.stderr)

        dest_x = self.width // 2
        dest_y = self.height // 2
        destination = [dest_x, dest_y]

        powerup = self.find_powerup()
        if powerup is not None:
            dest_x = powerup[0]
            dest_y = powerup[1]
            destination = powerup

        # Write your code here... For demonstration, this bot just shoots randomly every turn.

        x1 = my_tank_position[0]
        x2 = my_tank_position[1]
        y1 = enemey_tank_position[0]
        y2 = enemey_tank_position[1]
        angle = math.atan2(y2 - y1, x2 - x1) * 100 / math.pi

        comms.post_message({
            # "shoot": random.uniform(0, random.randint(1, 360)),
            # "shoot": angle
            "shoot": self.calculate_angle(my_tank_position, enemey_tank_position),
            # "shoot": 90
            # "path": [dest_x, dest_y],
        })


