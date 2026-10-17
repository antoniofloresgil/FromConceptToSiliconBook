/* SPDX-License-Identifier: MIT
 * PID 1 + userspace regression; time values describe an emulated platform.
 */
#define _GNU_SOURCE
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/ioctl.h>
#include <sys/mount.h>
#include <sys/reboot.h>
#include <time.h>
#include "dotproduct-uapi.h"
static struct hsd_job job;
static void fail(const char *s) {printf("HSD_LINUX_ACCEL_FAIL %s errno=%d\n",s,errno);reboot(RB_POWER_OFF);for(;;)pause();}
static uint64_t now(void){struct timespec t;clock_gettime(CLOCK_MONOTONIC,&t);return (uint64_t)t.tv_sec*1000000000+t.tv_nsec;}
static __attribute__((noinline)) int64_t reference(unsigned n)
{
    int64_t sum=0;unsigned i;
    for(i=0;i<n;i++) {
        int32_t a=job.a[i]&65535,b=job.b[i]&65535;
        if(a>=32768)a-=65536;if(b>=32768)b-=65536;
        sum+=(int64_t)a*b;
    }
    return sum;
}
int main(void)
{
    int fd,cmdline,ret;char mode[2048]={0};unsigned i,k,poll;const unsigned sizes[]={1,8,32,128,256};
    setbuf(stdout,NULL);
    if(mount("devtmpfs","/dev","devtmpfs",0,NULL) || mount("proc","/proc","proc",0,NULL) || mount("sysfs","/sys","sysfs",0,NULL))fail("mount");
    cmdline=open("/proc/cmdline",O_RDONLY);if(cmdline<0)fail("cmdline");read(cmdline,mode,sizeof(mode)-1);close(cmdline);
    fd=open("/dev/dotproduct",O_RDWR);if(fd<0)fail("driver device");
    for(i=0;i<256;i++){job.a[i]=0xdead0000u|((i*997u+32768u)&65535u);job.b[i]=0xbeef0000u|((i*313u+32768u)&65535u);}
    job.length=32;
    if(strstr(mode,"hsd.test=timeout")) {
        ret=ioctl(fd,HSD_RUN,&job);if(ret!=-1 || errno!=ETIMEDOUT)fail("expected timeout");
        ret=ioctl(fd,HSD_RUN,&job);if(ret!=-1 || errno!=EIO)fail("timeout quarantine");
        puts("HSD_TIMEOUT_QUARANTINE_PASS");goto done;
    }
    if(strstr(mode,"hsd.test=dma-error")) {
        ret=ioctl(fd,HSD_RUN,&job);if(ret!=-1 || errno!=EIO || job.error!=2)fail("expected DMA error");
        puts("HSD_DMA_ERROR_PASS");goto done;
    }
    for(poll=0;poll<2;poll++)for(k=0;k<5;k++) {
        uint64_t begin,sw,end,total;volatile int64_t expected;
        job.length=sizes[k];job.flags=poll?HSD_POLL:0;
        begin=now();expected=reference(job.length);sw=now()-begin;
        begin=now();ret=ioctl(fd,HSD_RUN,&job);end=now();total=end-begin;
        if(ret || (int64_t)job.result!=expected || (job.status&7)!=2 || job.error) {
            printf("HSD_RESULT_DIAGNOSTIC mode=%s n=%u ret=%d status=%#x error=%u result=%#llx expected=%#llx a0=%#x b0=%#x\n",
                   poll?"poll":"irq",job.length,ret,job.status,job.error,
                   (unsigned long long)job.result,(unsigned long long)expected,job.a[0],job.b[0]);
            fail("arithmetic/status");
        }
        printf("HSD_METRIC mode=%s n=%u software_ns=%llu end_to_end_ns=%llu kernel_ns=%llu\n",poll?"poll":"irq",job.length,
               (unsigned long long)sw,(unsigned long long)total,(unsigned long long)job.kernel_ns);
    }
    job.length=0;if(ioctl(fd,HSD_RUN,&job)!=-1 || errno!=EINVAL)fail("zero length");
    job.length=257;if(ioctl(fd,HSD_RUN,&job)!=-1 || errno!=EINVAL)fail("excess length");
    job.length=1;job.flags=2;if(ioctl(fd,HSD_RUN,&job)!=-1 || errno!=EINVAL)fail("flags");
    if(ioctl(fd,HSD_RUN,(void *)1)!=-1 || errno!=EFAULT)fail("user pointer");
    if(ioctl(fd,0,&job)!=-1 || errno!=ENOTTY)fail("unknown ioctl");
    puts("HSD_LINUX_ACCEL_PASS");
done:close(fd);reboot(RB_POWER_OFF);for(;;)pause();
}
