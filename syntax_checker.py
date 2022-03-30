import pysndfile
import osascript
import sounddevice as sd
import librosa
import subprocess
import pyautogui
import keyboard

class Checker(object):
    def __init__(self):
        self.command_list = []
        self.tree = Tree()
        self.prepare_command_list()

    def prepare_command_list(self):
        command1 = ["turn up volume", "turn_up_volume", False]
        command2 = ["turn down volume", "turn_down_volume", False]
        command5 = ["set volume to", "set_volume", True]
        command3 = ["open", "open_app", True]
        command4 = ["click", "click", False]
        command6 = ["open new tab", "open_new_tab", False]
        command7 = ["next tab", "next_tab", False]
        command8 = ["open new window", "open_new_window", False]
        self.command_list.append(command1)
        self.command_list.append(command2)
        self.command_list.append(command3)
        self.command_list.append(command4)
        self.command_list.append(command5)
        self.command_list.append(command6)
        self.command_list.append(command7)
        self.command_list.append(command8)
        for command in self.command_list:
            self.tree.add_command(command)

    def execute_command(self, command):
        valid, terminal, arguments = self.tree.check_command(command)
        if valid:
            if arguments is not None:
                terminal.add_arguments(arguments)
            terminal.call_command()
        else:
            print('Not valid command, skip')


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

application_mapping = {'CHROME': 'Google Chrome','MICROSOFT POWERPOINT': 'Microsoft PowerPoint', 'POWERPOINT': 'Microsoft PowerPoint', 'NOTION': 'Notion'}
