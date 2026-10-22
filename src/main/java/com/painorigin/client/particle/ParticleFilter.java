package com.painorigin.client.particle;

import com.painorigin.PainClientConfig;
import net.minecraft.client.multiplayer.ClientLevel;

/** The client-side "disable / reduce particles" switches, applied by every provider. */
final class ParticleFilter {
    private ParticleFilter() {}

    /**
     * @param essential true for the main sprites (shockwave ring, flash, core): kept even in reduced mode.
     *                  false for decorative ones (streaks, vortex, debris): about one in three is kept in
     *                  reduced mode.
     */
    static boolean allow(ClientLevel level, boolean essential) {
        if (!PainClientConfig.PARTICLES_ENABLED.get()) {
            return false;
        }
        if (essential || !PainClientConfig.PARTICLES_REDUCED.get()) {
            return true;
        }
        return level.getRandom().nextFloat() < 0.35F;
    }
}
