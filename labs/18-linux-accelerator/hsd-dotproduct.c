/* SPDX-License-Identifier: MIT
 * Software-visible word-MMIO model, not an AXI or RTL timing model.
 */
#include "qemu/osdep.h"
#include "hw/misc/hsd-dotproduct.h"
#include "hw/qdev-properties.h"
#include "qapi/error.h"
#include "qemu/module.h"
#include "qemu/timer.h"
#include "exec/address-spaces.h"
#include "sysemu/device_tree.h"
#define TYPE_HSD "hsd-dotproduct"
#define BASE 0x10080000
#define POOL 0x88000000ULL
#define LIMIT (POOL + 0x4000)
OBJECT_DECLARE_SIMPLE_TYPE(HSDState, HSD)
struct HSDState {
    SysBusDevice parent_obj;
    MemoryRegion mmio;
    qemu_irq irq;
    QEMUTimer *timer;
    uint32_t a, b, dst, n, status, error, enable;
    uint64_t delay_ns;
    bool drop_irq, dma_error;
};
static void update_irq(HSDState *s)
{ qemu_set_irq(s->irq, !!(s->status & 8) && !s->drop_irq); }
static void finish(HSDState *s, uint32_t error, unsigned reads, unsigned writes)
{
    s->error=error;
    s->status=(error ? 4 : 2) | (s->enable ? 8 : 0);
    /* Writes have completed before DONE / IRQ become visible. */
    update_irq(s);
    fprintf(stderr,"HSD_MODEL n=%u error=%u reads=%u writes=%u\n",s->n,error,reads,writes);
}
static bool valid_range(uint64_t addr, uint64_t bytes)
{ return addr >= POOL && addr + bytes <= LIMIT; }
static void execute(void *opaque)
{
    HSDState *s=opaque;
    int64_t sum=0;
    unsigned i, reads=0;
    uint32_t a,b,word;
    if (s->dma_error) { finish(s,2,0,0); return; }
    for(i=0;i<s->n;i++) {
        if(address_space_read(&address_space_memory,s->a+4*i,MEMTXATTRS_UNSPECIFIED,&a,4)!=MEMTX_OK) {
            finish(s,2,reads,0); return;
        }
        reads++;
        if(address_space_read(&address_space_memory,s->b+4*i,MEMTXATTRS_UNSPECIFIED,&b,4)!=MEMTX_OK) {
            finish(s,2,reads,0); return;
        }
        reads++;
        sum+=(int64_t)(int16_t)le32_to_cpu(a)*(int16_t)le32_to_cpu(b);
    }
    word=cpu_to_le32((uint64_t)sum);
    if(address_space_write(&address_space_memory,s->dst,MEMTXATTRS_UNSPECIFIED,&word,4)!=MEMTX_OK) {
        finish(s,3,reads,0);return;
    }
    word=cpu_to_le32((uint64_t)sum>>32);
    if(address_space_write(&address_space_memory,s->dst+4,MEMTXATTRS_UNSPECIFIED,&word,4)!=MEMTX_OK) {
        finish(s,3,reads,1);return;
    }
    finish(s,0,reads,2);
}
static uint64_t read_mmio(void *opaque, hwaddr addr, unsigned size)
{
    HSDState *s=opaque;
    switch(addr) {
    case 0:return s->enable ? 2:0;case 4:return s->status;
    case 8:return s->a;case 12:return s->b;case 16:return s->dst;
    case 20:return s->n;case 24:return s->error;default:return 0;
    }
}
static void write_mmio(void *opaque, hwaddr addr, uint64_t value, unsigned size)
{
    HSDState *s=opaque;
    if(addr==28) {if(value&1) {s->status&=~8;update_irq(s);}return;}
    if(s->status&1)return; /* Driver serializes jobs; no AXI response-channel model. */
    switch(addr) {
    case 8:s->a=value;return;case 12:s->b=value;return;
    case 16:s->dst=value;return;case 20:s->n=value;return;
    case 0:
        s->enable=!!(value&2);
        if(!(value&1))return;
        s->status=0;s->error=0;update_irq(s);
        if(!s->n || s->n>256 || (s->a&3) || (s->b&3) || (s->dst&7) ||
           !valid_range(s->a,4ULL*s->n) || !valid_range(s->b,4ULL*s->n) || !valid_range(s->dst,8) ||
           (s->dst<(uint64_t)s->a+4*s->n && s->a<(uint64_t)s->dst+8) ||
           (s->dst<(uint64_t)s->b+4*s->n && s->b<(uint64_t)s->dst+8)) {
            finish(s,1,0,0);return;
        }
        s->status=1;
        timer_mod(s->timer,qemu_clock_get_ns(QEMU_CLOCK_VIRTUAL)+s->delay_ns);
    }
}
static const MemoryRegionOps ops={.read=read_mmio,.write=write_mmio,.endianness=DEVICE_LITTLE_ENDIAN,
    .valid={.min_access_size=4,.max_access_size=4,.unaligned=false},
    .impl={.min_access_size=4,.max_access_size=4}};
