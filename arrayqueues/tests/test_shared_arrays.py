from arrayqueues.shared_arrays import ArrayQueue, TimestampedArrayQueue
from multiprocessing import Process
import numpy as np
from queue import Empty, Full
import unittest
import time


class SourceProcess(Process):
    def __init__(self, n_items=100, timestamped=False,
                 n_mbytes=2, wait=0):
        super().__init__()
        self.source_array = TimestampedArrayQueue(max_mbytes=n_mbytes) if timestamped else ArrayQueue(max_mbytes=n_mbytes)
        self.n_items = n_items
        self.wait=wait

    def run(self):
        for i in range(self.n_items):
            try:
                self.source_array.put(np.full((100, 100), 5, np.uint8))
                print("I inserted ", self.source_array.view.i_item)
                print("Last item read was ", self.source_array.last_item)
            except Full:
                assert False
            if self.wait > 0:
                time.sleep(self.wait)
        print(self.source_array.view.total_shape)



class SinkProcess(Process):
    def __init__(self, source_array, limit=None):
        super().__init__()
        self.source_array = source_array
        self.limit = limit

    def run(self):
        while True:
            try:
                item = self.source_array.get(timeout=0.5)
                print('Got item')
                assert item[0, 0] == 5
            except Empty:
                break
            if self.limit is not None:
                self.limit -= 1
                if self.limit == 0:
                    break


class TimestampedSinkProcess(Process):
    def __init__(self, source_array):
        super().__init__()
        self.source_array = source_array

    def run(self):
        previous_time = None
        while True:
            try:
                time, item = self.source_array.get(timeout=0.5)
                assert item[0, 0] == 5
                if previous_time is not None:
                    assert time>=previous_time
                previous_time = time
            except Empty:
                break


class TestSample(unittest.TestCase):
    def test_shared_queues(self):
        p1 = SourceProcess(100)
        p2 = SinkProcess(source_array=p1.source_array)
        p1.start()
        p2.start()
        p1.join()
        p2.join()

    def test_shared_timestamped_queues(self):
        p1 = SourceProcess(100, timestamped=True)
        p2 = TimestampedSinkProcess(source_array=p1.source_array)
        p1.start()
        p2.start()
        p1.join()
        p2.join()

    def test_full_queue(self):
        p1 = SourceProcess(40, n_mbytes=0.2, wait=0.1)
        p2 = SinkProcess(source_array=p1.source_array, limit=4)
        p1.start()
        p2.start()
        p2.join()
        p1.join()


