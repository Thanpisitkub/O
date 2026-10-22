package com.painorigin;

import com.mojang.logging.LogUtils;
import net.minecraft.resources.ResourceLocation;
import net.minecraftforge.eventbus.api.IEventBus;
import net.minecraftforge.fml.ModLoadingContext;
import net.minecraftforge.fml.common.Mod;
import net.minecraftforge.fml.config.ModConfig;
import net.minecraftforge.fml.javafmlmod.FMLJavaModLoadingContext;
import org.slf4j.Logger;

/**
 * Deva Path (Six Paths of Pain) - Java add-on.
 *
 * <p>The powers themselves are data-driven Origins/Apoli JSON (see {@code data/painorigin/powers}).
 * This class only wires up what JSON cannot do: custom particle types, sound events (Apoli's
 * {@code play_sound} needs registered events), the {@code /painorigin} helper command used by the
 * JSON powers, the phased Chibaku Tensei, and the two config files.
 *
 * <p>There is deliberately NO compile-time dependency on Origins/Apoli/Calio: the add-on talks to the
 * JSON powers only through the {@code /painorigin} command, which Apoli's {@code execute_command}
 * action runs.
 */
@Mod(PainOrigin.MODID)
public class PainOrigin {
    public static final String MODID = "painorigin";
    public static final Logger LOGGER = LogUtils.getLogger();

    public PainOrigin() {
        IEventBus modBus = FMLJavaModLoadingContext.get().getModEventBus();
        ModParticles.PARTICLES.register(modBus);
        ModSounds.SOUNDS.register(modBus);

        // config/painorigin-common.toml  : gameplay + server-side particle settings (read by the server)
        // config/painorigin-client.toml  : per-player visual settings (particles / camera shake)
        ModLoadingContext.get().registerConfig(ModConfig.Type.COMMON, PainConfig.SPEC, "painorigin-common.toml");
        ModLoadingContext.get().registerConfig(ModConfig.Type.CLIENT, PainClientConfig.SPEC, "painorigin-client.toml");
    }

    public static ResourceLocation id(String path) {
        return new ResourceLocation(MODID, path);
    }
}
