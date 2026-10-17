/* SPDX-License-Identifier: MIT */
#ifndef HSD_DOTPRODUCT_UAPI_H
#define HSD_DOTPRODUCT_UAPI_H
#include <linux/types.h>
#include <linux/ioctl.h>
#define HSD_POLL 1u
struct hsd_job {
    __u32 length, flags;
    __u32 a[256],b[256];
    __aligned_u64 result, kernel_ns;
    __u32 status,error;
};
#define HSD_RUN _IOWR('H',0,struct hsd_job)
#endif
