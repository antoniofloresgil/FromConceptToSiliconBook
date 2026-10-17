// SPDX-License-Identifier: GPL-2.0-only
/* Built-in, one fixed device, no unbind: DMA buffers survive quarantined jobs. */
#include <linux/module.h>
#include <linux/compat.h>
#include <linux/platform_device.h>
#include <linux/of_reserved_mem.h>
#include <linux/dma-mapping.h>
#include <linux/interrupt.h>
#include <linux/completion.h>
#include <linux/iopoll.h>
#include <linux/miscdevice.h>
#include <linux/uaccess.h>
#include <linux/mutex.h>
#include <linux/ktime.h>
#include "dotproduct-uapi.h"
struct hsd_dev {
    struct device *dev;void __iomem *regs;void *buffer;dma_addr_t dma;
    struct miscdevice misc;struct mutex lock;struct completion complete;
    bool quarantined;
};
static irqreturn_t hsd_irq(int irq,void *opaque)
{
    struct hsd_dev *d=opaque;
    if(!(readl(d->regs+4)&8))return IRQ_NONE;
    writel(1,d->regs+28);complete(&d->complete);return IRQ_HANDLED;
}
static long hsd_ioctl(struct file *file,unsigned int cmd,unsigned long arg)
{
    struct miscdevice *misc=file->private_data;
    struct hsd_dev *d=container_of(misc,struct hsd_dev,misc);
    struct hsd_job *job;__le32 *a=d->buffer,*b=d->buffer+1024;
    __le64 *result=d->buffer+2048;
    unsigned i;u32 status;u64 begin;int ret=0;
    if(cmd!=HSD_RUN)return -ENOTTY;
    job=memdup_user((void __user *)arg,sizeof(*job));
    if(IS_ERR(job))return PTR_ERR(job);
    if(!job->length || job->length>256 || (job->flags&~HSD_POLL)) {ret=-EINVAL;goto free;}
    if(mutex_lock_interruptible(&d->lock)) {ret=-ERESTARTSYS;goto free;}
    if(d->quarantined) {ret=-EIO;goto unlock;}
    for(i=0;i<job->length;i++){a[i]=cpu_to_le32(job->a[i]);b[i]=cpu_to_le32(job->b[i]);}
    *result=0;reinit_completion(&d->complete);
    writel(1,d->regs+28);
    writel(lower_32_bits(d->dma),d->regs+8);
    writel(lower_32_bits(d->dma+1024),d->regs+12);
    writel(lower_32_bits(d->dma+2048),d->regs+16);writel(job->length,d->regs+20);
    dma_wmb();begin=ktime_get_ns();writel((job->flags&HSD_POLL)?1:3,d->regs);
    if(job->flags&HSD_POLL)ret=readl_poll_timeout(d->regs+4,status,!(status&1),10,100000);
    else if(!wait_for_completion_timeout(&d->complete,msecs_to_jiffies(100)))ret=-ETIMEDOUT;
    if(ret) {
        /* No hardware abort/reset register: never reuse/free possibly live DMA memory. */
        d->quarantined=true;writel(1,d->regs+28);ret=-ETIMEDOUT;goto unlock;
    }
    status=readl(d->regs+4);dma_rmb();
    job->status=status;job->error=readl(d->regs+24);job->result=le64_to_cpu(*result);
    job->kernel_ns=ktime_get_ns()-begin;
    if(copy_to_user((void __user *)arg,job,sizeof(*job)))ret=-EFAULT;
    else if((status&7)!=2)ret=-EIO;
unlock:mutex_unlock(&d->lock);
free:kfree(job);return ret;
}
static const struct file_operations hsd_fops={.owner=THIS_MODULE,.unlocked_ioctl=hsd_ioctl,
    .compat_ioctl=compat_ptr_ioctl,.open=nonseekable_open};
static int hsd_probe(struct platform_device *pdev)
{
    struct device *dev=&pdev->dev;struct hsd_dev *d;int irq,ret;
    d=devm_kzalloc(dev,sizeof(*d),GFP_KERNEL);if(!d)return -ENOMEM;
    d->dev=dev;mutex_init(&d->lock);init_completion(&d->complete);
    d->regs=devm_platform_ioremap_resource(pdev,0);if(IS_ERR(d->regs))return PTR_ERR(d->regs);
    ret=dma_set_mask_and_coherent(dev,DMA_BIT_MASK(32));if(ret)return ret;
    ret=of_reserved_mem_device_init(dev);if(ret)return dev_err_probe(dev,ret,"reserved DMA pool required\n");
    d->buffer=dma_alloc_coherent(dev,4096,&d->dma,GFP_KERNEL);
    if(!d->buffer) {of_reserved_mem_device_release(dev);return -ENOMEM;}
    if(d->dma<0x88000000ULL || d->dma+4096>0x88004000ULL) {ret=-ERANGE;goto release;}
    irq=platform_get_irq(pdev,0);if(irq<0) {ret=irq;goto release;}
    ret=devm_request_irq(dev,irq,hsd_irq,0,dev_name(dev),d);if(ret)goto release;
    d->misc=(struct miscdevice){.minor=MISC_DYNAMIC_MINOR,.name="dotproduct",.fops=&hsd_fops,.parent=dev,.mode=0600};
    ret=misc_register(&d->misc);if(ret)goto release;
    platform_set_drvdata(pdev,d);
    dev_info(dev,"HSD_DRIVER_READY dma=%pad irq=%d\n",&d->dma,irq);return 0;
release:dma_free_coherent(dev,4096,d->buffer,d->dma);of_reserved_mem_device_release(dev);return ret;
}
static const struct of_device_id matches[]={{.compatible="hsd,dotproduct-v1"},{}};
static struct platform_driver hsd_driver={.probe=hsd_probe,.driver={.name="hsd-dotproduct",.of_match_table=matches,
    .suppress_bind_attrs=true}};
builtin_platform_driver(hsd_driver);
MODULE_LICENSE("GPL");
