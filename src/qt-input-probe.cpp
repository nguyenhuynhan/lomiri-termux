#include <QCoreApplication>
#include <QMouseEvent>
#include <QDebug>
#include <QObject>
#include <QVariant>
#include <dlfcn.h>

using Notify = bool (*)(QObject *, QEvent *);
extern "C" bool qt_input_notify(QObject *, QEvent *) __asm__("_ZN16QCoreApplication15notifyInternal2EP7QObjectP6QEvent");
extern "C" bool qt_input_notify(QObject *receiver, QEvent *event)
{
    static auto real = reinterpret_cast<Notify>(dlsym(RTLD_NEXT, "_ZN16QCoreApplication15notifyInternal2EP7QObjectP6QEvent"));
    static unsigned samples = 0;
    static thread_local bool inspecting = false;
    if (!inspecting && samples < 30 &&
        (event->type() == QEvent::MouseButtonPress || event->type() == QEvent::MouseButtonRelease || event->type() == QEvent::MouseMove)) {
        inspecting = true;
        ++samples;
        auto *mouse = static_cast<QMouseEvent *>(event);
        qInfo() << "POC_QT_EVENT" << event->type() << receiver->metaObject()->className()
                << receiver->objectName() << "local" << mouse->localPos()
                << "global" << mouse->screenPos() << "buttons" << mouse->buttons()
                << "enabled" << receiver->property("enabled");
        if (event->type() == QEvent::MouseButtonPress) {
            for (auto *child : receiver->findChildren<QObject *>()) {
                if (child->objectName() == "surfaceItem" || child->objectName() == "surfaceContainer") {
                    qInfo() << "POC_SURFACE_INPUT" << child->objectName() << "enabled" << child->property("enabled")
                            << "visible" << child->property("visible") << "consumes" << child->property("consumesInput")
                            << "size" << child->property("width") << child->property("height");
                }
            }
        }
        inspecting = false;
    }
    return real(receiver, event);
}
