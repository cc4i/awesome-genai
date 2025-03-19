
import numpy as np
import uuid
import re
import json
import os
from collections import Counter
from agent.tools.llm_player import what_to_next

class Dice:
    def __init__(self, num:int, onboard:bool) -> None:
        self.num  = num
        self.onboard = onboard
    
    @classmethod
    def roll_dices(self, num_dices:int) -> list['Dice']:
        dices = []
        vals =  np.random.randint(low=1, high=7, size=(num_dices,)).tolist()
        for v in vals:
            dices.append(Dice(v, True))
        return dices
   

class Player:
    def __init__(self, name:str, status:str="ready", score:int=0,) -> None:
        self.id = uuid.uuid4()
        self.name = name
        self.score = 0
        # who's turn? standby/play
        self.status = status


class FGame:
    def __init__(self, player1:Player, player2:Player, init_num_dices:int = 6) -> None:
        print(f"fn:__init__ -> .")
        self.init_num_dices = init_num_dices
        self.onboarded_dices = []
        self.picked_dices = []
        self.all_picked_dices = []
        self.player1 = player1
        self.player2 = player2
        self.round = 0
        self.player = None
        self.rolling_allowed = True
        self.t_score=0
        self.winner = None
        
        
    # Restart a new game
    def restart_game(self):
        print(f"fn:restart_game -> .")
        self.onboarded_dices = np.random.randint(low=1, high=7, size=(self.init_num_dices,)).tolist()
        self.picked_dices = []
        self.all_picked_dices = []
        self.player1.score = 0
        self.player2.score = 0
        self.round = 1
        self.player = self.player1
        self.rolling_allowed = True
        self.t_score=0
        self.winner = None
    

    # check winner
    def check_winner(self):
        print(f"fn:check_winner -> .")
        if self.player1.score >= 10000:
            self.winner = self.player1
            return True
        elif self.player2.score >= 10000:
            self.winner = self.player2
            return True
        else:
            return False
    



    # Switch player
    def switch_player(self):
        print(f"fn:switch_player -> .")
        if self.player.id == player1.id:
            self.player = self.player2
        else:
            self.player = self.player1
        
        self.onboarded_dices = np.random.randint(low=1, high=7, size=(self.init_num_dices,)).tolist()
        self.picked_dices = []
        self.all_picked_dices = []
        self.t_score=0
        self.round = self.round + 1


    def throw(self) -> list[int]:
        print(f"fn:throw -> .")
        for x in self.picked_dices:
            self.all_picked_dices.append(x)
        self.picked_dices=[]
        num_dices = self.init_num_dices - len(self.all_picked_dices)
        self.onboarded_dices = np.random.randint(low=1, high=6, size=(num_dices,)).tolist()
        self.rolling_allowed = False
        return self.onboarded_dices
    


    def has_x_of_a_kind(self, x:int, numbers:list[int]):
        counts = Counter(numbers)
        for num in range(1, 7):  # Check numbers from 1 to 6
            if counts[num] >= x:
                return True
        return False

    def has_three_pairs(self, numbers:list[int]):
        counts = Counter(numbers)
        pair_count = 0
        for num in range(1, 7):  # Check numbers from 1 to 6
            if counts[num] >= 2:  # Check for a pair
                pair_count += 1
        return pair_count >= 3 

    def validate_dices(self, dices:list[int]) -> int:
        print(f"fn:validate_dices -> {dices}")
        score = 0
        if dices == [1, 2, 3, 4, 5, 6]:
            score = score + 2500
        elif self.has_three_pairs(dices):
            score = score + 1500
        else:
            if self.has_x_of_a_kind(6, dices):
                score = score + 3000
            else:
                if self.has_x_of_a_kind(5, dices):
                    score = score + 1000
                else:
                    if self.has_x_of_a_kind(4, dices):
                        score = score + 1000
                    else:
                        if dices.count(1)>0:
                            if dices.count(1)==3:
                                score = score + 1000
                            else:
                                score = score + dices.count(1)*100
                        if dices.count(5)>0:
                            if dices.count(5)==3:
                                score = score + 500
                            else:
                                score = score + dices.count(5)*50
                        if dices.count(2)==3:
                            score = score + 200
                        if dices.count(3)==3:
                            score = score + 300
                        if dices.count(4)==3:
                            score = score + 400
        return score

    def validate(self) -> int:
        return self.validate_dices(self.picked_dices)


    def play_mutiple_steps(self, steps:list[dict]):
        print(f"fn:play_mutiple_steps -> {steps}")
        for step in steps:
            if 'dice' in step:
                for d in step['dice']:
                    self.play(step['action'], d)
            else:
                self.play(step['action'], 0)
        return self.onboarded_dices, self.picked_dices+self.all_picked_dices, self.t_score + self.validate(), self.player, self.winner


    def play(self, action:str, val:int):
        """
        action: "roll", "pick", "unpick", "bank" 
        """
        # round = self.round
        # player = self.player
        # num_dices = len(self.onboarded_dices) - len(self.picked_dices)
        print(f"fn:play -> action: {action}, val: {val}")
        
        if self.check_winner()==False:
            if action == "roll":
                if (self.rolling_allowed and len(self.onboarded_dices)>0 and self.validate_dices(self.onboarded_dices)!=0) or (self.validate_dices(self.onboarded_dices)==0 and len(self.onboarded_dices)==self.init_num_dices):
                    self.t_score = self.t_score+ self.validate()
                    self.throw()
                elif self.validate_dices(self.onboarded_dices)==0:
                    self.switch_player()
                else:
                    print(f"{self.player.name} can not roll again before pick dices!!!")
            elif action == "pick":
                print(f"Board: {self.onboarded_dices}")
                print(f"Picked {val}")
                if len(self.onboarded_dices)>0:
                    self.onboarded_dices.remove(val)
                self.picked_dices.append(val)
                if self.validate() > 0:
                    self.rolling_allowed = True
            elif action == "unpick":
                print(f"Board: {self.onboarded_dices}")
                print(f"Picked {val}")
                self.onboarded_dices.append(val)
                if len(self.picked_dices)>0:
                    self.picked_dices.remove(val)
                if self.validate() > 0:
                    self.rolling_allowed = True
            elif action == "bank":
                # if len(self.onboarded_dices)==0:
                self.t_score = self.t_score+ self.validate()
                self.player.score = self.player.score + self.t_score
                self.switch_player()
            elif action == "score":
                print(f"player 1: {self.player1.score} vs player 2: {self.player2.score}")
            else:
                self.rules()
        else:
            print(f"Game is over, winner is {self.winner.name}")
        print(f"{self.player.name}")
        print(f"Board: {self.onboarded_dices}")
        print(f"Picked: {self.picked_dices} + {self.all_picked_dices}")
        print(f"Picked dices are worth : {self.t_score + self.validate()}")
        print(f"player {self.player1.name}: {self.player1.score} vs player {self.player2.name}: {self.player2.score}")

        return self.onboarded_dices, self.picked_dices+self.all_picked_dices, self.t_score + self.validate(), self.player, self.winner

    def rules(self):
        print("""
        - Ones: Any die depicting a one. Worth 100 points each.
        - Fives: Any die depicting a five. Worth 50 points each.
        - Three Ones: A set of three dice depicting a one. worth 1000 points
        - Three Twos: A set of three dice depicting a two. worth 200 points
        - Three Threes: A set of three dice depicting a three. worth 300 points
        - Three Fours: A set of three dice depicting a four. worth 400 points
        - Three Fives: A set of three dice depicting a five. worth 500 points
        - Three Sixes: A set of three dice depicting a six. worth 600 points
        - Four of a kind: Any set of four dice depicting the same value. Worth 1000 points
        - Five of a kind: Any set of five dice depicting the same value. Worth 2000 points
        - Six of a kind: Any set of six dice depicting the same value. Worth 3000 points
        - Three Pairs: Any three sets of two pairs of dice. Includes having a four of a kind plus a pair. Worth 1500 points
        - Run: Six dice in a sequence (1,2,3,4,5,6). Worth 2500 points
        """)

    # All history actions for each round
    def history(self):
        pass 




