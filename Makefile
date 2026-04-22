TARGET := iphone:clang:latest:16.0
ARCHS := arm64
DEBUG := 0
FINALPACKAGE := 1

include $(THEOS)/makefiles/common.mk

TWEAK_NAME := nexus
nexus_FILES := src/main.mm \
               src/core_server.mm \
               src/memory_engine.mm \
               src/hook_engine.mm \
               src/module_analyzer.mm \
               src/exploit_framework.mm

nexus_CFLAGS := -fobjc-arc -fno-modules \
                -Wno-deprecated-declarations \
                -Wno-unused-variable \
                -std=c++17

nexus_FRAMEWORKS := UIKit Foundation Security
nexus_LIBRARIES  := z

include $(THEOS_MAKE_PATH)/tweak.mk
