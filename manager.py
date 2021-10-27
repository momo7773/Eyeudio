import status

class Manager(object):
    def __init__():
        self.eye_controller = None
        self.audio_controller = None
        self.lip_reading_controller = None

        self.eye_tracking_status = Status.END
        self.audio_status = Status.END
        self.lip_reading_status = Status.END

    def start_eye_tracking():
        if self.eye_controller == None:
            self.eye_controller = # eye controller initialization
        self.eye_tracking_status = Status.START
        self.eye_controller.start()
    def start_audio():
        if self.audio_controller == None:
            self.audio_controller = # audio controller initialization

        self.audio_status = Status.START
        self.audio_controller.start()
    def start_lip_reading():
        if self.lip_reading_controller == None:
            self.lip_reading_controller = #lip_reading_controller initialization

        self.lip_reading_status = Status.START
        self.lip_reading_controller.start()

    def stop_eye_tracking():
        pass

    def stop_audio():
        pass

    def stop_lip_reading():
        pass
