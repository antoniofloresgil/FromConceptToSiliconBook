/* SPDX-License-Identifier: MIT */
#ifndef HSD_DOTPRODUCT_H
#define HSD_DOTPRODUCT_H
#include "hw/sysbus.h"
void hsd_dotproduct_create(DeviceState *irqchip);
void hsd_dotproduct_fdt(void *fdt, uint32_t parent, uint32_t pool);
#endif
