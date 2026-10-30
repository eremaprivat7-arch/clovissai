# python, games.py
import random

def start_guess_game():
    return random.randint(1, 100)

def check_guess(target, guess):
    if guess < target:
        return "Больше!"
    elif guess > target:
        return "Меньше!"
    else:
        return "Угадал! 🎉"