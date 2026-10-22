package com.painorigin.client.particle;

import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.client.particle.Particle;
import net.minecraft.client.particle.ParticleProvider;
import net.minecraft.client.particle.SpriteSet;
import net.minecraft.core.particles.SimpleParticleType;

/**
 * {@code painorigin:bansho_tenin_aura} - the dark-violet three-arm spiral of the pull.
 *
 * <p>Server parameters (a, b, c) = velocity in blocks per tick. A non-zero velocity is a small spiral that
 * flows along the pull ray toward the caster (or into the caster during the Massive Shinra charge-up);
 * (0, 0, 0) is a stationary larger spiral flash on a creature that was grabbed. Lives 12 ticks.
 */
public class BanshoAuraParticle extends PainParticle {
    private static final int LIFETIME = 12;

    private final boolean still;
    private final float baseSize;
    private final float spin;

    private BanshoAuraParticle(ClientLevel level, double x, double y, double z,
                               double vx, double vy, double vz, SpriteSet sprites) {
        super(level, x, y, z, sprites);
        this.xd = vx;
        this.yd = vy;
        this.zd = vz;
        this.still = vx * vx + vy * vy + vz * vz < 1.0E-6D;
        this.lifetime = LIFETIME;
        this.baseSize = this.still ? 0.95F : 0.40F + this.random.nextFloat() * 0.20F;
        this.roll = this.random.nextFloat() * TAU;
        this.oRoll = this.roll;
        float rate = 0.26F + this.random.nextFloat() * 0.14F;
        this.spin = this.random.nextBoolean() ? rate : -rate;
    }

    @Override
    protected float alphaAt(float t) {
        return this.still ? 0.90F * fade(t, 0.05F, 0.90F) : 0.85F * fade(t, 0.20F, 0.45F);
    }

    @Override
    protected float sizeAt(float t) {
        return this.still ? this.baseSize * (0.60F + 0.80F * easeOutCubic(t)) : this.baseSize * (1.0F - 0.55F * t);
    }

    @Override
    protected void onTick() {
        this.setPos(this.x + this.xd, this.y + this.yd, this.z + this.zd);
        this.roll += this.spin;
    }

    public static class Provider implements ParticleProvider<SimpleParticleType> {
        private final SpriteSet sprites;

        public Provider(SpriteSet sprites) {
            this.sprites = sprites;
        }

        @Override
        public Particle createParticle(SimpleParticleType type, ClientLevel level, double x, double y, double z,
                                       double vx, double vy, double vz) {
            boolean stationary = vx * vx + vy * vy + vz * vz < 1.0E-6D;
            if (!ParticleFilter.allow(level, stationary)) {
                return null;
            }
            return new BanshoAuraParticle(level, x, y, z, vx, vy, vz, this.sprites);
        }
    }
}
