class CacheModel:
    def __init__(self, sets=4, ways=1, line_bytes=16, memory=None):
        assert sets > 0 and sets & (sets - 1) == 0
        assert ways > 0
        assert line_bytes >= 4 and line_bytes & (line_bytes - 1) == 0
        self.sets, self.ways, self.line_bytes = sets, ways, line_bytes
        self.words = line_bytes // 4
        self.memory = {} if memory is None else memory
        self.rows = [[dict(tag=None, dirty=False, age=0,
                           data=[0] * self.words)
                      for _ in range(ways)] for _ in range(sets)]
        self.clock = self.hits = self.misses = self.writebacks = 0

    def _writeback(self, index, line):
        if line['tag'] is None or not line['dirty']:
            return
        old_block = line['tag'] * self.sets + index
        base = old_block * self.line_bytes
        for word, value in enumerate(line['data']):
            self.memory[base + 4 * word] = value
        line['dirty'] = False
        self.writebacks += 1

    def access(self, address, value=None, mask=0xF):
        if address < 0 or address >= 2**32 or address % 4:
            raise ValueError('aligned 32-bit address required')
        if not 0 <= mask <= 0xF:
            raise ValueError('four byte strobes required')
        block = address // self.line_bytes
        index, tag = block % self.sets, block // self.sets
        row = self.rows[index]
        self.clock += 1
        line = next(
            (entry for entry in row if entry['tag'] == tag), None)
        if line is not None:
            self.hits += 1
        else:
            self.misses += 1
            line = next(
                (entry for entry in row if entry['tag'] is None), None)
            if line is None:
                line = min(row, key=lambda entry: entry['age'])
            self._writeback(index, line)
            base = block * self.line_bytes
            line.update(tag=tag, dirty=False,
                        data=[self.memory.get(base + 4*i, 0)
                              for i in range(self.words)])
        word = (address % self.line_bytes) // 4
        if value is not None and mask:
            bits = sum(0xFF << (8*b) for b in range(4) if mask & (1 << b))
            line['data'][word] = ((line['data'][word] & ~bits) |
                                  (value & bits)) & 0xFFFFFFFF
            line['dirty'] = True
        line['age'] = self.clock
        return line['data'][word]

    def clean(self):
        for index, row in enumerate(self.rows):
            for line in row:
                self._writeback(index, line)

    def invalidate(self):
        if any(line['dirty'] for row in self.rows for line in row):
            raise RuntimeError('clean dirty lines before invalidation')
        for row in self.rows:
            for line in row:
                line['tag'] = None


if __name__ == '__main__':
    for label, sets, ways in [('direct', 4, 1), ('two-way', 2, 2)]:
        cache = CacheModel(sets, ways)
        cache.access(0x100)
        cache.access(0x104)
        cache.access(0x100, 0xDEADBEEF)
        cache.access(0x140)
        assert cache.access(0x100) == 0xDEADBEEF
        print(label, cache.hits, cache.misses, cache.writebacks)
        cache.clean()
        assert cache.memory[0x100] == 0xDEADBEEF
        cache.invalidate()
