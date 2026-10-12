#pragma once

#include <memory>
#include <rex/rex_app.h>
#include <rex/ui/windowed_app_context.h>

class BlackOps1App : public rex::ReXApp {
public:
    using rex::ReXApp::ReXApp;

    static std::unique_ptr<rex::ui::WindowedApp> Create(
        rex::ui::WindowedAppContext& ctx) {
        return std::unique_ptr<BlackOps1App>(
            new BlackOps1App(
                ctx,
                "blackops1",
                PPCImageConfig
            )
        );
    }
};
