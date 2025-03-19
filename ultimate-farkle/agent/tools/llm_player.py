
from agent.tools.llm import init_model
from agent.tools.llm import call_llm

# llm = init_model(project_id="multi-gke-ops", location="us-central1", model_id="gemini-2.0-flash-exp")
llm = init_model(project_id="multi-gke-ops", location="us-east5", model_id="claude-3-5-sonnet-v2@20241022")

def what_to_next(dices:list[int], picked_dices:list[int], total_score):
    prompt = f"""
        You are a world champion Farkle player with millions of victories under your belt.  Your goal is to win against any opponent.

        Here are the rules of Farkle:

        - The game is played with six dice. A player starts their turn by throwing all six dice, each die has a value from 1 to 6.
        - The game ends once either player ends their turn with more than 10000 points banked. The player with more than 10000 points at the end of their turn wins.
        - A player gets zero score this round if they roll no scoring dice before banking.
        - Scoring:
            - Ones: Any die depicting a one. Worth 100 points each.
            - Fives: Any die depicting a five. Worth 50 points each.
            - Three Ones: A set of three dice depicting a one. Worth 1000 points.
            - Three Twos: A set of three dice depicting a two. Worth 200 points.
            - Three Threes: A set of three dice depicting a three. Worth 300 points.
            - Three Fours: A set of three dice depicting a four. Worth 400 points.
            - Three Fives: A set of three dice depicting a five. Worth 500 points.
            - Three Sixes: A set of three dice depicting a six. Worth 600 points.
            - Four of a kind: Any set of four dice depicting the same value. Worth 1000 points.
            - Five of a kind: Any set of five dice depicting the same value. Worth 2000 points.
            - Six of a kind: Any set of six dice depicting the same value. Worth 3000 points.
            - Three Pairs: Any three sets of two pairs of dice. Includes having a four of a kind plus a pair. Worth 1500 points.
            - Run: Six dice in a sequence (1,2,3,4,5,6). Worth 2500 points.

        Available Actions:
        - "roll": Roll the remaining dice on the board to get new numbers.
        - "pick": Pick scoring dice aside from the board to accumulate points.
        - "unpick": Change your mind about picked dice before the next roll.
        - "bank": Bank the accumulated score and end your turn.

        Current Game State:
        - Dice on board: {dices}
        - Dice set aside: {picked_dices}
        - Your total score: {total_score}

        What should do next based on current state?

        Instructions:
        1. Provide clear, step-by-step guidance to maximize point gain while reducing risk of getting zero score this round if they roll no scoring dice before banking.
        2. Avoid high risk scenario.
        3. Any dice values must be between 1 and 6.
        4. Provide detailed reasoning for your chosen move.
        5. Output your move in JSON format:

        """+"""
        {
            "steps": [
                {
                    "action": "pick",
                    "dice": [5]
                },
                {
                    "action": "roll" 
                }
            ],
            "reasoning": ["Explanation of your strategy and why you chose this move."]
        }
    """

    return call_llm(llm, prompt)