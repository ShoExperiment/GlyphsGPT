# encoding: utf-8

from __future__ import division, print_function, unicode_literals
import objc
from GlyphsApp import *
from GlyphsApp.plugins import *
from AppKit import (
    NSApp, NSMenuItem, NSImageOnly,
    NSWindowCollectionBehaviorCanJoinAllSpaces, NSFloatingWindowLevel
)
import openai
import sys
sys.path.insert(0, "PATH to your Glyphs Python like the following /Users/yourMac/Library/Application Support/Glyphs 3/Repositories/GlyphsPythonPlugin/Python.framework/Versions/3.10/lib/python3.10/site-packages/")

import anthropic
import re
import os

class GlyphsGPT(GeneralPlugin):

    # IBOutlets
    dialog = objc.IBOutlet()
    runButton = objc.IBOutlet()
    settingsButton = objc.IBOutlet()
    settingsPanel = objc.IBOutlet()
    modelSelector = objc.IBOutlet()

    autopilotButton = objc.IBOutlet()

    # The checkbox for toggling the pre-defined prompt
    predefinedPromptButton = objc.IBOutlet()

    @objc.python_method
    def settings(self):
        self.name = Glyphs.localize({'en': 'GlyphsGPT'})
        self.loadNib('IBdialog', __file__)
        self.setupSettingsButton()
        self.settingsPanel.orderOut_(None)  # Hide settings panel initially
        self.setupClaudeClient()
        self.setupOpenAIClient()
        self.loadPreferences()
        self.setupWindowBehavior()
        self.dialog.setDelegate_(self)

    @objc.python_method
    def setupClaudeClient(self):
        self.claude_client = anthropic.Anthropic(api_key=self.getClaudeAPIKey())

    @objc.python_method
    def setupOpenAIClient(self):
        openai.api_key = self.getGPTAPIKey()

    @objc.python_method
    def start(self):
        newMenuItem = NSMenuItem(self.name, self.showWindow_)
        Glyphs.menu[WINDOW_MENU].append(newMenuItem)

    def showWindow_(self, sender):
        self.dialog.makeKeyAndOrderFront_(None)

    @objc.python_method
    def setupSettingsButton(self):
        if self.settingsButton:
            self.settingsButton.setBezelStyle_(NSImageOnly)
            self.settingsButton.setBordered_(False)
            self.settingsButton.setImage_(NSImage.imageNamed_("NSActionTemplate"))
            self.settingsButton.setToolTip_("Toggle Settings")

    @objc.python_method
    def setupWindowBehavior(self):
        self.dialog.setCollectionBehavior_(NSWindowCollectionBehaviorCanJoinAllSpaces)
        self.dialog.setLevel_(NSFloatingWindowLevel)

    @objc.python_method
    def loadPreferences(self):
        # Restore the selected model
        selectedModel = Glyphs.defaults['com.yourdomain.GlyphsGPT.selectedModel']
        if selectedModel is not None:
            self.modelSelector.setSelectedSegment_(selectedModel)

        # Restore autopilot
        autopilotEnabled = Glyphs.defaults['com.yourdomain.GlyphsGPT.autopilotEnabled']
        if autopilotEnabled is not None:
            self.autopilotButton.setState_(1 if autopilotEnabled else 0)
            self.runButton.setTitle_("AUTO" if autopilotEnabled else "Run")

        # Restore the pre-defined prompt checkbox
        predefinedPromptEnabled = Glyphs.defaults['com.yourdomain.GlyphsGPT.predefinedPromptEnabled']
        if predefinedPromptEnabled is not None:
            self.predefinedPromptButton.setState_(1 if predefinedPromptEnabled else 0)

    @objc.python_method
    def savePreferences(self):
        Glyphs.defaults['com.yourdomain.GlyphsGPT.selectedModel'] = self.modelSelector.selectedSegment()
        # autopilot and pre-defined prompt states are saved in their toggle actions

    @objc.IBAction
    def toggleSettings_(self, sender):
        if self.settingsPanel.isVisible():
            self.settingsPanel.orderOut_(None)
        else:
            self.settingsPanel.orderFront_(None)

    @objc.IBAction
    def runAI_(self, sender):
        print("runAI_ method called")
        macro_text = self.getContentFromMacro_(None)
        if not macro_text:
            print("No text was retrieved from the Macro Panel")
            return

        print("Text retrieved from Macro:", macro_text)

        # Decide which model to call
        if self.modelSelector.selectedSegment() == 0:
            response = self.chat_with_gpt(macro_text)
        else:
            response = self.chat_with_claude(macro_text)

        self.sendResponseToMacro_(response)
        print("Response set to Macro Panel")
        self.savePreferences()

        # === Autopilot logic ===
        autopilot_enabled = bool(self.autopilotButton.state())
        if autopilot_enabled:
            print("Autopilot is enabled. Attempting to extract and execute Python code.")
            code_to_run = self.extract_python_code(response)
            if code_to_run:
                print("Code block found:\n", code_to_run)
                try:
                    exec(code_to_run, globals(), locals())
                    print("Autopilot code executed successfully.")
                except Exception as e:
                    print("Error executing autopilot code:", e)
            else:
                print("No Python code block found in the response.")

    @objc.IBAction
    def getContentFromMacro_(self, sender):
        print("getContentFromMacro_ called")
        try:
            macroViewControllers = NSApp.delegate().macroPanelController().tabBarControl().tabItems()
            tabBarControl = NSApp.delegate().macroPanelController().tabBarControl()
            selectedTab = tabBarControl.selectionIndex()
            content_macro = macroViewControllers[selectedTab].macroText().string()
            print("selectedTab:", selectedTab)
            print("content_macro:", content_macro)
            return content_macro
        except Exception as e:
            print(f"Error in getContentFromMacro_: {str(e)}")
        return ""

    @objc.IBAction
    def sendResponseToMacro_(self, text):
        print("sendResponseToMacro_ called")
        try:
            macroViewControllers = NSApp.delegate().macroPanelController().tabBarControl().tabItems()
            tabBarControl = NSApp.delegate().macroPanelController().tabBarControl()
            selectedTab = tabBarControl.selectionIndex()
            macroViewControllers[selectedTab].macroText().setString_(text)
            print("Response set to Macro Panel")
        except Exception as e:
            print(f"Error in sendResponseToMacro_: {str(e)}")

    @objc.python_method
    def chat_with_gpt(self, prompt):
        """
        If 'predefinedPromptEnabled' is True, send the specialized content.
        Otherwise, send an empty string.
        """
        predefinedPromptEnabled = Glyphs.defaults['com.yourdomain.GlyphsGPT.predefinedPromptEnabled']
        if predefinedPromptEnabled:
            systemContent = "You are a helpful assistant specialized in Glyphs 3 App and Python3 coding."
        else:
            systemContent = ""

        messages = [
            {"role": "system", "content": systemContent},
            {"role": "user", "content": prompt}
        ]

        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=messages
            )
            return response['choices'][0]['message']['content']
        except Exception as e:
            return f"An error occurred with GPT: {str(e)}"

    @objc.python_method
    def chat_with_claude(self, prompt):
        """
        If 'predefinedPromptEnabled' is True, send the specialized content.
        Otherwise, send an empty string.
        """
        predefinedPromptEnabled = Glyphs.defaults['com.yourdomain.GlyphsGPT.predefinedPromptEnabled']
        if predefinedPromptEnabled:
            system_text = "You are a helpful assistant specialized in Glyphs 3 App and Python3 coding."
        else:
            system_text = ""

        try:
            message = self.claude_client.messages.create(
                model="claude-3-7-sonnet-20250219",
                max_tokens=1000,
                temperature=0,
                system=system_text,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ]
            )
            return message.content[0].text
        except Exception as e:
            return f"An error occurred with Claude: {str(e)}"

    @objc.IBAction
    def toggleAutopilot_(self, sender):
        autopilot_state = bool(sender.state())
        Glyphs.defaults['com.yourdomain.GlyphsGPT.autopilotEnabled'] = autopilot_state
        self.runButton.setTitle_("AUTO" if autopilot_state else "Run")
        print("Autopilot mode set to:", autopilot_state)

    @objc.IBAction
    def togglePredefinedPrompt_(self, sender):
        """
        If ON => system prompt is "You are a helpful assistant specialized…"
        If OFF => system prompt is ""
        """
        predefPromptState = bool(sender.state())
        Glyphs.defaults['com.yourdomain.GlyphsGPT.predefinedPromptEnabled'] = predefPromptState
        print("Predefined prompt enabled:", predefPromptState)

    @objc.python_method
    def extract_python_code(self, text):
        """
        Look for a Python code block enclosed in triple backticks.
        Returns the first code block found, or None if none is found.
        """
        pattern = r"```python(.*?)```"
        match = re.search(pattern, text, re.DOTALL)
        if match:
            return match.group(1).strip()
        return None

    def windowWillClose_(self, notification):
        if self.settingsPanel.isVisible():
            self.settingsPanel.orderOut_(None)

    @objc.python_method
    def getClaudeAPIKey(self):
        # Return your actual Claude key
        return ""

    @objc.python_method
    def getGPTAPIKey(self):
        # Return your actual GPT key
        return ""

    @objc.python_method
    def __file__(self):
        """Please leave this method unchanged"""
        return __file__

