# encoding: utf-8

from __future__ import division, print_function, unicode_literals
import objc
from GlyphsApp import *
from GlyphsApp.plugins import *
from AppKit import NSApp, NSMenuItem, NSButton, NSImageOnly, NSWindowCollectionBehaviorCanJoinAllSpaces, NSFloatingWindowLevel
import openai
import sys
sys.path.insert(0, "PATH to your Glyphs Python like the following /Users/yourMac/Library/Application Support/Glyphs 3/Repositories/GlyphsPythonPlugin/Python.framework/Versions/3.10/lib/python3.10/site-packages/")

import anthropic

class GlyphsGPT(GeneralPlugin):

    # Definitions of IBOutlets
    dialog = objc.IBOutlet()
    runButton = objc.IBOutlet()
    settingsButton = objc.IBOutlet()
    settingsPanel = objc.IBOutlet()
    modelSelector = objc.IBOutlet()

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
        self.dialog.setDelegate_(self)  # Set the main dialog as its own delegate

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
        selectedModel = Glyphs.defaults['com.yourdomain.GlyphsGPT.selectedModel']
        if selectedModel is not None:
            self.modelSelector.setSelectedSegment_(selectedModel)

    @objc.python_method
    def savePreferences(self):
        Glyphs.defaults['com.yourdomain.GlyphsGPT.selectedModel'] = self.modelSelector.selectedSegment()

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
        
        if self.modelSelector.selectedSegment() == 0:
            response = self.chat_with_gpt(macro_text)
        else:
            response = self.chat_with_claude(macro_text)
        
        self.sendResponseToMacro_(response)
        print("Response set to Macro Panel")
        self.savePreferences()

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
        customInstruction = ""
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant specialized in Glyphs 3 App and Python3 coding."},
                    {"role": "user", "content": customInstruction + prompt}
                ]
            )
            return response['choices'][0]['message']['content']
        except Exception as e:
            return f"An error occurred with GPT: {str(e)}"

    @objc.python_method
    def chat_with_claude(self, prompt):
        customInstruction = ""
        try:
            message = self.claude_client.messages.create(
                model="claude-3-5-sonnet-20240620",
                max_tokens=1000,
                temperature=0,
                system="You are a helpful assistant specialized in Glyphs 3 App and Python3 coding.",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": customInstruction + prompt
                            }
                        ]
                    }
                ]
            )
            return message.content[0].text
        except Exception as e:
            return f"An error occurred with Claude: {str(e)}"

    # This method is called when the main dialog window is about to close
    def windowWillClose_(self, notification):
        if self.settingsPanel.isVisible():
            self.settingsPanel.orderOut_(None)

    # Define the method to get the Claude API key
    @objc.python_method
    def getClaudeAPIKey(self):
        # You can directly return the API key here for testing purposes
        # For example: return "your-claude-api-key"
        return "your-claude-api-key"

    @objc.python_method
    def getGPTAPIKey(self):
        # TODO: Implement a secure method to retrieve the GPT API key
        return "your-ChatGPT-api-key"

    @objc.python_method
    def __file__(self):
        """Please leave this method unchanged"""
        return __file__