static void reset_device(DeviceState *dev)
{
    HSDState *s=HSD(dev);timer_del(s->timer);
    s->a=s->b=s->dst=s->n=s->status=s->error=s->enable=0;update_irq(s);
}
static void instance_init(Object *obj)
{
    HSDState *s=HSD(obj);
    memory_region_init_io(&s->mmio,obj,&ops,s,TYPE_HSD,0x20);
    sysbus_init_mmio(SYS_BUS_DEVICE(obj),&s->mmio);
    sysbus_init_irq(SYS_BUS_DEVICE(obj),&s->irq);
    s->timer=timer_new_ns(QEMU_CLOCK_VIRTUAL,execute,s);
}
static Property properties[]={
    DEFINE_PROP_UINT64("delay-ns",HSDState,delay_ns,10000),
    DEFINE_PROP_BOOL("drop-irq",HSDState,drop_irq,false),
    DEFINE_PROP_BOOL("dma-error",HSDState,dma_error,false),DEFINE_PROP_END_OF_LIST()
};
static void class_init(ObjectClass *klass,void *data)
{
    DeviceClass *dc=DEVICE_CLASS(klass);dc->reset=reset_device;
    device_class_set_props(dc,properties);
    dc->desc="HSD signed dot product, word-MMIO teaching model";
    /* This fixed experimental machine does not support migration. */
    dc->user_creatable=false;
}
static const TypeInfo info={.name=TYPE_HSD,.parent=TYPE_SYS_BUS_DEVICE,
    .instance_size=sizeof(HSDState),.instance_init=instance_init,.class_init=class_init};
static void register_types(void) {type_register_static(&info);}
type_init(register_types)
void hsd_dotproduct_create(DeviceState *irqchip)
{
    DeviceState *dev=qdev_new(TYPE_HSD);
    sysbus_realize_and_unref(SYS_BUS_DEVICE(dev),&error_fatal);
    sysbus_mmio_map(SYS_BUS_DEVICE(dev),0,BASE);
    sysbus_connect_irq(SYS_BUS_DEVICE(dev),0,qdev_get_gpio_in(irqchip,20));
}
void hsd_dotproduct_fdt(void *fdt,uint32_t parent,uint32_t pool)
{
    const char *r="/reserved-memory",*p="/reserved-memory/dma-pool@88000000",*d="/soc/dotproduct@10080000";
    qemu_fdt_add_subnode(fdt,r);
    qemu_fdt_setprop_cell(fdt,r,"#address-cells",2);qemu_fdt_setprop_cell(fdt,r,"#size-cells",2);
    qemu_fdt_setprop(fdt,r,"ranges",NULL,0);
    qemu_fdt_add_subnode(fdt,p);qemu_fdt_setprop_string(fdt,p,"compatible","shared-dma-pool");
    qemu_fdt_setprop_cells(fdt,p,"reg",0,(uint32_t)POOL,0,0x4000);
    qemu_fdt_setprop(fdt,p,"no-map",NULL,0);qemu_fdt_setprop_cell(fdt,p,"phandle",pool);
    qemu_fdt_add_subnode(fdt,d);qemu_fdt_setprop_string(fdt,d,"compatible","hsd,dotproduct-v1");
    qemu_fdt_setprop_cells(fdt,d,"reg",0,BASE,0,0x20);
    qemu_fdt_setprop_cell(fdt,d,"interrupt-parent",parent);qemu_fdt_setprop_cell(fdt,d,"interrupts",20);
    qemu_fdt_setprop_cell(fdt,d,"memory-region",pool);
    /* QEMU model reads/writes the same RAM. Not a hardware cache-coherence claim. */
    qemu_fdt_setprop(fdt,d,"dma-coherent",NULL,0);
}
