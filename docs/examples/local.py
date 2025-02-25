from grwiki import OpenAILM, Wiki

OPENAI_API_KEY = "YOUR-API-KEY"
topic = """I'm researching AI startups and want to understand their business models and what they do."""
lm = OpenAILM(model="gpt-4o-mini", max_input_tokens=128_000, api_key=OPENAI_API_KEY, base_url=None)
wiki = Wiki(topic=topic, title="AI Startups", path="startups.db", replace=True)

# Here is the key line, in which a source is taken from a local file instead of a website.
# You can specify many types of files; if it doesn't recognize the file type or path, an warning will be shown.
paths = ["/path/to/file.pdf"]
wiki.load_local_sources(paths)

wiki.make_entities(lm)
wiki.write_articles(lm)

wiki.serve()
