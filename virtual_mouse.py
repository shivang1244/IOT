import socket
import pyautogui
import threading
import time
from collections import deque


class VirtualMouse:
    def __init__(self, host='0.0.0.0', port=8888):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((host, port))

        # Mouse control parameters
        self.sensitivity = 2.0
        self.smoothing_factor = 0.7
        self.movement_history = deque(maxlen=5)

        # Click state tracking
        self.left_click_active = False
        self.right_click_active = False

        print(f"Virtual Mouse Server listening on {host}:{port}")

    def smooth_movement(self, x, y):
        """Apply smoothing to mouse movement"""
        self.movement_history.append((x, y))

        # Calculate weighted average
        total_x, total_y = 0, 0
        weight_sum = 0

        for i, (hist_x, hist_y) in enumerate(self.movement_history):
            weight = (i + 1) / len(self.movement_history)
            total_x += hist_x * weight
            total_y += hist_y * weight
            weight_sum += weight

        if weight_sum > 0:
            smooth_x = total_x / weight_sum
            smooth_y = total_y / weight_sum
            return smooth_x, smooth_y

        return x, y

    def process_data(self, data):
        """Process incoming sensor data"""
        try:
            parts = data.split(',')
            if len(parts) == 4:
                x = int(parts[0]) * self.sensitivity
                y = int(parts[1]) * self.sensitivity
                left_click = parts[2] == '1'
                right_click = parts[3] == '1'

                return x, y, left_click, right_click
        except ValueError:
            pass

        return 0, 0, False, False

    def handle_clicks(self, left_click, right_click):
        """Handle mouse click events"""
        # Left click handling
        if left_click and not self.left_click_active:
            pyautogui.mouseDown(button='left')
            self.left_click_active = True
        elif not left_click and self.left_click_active:
            pyautogui.mouseUp(button='left')
            self.left_click_active = False

        # Right click handling
        if right_click and not self.right_click_active:
            pyautogui.mouseDown(button='right')
            self.right_click_active = True
        elif not right_click and self.right_click_active:
            pyautogui.mouseUp(button='right')
            self.right_click_active = False

    def start(self):
        """Start the virtual mouse server"""
        try:
            while True:
                # Receive data from ESP8266
                data, addr = self.sock.recvfrom(1024)
                data_str = data.decode('utf-8').strip()

                # Process the sensor data
                x, y, left_click, right_click = self.process_data(data_str)

                # Apply smoothing to movement
                smooth_x, smooth_y = self.smooth_movement(x, y)

                # Move mouse
                if smooth_x != 0 or smooth_y != 0:
                    pyautogui.moveRel(smooth_x, smooth_y)

                # Handle clicks
                self.handle_clicks(left_click, right_click)

                # Print status (optional)
                print(f"X: {smooth_x:6.2f}, Y: {smooth_y:6.2f}, "
                      f"Left: {'↓' if left_click else '↑'}, "
                      f"Right: {'↓' if right_click else '↑'}")

        except KeyboardInterrupt:
            print("\nStopping virtual mouse...")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            self.sock.close()


def main():
    # Disable pyautogui fail-safe for better performance
    pyautogui.FAILSAFE = False
    pyautogui.PAUSE = 0

    # Create and start virtual mouse
    mouse = VirtualMouse()
    mouse.start()


if __name__ == "__main__":
    main()