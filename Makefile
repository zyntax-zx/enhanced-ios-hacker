include $(THEOS)/makefiles/common.mk

TWEAK_NAME = enhanced-ios-hacker
enhanced-ios-hacker_FILES = main.cpp \
    core_server/server.cpp \
    hook_engine/hook_engine.cpp \
    memory_engine/memory_engine.cpp \
    exploit_framework/exploit_framework.cpp \
    overlay/imgui_overlay.mm \
    utils/utils.cpp

enhanced-ios-hacker_CFLAGS = -fobjc-arc -std=c++20 -I$(THEOS)/vendor/orion/fishhook
enhanced-ios-hacker_LDFLAGS = -framework Metal -framework UIKit -framework Foundation

include $(THEOS_MAKE_PATH)/tweak.mk

after-package::
	@echo "✅ enhanced-ios-hacker.dylib compilado correctamente"