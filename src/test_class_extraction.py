from PIL import Image
from ollama import chat

IMAGE_FILE = (
	"data/raw/"
	"f615e34f-3798-49b9-8b28-ce2934e891a2.jpeg"
	)


img = Image.open(IMAGE_FILE)

width, height = img.size 

crop = img.crop( 
	( 
		0, # left 
		0, # top 
		int(width * 0.50), # right 
		height # bottom 
	) 
)

crop.save("data/cropped/class_test.jpeg")

print("Saved class_test.jpeg")

INPUT_FILE = ( "data/cropped/class_test.jpeg" )

PROMPT = """ 
	This image contains the competitor identification section of a sailing race scoresheet. 

	Extract every competitor. 

	Return: CLASS | SAIL_NUMBER | HELM_CREW 

	Return one competitor per line. 

	Do not explain. 

	Do not describe the image. 
	"""

response = chat(
	model='qwen2.5vl:3b',
	messages=[
		{
			'role': 'user',
			'content': PROMPT,
			'images': [INPUT_FILE],
		}
	]
)

print(response["message"]["content"])