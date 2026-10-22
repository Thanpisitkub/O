package com.painorigin.client.particle;

import com.painorigin.FxStyle;
import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.client.particle.Particle;
import net.minecraft.client.particle.ParticleProvider;
import net.minecraft.client.particle.SpriteSet;
import net.minecraft.core.particles.SimpleParticleType;
import net.minecraft.util.Mth;

/**
 * {@code painorigin:chibaku_tensei_core} - the dark-violet sphere with a glowing rim that hangs above the
 * ground while Chibaku Tensei is active (and the expanding sphere of the final collapse).
 *
 * <p>Server parameters (a, b, c) = (radius now in blocks, growth in blocks per tick, {@link FxStyle}).
 * The server respawns the core every 4 ticks; each copy lives 6 ticks and grows by {@code b} per tick, so
 * consecutive copies cross-fade. The slow swirl rotation is derived from the world time (not from each
 * copy's own age), otherwise the swirl pattern would jump every time a new copy takes over.
 */
public class ChibakuCoreParticle extends PainParticle {
    /** Radius of the solid sphere body in the PNG as a fraction of the half-size of the texture. */
    private static final float BODY_FRACTION = 0.89F;
    /** 34 full turns per 3600 ticks, so the phase wraps seamlessly when game time is taken modulo 3600. */
    private static final float SWIRL_PER_TICK = TAU * 34.0F / 3600.0F;

    private final float startRadius;
    private final float growth;

    private ChibakuCoreParticle(ClientLevel level, double x, double y, double z,
                                double radius, double growthPerTick, double style, SpriteSet sprites) {
        super(level, x, y, z, sprites);
        this.startRadius = (float) Mth.clamp(radius, 0.3D, 40.0D);
        this.growth = (float) Mth.clamp(growthPerTick, -2.0D, 2.0D);
        this.lifetime = (int) Math.round(style) == FxStyle.COLLAPSE ? 8 : 6;
        float phase = (level.getGameTime() % 3600L) * SWIRL_PER_TICK;
        this.roll = phase;
        this.oRoll = phase;
    }

    @Override
    protected float alphaAt(float t) {
        return 0.97F * fade(t, 0.28F, 0.32F);
    }

    @Override
    protected float sizeAt(float t) {
        float ticks = t * this.lifetime;
        return Math.max(0.2F, this.startRadius + this.growth * ticks) / BODY_FRACTION;
    }

    /** A camera that is inside (or right next to) the sphere would see a solid dark screen: thin it out. */
    @Override
    protected float viewFade(float cameraDistance) {
        float r = this.startRadius;
        return 0.25F + 0.75F * ramp(cameraDistance, 0.3F * r, 1.3F * r);
    }

    @Override
    protected void onTick() {
        long phaseTick = this.level.getGameTime() % 3600L;
        this.oRoll = phaseTick * SWIRL_PER_TICK;
        this.roll = (phaseTick + 1L) * SWIRL_PER_TICK;
    }

    public static class Provider implements ParticleProvider<SimpleParticleType> {
        private final SpriteSet sprites;

        public Provider(SpriteSet sprites) {
            this.sprites = sprites;
        }

        @Override
        public Particle createParticle(SimpleParticleType type, ClientLevel level, double x, double y, double z,
                                       double radius, double growthPerTick, double style) {
            if (!ParticleFilter.allow(level, true)) {
                return null;
            }
            return new ChibakuCoreParticle(level, x, y, z, radius, growthPerTick, style, this.sprites);
        }
    }
}
