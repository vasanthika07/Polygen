import sys
import os
sys.path.insert(0, os.path.abspath("backend"))

from app.services.prompt_engine import prompt_engine

def test_sword_prompt():
    prompt = "A rusted medieval broadsword with a glowing blue sapphire in the hilt."
    structured = prompt_engine.process(prompt)
    
    assert "sword" in structured.object or "broadsword" in structured.object
    assert "medieval" in structured.style or "fantasy" in structured.style
    assert "iron" in structured.material or "rust" in structured.material
    assert any("sapphire" in d or "blue" in d or "glowing" in d for d in structured.details)
    assert structured.polygon_budget == 10000
    print("test_sword_prompt passed!")

def test_chair_prompt():
    prompt = "A rustic oak wooden chair with carved armrests."
    structured = prompt_engine.process(prompt, style_override="realistic")
    
    assert "chair" in structured.object
    assert "wood" in structured.material or "oak" in structured.material
    assert structured.style == "realistic"
    print("test_chair_prompt passed!")

def test_robot_prompt():
    prompt = "A futuristic metallic battle robot with neon green visor."
    structured = prompt_engine.process(prompt)
    
    assert "robot" in structured.object or "battle" in structured.object
    assert "sci-fi" in structured.style
    assert any("neon" in d or "visor" in d for d in structured.details)
    print("test_robot_prompt passed!")

if __name__ == "__main__":
    test_sword_prompt()
    test_chair_prompt()
    test_robot_prompt()
    print("All prompt engine tests passed successfully!")

