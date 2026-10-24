// QtMir 0.8 posts mouse events to a plain QtEventFeeder QObject. Route those
// events to the shell QWindow through Qt5's private mouse interface. This local
// preload bridge is tied to the Qt/QtMir packages recorded by the build script.
#include <QGuiApplication>
#include <QWindow>
#include <QMouseEvent>
#include <dlfcn.h>
#include <cstring>
#include <cstdio>
#include <cstdlib>
#include <typeinfo>

#define NOTIFY_ENTRY "_ZN16QCoreApplication15notifyInternal2EP7QObjectP6QEvent"
#define MOUSE_ENTRY "_ZN22QWindowSystemInterface16handleMouseEventINS_15DefaultDeliveryEEEbP7QWindowmRK7QPointFS6_6QFlagsIN2Qt11MouseButtonEES9_N6QEvent4TypeES7_INS8_16KeyboardModifierEENS8_16MouseEventSourceE"
using MouseEntry = bool (*)(QWindow *, ulong, const QPointF &, const QPointF &,
                           Qt::MouseButtons, Qt::MouseButton, QEvent::Type,
                           Qt::KeyboardModifiers, Qt::MouseEventSource);

extern "C" bool compat_notify(QObject *, QEvent *) __asm__(NOTIFY_ENTRY);
extern "C" bool compat_notify(QObject *receiver, QEvent *event)
{
    using Notify = bool (*)(QObject *, QEvent *);
    static auto originalNotify = reinterpret_cast<Notify>(dlsym(RTLD_NEXT, NOTIFY_ENTRY));
    if (!originalNotify) {
        std::fputs("Lomiri input bridge: incompatible Qt notifier ABI. Rebuild the bridge.\n", stderr);
        std::abort();
    }
    if (!receiver || !event) return originalNotify(receiver, event);
    const bool pointer = event->type() == QEvent::MouseMove ||
        event->type() == QEvent::MouseButtonPress || event->type() == QEvent::MouseButtonRelease;
    // Exact Itanium RTTI name from the installed QtMir class; no other receivers.
    if (pointer && std::strcmp(typeid(*receiver).name(), "13QtEventFeeder") == 0) {
        auto *mouse = static_cast<QMouseEvent *>(event);
        const auto windows = QGuiApplication::topLevelWindows();
        QWindow *window = windows.size() == 1 ? windows.first() : nullptr;
        if (!window) for (auto *candidate : windows) {
            if (candidate->isVisible() && candidate->geometry().contains(mouse->screenPos().toPoint())) {
                window = candidate;
                break;
            }
        }
        static auto mouseEntry = reinterpret_cast<MouseEntry>(dlsym(RTLD_NEXT, MOUSE_ENTRY));
        if (window && mouseEntry) {
            const QPointF local = mouse->screenPos() - QPointF(window->mapToGlobal(QPoint(0, 0)));
            return mouseEntry(window, mouse->timestamp(), local, mouse->screenPos(),
                              mouse->buttons(), mouse->button(), event->type(),
                              mouse->modifiers(), mouse->source());
        }
    }
    return originalNotify(receiver, event);
}
