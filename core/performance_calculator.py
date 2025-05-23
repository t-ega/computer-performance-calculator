import multiprocessing
import os
import time
import tracemalloc
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from datetime import datetime

import psutil

from core.utils import PerformanceMetrics


class PerformanceCalculator:
    """High-performance calculator with different processing paradigms"""

    @staticmethod
    def calculate_chunk(start: int, end: int) -> float:
        result = 0.0
        for k in range(start, end + 1):
            result += 1.0 / (k * k)
        return result

    @staticmethod
    def calculate_sequential(i: int, j: int) -> PerformanceMetrics:
        """Sequential processing implementation"""
        process = psutil.Process()

        # Start monitoring
        tracemalloc.start()
        start_time = time.time()
        start_cpu_time = time.process_time()
        cpu_percent_start = process.cpu_percent()

        # Perform calculation
        result = 0.0
        for k in range(i, j + 1):
            result += 1.0 / (k * k)

        # End monitoring
        end_time = time.time()
        end_cpu_time = time.process_time()
        current, peak_memory = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        # Get CPU utilization
        cpu_percent_end = process.cpu_percent()
        cpu_utilization = max(cpu_percent_start, cpu_percent_end)

        return PerformanceMetrics(
            timestamp=datetime.now().isoformat(),
            lower_bound=i,
            upper_bound=j,
            processing_mode="sequential",
            execution_time=end_time - start_time,
            cpu_time=end_cpu_time - start_cpu_time,
            memory_usage=peak_memory / 1024 / 1024,  # Convert to MB
            cpu_utilization=cpu_utilization,
            result_value=result,
            cores_used=1
        )

    @staticmethod
    def calculate_threading(i: int, j: int) -> PerformanceMetrics:
        """Multithreading implementation"""
        process = psutil.Process()
        num_threads = min(os.cpu_count(), 8)  # Limit threads

        # Start monitoring
        tracemalloc.start()
        start_time = time.time()
        start_cpu_time = time.process_time()
        cpu_percent_start = process.cpu_percent()

        # Calculate chunk size
        total_range = j - i + 1
        chunk_size = max(1, total_range // num_threads)

        def worker(start: int, end: int) -> float:
            return PerformanceCalculator.calculate_chunk(start, end)

        result = 0.0
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = []
            for t in range(num_threads):
                chunk_start = i + t * chunk_size
                chunk_end = min(chunk_start + chunk_size - 1, j)
                if chunk_start <= j:
                    futures.append(executor.submit(worker, chunk_start, chunk_end))

            for future in futures:
                result += future.result()

        end_time = time.time()
        end_cpu_time = time.process_time()
        current, peak_memory = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        cpu_percent_end = process.cpu_percent()
        cpu_utilization = max(cpu_percent_start, cpu_percent_end)

        return PerformanceMetrics(
            timestamp=datetime.now().isoformat(),
            lower_bound=i,
            upper_bound=j,
            processing_mode="threading",
            execution_time=end_time - start_time,
            cpu_time=end_cpu_time - start_cpu_time,
            memory_usage=peak_memory / 1024 / 1024,
            cpu_utilization=cpu_utilization,
            result_value=result,
            cores_used=num_threads
        )

    @staticmethod
    def calculate_multiprocessing(i: int, j: int) -> PerformanceMetrics:
        """Multiprocessing implementation (manual process spawning)"""
        process = psutil.Process()
        num_processes = min(os.cpu_count(), 8)

        tracemalloc.start()
        start_time = time.time()
        start_cpu_time = time.process_time()
        cpu_percent_start = process.cpu_percent()

        def cpu_bound_task(start, end, result_list):
            partial = 0.0
            for k in range(start, end + 1):
                partial += 1.0 / (k * k)
            result_list.append(partial)

        total_range = j - i + 1
        chunk_size = max(1, total_range // num_processes)

        with multiprocessing.Manager() as manager:
            result_list = manager.list()
            processes = []

            for p in range(num_processes):
                chunk_start = i + p * chunk_size
                chunk_end = min(chunk_start + chunk_size - 1, j)
                if chunk_start <= j:
                    proc = multiprocessing.Process(target=cpu_bound_task, args=(chunk_start, chunk_end, result_list))
                    processes.append(proc)
                    proc.start()

            for proc in processes:
                proc.join()

            result = sum(result_list)

        # End monitoring
        end_time = time.time()
        end_cpu_time = time.process_time()
        current, peak_memory = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        cpu_percent_end = process.cpu_percent()
        cpu_utilization = max(cpu_percent_start, cpu_percent_end)

        return PerformanceMetrics(
            timestamp=datetime.now().isoformat(),
            lower_bound=i,
            upper_bound=j,
            processing_mode="multiprocessing",
            execution_time=end_time - start_time,
            cpu_time=end_cpu_time - start_cpu_time,
            memory_usage=peak_memory / 1024 / 1024,
            cpu_utilization=cpu_utilization,
            result_value=result,
            cores_used=num_processes
        )