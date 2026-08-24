from ollama import chat

IMAGE_FILE = (
	"data/raw/"
	"09f759ce-d691-4870-ace9-cbaf26703d56.jpeg"
	)

PROMPT = """
	This is a sailing race scoresheet. 

	Extract every competitor visible in the table.

	For each competitor provide:
	CLASS | SAIL_NUMBER | HELM_CREW 

	Read as many competitors as possible. 

	If the boat class is unclear, write UNKNOWN.

	Do not explain anything. 

	Do not describe the sheet. 

	Return only the competitor entries.
	"""

response = chat(
	model='qwen2.5vl:3b',
	messages=[
		{
			'role': 'user',
			'content': PROMPT_CLASS,
			'images': [IMAGE_FILE],
		}
	]
)

print(response['message']['content'])