#include <fcitx/addonfactory.h>
#include <fcitx/addoninstance.h>
#include <fcitx/addonmanager.h>
#include <fcitx/event.h>
#include <fcitx/focusgroup.h>
#include <fcitx/inputcontext.h>
#include <fcitx/inputcontextmanager.h>
#include <fcitx/instance.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <unistd.h>
#include <cstdlib>
#include <cstring>
#include <string>
#include <vector>

// Keep the shell's disabled context from displacing an application's focus.
// This addon never handles keys or text.
class KeyboardFocus final : public fcitx::AddonInstance {
public:
    explicit KeyboardFocus(fcitx::Instance *instance) : instance_(instance) {
        const char *path = std::getenv("LOMIRI_KEYBOARD_EVENT_SOCKET");
        if (!path || std::strlen(path) >= sizeof(address_.sun_path)) {
            return;
        }
        address_.sun_family = AF_UNIX;
        std::strcpy(address_.sun_path, path);
        fd_ = socket(AF_UNIX, SOCK_DGRAM | SOCK_NONBLOCK | SOCK_CLOEXEC, 0);
        handlers_.emplace_back(instance_->watchEvent(
            fcitx::EventType::FocusGroupFocusChanged, fcitx::EventWatcherPhase::PostInputMethod,
            [](fcitx::Event &event) {
                auto &changed = static_cast<fcitx::FocusGroupFocusChangedEvent &>(event);
                auto *current = changed.newFocus();
                if (current && current->program() == "lomiri"
                    && current->capabilityFlags().test(fcitx::CapabilityFlag::Disable)) {
                    auto *previous = changed.oldFocus();
                    if (previous && previous->capabilityFlags().test(fcitx::CapabilityFlag::Disable)) {
                        previous = nullptr;
                    }
                    changed.group()->setFocusedInputContext(previous);
                }
            }));
        for (auto type : {fcitx::EventType::InputContextFocusIn,
                          fcitx::EventType::InputContextFocusOut,
                          fcitx::EventType::InputContextCapabilityChanged}) {
            handlers_.emplace_back(instance_->watchEvent(
                type, fcitx::EventWatcherPhase::PostInputMethod,
                [this, type](fcitx::Event &event) {
                    if (type == fcitx::EventType::InputContextCapabilityChanged) {
                        auto *context = static_cast<fcitx::InputContextEvent &>(event).inputContext();
                        if (context->program() == "lomiri") {
                            if (context->capabilityFlags().test(fcitx::CapabilityFlag::Disable)) {
                                context->focusOut();
                            } else {
                                context->focusIn();
                            }
                        }
                    }
                    bool focused = false;
                    instance_->inputContextManager().foreachFocused([&focused](fcitx::InputContext *context) {
                        focused |= !context->capabilityFlags().test(fcitx::CapabilityFlag::Disable);
                        return true;
                    });
                    std::string payload = std::string("{\"focused\":")
                        + (focused ? "true" : "false") + ",\"request\":"
                        + (type == fcitx::EventType::InputContextFocusIn ? "true" : "false") + "}";
                    sendto(fd_, payload.data(), payload.size(), MSG_NOSIGNAL,
                           reinterpret_cast<sockaddr *>(&address_), sizeof(address_));
                }));
        }
        handlers_.emplace_back(instance_->watchEvent(
            fcitx::EventType::InputContextSwitchInputMethod, fcitx::EventWatcherPhase::PostInputMethod,
            [this](fcitx::Event &event) {
                auto &switched = static_cast<fcitx::InputContextSwitchInputMethodEvent &>(event);
                auto *context = switched.inputContext();
                if (switched.reason() == fcitx::InputMethodSwitchedReason::Other
                    || !context->hasFocus()
                    || context->capabilityFlags().test(fcitx::CapabilityFlag::Disable)) {
                    return;
                }
                auto mode = instance_->inputMethod(context);
                if (mode != "unikey" && mode != "keyboard-us") {
                    return;
                }
                std::string payload = std::string("{\"vietnamese\":")
                    + (mode == "unikey" ? "true}" : "false}");
                sendto(fd_, payload.data(), payload.size(), MSG_NOSIGNAL,
                       reinterpret_cast<sockaddr *>(&address_), sizeof(address_));
            }));
    }
    ~KeyboardFocus() override {
        if (fd_ >= 0) {
            close(fd_);
        }
    }
private:
    fcitx::Instance *instance_;
    int fd_ = -1;
    sockaddr_un address_{};
    std::vector<std::unique_ptr<fcitx::HandlerTableEntry<fcitx::EventHandler>>> handlers_;
};

class KeyboardFocusFactory final : public fcitx::AddonFactory {
public:
    fcitx::AddonInstance *create(fcitx::AddonManager *manager) override {
        return new KeyboardFocus(manager->instance());
    }
};
FCITX_ADDON_FACTORY(KeyboardFocusFactory);