# Process input string
def convert_string(what: str) -> list[int]:
    return [int(x.strip()) for x in what.split(',')]


# main
if __name__ == "__main__":
    player1 = Player("robo")
    player2 = Player("cc")
    game = FGame(player1, player2)
    game.restart_game()
    print(f"Farkle is begining with player 1: {player1.name} and player 2: {player2.name}")

    while True:
        # Begin
        # round = game.round
        print(f"It's {game.player.name}'s turn.")
        input_str = input()
        if input_str=="quit" or input_str=="exit" or input_str=="q": 
            print("Quit the game!!!")
            os._exit(0)
        else:
            pattern = r"^[\w]+:\d+$"
            ss = input_str.split(":")
            action=ss[0]
            if re.match(pattern, input_str):
                val = int(ss[1])
                d, pd, cs, player, winner = game.play(action, val)
            else:
                d, pd, cs, player, winner = game.play(action, 0)
            
            if winner is not None:
                os._exit(0)
            # print(llm_guidance)
            if game.player.name=="robo":
                llm_guidance = json.loads(what_to_next(d, pd, cs, player.score))
                game.play_mutiple_steps(llm_guidance['steps'])


            # cmd=[]
            # for act in llm_guidance['steps']:
            #     if 'dices' in act:
            #         for d in act['dices']:
            #             cmd.append(f"{act['action']}:{d}")
            #     else:
            #         cmd.append(f"{act['action']}")
            # print(cmd)
    
