
# GlyphsGPT

GlyphsGPT is a plugin for the Glyphs App that integrates OpenAI's GPT and Anthropic's Claude AI to assist with Python scripting within the app. This tool allows users to leverage powerful language models to generate code snippets, automate tasks, and enhance their workflow in Glyphs.

## Features

- **Generate Python scripts** within the Glyphs App using AI-powered assistants.
- **Supports both OpenAI's GPT** and **Anthropic's Claude AI**.
- **Customizable and extendable** to fit various workflows within the Glyphs environment.

## Requirements

- **Glyphs App**: Version 3.0 or later.
- **Python Version**: The plugin has been tested with Python 3.10.12 installed via Homebrew.
- **Required Libraries**:
  - `openai`
  - `anthropic`

## Installation

### 0. Install Python via Homebrew

The Python runtime that comes with the Glyphs App **DOES NOT WORK** for this plugin.

You must install Python via Homebrew. After installation, you need to configure Glyphs to use the correct Python version. Go to Settings > Addons > Python versions and select the correct one.

You will also need to know the path to the Python installation. This path will be used to install the required libraries and must be hard-coded into this plugin.

The path should look something like this:

```
/Users/your-computer-name/Library/Application Support/Glyphs 3/Repositories/GlyphsPythonPlugin/Python.framework/Versions/3.10/lib/python3.10/site-packages/
```

### 1. Install the Required Libraries

To ensure that Glyphs can access the required Python libraries, use the following commands:

```sh
pip install --target="your-glyphs-python-plugin-path/site-packages/" openai

pip install --target="your-glyphs-python-plugin-path/site-packages/" anthropic
```

**Note**: Replace `your-glyphs-python-plugin-path` with the actual path where your Glyphs Python environment is located.

### 2. Path Configuration

You need to configure the path within the plugin to ensure it can access the installed libraries:

```python
sys.path.insert(0, "your-glyphs-python-plugin-path/site-packages/")
```

### 3. Set the API Keys

The API keys for Claude AI and ChatGPT need to be hard-coded within the plugin. You should edit the plugin code directly to securely store the keys.

### 4. Usage

- **Write Your Request**: In the Macro panel editor, write your request for what you need assistance with.
- **Press the Run Button**: After writing your request, press the "Run" button in the plugin.
- **View the Response**: The AI-generated response will be displayed in the Macro panel editor.

### 5. Notes

- **AI Models**: The AI models used (ChatGPT 3.5 and Claude 3.5 sonnet) are hard-coded in the plugin. If you want to use a different model, you will need to modify the plugin code. For example:

```python
model="claude-3-5-sonnet-20240620"
```

- **API Usage**: This plugin uses API calls to communicate with the AI models. Make sure you have the appropriate API keys. Note that each conversation with the AI is treated as a new session; the AI does not remember previous interactions.

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
