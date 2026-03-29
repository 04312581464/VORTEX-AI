import random
import time
import threading
from livekit.agents import function_tool

# Global storage for running tasks
running_tasks = {}

@function_tool()
def generate_random_numbers(min_val: int, max_val: int, interval_seconds: int) -> str:
    """
    Generate random numbers in a range at specified intervals and speak them aloud.
    
    Args:
        min_val (int): Minimum value for random numbers
        max_val (int): Maximum value for random numbers  
        interval_seconds (int): Interval between generations in seconds
        
    Returns:
        str: Confirmation that random number generation has started
    """
    def random_worker():
        task_id = f"random_{min_val}_{max_val}_{int(time.time())}"
        running_tasks[task_id] = True
        count = 0
        
        while running_tasks.get(task_id, False):
            num = random.randint(min_val, max_val)
            count += 1
            timestamp = time.strftime("%H:%M:%S")
            
            # Print to console AND prepare for speech
            print(f"🎲 [{timestamp}] Random #{count}: {num}")
            
            # Return the number as speech text
            speech_text = f"Random number {num}"
            print(f"🗣️ Speaking: {speech_text}")
            
            time.sleep(interval_seconds)
    
    # Start background thread
    thread = threading.Thread(target=random_worker, daemon=True)
    thread.start()
    
    return f"🎲 Started generating random numbers from {min_val} to {max_val} every {interval_seconds} seconds. I will speak each number as it's generated."

@function_tool()
def start_countdown(seconds: int) -> str:
    """
    Start a countdown timer for specified seconds and speak the countdown.
    
    Args:
        seconds (int): Number of seconds to count down
        
    Returns:
        str: Confirmation that countdown has started
    """
    def countdown_worker():
        remaining = seconds
        while remaining > 0:
            mins, secs = divmod(remaining, 60)
            time_str = f"{mins:02d}:{secs:02d}"
            
            # Print to console
            print(f"⏰ Countdown: {time_str} remaining")
            
            # Speak important milestones
            if remaining <= 10 or remaining % 30 == 0:
                speech_text = f"{remaining} seconds remaining"
                print(f"🗣️ Speaking: {speech_text}")
            
            time.sleep(1)
            remaining -= 1
        
        # Final announcement
        print(f"🎯 Countdown completed! {seconds} seconds finished!")
        print(f"🗣️ Speaking: Countdown completed!")
    
    # Start background thread
    thread = threading.Thread(target=countdown_worker, daemon=True)
    thread.start()
    
    return f"⏰ Started {seconds} second countdown. I will announce the remaining time."

@function_tool()
def calculate_expression(expression: str) -> str:
    """
    Calculate mathematical expressions safely and speak the result.
    
    Args:
        expression (str): Mathematical expression to calculate (e.g., "2 + 3 * 4")
        
    Returns:
        str: Result of the calculation
    """
    try:
        # Safe math evaluation
        allowed_chars = set('0123456789+-*/().^ ')
        if not all(c in allowed_chars for c in expression):
            return "❌ Invalid characters in math expression"
        
        # Replace ^ with ** for exponentiation
        expression = expression.replace('^', '**')
        result = eval(expression)
        
        # Prepare speech text
        speech_text = f"The result of {expression} is {result}"
        print(f"🗣️ Speaking: {speech_text}")
        
        return f"🧮 {expression} = {result}. I've spoken the result aloud."
        
    except Exception as e:
        return f"❌ Error calculating: {str(e)}"

@function_tool()
def create_text_file(filename: str, content: str) -> str:
    """
    Create a text file with specified content and announce completion.
    
    Args:
        filename (str): Name of the file to create
        content (str): Content to write to the file
        
    Returns:
        str: Confirmation that file was created
    """
    try:
        with open(filename, 'w') as f:
            f.write(content)
        
        # Announce completion
        speech_text = f"File {filename} created successfully"
        print(f"🗣️ Speaking: {speech_text}")
        
        return f"📝 Created file '{filename}' with content: {content}. I've announced the completion."
    except Exception as e:
        return f"❌ Error creating file: {str(e)}"

@function_tool()
def speak_number(number: int) -> str:
    """
    Speak any number immediately.
    
    Args:
        number (int): The number to speak
        
    Returns:
        str: Confirmation that the number was spoken
    """
    speech_text = str(number)
    print(f"🗣️ Speaking: {speech_text}")
    return f"🗣️ Spoken number: {number}"
