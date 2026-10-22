package com.painorigin;

import java.util.List;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.sounds.SoundEvent;
import net.minecraftforge.registries.DeferredRegister;
import net.minecraftforge.registries.ForgeRegistries;
import net.minecraftforge.registries.RegistryObject;

/**
 * Sound events. The event ids ARE referenced by the JSON powers ({@code apoli:play_sound}), which
 * look them up in the sound-event registry, so they must be registered here even though the
 * {@code assets/painorigin/sounds.json} file also declares them.
 *
 * <p>Six sound groups: Shinra Tensei charge / release / shockwave, Bansho Ten'in pull,
 * Chibaku Tensei (core, debris, collapse) and Universal Defense.
 */
public final class ModSounds {
    public static final DeferredRegister<SoundEvent> SOUNDS =
            DeferredRegister.create(ForgeRegistries.SOUND_EVENTS, PainOrigin.MODID);

    public static final RegistryObject<SoundEvent> SHINRA_CHARGE = reg("shinra_tensei.charge");
    public static final RegistryObject<SoundEvent> SHINRA_RELEASE = reg("shinra_tensei.release");
    public static final RegistryObject<SoundEvent> SHINRA_SHOCKWAVE = reg("shinra_tensei.shockwave");
    public static final RegistryObject<SoundEvent> BANSHO_PULL = reg("bansho_tenin.pull");
    public static final RegistryObject<SoundEvent> CHIBAKU_CORE = reg("chibaku_tensei.core");
    public static final RegistryObject<SoundEvent> CHIBAKU_DEBRIS = reg("chibaku_tensei.debris");
    public static final RegistryObject<SoundEvent> CHIBAKU_COLLAPSE = reg("chibaku_tensei.collapse");
    public static final RegistryObject<SoundEvent> DEFENSE_BLOCK = reg("universal_defense.block");

    /** Every sound event of this mod (used by the self-test command). */
    public static final List<RegistryObject<SoundEvent>> ALL = List.of(
            SHINRA_CHARGE, SHINRA_RELEASE, SHINRA_SHOCKWAVE, BANSHO_PULL,
            CHIBAKU_CORE, CHIBAKU_DEBRIS, CHIBAKU_COLLAPSE, DEFENSE_BLOCK);

    private static RegistryObject<SoundEvent> reg(String name) {
        return SOUNDS.register(name,
                () -> SoundEvent.createVariableRangeEvent(new ResourceLocation(PainOrigin.MODID, name)));
    }

    private ModSounds() {}
}
