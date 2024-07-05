from queue import Queue
from threading import Thread, Lock
from typing import Optional


class EasyGuiQt:

    def __init__(self):
        super().__init__()
        self.lock = Lock()
        self.request_queue = Queue()
        self.result_queue = Queue()
        self.thread = Thread(target=self._run, daemon=True)
        self.thread.start()

    def _run(self):
        import easygui_qt
        while True:
            message, title, q_type = self.request_queue.get()
            if q_type == 'string':
                result = easygui_qt.get_string(message, title)
            elif q_type == 'yes/no':
                result = easygui_qt.get_yes_or_no(message, title)
            else:
                raise AssertionError(q_type)
            self.result_queue.put(result)

    def get_string(self, message: str, title='Title') -> str:
        with self.lock:
            self.request_queue.put((message, title, 'string'))
            return self.result_queue.get()

    def get_yes_no(self, message: str, title='Title') -> Optional[bool]:
        with self.lock:
            self.request_queue.put((message, title, 'yes/no'))
            return self.result_queue.get()
