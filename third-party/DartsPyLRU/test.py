
from threading import Thread, RLock, Condition
from unittest import TestCase, main
from darts.lib.utils.lru import AutoLRUCache, CacheLoadError, CacheAbandonedError
from time import sleep
from random import shuffle


class AutoCacheThreadingTest(TestCase):

    """Tests the AutoLRUCache implementation

    This class adds tests for the AutoLRUCache class, 
    which are hard to do in doctest (e.g., due to threading)
    Testing for race conditions and bugs stemming from
    concurrency is notoriously hard. This test case runs 
    enough threads (and iterations per thread) to make
    sure, that there is nothing glaringly obvious wrong
    with the implementation, but it is unlikely to be 
    able to find non-trivial bugs.

    TODO: 
    
      - Need tests for the abandoning stuff (clear with
        parameter discard_loads=True)

      - Need to figure out a way to force a key to be
        loaded concurrently, and exercise the error 
        handling when the loading thread encounters 
        an exception from the loader function. All 
        conurrently running threads loading the same
        key have to abort properly with the error
        signalled by the loader, wrapped as CacheLoadError
        exception.
    """

    def test_concurrent_access(self):

        """Test concurrent access of AutoLRUCaches
        
        This test function tests the nominal behaviour of a
        cache instance, not expecting any exceptions to be 
        raised.

        This test makes sure, that:

        - the logic, which keeps track of keys currently 
          being loaded in a cache, works as advertised, 
          and collapses multiple concurrent read requests
          for the same key into a single `loader` call.

        - nothing is ever evicted if the cache is large 
          enough to accomodate all objects ever being
          requested from it.
        """

        iterations_per_thread = 1000
        number_of_threads = 100
        key_range = list(range(4))

        loads_lock = RLock()
        loads = dict()
        start_lock = RLock()
        start_condition = Condition(start_lock)
        ready_condition = Condition(start_lock)
        start_now = False
        ready_list = list()

        def loader(key):
            with loads_lock:
                loads[key] = loads.get(key, 0) + 1
            # Fake a complicated computation here.
            # This should not slow down the test too
            # much, as it is ever only called 4 times
            # at all (if the cache implementation has
            # no bug in the load-coalescing code), so
            # we should sleep for at most 4 seconds,
            # and expect to sleep less, since these
            # sleep calls are likely to happen in parallel
            # on different threads.
            sleep(1)
            return "R(%r)" % (key,)

        def shuffled(seq):
            copy = list(seq)
            shuffle(copy)
            return copy

        cache = AutoLRUCache(loader, capacity=len(key_range))
        
        def reader():
            with start_lock:
                while not start_now:
                    start_condition.wait()
            for k in range(iterations_per_thread):
                for i in shuffled(key_range):
                    answer = cache.load(i)
                    self.assertEqual("R(%r)" % (i,), answer)
            with start_lock:
                ready_list.append(1)
                ready_condition.notifyAll()

        with start_lock:
        
            for k in range(number_of_threads):
                thr = Thread(target=reader)
                thr.start()

            # Ok. All threads have been started. Now, we can
            # send them the start signal

            start_now = True
            start_condition.notifyAll()

        # Must happen in a different `with` block, so that the
        # mutex gets released, and the threads have a chance to
        # read the start signal. Now, wait for all threads to 
        # terminate.

        with start_lock:
            while len(ready_list) < number_of_threads:
                ready_condition.wait()

        # Make sure, that all keys have actually been requested
        # at least once.

        self.assertEqual(set(key_range), set(loads.keys()))

        # The cache has a capacity such, that it can hold all
        # elements nominally ever requested by the readers. So,
        # we expect, that every requested key is loaded exactly
        # once (due to the cache keeping track of what it is 
        # currently loading).

        for key,count in loads.items():
            self.assertEqual(1, count)
            self.assertTrue(key in key_range)



if __name__ == '__main__':
    main()
