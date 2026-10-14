# 03 — Transaction pipelines

Run `python labs/run.py run transport`. Tools: Icarus; prerequisite: independent request/response ownership and ready/valid stability.

Tests run queue depths 2, 3 and 8, including non-power-of-two pointer wrap. Each configuration checks 500 memory operations and 5000 FIFO cycles. A stopped consumer fills both queues and the retained service response; maximum outstanding count must reach `2*depth+1`. Read/write tags and byte data are checked in order, stalled outputs remain stable, and an already applied write persists across protocol reset.

The delayed-memory engine executes one operation at a time. Queue depth is not execution concurrency. Measure acceptance and completion separately using waveforms or additional counters.

Exercise: implement a genuinely pipelined read engine with reserved response capacity. Demonstrate that an indefinitely paused consumer cannot cause an in-flight result to disappear. Explain the full-FIFO recovery bubble before optimizing it.
