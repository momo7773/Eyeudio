class Eye_Controller(Controller):
    def __init__():
        self.input = None
        self.process = None
        self.model = #initialize model
        self.cursor_controller = None

    def start():
        if self.input == None:
            self.input =
        if self.process == None:
            self.process =
        if self.cursor_controller == None:
            self.cursor_controller =

        # way of proceessing
        while(True):
            frames = self.input.get_frames()
            processed_frames = self.process.process()

            output_position = self.model(processed_frames)

            self.cursor_controller.move_cursor(output_position)
