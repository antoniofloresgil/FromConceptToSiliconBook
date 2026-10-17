"""Apply explicit, guarded changes to private pinned QEMU/Linux source copies."""
from pathlib import Path
import shutil
import sys

HERE=Path('/opt/hsd')
def replace(path,old,new):
    text=path.read_text()
    if text.count(old)!=1:raise ValueError('Unexpected upstream source: '+str(path))
    path.write_text(text.replace(old,new))

q=Path('/opt/qemu');k=Path('/opt/linux')
if '--kernel' in sys.argv:
    target=k/'drivers/misc/hsd';target.mkdir()
    for name in ['dotproduct-driver.c','dotproduct-uapi.h']:shutil.copyfile(HERE/name,target/name)
    (target/'Makefile').write_text('obj-y += dotproduct-driver.o\n')
    with (k/'drivers/misc/Makefile').open('a') as stream:stream.write('\nobj-y += hsd/\n')
    sys.exit(0)
shutil.copyfile(HERE/'hsd-dotproduct.c',q/'hw/misc/hsd-dotproduct.c')
shutil.copyfile(HERE/'hsd-dotproduct.h',q/'include/hw/misc/hsd-dotproduct.h')
with (q/'hw/misc/meson.build').open('a') as stream:
    stream.write("\nsystem_ss.add(when: 'CONFIG_RISCV_VIRT', if_true: files('hsd-dotproduct.c'))\n")
replace(q/'hw/riscv/virt.c','#include "qemu/osdep.h"',
        '#include "qemu/osdep.h"\n#include "hw/misc/hsd-dotproduct.h"')
replace(q/'hw/riscv/virt.c','    create_platform_bus(s, mmio_irqchip);',
        '    create_platform_bus(s, mmio_irqchip);\n    hsd_dotproduct_create(mmio_irqchip);')
replace(q/'hw/riscv/virt.c','    create_fdt_rtc(s, virt_memmap, irq_mmio_phandle);',
        '    create_fdt_rtc(s, virt_memmap, irq_mmio_phandle);\n    hsd_dotproduct_fdt(MACHINE(s)->fdt, irq_mmio_phandle, phandle++);')
