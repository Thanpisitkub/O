package com.painorigin.client.particle;

import com.painorigin.FxStyle;
import com.painorigin.client.CameraShake;
import net.minecraft.client.Minecraft;
import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.client.particle.Particle;
import net.minecraft.client.particle.ParticleProvider;
import net.minecraft.client.particle.SpriteSet;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.core.particles.SimpleParticleType;
import net.minecraft.util.Mth;
import net.minecraft.world.phys.Vec3;

/**
 * {@code painorigin:shinra_tensei_burst} - the camera-facing white/blue starburst flash.
 *
 * <p>Server parameters (a, b, c) = (visible radius in blocks, lifetime in ticks, {@link FxStyle}).
 * Its provider also triggers the camera shake for the local player (the shake has its own switch in the
 * client config and works even when particles are disabled).
 */
public class ShinraBurstParticle extends PainParticle {
    /** Visible radius of the starburst in the PNG as a fraction of the half-size of the texture. */
    private static final float VISIBLE_FRACTION = 0.73F;

    private final float visibleRadius;
    private final float baseAlpha;
    private final float spin;

    private ShinraBurstParticle(ClientLevel level, double x, double y, double z,
                                double size, double life, double style, SpriteSet sprites) {
        super(level, x, y, z, sprites);
        this.visibleRadius = (float) Mth.clamp(size, 0.3D, 24.0D);
        this.lifetime = Mth.clamp((int) Math.round(life), 3, 60);
        float alpha = 0.95F;
        switch ((int) Math.round(style)) {
            case FxStyle.MASSIVE -> this.setColor(0.85F, 0.85F, 1.00F);
            case FxStyle.DEFENSE -> {
                this.setColor(0.60F, 0.90F, 1.00F);
                alpha = 0.85F;
            }
            case FxStyle.HIT -> alpha = 0.80F;
            case FxStyle.COLLAPSE -> this.setColor(0.85F, 0.60F, 1.00F);
            default -> this.setColor(1.0F, 1.0F, 1.0F);
        }
        this.baseAlpha = alpha;
        this.roll = this.random.nextFloat() * TAU;
        this.oRoll = this.roll;
        float rate = 0.04F + this.random.nextFloat() * 0.05F;
        this.spin = this.random.nextBoolean() ? rate : -rate;
    }

    @Override
    protected boolean glows() {
        return true;
    }

    @Override
    protected float alphaAt(float t) {
        return this.baseAlpha * fade(t, 0.04F, 0.90F);
    }

    @Override
    protected float sizeAt(float t) {
        float grow = 0.45F + 0.55F * easeOutCubic(Math.min(1.0F, t * 2.2F));
        return this.visibleRadius / VISIBLE_FRACTION * grow;
    }

    /** Standing inside the flash (the caster) must not white-out the screen: dim it when it is close. */
    @Override
    protected float viewFade(float cameraDistance) {
        return 0.18F + 0.82F * ramp(cameraDistance, 0.25F * this.visibleRadius, this.visibleRadius);
    }

    @Override
    protected void onTick() {
        this.roll += this.spin;
    }

    public static class Provider implements ParticleProvider<SimpleParticleType> {
        private final SpriteSet sprites;

        public Provider(SpriteSet sprites) {
            this.sprites = sprites;
        }

        @Override
        public Particle createParticle(SimpleParticleType type, ClientLevel level, double x, double y, double z,
                                       double size, double life, double style) {
            shake(x, y, z, (int) Math.round(style));
            if (!ParticleFilter.allow(level, true)) {
                return null;
            }
            return new ShinraBurstParticle(level, x, y, z, size, life, style, this.sprites);
        }

        /** Camera shake for the local player, by effect style and distance (none for HIT / DEFENSE / FIELD). */
        private static void shake(double x, double y, double z, int style) {
            double reach;
            float degrees;
            int ticks;
            switch (style) {
                case FxStyle.NORMAL -> {
                    reach = 14.0D;
                    degrees = 1.2F;
                    ticks = 10;
                }
                case FxStyle.MASSIVE -> {
                    reach = 40.0D;
                    degrees = 3.0F;
                    ticks = 20;
                }
                case FxStyle.COLLAPSE -> {
                    reach = 48.0D;
                    degrees = 3.6F;
                    ticks = 26;
                }
                default -> {
                    return;
                }
            }
            LocalPlayer player = Minecraft.getInstance().player;
            if (player == null) {
                return;
            }
            double distance = player.position().distanceTo(new Vec3(x, y, z));
            if (distance >= reach) {
                return;
            }
            CameraShake.trigger(degrees * (float) (1.0D - distance / reach), ticks);
        }
    }
}
