package com.painorigin;

import java.util.List;
import net.minecraft.core.particles.ParticleType;
import net.minecraft.core.particles.SimpleParticleType;
import net.minecraftforge.registries.DeferredRegister;
import net.minecraftforge.registries.ForgeRegistries;
import net.minecraftforge.registries.RegistryObject;

/**
 * The six custom particle types. Each one has
 * <ul>
 *   <li>a definition {@code assets/painorigin/particles/<name>.json} (texture list),</li>
 *   <li>a transparent PNG {@code assets/painorigin/textures/particle/<name>.png},</li>
 *   <li>a client provider registered in {@code client.ClientSetup}.</li>
 * </ul>
 * The server sends them with {@code count = 0}, so the three "velocity" doubles of the packet reach the
 * client unchanged and are used as three free parameters (see {@link Fx} for the exact meaning).
 */
public final class ModParticles {
    public static final DeferredRegister<ParticleType<?>> PARTICLES =
            DeferredRegister.create(ForgeRegistries.PARTICLE_TYPES, PainOrigin.MODID);

    public static final RegistryObject<SimpleParticleType> SHINRA_TENSEI_WAVE = simple("shinra_tensei_wave");
    public static final RegistryObject<SimpleParticleType> SHINRA_TENSEI_BURST = simple("shinra_tensei_burst");
    public static final RegistryObject<SimpleParticleType> BANSHO_TENIN_AURA = simple("bansho_tenin_aura");
    public static final RegistryObject<SimpleParticleType> CHIBAKU_TENSEI_CORE = simple("chibaku_tensei_core");
    public static final RegistryObject<SimpleParticleType> CHIBAKU_TENSEI_DEBRIS = simple("chibaku_tensei_debris");
    public static final RegistryObject<SimpleParticleType> RINNEGAN_ENERGY = simple("rinnegan_energy");

    /** Every particle type of this mod (used by the self-test command). */
    public static final List<RegistryObject<SimpleParticleType>> ALL = List.of(
            SHINRA_TENSEI_WAVE, SHINRA_TENSEI_BURST, BANSHO_TENIN_AURA,
            CHIBAKU_TENSEI_CORE, CHIBAKU_TENSEI_DEBRIS, RINNEGAN_ENERGY);

    private static RegistryObject<SimpleParticleType> simple(String name) {
        return PARTICLES.register(name, () -> new SimpleParticleType(false));
    }

    private ModParticles() {}
}
