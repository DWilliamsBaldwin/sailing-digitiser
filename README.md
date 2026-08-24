# Sailing Digitiser 
Local AI-assisted digitisation of sailing race scoresheets. 

Current status (v0.01): 

- Qwen2.5VL 3B tested locally via Ollama 
- Full-sheet identity extraction working 
- 18/18 competitor recall on benchmark sheet 
- Near-perfect sail number extraction 
- Names extracted with minor OCR errors 
- Class extraction under investigation 

Next steps: 

- Build correction layer using sail-number reference database 
- Test pursuit and handicap sheet-specific prompts 
- Improve class extraction for grouped-class sheets