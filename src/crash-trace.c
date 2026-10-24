/* Diagnostic preload for a PRoot tracee, where another ptrace debugger may conflict.
 * Activated only by scripts/trace-crash.sh; not part of the normal launch path. */
#define _GNU_SOURCE
#include <dlfcn.h>
#include <execinfo.h>
#include <signal.h>
#include <stdio.h>
#include <unistd.h>

static int (*real_sigaction)(int, const struct sigaction *, struct sigaction *);

static void crash_trace(int sig, siginfo_t *info, void *context)
{
    (void)context;
    void *frames[64];
    dprintf(STDERR_FILENO, "\nLOMIRI_CRASH_TRACE signal=%d address=%p\n", sig, info->si_addr);
    int count = backtrace(frames, 64);
    backtrace_symbols_fd(frames, count, STDERR_FILENO);
    _exit(128 + sig);
}

int sigaction(int sig, const struct sigaction *action, struct sigaction *old_action)
{
    if (!real_sigaction) real_sigaction = dlsym(RTLD_NEXT, "sigaction");
    if (!real_sigaction) _exit(125);
    if (action && (sig == SIGSEGV || sig == SIGABRT)) {
        struct sigaction traced = *action;
        traced.sa_sigaction = crash_trace;
        traced.sa_flags = SA_SIGINFO | SA_RESETHAND;
        return real_sigaction(sig, &traced, old_action);
    }
    return real_sigaction(sig, action, old_action);
}

__attribute__((constructor)) static void init_trace(void)
{
    real_sigaction = dlsym(RTLD_NEXT, "sigaction");
    void *frames[4];
    backtrace(frames, 4); /* Preload unwinder before the crash handler needs it. */
    struct sigaction action = {0};
    sigemptyset(&action.sa_mask);
    action.sa_sigaction = crash_trace;
    action.sa_flags = SA_SIGINFO | SA_RESETHAND;
    real_sigaction(SIGSEGV, &action, NULL);
    real_sigaction(SIGABRT, &action, NULL);
}
