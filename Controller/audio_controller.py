class Audio_Controller(Controller):
    def __init__(self):
        self.input = None
        self.process = None
        # self.model = #initialize model
        # self.checker = #initialize Syntax_Check
        # self.executor = #initialize executor

    # def start(self):
    #     if self.input == None:
    #         self.input =
    #     if self.process == None:
    #         self.process =
    #
    #     while(True):
    #         audio = self.input.get_audio()
    #
    #         processed_audio = self.process.process()
    #
    #         command = self.model(processed_audio)
    #
    #         valid = self.checker.check_syntax(command)
    #
    #         if valid:
    #             self.executor.execute(command)
    #
    # def stop():
