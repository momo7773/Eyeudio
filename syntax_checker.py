import osascript
import subprocess
import pyautogui
from fuzzywuzzy import fuzz
from fuzzywuzzy import process

class Checker(object):
    def __init__(self):
        self.command_list = []
        self.prepare_command_list()

    def prepare_command_list(self):
        command1 = ["turn up volume", "turn_up_volume", -1]
        command2 = ["turn down volume", "turn_down_volume", -1]
        # command3 = ["open", "open_app", True]
        command4 = ["single click", "click", -1]
        # command5 = ["set volume to", "set_volume", True]
        command6 = ["open new tab", "add_new_tab", -1]
        command7 = ["next tab", "next_tab", -1]
        command8 = ["open new window", "open_new_window", -1]
        command9 = ["open chrome", "open_app", 1]
        command10 = ["open microsoft powerpoint", "open_app", 1]
        command11 = ["open notion", "open_app", 1]
        self.command_list.append(command1)
        self.command_list.append(command2)
        # self.command_list.append(command3)
        self.command_list.append(command4)
        # self.command_list.append(command5)
        self.command_list.append(command6)
        self.command_list.append(command7)
        self.command_list.append(command8)
        self.command_list.append(command9)
        self.command_list.append(command10)
        self.command_list.append(command11)

        # for command in self.command_list:
        #     self.tree.add_command(command)

    def execute_command(self, tokens):
        valid, command = self.validate_command(tokens.lower())
        if valid:
            self.call_command(command[2], command[1], command[0])
            return command[0]
        else:
            #TODO: change to pop up
            print('Not valid command, skip')
    def validate_command(self, tokens):
        confident_command = []
        confidence = 0
        for command in self.command_list:
            conf = fuzz.partial_ratio(command[0], tokens)
            if conf > confidence:
                confidence = conf
                confident_command = command
        if confidence >= 80:
            return True, confident_command
        return False, None

    def call_command(self, argument_start_index, function_call, command):
        if argument_start_index == -1:
            globals()[function_call]()
        else:
            arguments = ' '.join(command.split()[argument_start_index :])
            globals()[function_call](arguments)
        return command

class Tree(object):
    def __init__(self):
        self.root = Node('')
    def add_command(self, command):
        print(command)
        command_words = command[0].split(' ')
        function = command[1]
        has_arguments = command[2]
        temp = self.root
        for word in command_words:
            word = word.lower()
            print(word)
            if word == command_words[-1]:
                temp = temp.add_terminal_child(word, function, has_arguments)
            else:
                temp = temp.add_child(word)

    # return: Boolean, TerminalNode
    def check_command(self, command):
        command_words = command.split(' ')
        temp = self.root
        for i in range(len(command_words)):
            word = command_words[i]
            word = word.lower()
            if temp.exist_child(word):
                temp = temp.get_child(word)
                if isinstance(temp, TerminalNode):
                    break
            else:
                return False, None, None

        if not isinstance(temp, TerminalNode):
            return False, None, None
        else:
            if temp.has_arguments:
                return True, temp, ' '.join(command_words[i+1:])
            return True, temp, None

class Node(object):
    def __init__(self, name):
        self.name = name
        self.children = dict()

    def add_child(self, child_name):
        if child_name not in self.children.keys():
            self.children[child_name] = Node(child_name)
        return self.children[child_name]

    def add_terminal_child(self, child_name, function, has_arguments):
        if child_name not in self.children.keys():
            self.children[child_name] = TerminalNode(child_name, function, has_arguments)
        return self.children[child_name]

    def exist_child(self, child_name):
        return child_name in self.children.keys()

    def get_child(self, child_name):
        return self.children[child_name]

class TerminalNode(Node):
    def __init__(self, name, function, has_arguments=False):
        self.name = name
        self.function_call = function
        self.has_arguments = has_arguments
        self.arguments = None
        Node.__init__(self, name)

    def has_arguments(self):
        return self.has_arguments

    def add_arguments(self, arguments):
        self.arguments = arguments

    def call_command(self):
        if not self.has_arguments:
            globals()[self.function_call]()
        else:
            globals()[self.function_call](self.arguments)

def text_normalizer(text):
    text = text.upper()
    return text.translate(str.maketrans('', '', string.punctuation))

def click():
    print('call click')
    pyautogui.click()

def move_click(x, y):
    pyautogui.click(x=x, y=y)

def turn_up_volume():
    code, out, err = osascript.run("output volume of (get volume settings)")
    if not err:
        new_volume = int(out) + 10
        if new_volume > 100:
            new_volume = 100
        osascript.run("set volume output volume {}".format(new_volume))
    code, out, err = osascript.run("output volume of (get volume settings)")
    print(out)

def turn_down_volume():
    code, out, err = osascript.run("output volume of (get volume settings)")
    if not err:
        new_volume = int(out) - 10
        if new_volume < 0:
            new_volume = 0
        osascript.run("set volume output volume {}".format(new_volume))
    code, out, err = osascript.run("output volume of (get volume settings)")
    print(out)

def turn_up_brightness(value):
    code, out, err = osascript.run("tell application \"Terminal\" \nset currentTab to do script (\"brightness {}\") \n end tell".format(value))
    if not err:
        print(out)
    else:
        print(err)

def set_volume(values):
    value = values[0]
    osascript.run("set volume output volume {}".format(value))
    code, out, err = osascript.run("output volume of (get volume settings)")
    print(out)

def is_open_command(tokens):
    return True if tokens[0] == 'OPEN' else False

def open_app(app):
    # TODO: find whether the app exists (using regex?)
    # TODO: multiple directories; check duplicate
    directory = '/Applications/'
    if app in application_mapping.keys():
        app = application_mapping[app]
        Proc = subprocess.Popen(['open', directory + app + '.app'])
    else:
        print('Not in available application')

def add_new_tab():
    pyautogui.hotkey('command', 't', interval=0.25)

def add_new_window():
    pyautogui.hotkey('command', 'n', interval=0.25)

def next_tab():
    pyautogui.hotkey('command', 'tab', interval=0.25)

application_mapping = {'chrome': 'Google Chrome','microsoft powerpoint': 'Microsoft PowerPoint', 'powerpoint': 'Microsoft PowerPoint', 'notion': 'Notion'}
