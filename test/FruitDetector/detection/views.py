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

from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse

@csrf_exempt


def upload_image(request):
    if request.method == "POST" and 'image' in request.FILES:
        image = request.FILES.get('image')
        # Save the image to a temporary location
        with open('temp_image.jpg', 'wb') as f:
            for chunk in image.chunks():
                f.write(chunk)

        image_path = 'temp_image.jpg'
        detected_fruits = detect_fruits(image_path)

        if isinstance(detected_fruits, set):
            detected_fruits = list(detected_fruits)

        # Store detected fruits in session
        request.session['detected_fruits'] = detected_fruits

        # Initialize the conversation
        history = request.session.get('history', [])
        conversation = Conversation(history=history)

        # Create a prompt based on detected fruits
        prompt_text = f"Only say and nothing else 'The detected fruit(s) are {', '.join(detected_fruits)}. What queries do you have?'"
        conversation.add_message("Bot", prompt_text)

        # Generate the initial response
        response = conversation.get_response(prompt_text)
        if response:
            conversation.add_message("Bot", response)

        # Store the initial response in session
        request.session['history'] = conversation.history

        return render(request, 'chat.html', {'initial_response': response})

    return redirect(reverse('index'))

def chat(request):
    if request.method == "POST":
        user_input = request.POST.get('message')
        history = request.session.get('history', [])
        conversation = Conversation(history=history)

        # Add user input to conversation history
        conversation.add_message("You", user_input)

        # Generate and print response based on updated conversation history
        response = conversation.get_response(user_input)
        if response:
            conversation.add_message("Bot", response)

        # Store updated history in session
        request.session['history'] = conversation.history

        return JsonResponse({'message': response})

    return render(request, 'chat.html')

class Conversation:
    def __init__(self, history=None):
        self.history = []
        self.model = genai.GenerativeModel("gemini-pro")  # Initialize the model
        self.chat = self.model.start_chat(history=self.history)  # Initialize chat with history

    def add_message(self, role, message):
        self.history.append({"role": role, "message": message})
        # Send the message in the format accepted by the API

        self.chat.send_message(message, stream = False)

    def get_conversation(self):
        return "\n".join([f"{role}: {text}" for role, text in self.history])
    
    def get_response(self, question):  # Ensure user message is added to history
        response = self.chat.send_message(question, stream=True)
        reply = ""
        for chunk in response:
            reply += chunk.text  # Ensure bot's reply is added to history
        return reply.strip()
