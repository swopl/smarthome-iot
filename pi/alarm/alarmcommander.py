class AlarmCommander:
    def __init__(self):
        self.abz_queues = []

    def activate(self):
        pass

    def attach_abz(self, abz_queue):
        self.abz_queues.append(abz_queue)

    def _buzz_all(self):
        buzz = {"pitch": 440, "duration": 1.0}
        for abz_queue in self.abz_queues:
            abz_queue.put(buzz)
