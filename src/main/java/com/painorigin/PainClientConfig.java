package com.painorigin;

import net.minecraftforge.common.ForgeConfigSpec;

/**
 * config/painorigin-client.toml - purely visual, per-player settings. Only client classes read these
 * values; the file is registered on both sides because registering is harmless on a dedicated server.
 */
public final class PainClientConfig {
    public static final ForgeConfigSpec SPEC;

    public static final ForgeConfigSpec.BooleanValue PARTICLES_ENABLED;
    public static final ForgeConfigSpec.BooleanValue PARTICLES_REDUCED;
    public static final ForgeConfigSpec.BooleanValue ADDITIVE_BLEND;
    public static final ForgeConfigSpec.DoubleValue PARTICLE_OPACITY;
    public static final ForgeConfigSpec.BooleanValue CAMERA_SHAKE;
    public static final ForgeConfigSpec.DoubleValue CAMERA_SHAKE_STRENGTH;

    static {
        ForgeConfigSpec.Builder b = new ForgeConfigSpec.Builder();

        b.comment("Pain Origin particles on THIS client.").push("particles");
        PARTICLES_ENABLED = b
                .comment("false = never show this mod's particles (the powers keep working).")
                .define("enabled", true);
        PARTICLES_REDUCED = b
                .comment("true = keep only the main sprites (shockwave ring, flash, core) and about one third of the",
                        "decorative ones (energy streaks, vortex, debris). Good for weak PCs.")
                .define("reduced", false);
        ADDITIVE_BLEND = b
                .comment("true = glowing (additive) blending for the energy-like particles.",
                        "false = normal alpha blending; try this if a shader pack makes the effects look washed out.")
                .define("additiveBlend", true);
        PARTICLE_OPACITY = b
                .comment("Overall opacity of this mod's particles (0.1 - 1.0).")
                .defineInRange("opacity", 1.0, 0.1, 1.0);
        b.pop();

        b.comment("Screen shake caused by Shinra Tensei and Chibaku Tensei.").push("camera");
        CAMERA_SHAKE = b
                .comment("false = never shake the camera (recommended if you get motion sick).")
                .define("shake", true);
        CAMERA_SHAKE_STRENGTH = b
                .comment("Strength multiplier of the shake (0 - 2).")
                .defineInRange("shakeStrength", 1.0, 0.0, 2.0);
        b.pop();

        SPEC = b.build();
    }

    private PainClientConfig() {}
}
