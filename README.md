# GlyphsGPT
<img width="975" alt="image" src="https://github.com/user-attachments/assets/0bfdd992-8f53-49b7-9df8-6d530b0954d5" />





GlyphsGPT is a plugin for the Glyphs App that integrates OpenAI's ChatGPT and Anthropic's Claude AI to assist with Python scripting within the app. This tool allows users to leverage powerful language models to generate code snippets, automate tasks, and enhance their workflow in Glyphs.

## Features
- **Instruction** to ask non-Glyphs-related tasks.
- **Autopilot** to excute code directly.
- **Conversation History** to excute code directly.
- **Max Tokens** to controll token amount.
- **Supports both OpenAI's GPT** and **Anthropic's Claude AI**.

**Autopilot**

A feature that automatically executes any Python code returned by ChatGPT or Claude.
It scans the AI’s response for code blocks (e.g., enclosed in triple backticks) and runs them immediately in the Glyphs Macro Panel environment.


## Requirements

- **Glyphs App**: Version 3.1 or later
- **Python Version**: The plugin has been tested with Python 3.10.12 installed via Homebrew. It will not work with Glyphs Python runtime.
- **API keys**: ChatGPT and/or Claude
- **Required Libraries**:
  - `openai 1.6`
  - `anthropic 0.49`

## Installation

### 0. Install Python via Homebrew

The Python runtime that comes with the Glyphs App **DOES NOT WORK** for this plugin.

You must install Python via Homebrew. After installation, you need to configure Glyphs to use the correct Python version. Go to Settings > Addons > Python versions and select the correct one.

<img width="735" alt="image" src="https://github.com/user-attachments/assets/bc8bdf21-452d-4b6a-b972-dc65cdde3130">

### 1. Install the Required Libraries

Install required libraries to the Python.
Run below the code on your Macro editor to make sure.

```
import openai
import anthropic
import jiter
print("✅ OpenAI Version:", openai.__version__)
print("✅ OpenAI Version:", anthropic.__version__)
print("✅ Jiter is installed correctly!", jiter.__version__)
```

### 2. Set the API Keys

The API keys for Claude AI and ChatGPT need to be hard-coded within the plugin. You should edit the plugin code directly to securely store the keys.

```
    #
    # Provide your API keys
    #
    @objc.python_method
    def getClaudeAPIKey(self):
        return ""  # truncated

    @objc.python_method
    def getGPTAPIKey(self):
        return ""  # truncated
```

### 3. Change some configurations (optional)

To change the model.
```
chat_completion = self.openai_client.chat.completions.create(
                model="gpt-4o",  # or "gpt-4", "gpt-4o", etc.
                messages=messages,
                max_tokens=max_tokens
            )
```
```
message = self.claude_client.messages.create(
                model="claude-3-7-sonnet-20250219",
                max_tokens=max_tokens,
                temperature=0,
                system=system_text,
                messages=claude_messages
            )
```


To increase conversation history, change the followings.
```
self.conversation_gpt = self.conversation_gpt[-6:]
```

```
self.conversation_claude = self.conversation_claude[-6:]
```
You can also change instruction as well.
```
system_text = (
            "You are a helpful assistant specialized in Type Design, Glyphs 3 App and Python3 coding. You fully understand the differences between Glyphs 2 API and Glyphs 3 API"
            if predefinedPromptEnabled else
            ""
        )
```
```
systemContent = (
            "You are a helpful assistant specialized in Type Design, Glyphs 3 App and Python3 coding. You fully understand the differences between Glyphs 2 API and Glyphs 3 API"
            if predefinedPromptEnabled else
            ""
        )
```
### 4. Usage

- **Write Your Request**: In the Macro panel editor, write your request for what you need assistance with.
<img width="446" alt="image" src="https://github.com/user-attachments/assets/48f49d3e-44f4-464e-a4cf-c675a9b778f1">

- **Press the Run Button**: After writing your request, press the "Run" button in the plugin.
<img width="142" alt="image" src="https://github.com/user-attachments/assets/144372f0-3605-4807-94fe-c495396b0a82">

- **View the Response**: The AI-generated response will be displayed in the Macro panel editor.
<img width="569" alt="image" src="https://github.com/user-attachments/assets/ba48f125-86c5-43d2-a867-42dfe598e514">

### 5. Notes




## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contributing

If you'd like to contribute, please fork the repository and use a feature branch. Pull requests are welcome!

## Acknowledgments

- **OpenAI** for providing the GPT API.
- **Anthropic** for providing the Claude AI API.
- The **Glyphs App** team for making an extensible and powerful font editor.

---

Feel free to reach out for any questions or issues regarding GlyphsGPT!
