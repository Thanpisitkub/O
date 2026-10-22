package com.painorigin.client.particle;

import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.client.particle.Particle;
import net.minecraft.client.particle.ParticleProvider;
import net.minecraft.client.particle.SpriteSet;
import net.minecraft.core.particles.SimpleParticleType;
import net.minecraft.util.Mth;

/**
 * {@code painorigin:rinnegan_energy} - a small cluster of dark-violet energy filaments.
 *
 * <p>Server parameters (a, b, c) = initial velocity in blocks per tick. Fast ones (the streaks thrown out
 * by Shinra Tensei) lose speed quickly and live ~14 ticks; slow ones (the Rinnegan ambience and the
 * Universal Defense sparks) drift for ~25 ticks.
 */
public class RinneganEnergyParticle extends PainParticle {
    private final float friction;
    private final float baseSize;
    private final float spin;

    private RinneganEnergyParticle(ClientLevel level, double x, double y, double z,
                                   double vx, double vy, double vz, SpriteSet sprites) {
        super(level, x, y, z, sprites);
        this.xd = vx;
        this.yd = vy;
        this.zd = vz;
        float speed = (float) Math.sqrt(vx * vx + vy * vy + vz * vz);
        this.friction = Mth.clamp(0.985F - 0.09F * speed, 0.88F, 0.985F);
        this.lifetime = Mth.clamp((int) (26.0F - 14.0F * Math.min(speed, 1.0F)) + this.random.nextInt(4), 12, 30);
        this.baseSize = 0.32F + this.random.nextFloat() * 0.22F;
        this.spin = (this.random.nextFloat() - 0.5F) * 0.30F;
        this.roll = this.random.nextFloat() * TAU;
        this.oRoll = this.roll;
    }

    @Override
    protected float alphaAt(float t) {
        return 0.90F * fade(t, 0.12F, 0.55F);
    }

    @Override
    protected float sizeAt(float t) {
        return this.baseSize * (0.70F + 0.50F * easeOutCubic(t));
    }

    @Override
    protected void onTick() {
        this.setPos(this.x + this.xd, this.y + this.yd, this.z + this.zd);
        this.xd *= this.friction;
        this.yd *= this.friction;
        this.zd *= this.friction;
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
            if (!ParticleFilter.allow(level, false)) {
                return null;
            }
            return new RinneganEnergyParticle(level, x, y, z, vx, vy, vz, this.sprites);
        }
    }
}
