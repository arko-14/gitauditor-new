# vulnerable.py
import os

def insecure():
    os.system(input("Enter a command: "))  # Command injection vulnerability
