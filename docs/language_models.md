# Language Models

This package supports all OpenAI API compatible language model APIs via the `grwiki.OpenAILM` class.

## Initilization and Attributes

- `model` (required): A string to pass as the "model" parameter in the API
- `max_input_tokens` (defaults to 8096): the maximum length the package will try to respect when calling the API
- `accepts_images` (defaults to `False`): Whether the model is a vision model
- `api_key` (defaults to the `OPENAI_API_KEY` environment variable): the API key for the URL
- `base_url` (defaults to 'https://api.openai.com/v1'): The base URL for the API
- `fail_on_overflow` (defaults to `False`): Whether the LM object throws an error when using a prompt that is suspected of exceeding `max_input_tokens`

## Functions

All LM objects have one function, `run`:

- `run(self, prompt, system="", context: list = [], json_schema=None)`: Returns an `LMResponse` object. The `prompt` argument is the user prompt; the `system` argument is the `system` or `developer` prompt; context is a list of messages placed in between the system and user prompts, in OpenAI message format (dictionaries with `role` and `content` keys). Setting `json_schema` to a type enforces a JSON schema. It's passed directly to the OpenAI API python library, and the type is a class the inherits from a pydantic base class. See the [OpenAI API docs](https://platform.openai.com/docs/api-reference/introduction) for more information.

## LMResponse

The `LMResponse` object is a an object specified from this class:

```
class LMResponse():
    def __init__(self, text, parsed=None):
        self.text = text
        self.parsed = parsed
```

If `json_schema` was specified, `text` may be empty and only `parsed` will be used (it will be a dictionary). Otherwise, `text` stores the language model response.
