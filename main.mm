#import "nexus.h"
#import <UIKit/UIKit.h>
#include <os/log.h>
#include <stdarg.h>

NexusMode g_nexus_mode = NEXUS_MODE_RESEARCH;

// Sistema de logs: escribe en Documents y en os_log
void nexus_log(const char *module, const char *fmt, ...) {
    char buffer[1024];
    va_list args;
    va_start(args, fmt);
    vsnprintf(buffer, sizeof(buffer), fmt, args);
    va_end(args);

    static os_log_t log = NULL;
    if (!log) log = os_log_create("com.nexus.enhanced", "Core");
    os_log_with_type(log, OS_LOG_TYPE_DEFAULT, "[NEXUS][%{public}s] %{public}s", module, buffer);

    // Escritura a archivo de log
    NSString *logPath = [NSHomeDirectory() stringByAppendingPathComponent:@"Documents/NEXUS_LOG.txt"];
    NSString *entry   = [NSString stringWithFormat:@"[NEXUS][%s] %s\n", module, buffer];
    NSFileHandle *fh  = [NSFileHandle fileHandleForWritingAtPath:logPath];
    if (!fh) {
        [@"" writeToFile:logPath atomically:YES encoding:NSUTF8StringEncoding error:nil];
        fh = [NSFileHandle fileHandleForWritingAtPath:logPath];
    }
    [fh seekToEndOfFile];
    [fh writeData:[entry dataUsingEncoding:NSUTF8StringEncoding]];
    [fh closeFile];
}

// Toast visual
void nexus_toast(NSString *msg, UIColor *color) {
    dispatch_async(dispatch_get_main_queue(), ^{
        UIWindow *window = nil;
        if (@available(iOS 13.0, *)) {
            for (UIScene *scene in [UIApplication sharedApplication].connectedScenes) {
                if (scene.activationState == UISceneActivationStateForegroundActive
                    && [scene isKindOfClass:[UIWindowScene class]]) {
                    window = ((UIWindowScene *)scene).windows.firstObject;
                    break;
                }
            }
        }
        if (!window) return;

        UILabel *lbl = [[UILabel alloc] init];
        lbl.text          = msg;
        lbl.textColor     = UIColor.whiteColor;
        lbl.font          = [UIFont boldSystemFontOfSize:12];
        lbl.numberOfLines = 0;
        [lbl sizeToFit];

        UIView *toast = [[UIView alloc] initWithFrame:CGRectMake(0,0,
            lbl.frame.size.width + 32, lbl.frame.size.height + 16)];
        toast.backgroundColor    = color;
        toast.layer.cornerRadius = 12;
        lbl.center = CGPointMake(toast.frame.size.width/2, toast.frame.size.height/2);
        [toast addSubview:lbl];
        toast.center = CGPointMake(window.frame.size.width/2, 80);
        toast.alpha  = 0;
        [window addSubview:toast];

        [UIView animateWithDuration:0.3 animations:^{ toast.alpha = 1; }
                         completion:^(BOOL f){
            [UIView animateWithDuration:0.4 delay:3.5 options:0
                             animations:^{ toast.alpha = 0; }
                             completion:^(BOOL f2){ [toast removeFromSuperview]; }];
        }];
    });
}

__attribute__((constructor))
static void nexus_bootstrap(void) {
    nexus_log("CORE", "NEXUS v%s bootstrapping...", NEXUS_VERSION);

    memory_engine_init();
    hook_engine_init();
    module_analyzer_init();
    exploit_framework_init();
    core_server_init(); // Último: necesita que los módulos estén listos

    dispatch_after(dispatch_time(DISPATCH_TIME_NOW, 5 * NSEC_PER_SEC),
                   dispatch_get_main_queue(), ^{
        extern void nexus_toast(NSString*, UIColor*);
        nexus_toast(@"NEXUS v1.0 Activo\nConecta desde PC al puerto 27042",
                    [UIColor colorWithRed:0.1 green:0.1 blue:0.4 alpha:0.92]);
    });
}
