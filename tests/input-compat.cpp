// Real Qt delivery probe: feeder -> QWindow, preserving coordinates/buttons;
// unrelated QObject receivers must still receive their events.
#include <QGuiApplication>
#include <QMouseEvent>
#include <QWindow>
#include <cstdio>

class QtEventFeeder : public QObject {};
class OtherReceiver : public QObject {
public:
    int events = 0;
    bool event(QEvent *e) override {
        if (e->type() == QEvent::MouseButtonPress || e->type() == QEvent::User) { ++events; return true; }
        return QObject::event(e);
    }
};
class ProbeWindow : public QWindow {
public:
    int presses = 0, releases = 0;
    bool correct = true;
    bool event(QEvent *e) override {
        if (e->type() == QEvent::MouseButtonPress || e->type() == QEvent::MouseButtonRelease) {
            auto *mouse = static_cast<QMouseEvent *>(e);
            const bool pressed = e->type() == QEvent::MouseButtonPress;
            if (pressed) ++presses; else ++releases;
            correct &= mouse->localPos() == QPointF(70.5, 80.25) && mouse->button() == Qt::LeftButton &&
                mouse->buttons() == (pressed ? Qt::LeftButton : Qt::NoButton) && mouse->modifiers() == Qt::ShiftModifier;
            return true;
        }
        return QWindow::event(e);
    }
};
int main(int argc, char **argv) {
    QGuiApplication app(argc, argv);
    ProbeWindow window;
    window.setGeometry(20, 30, 200, 200);
    window.show();
    app.processEvents();
    QtEventFeeder feeder;
    OtherReceiver other;
    const QPointF global = QPointF(window.mapToGlobal(QPoint(0, 0))) + QPointF(70.5, 80.25);
    for (auto type : {QEvent::MouseButtonPress, QEvent::MouseButtonRelease}) {
        app.postEvent(&feeder, new QMouseEvent(type, QPointF(1, 2), global, Qt::LeftButton,
            type == QEvent::MouseButtonPress ? Qt::LeftButton : Qt::NoButton, Qt::ShiftModifier));
        app.processEvents();
        app.processEvents();
    }
    app.postEvent(&other, new QMouseEvent(QEvent::MouseButtonPress, QPointF(4, 5), Qt::LeftButton, Qt::LeftButton, Qt::NoModifier));
    app.postEvent(&other, new QEvent(QEvent::User));
    app.processEvents();
    if (window.presses != 1 || window.releases != 1 || !window.correct || other.events != 2) {
        std::fprintf(stderr, "FAIL delivery: presses=%d releases=%d coords/buttons=%d unrelated=%d\n",
                     window.presses, window.releases, window.correct, other.events);
        return 1;
    }
    std::puts("PASS: Qt window receives press/release and fractional coordinates; unrelated receivers pass through.");
}
