from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
import json
import os
import time
from dotenv import load_dotenv
import google.generativeai as genai
from ultralytics import YOLO
# Load environment variables
load_dotenv()

# Access your API key from an environment variable
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

class Conversation:
    def __init__(self, history=None):
        if history is None:
            history = []
        self.history = history
        self.model = genai.GenerativeModel("gemini-pro")  # Initialize the model
        self.chat = self.model.start_chat()  # Initialize chat without history

    def add_message(self, role, message):
        self.history.append({"role": role, "content": message})
        # Send the message in the format accepted by the API
        self.chat.send_message(message)

    def get_conversation(self):
        return "\n".join([f"{msg['role']}: {msg['content']}" for msg in self.history])

    def get_response(self, question):
        response = self.chat.send_message(question, stream=True)
        reply = ""
        for chunk in response:
            reply += chunk.text
        return reply.strip()




def detect_fruits(image_path):
    # Load the YOLOv8s model
    model = YOLO("/home/lc/test/FruitDetector/best.pt")
    print("Model loaded successfully")
    
    # Perform inference on an image
    results = model(image_path, show=True, save=True)
    print("Inference completed")
    
    # Check if `obb` contains detections
    obb = results[0].obb
    if obb is None or len(obb.cls) == 0:
        print("No detections found")
        return "No fruits detected in the image."
    
    # Extract detected fruits
    detected_fruits = []
    for i in range(len(obb.cls)):
        confidence = obb.conf[i].item()
        class_id = int(obb.cls[i].item())
        
        if confidence > 0.5 and class_id in results[0].names:
            detected_fruits.append(results[0].names[class_id])
    
    if not detected_fruits:
        print("No detections found with confidence > 0.5")
        return "No fruits detected in the image."
    
    return detected_fruits

def index(request):
    return render(request, 'index.html')

def upload_image(request):
    if request.method == "POST":
        image = request.FILES['image']
        # Save the image to a temporary location
        with open('temp_image.jpg', 'wb') as f:
            for chunk in image.chunks():
                f.write(chunk)

        image_path = 'temp_image.jpg'
        detected_fruits = detect_fruits(image_path)
        
        # Store detected fruits in session
        request.session['detected_fruits'] = detected_fruits

        # Initialize the conversation
        history = request.session.get('history', [])
        conversation = Conversation(history=history)
        if isinstance(detected_fruits, str):
            return JsonResponse({'message': detected_fruits})
        
        # Create a prompt based on detected fruits
        prompt_text = f"Only say and nothing else 'The detected fruit(s) are {', '.join(detected_fruits)}. What queries do you have?'"
        conversation.add_message("Bot", prompt_text)
        
        # Generate the initial response
        response = conversation.get_response(prompt_text)
        
        # Store the initial response in session
        request.session['history'] = conversation.history
        
        # Pass the response and initial conversation history to the template
        return render(request, 'chat.html', {'initial_response': response})
    
    return redirect(reverse('index'))


@csrf_exempt
def chat(request):
    if request.method == "POST":
        try:
            
            # Retrieve the conversation history from the session
            history = request.session.get('history', [])

            # Initialize the conversation with history
            conversation = Conversation(history=history)

            # Extract user input from the request
            user_input = request.POST.get('message', '').strip()
            
            if not user_input:
                return JsonResponse({'error': 'No message provided'}, status=400)

            # Add user input to conversation history
            conversation.add_message("You", user_input)

            # Get response from the bot
            response = conversation.get_response(user_input)
            
            # Update the history in the session
            request.session['history'] = conversation.history
            
            return JsonResponse({'message': response})
        
        except Exception as e:
            # Log the exception and return a generic error response
            print(f"Error in chat view: {e}")
            return JsonResponse({'error': 'An error occurred'}, status=500)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)
