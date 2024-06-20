from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class Rectangle(BaseModel):
    length: float
    breadth: float

@app.post("/calculate_area")
def calculate_area(rectangle: Rectangle):
    area = rectangle.length * rectangle.breadth
    return {"area": area}