package com.painorigin.client;

import com.painorigin.ModParticles;
import com.painorigin.PainOrigin;
import com.painorigin.client.particle.BanshoAuraParticle;
import com.painorigin.client.particle.ChibakuCoreParticle;
import com.painorigin.client.particle.ChibakuDebrisParticle;
import com.painorigin.client.particle.RinneganEnergyParticle;
import com.painorigin.client.particle.ShinraBurstParticle;
import com.painorigin.client.particle.ShinraWaveParticle;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.client.event.RegisterParticleProvidersEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;

/** Mod-bus client setup: attaches a provider (the client class that builds the particle) to each type. */
@Mod.EventBusSubscriber(modid = PainOrigin.MODID, bus = Mod.EventBusSubscriber.Bus.MOD, value = Dist.CLIENT)
public final class ClientSetup {
    private ClientSetup() {}

    @SubscribeEvent
    public static void registerParticleProviders(RegisterParticleProvidersEvent event) {
        event.registerSpriteSet(ModParticles.SHINRA_TENSEI_WAVE.get(), ShinraWaveParticle.Provider::new);
        event.registerSpriteSet(ModParticles.SHINRA_TENSEI_BURST.get(), ShinraBurstParticle.Provider::new);
        event.registerSpriteSet(ModParticles.BANSHO_TENIN_AURA.get(), BanshoAuraParticle.Provider::new);
        event.registerSpriteSet(ModParticles.CHIBAKU_TENSEI_CORE.get(), ChibakuCoreParticle.Provider::new);
        event.registerSpriteSet(ModParticles.CHIBAKU_TENSEI_DEBRIS.get(), ChibakuDebrisParticle.Provider::new);
        event.registerSpriteSet(ModParticles.RINNEGAN_ENERGY.get(), RinneganEnergyParticle.Provider::new);
    }
}
