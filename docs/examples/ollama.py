from nichey import OpenAILM

# To use Ollama on localhost, simply change the base URL, set the api_key to "ollama"
# ... set the appropriate model name, and give the right max_input_tokens (context length)
lm = OpenAILM(model="llama3.2", base_url="http://localhost:11434/v1", api_key="ollama", max_input_tokens=8096, accepts_images=False)
