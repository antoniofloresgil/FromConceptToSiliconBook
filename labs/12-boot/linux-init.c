/* Guided Linux exercise: static PID 1, independent of the supervisor payload. */
#include <stdio.h>
#include <sys/mount.h>
#include <unistd.h>

int main(void) {
    if (getpid() != 1) {
        fputs("Run this program only as the guest's PID 1.\n", stderr);
        return 1;
    }
    if (mount("proc", "/proc", "proc", 0, NULL) != 0 ||
        mount("sysfs", "/sys", "sysfs", 0, NULL) != 0) {
        perror("guest mount");
        for (;;) pause();
    }
    puts("HSD_LINUX_USERSPACE_PASS");
    fflush(stdout);
    for (;;) pause();
}
