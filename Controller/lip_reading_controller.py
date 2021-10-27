class Lip_Reading_Controller(Controller):
    def __init__():
        #may include multiple input and process(image & voice)
        self.input = None
        self.process = None
        self.model = #initialize model
        self.checker = #initialize Syntax_Check
        self.executor = #initialize executor

    def start():
        if self.input == None:
            self.input =
        if self.process == None:
            self.process =

        while(True):
            frames = self.input.get_frames()

            processed_frames = self.process.process(frames)

            command = self.model()

            valid = self.checker.check_syntax(command)

            if valid:
                self.executor.execute(command)

        def stop():
