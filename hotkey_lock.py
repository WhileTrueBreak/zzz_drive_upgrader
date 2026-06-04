from pynput import keyboard
import pyautogui

from game_controller import toggle_lock, toggle_trash

STOP_FLAG = False

def on_press(key):
    global STOP_FLAG
    try:
        if hasattr(key, 'char') and key.char:
            char = key.char.lower()
            if char == 'p':
                print("\n[P] pressed — stopping script.")
                STOP_FLAG = True
                return False  # Stop listener
            elif char == 'z':
                prev_pos = pyautogui.position()
                toggle_trash(click_delay=0)
                pyautogui.moveTo(prev_pos)
            elif char == 'c':
                prev_pos = pyautogui.position()
                toggle_lock(click_delay=0)
                pyautogui.moveTo(prev_pos)
    except Exception:
        pass

def start_keyboard_listener():
    listener = keyboard.Listener(on_press=on_press)
    listener.daemon = True  # Listener closes with main program
    listener.start()
    print("Keyboard listener started.")
    print("Press 'z', 'c' for actions, 'p' to stop.")
    return listener

if __name__ == "__main__":
    listener = start_keyboard_listener()
    
    while not STOP_FLAG:
        pass

    print("Script stopped.")
