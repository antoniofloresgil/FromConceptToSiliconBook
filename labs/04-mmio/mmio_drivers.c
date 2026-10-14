#include <stdint.h>
#define UART_BASE 0x10000000u
#define UART8(off) (*(volatile uint8_t *)(uintptr_t)(UART_BASE + (off)))
#define MMIO32(addr) (*(volatile uint32_t *)(uintptr_t)(addr))

static inline void io_fence(void) {
  __asm__ volatile ("fence iorw, iorw" ::: "memory");
}

int uart_init_divisor(uint16_t divisor) {
  if (divisor == 0) return -1;
  UART8(3) = 0x03; // DLAB off
  io_fence();
  UART8(1) = 0; // disable local interrupts
  io_fence();
  UART8(3) = 0x83; // 8N1, divisor bank
  io_fence();
  UART8(0) = (uint8_t)divisor;
  UART8(1) = (uint8_t)(divisor >> 8);
  io_fence();
  UART8(3) = 0x03;
  io_fence();
  UART8(2) = 0x07; // enable and clear FIFOs
  io_fence();
  return 0;
}

int uart_send_byte(uint8_t byte, unsigned poll_budget) {
  while (poll_budget--) {
    uint8_t status = UART8(5);
    if (status & 0x20) { // THRE
      io_fence();
      UART8(0) = byte;
      io_fence();
      return 0;
    }
  }
  return -1;
}

int uart_try_receive(uint8_t *byte, uint8_t *errors) {
  uint8_t status = UART8(5);
  *errors = status & 0x1E;
  if (!(status & 1)) return 0;
  io_fence();
  *byte = UART8(0); // consumes one available byte
  io_fence();
  return 1;
}

#define SPI_BASE 0x10040000u
#define SPI_TXDATA (SPI_BASE + 0x48u)
#define SPI_RXDATA (SPI_BASE + 0x4Cu)
#define FIFO_FLAG 0x80000000u

int spi_transfer_byte(uint8_t tx, uint8_t *rx, unsigned poll_budget) {
  while (poll_budget && (MMIO32(SPI_TXDATA) & FIFO_FLAG))
    --poll_budget;
  if (!poll_budget) return -1;
  io_fence();
  MMIO32(SPI_TXDATA) = tx;
  io_fence();
  while (poll_budget--) {
    uint32_t result = MMIO32(SPI_RXDATA);
    io_fence();
    if (!(result & FIFO_FLAG)) {
      *rx = (uint8_t)result;
      return 0;
    }
  }
  return -1;
}
