# encoding: utf-8

from __future__ import division, print_function, unicode_literals
import objc
from GlyphsApp import *
from GlyphsApp.plugins import *
from AppKit import (
    NSApp, NSMenuItem, NSImageOnly,
    NSWindowCollectionBehaviorCanJoinAllSpaces, NSFloatingWindowLevel
)
import sys

#If some of your libraries are installed in your Python runtime of Glyphs app activate below the code and specify the location:
#sys.path.insert(0, "/Users/(username)/Library/Application Support/Glyphs 3/Repositories/GlyphsPythonPlugin/Python.framework/Versions/3.10/lib/python3.10/site-packages/")

import openai
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
    predefinedPromptButton = objc.IBOutlet()
    conversationHistoryButton = objc.IBOutlet()  # toggle for conversation history

    # Text field controlling max tokens
    maxTokensField = objc.IBOutlet()

    @objc.python_method
    def settings(self):
        """
        Called once when the plugin is loaded.
        We load the nib here, but we do NOT rely on “Visible at Launch”.
        Make sure to uncheck “Visible at Launch” for the window in IB.
        """
        self.name = Glyphs.localize({'en': 'GlyphsGPT'})
        self.loadNib('IBdialog', __file__)  # This just loads the nib; it won't show the window.
        
        self.setupSettingsButton()
        # Hide the settings panel at launch (optional):
        if self.settingsPanel:
            self.settingsPanel.orderOut_(None)

        self.setupClaudeClient()
        self.setupOpenAIClient()
        self.loadPreferences()
        self.setupWindowBehavior()

        # Initialize conversation histories
        self.conversation_gpt = []
        self.conversation_claude = []

        # Set the dialog delegate so we can intercept close events if we want
        if self.dialog:
            self.dialog.setDelegate_(self)

    @objc.python_method
    def setupClaudeClient(self):
        self.claude_client = anthropic.Anthropic(api_key=self.getClaudeAPIKey())

    @objc.python_method
    def setupOpenAIClient(self):
        """
        For openai>=1.0 (post-Nov 6, 2023).
        We create a client using the new class-based interface:
            from openai import OpenAI
            client = OpenAI(api_key=...)
        """
        self.openai_client = openai.OpenAI(
            api_key=self.getGPTAPIKey()
        )

    @objc.python_method
    def start(self):
        """
        Called after settings(). Add the plugin to the Window menu
        so the user can open the dialog on demand.
        """
        if Glyphs.buildNumber >= 3320:
            from GlyphsApp.UI import MenuItem
            newMenuItem = MenuItem(self.name, action=self.showWindow_, target=self)
        else:
            newMenuItem = NSMenuItem.new()
            newMenuItem.setTitle_(self.name)
            newMenuItem.setAction_(self.showWindow_)
            newMenuItem.setTarget_(self)
        Glyphs.menu[WINDOW_MENU].append(newMenuItem)

    def showWindow_(self, sender):
        """
        Called when the user selects the plugin from the Window menu.
        If the window is not “Visible at Launch,” we explicitly show it here.
        
        If you want to reload the nib each time (in case it's been closed/released),
        you could do something like:
        
            if not self.dialog or not self.dialog.isVisible():
                self.loadNib('IBdialog', __file__)
                self.setupWindowBehavior()
                self.dialog.setDelegate_(self)
        
        For now, we assume "Release When Closed" is unchecked in IB,
        so we can simply show the existing window object.
        """
        if self.dialog:
            self.dialog.makeKeyAndOrderFront_(None)
        else:
            print("Error: dialog is None, nib may not have loaded properly.")

    @objc.python_method
    def setupSettingsButton(self):
        if self.settingsButton:
            self.settingsButton.setBezelStyle_(NSImageOnly)
            self.settingsButton.setBordered_(False)
            self.settingsButton.setImage_(NSImage.imageNamed_("NSActionTemplate"))
            self.settingsButton.setToolTip_("Toggle Settings")

    @objc.python_method
    def setupWindowBehavior(self):
        """
        Make the plugin window float above other windows, etc.
        """
        if self.dialog:
            self.dialog.setCollectionBehavior_(NSWindowCollectionBehaviorCanJoinAllSpaces)
            self.dialog.setLevel_(NSFloatingWindowLevel)
        else:
            print("setupWindowBehavior: dialog is None")

    @objc.python_method
    def loadPreferences(self):
        selectedModel = Glyphs.defaults.get('com.yourdomain.GlyphsGPT.selectedModel')
        if selectedModel is not None and self.modelSelector:
            self.modelSelector.setSelectedSegment_(selectedModel)

        autopilotEnabled = Glyphs.defaults.get('com.yourdomain.GlyphsGPT.autopilotEnabled')
        if autopilotEnabled is not None and self.autopilotButton:
            self.autopilotButton.setState_(1 if autopilotEnabled else 0)
            if self.runButton:
                self.runButton.setTitle_("AUTO" if autopilotEnabled else "Run")

        predefinedPromptEnabled = Glyphs.defaults.get('com.yourdomain.GlyphsGPT.predefinedPromptEnabled')
        if predefinedPromptEnabled is not None and self.predefinedPromptButton:
            self.predefinedPromptButton.setState_(1 if predefinedPromptEnabled else 0)

        # Load max tokens from defaults with explicit type conversion
        max_tokens = int(Glyphs.defaults.get('com.yourdomain.GlyphsGPT.maxTokens', 1000))
        if self.maxTokensField:
            self.maxTokensField.setStringValue_(str(max_tokens))
        print(f"Loaded max tokens from preferences: {max_tokens}")
    
        # Load conversation history preference
        conversationHistoryEnabled = Glyphs.defaults.get('com.yourdomain.GlyphsGPT.conversationHistoryEnabled', False)
        if self.conversationHistoryButton:
            self.conversationHistoryButton.setState_(1 if conversationHistoryEnabled else 0)

    @objc.python_method
    def savePreferences(self):
        if self.modelSelector:
            Glyphs.defaults['com.yourdomain.GlyphsGPT.selectedModel'] = self.modelSelector.selectedSegment()
    
        # Also save max tokens
        if self.maxTokensField:
            try:
                max_tokens = int(self.maxTokensField.stringValue())
                Glyphs.defaults['com.yourdomain.GlyphsGPT.maxTokens'] = max_tokens
                print(f"Saved max tokens: {max_tokens}")
            except ValueError:
                pass  # Ignore if not a valid integer

        # Force synchronize
        NSUserDefaults.standardUserDefaults().synchronize()

    #
    # IBAction methods
    #
    @objc.IBAction
    def toggleSettings_(self, sender):
        if self.settingsPanel and self.settingsPanel.isVisible():
            self.settingsPanel.orderOut_(None)
        elif self.settingsPanel:
            self.settingsPanel.orderFront_(None)

    @objc.IBAction
    def runAI_(self, sender):
        print("runAI_ method called")
        # Save preferences FIRST before processing the request
        self.savePreferences()
        print("Preferences saved before processing request")

        macro_text = self.getContentFromMacro_(None)
        if not macro_text:
            print("No text was retrieved from the Macro Panel")
            return

        print("Text retrieved from Macro:", macro_text)

        # Decide which model to call
        if self.modelSelector and self.modelSelector.selectedSegment() == 1:
            response = self.chat_with_claude(macro_text)
        else:
            response = self.chat_with_gpt(macro_text)

        self.sendResponseToMacro_(response)
        print("Response set to Macro Panel")
        
        self.savePreferences()

        # Autopilot feature: run extracted Python code
        autopilot_enabled = bool(self.autopilotButton.state()) if self.autopilotButton else False
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

    @objc.IBAction
    def toggleAutopilot_(self, sender):
        autopilot_state = bool(sender.state())
        Glyphs.defaults['com.yourdomain.GlyphsGPT.autopilotEnabled'] = autopilot_state
        if self.runButton:
            self.runButton.setTitle_("AUTO" if autopilot_state else "Run")
        print("Autopilot mode set to:", autopilot_state)

    @objc.IBAction
    def togglePredefinedPrompt_(self, sender):
        predefPromptState = bool(sender.state())
        Glyphs.defaults['com.yourdomain.GlyphsGPT.predefinedPromptEnabled'] = predefPromptState
        print("Predefined prompt enabled:", predefPromptState)

    @objc.IBAction
    def maxTokensFieldChanged_(self, sender):
        value = sender.stringValue()
        try:
            tokens = int(value)
            if tokens < 1:
                tokens = 1
            # Save the value immediately
            Glyphs.defaults['com.yourdomain.GlyphsGPT.maxTokens'] = tokens
            NSUserDefaults.standardUserDefaults().synchronize()
            print(f"Max tokens immediately set to: {tokens}")
        except ValueError:
            print("Invalid input for max tokens. Please enter a positive integer.")

    #
    # Toggle Conversation History
    #
    @objc.IBAction
    def toggleConversationHistory_(self, sender):
        conversationHistoryState = bool(sender.state())
        Glyphs.defaults['com.yourdomain.GlyphsGPT.conversationHistoryEnabled'] = conversationHistoryState

        if not conversationHistoryState:
            # Clear conversation when turned off
            self.conversation_gpt = []
            self.conversation_claude = []

        print("Conversation history set to:", conversationHistoryState)

    #
    # Chat with GPT + conversation history
    #
    @objc.python_method
    def chat_with_gpt(self, prompt):
        predefinedPromptEnabled = Glyphs.defaults.get('com.yourdomain.GlyphsGPT.predefinedPromptEnabled', False)
        systemContent = (
            "You are a helpful assistant specialized in Type Design, Glyphs 3 App and Python3 coding. You fully understand the differences between Glyphs 2 API and Glyphs 3 API"
            if predefinedPromptEnabled else
            ""
        )

        conversationHistoryEnabled = Glyphs.defaults.get('com.yourdomain.GlyphsGPT.conversationHistoryEnabled', False)

        # Build messages
        if conversationHistoryEnabled:
            messages = []
            # System message if needed
            if systemContent:
                messages.append({"role": "system", "content": systemContent})
            # Previous conversation
            messages.extend(self.conversation_gpt)
            # Current user prompt
            messages.append({"role": "user", "content": prompt})
        else:
            messages = [
                {"role": "system", "content": systemContent},
                {"role": "user", "content": prompt}
            ]

        max_tokens = int(Glyphs.defaults.get('com.yourdomain.GlyphsGPT.maxTokens', 1000))
        print(f"Using max_tokens for ChatGPT API call: {max_tokens}")

        try:
            chat_completion = self.openai_client.chat.completions.create(
                model="gpt-4o",  # or "gpt-4", "gpt-4o", etc.
                messages=messages,
                max_tokens=max_tokens
            )
            response = chat_completion.choices[0].message.content
        except Exception as e:
            response = f"An error occurred with GPT: {str(e)}"

        # Store conversation if enabled
        if conversationHistoryEnabled:
            self.conversation_gpt.append({"role": "user", "content": prompt})
            self.conversation_gpt.append({"role": "assistant", "content": response})
            # Limit conversation to last 6 entries
            self.conversation_gpt = self.conversation_gpt[-6:]

        return response

    #
    # Chat with Claude + conversation history
    #
    @objc.python_method
    def chat_with_claude(self, prompt):
        predefinedPromptEnabled = Glyphs.defaults.get('com.yourdomain.GlyphsGPT.predefinedPromptEnabled', False)
        system_text = (
            "You are a helpful assistant specialized in Type Design, Glyphs 3 App and Python3 coding. You fully understand the differences between Glyphs 2 API and Glyphs 3 API"
            if predefinedPromptEnabled else
            ""
        )

        conversationHistoryEnabled = Glyphs.defaults.get('com.yourdomain.GlyphsGPT.conversationHistoryEnabled', False)
        max_tokens = int(Glyphs.defaults.get('com.yourdomain.GlyphsGPT.maxTokens', 1000))
        print(f"Using max_tokens for Claude API call: {max_tokens}")

        # Build messages for Claude
        if conversationHistoryEnabled:
            claude_messages = []
            for msg in self.conversation_claude:
                if msg["role"] == "user":
                    claude_messages.append({
                        "role": "user",
                        "content": [{"type": "text", "text": msg["content"]}]
                    })
                elif msg["role"] == "assistant":
                    claude_messages.append({
                        "role": "assistant",
                        "content": [{"type": "text", "text": msg["content"]}]
                    })
            # Add the new user prompt
            claude_messages.append({
                "role": "user",
                "content": [{"type": "text", "text": prompt}]
            })
        else:
            claude_messages = [{
                "role": "user",
                "content": [{"type": "text", "text": prompt}]
            }]

        try:
            message = self.claude_client.messages.create(
                model="claude-3-7-sonnet-20250219",
                max_tokens=max_tokens,
                temperature=0,
                system=system_text,
                messages=claude_messages
            )
            response = message.content[0].text
        except Exception as e:
            response = f"An error occurred with Claude: {str(e)}"

        # Store conversation if enabled
        if conversationHistoryEnabled:
            self.conversation_claude.append({"role": "user", "content": prompt})
            self.conversation_claude.append({"role": "assistant", "content": response})
            self.conversation_claude = self.conversation_claude[-6:]

        return response

    #
    # Utility: extract Python code blocks
    #
    @objc.python_method
    def extract_python_code(self, text):
        pattern = r"```python(.*?)```"
        match = re.search(pattern, text, re.DOTALL)
        if match:
            return match.group(1).strip()
        return None

    #
    # Optional: intercept close to hide instead of destroying
    #
    # def windowShouldClose_(self, sender):
    #     """
    #     If you want the window to be hidden rather than truly closed,
    #     uncomment this. Then the user can re-open it from the menu.
    #     Make sure 'Release When Closed' is unchecked in IB or do this override.
    #     """
    #     self.dialog.orderOut_(None)
    #     return False

    #
    # Window close event
    #
    def windowWillClose_(self, notification):
        """
        Called when the window is actually closing.
        If you want to do cleanup, do it here.
        """
        if self.settingsPanel and self.settingsPanel.isVisible():
            self.settingsPanel.orderOut_(None)

    #
    # Provide your API keys
    #
    @objc.python_method
    def getClaudeAPIKey(self):
        return ""  # truncated

    @objc.python_method
    def getGPTAPIKey(self):
        return ""  # truncated

    @objc.python_method
    def __file__(self):
        return __file__

