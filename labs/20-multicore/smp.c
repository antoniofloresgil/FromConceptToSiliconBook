/* SPDX-License-Identifier: MIT
 * Two Linux CPUs, release/acquire ownership and the unchanged Lab 18 DMA ABI.
 */
#define _GNU_SOURCE
#include <stdatomic.h>
#include <stdalign.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <sched.h>
#include <signal.h>
#include <errno.h>
#include <sys/ioctl.h>
#include <sys/mman.h>
#include <sys/mount.h>
#include <sys/reboot.h>
#include <sys/wait.h>
#include <time.h>
#include "dotproduct-uapi.h"

enum { JOBS=64, CONTEND=16 };
struct shared {
  alignas(64) atomic_uint request;
  alignas(64) atomic_uint completed;
  alignas(64) atomic_uint contenders;
  atomic_uint contenders_done;
  uint64_t contention_begin[2],contention_end[2];
  alignas(64) struct hsd_job job;
};
_Static_assert(ATOMIC_INT_LOCK_FREE==2,"Shared publication needs lock-free atomics");
static void fail(const char *reason)
{
  printf("HSD_MULTICORE_FAIL pid=%d %s errno=%d\n",getpid(),reason,errno);
  if(getpid()==1){reboot(RB_POWER_OFF);for(;;)pause();}
  _exit(1);
}
static uint64_t now(void)
{
  struct timespec t;if(clock_gettime(CLOCK_MONOTONIC,&t))fail("clock");
  return (uint64_t)t.tv_sec*1000000000+t.tv_nsec;
}
static void pin(int cpu)
{
  cpu_set_t set;CPU_ZERO(&set);CPU_SET(cpu,&set);
  if(sched_setaffinity(0,sizeof(set),&set) || sched_getcpu()!=cpu)fail("affinity");
}
static void wait_epoch(atomic_uint *flag,unsigned epoch)
{
  uint64_t deadline=now()+5000000000ULL;
  while(atomic_load_explicit(flag,memory_order_acquire)!=epoch){
    if(now()>deadline)fail("publication deadline");
    sched_yield();
  }
}
static int64_t fill(struct hsd_job *job,unsigned epoch,unsigned n,unsigned poll)
{
  int64_t expected=0;*job=(struct hsd_job){.length=n,.flags=poll?HSD_POLL:0};
  for(unsigned i=0;i<n;i++){
    int32_t a=(int32_t)((epoch*11939u+i*997u+32768u)&65535u);
    int32_t b=(int32_t)((epoch*313u+i*113u+32768u)&65535u);
    if(a>=32768)a-=65536;if(b>=32768)b-=65536;
    job->a[i]=0xdead0000u|((uint32_t)a&65535u);
    job->b[i]=0xbeef0000u|((uint32_t)b&65535u);
    expected+=(int64_t)a*b;
  }
  return expected;
}
static void check_job(int fd,struct hsd_job *job,int cpu)
{
  if(sched_getcpu()!=cpu)fail("CPU migration");
  if(ioctl(fd,HSD_RUN,job) || (job->status&7)!=2 || job->error)fail("DMA/status");
}
static void contend(int fd,int cpu,struct shared *s)
{
  struct hsd_job job;
  atomic_fetch_add_explicit(&s->contenders,1,memory_order_acq_rel);
  wait_epoch(&s->contenders,2);
  s->contention_begin[cpu]=now();
  for(unsigned i=0;i<CONTEND;i++){
    int64_t expected=fill(&job,1000+cpu*CONTEND+i,32,i&1);
    check_job(fd,&job,cpu);
    if((int64_t)job.result!=expected)fail("contending result");
  }
  s->contention_end[cpu]=now();
  atomic_fetch_or_explicit(&s->contenders_done,1u<<cpu,memory_order_release);
}
int main(void)
{
  setbuf(stdout,NULL);
  if(mount("devtmpfs","/dev","devtmpfs",0,NULL) || mount("proc","/proc","proc",0,NULL)
     || mount("sysfs","/sys","sysfs",0,NULL))fail("mount");
  if(sysconf(_SC_NPROCESSORS_ONLN)!=2)fail("two online CPUs required");
  struct shared *s=mmap(NULL,sizeof(*s),PROT_READ|PROT_WRITE,MAP_SHARED|MAP_ANONYMOUS,-1,0);
  if(s==MAP_FAILED)fail("shared allocation");
  atomic_init(&s->request,0);atomic_init(&s->completed,0);
  atomic_init(&s->contenders,0);atomic_init(&s->contenders_done,0);
  if(!atomic_is_lock_free(&s->request) || !atomic_is_lock_free(&s->completed))fail("lock-free publication");
  int fd=open("/dev/dotproduct",O_RDWR);if(fd<0)fail("accelerator");
  pin(0);printf("HSD_SMP_READY online=2 producer_cpu=%d\n",sched_getcpu());
  pid_t child=fork();if(child<0)fail("fork");
  if(!child){
    pin(1);
    for(unsigned epoch=1;epoch<=JOBS;epoch++){
      wait_epoch(&s->request,epoch);
      uint64_t start=now();check_job(fd,&s->job,1);uint64_t elapsed=now()-start;
      printf("HSD_SMP_JOB epoch=%u cpu=%d n=%u mode=%s ioctl_ns=%llu\n",epoch,sched_getcpu(),
             s->job.length,(s->job.flags&HSD_POLL)?"poll":"irq",(unsigned long long)elapsed);
      atomic_store_explicit(&s->completed,epoch,memory_order_release);
    }
    contend(fd,1,s);close(fd);_exit(0);
  }
  const unsigned lengths[]={1,8,32,128,256};uint64_t start=now();
  for(unsigned epoch=1;epoch<=JOBS;epoch++){
    int64_t expected=fill(&s->job,epoch,lengths[(epoch-1)%5],epoch&1);
    atomic_store_explicit(&s->request,epoch,memory_order_release);
    wait_epoch(&s->completed,epoch);
    if(sched_getcpu()!=0 || (int64_t)s->job.result!=expected)fail("published result");
  }
  uint64_t handoff_ns=now()-start;contend(fd,0,s);
  wait_epoch(&s->contenders_done,3);
  uint64_t latest_start=s->contention_begin[0]>s->contention_begin[1]?s->contention_begin[0]:s->contention_begin[1];
  uint64_t earliest_end=s->contention_end[0]<s->contention_end[1]?s->contention_end[0]:s->contention_end[1];
  if(latest_start>=earliest_end)fail("caller phases did not overlap");
  int status;if(waitpid(child,&status,0)!=child || !WIFEXITED(status) || WEXITSTATUS(status))fail("worker status");
  FILE *interrupts=fopen("/proc/interrupts","r");if(!interrupts)fail("interrupt counts");
  int found_irq=0;char line[512];while(fgets(line,sizeof(line),interrupts))
    if(strstr(line,"dotproduct")){printf("HSD_SMP_IRQ_COUNTS %s",line);found_irq=1;}
  fclose(interrupts);
  if(!found_irq)fail("interrupt accounting");
  printf("HSD_SMP_CONTENTION_PASS cpu0_jobs=16 cpu1_jobs=16\n");
  printf("HSD_SMP_OVERLAP ns=%llu\n",(unsigned long long)(earliest_end-latest_start));
  printf("HSD_SMP_METRIC handoffs=64 elapsed_ns=%llu\n",(unsigned long long)handoff_ns);
  puts("HSD_MULTICORE_PASS jobs=96 producer_cpu=0 worker_cpu=1");
  close(fd);reboot(RB_POWER_OFF);for(;;)pause();
}
