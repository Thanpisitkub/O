package com.painorigin.client.particle;

import com.mojang.blaze3d.vertex.VertexConsumer;
import com.painorigin.FxStyle;
import net.minecraft.client.Camera;
import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.client.particle.Particle;
import net.minecraft.client.particle.ParticleProvider;
import net.minecraft.client.particle.SpriteSet;
import net.minecraft.core.particles.SimpleParticleType;
import net.minecraft.util.Mth;
import net.minecraft.world.phys.Vec3;

/**
 * {@code painorigin:shinra_tensei_wave} - the expanding shockwave ring, a FLAT HORIZONTAL quad.
 *
 * <p>Server parameters (a, b, c) = (max radius in blocks, lifetime in ticks, {@link FxStyle}).
 * The texture is a white ring ({@link #RING_FRACTION} of the half-size) with faint inner rings; the quad is
 * scaled so the bright ring reaches exactly the requested radius at the end of the animation.
 */
public class ShinraWaveParticle extends PainParticle {
    /** Radius of the bright ring in the PNG as a fraction of the half-size of the texture. */
    private static final float RING_FRACTION = 0.86F;

    private final float maxRadius;
    private final float baseAlpha;

    private ShinraWaveParticle(ClientLevel level, double x, double y, double z,
                               double radius, double life, double style, SpriteSet sprites) {
        super(level, x, y, z, sprites);
        this.maxRadius = (float) Mth.clamp(radius, 0.5D, 96.0D);
        this.lifetime = Mth.clamp((int) Math.round(life), 4, 80);
        float alpha = 0.95F;
        switch ((int) Math.round(style)) {
            case FxStyle.MASSIVE -> this.setColor(0.80F, 0.80F, 1.00F);
            case FxStyle.FIELD -> {
                this.setColor(0.62F, 0.52F, 1.00F);
                alpha = 0.60F;
            }
            case FxStyle.DEFENSE -> {
                this.setColor(0.55F, 0.85F, 1.00F);
                alpha = 0.90F;
            }
            case FxStyle.COLLAPSE -> {
                this.setColor(0.80F, 0.50F, 1.00F);
                alpha = 1.00F;
            }
            default -> this.setColor(1.0F, 1.0F, 1.0F);
        }
        this.baseAlpha = alpha;
    }

    @Override
    protected boolean glows() {
        return true;
    }

    @Override
    protected float alphaAt(float t) {
        return this.baseAlpha * fade(t, 0.06F, 0.70F);
    }

    /** Half-size of the quad (not of the ring) at normalised age t. */
    @Override
    protected float sizeAt(float t) {
        float radius = Math.max(0.25F, this.maxRadius * easeOutCubic(t));
        return radius / RING_FRACTION;
    }

    /** Draws one horizontal quad (no camera billboarding), so it lies flat on the ground like a shockwave. */
    @Override
    public void render(VertexConsumer buffer, Camera camera, float partialTick) {
        float t = progress(partialTick);
        float a = alphaAt(t) * this.opacity;
        if (a <= 0.002F) {
            return;
        }
        float half = sizeAt(t);
        Vec3 cam = camera.getPosition();
        float cx = (float) (Mth.lerp(partialTick, this.xo, this.x) - cam.x);
        float cy = (float) (Mth.lerp(partialTick, this.yo, this.y) - cam.y);
        float cz = (float) (Mth.lerp(partialTick, this.zo, this.z) - cam.z);
        float u0 = this.getU0();
        float u1 = this.getU1();
        float v0 = this.getV0();
        float v1 = this.getV1();
        int light = this.getLightColor(partialTick);
        float alpha = Mth.clamp(a, 0.0F, 1.0F);

        buffer.vertex(cx - half, cy, cz - half).uv(u0, v0).color(this.rCol, this.gCol, this.bCol, alpha).uv2(light).endVertex();
        buffer.vertex(cx - half, cy, cz + half).uv(u0, v1).color(this.rCol, this.gCol, this.bCol, alpha).uv2(light).endVertex();
        buffer.vertex(cx + half, cy, cz + half).uv(u1, v1).color(this.rCol, this.gCol, this.bCol, alpha).uv2(light).endVertex();
        buffer.vertex(cx + half, cy, cz - half).uv(u1, v0).color(this.rCol, this.gCol, this.bCol, alpha).uv2(light).endVertex();
    }

    public static class Provider implements ParticleProvider<SimpleParticleType> {
        private final SpriteSet sprites;

        public Provider(SpriteSet sprites) {
            this.sprites = sprites;
        }

        @Override
        public Particle createParticle(SimpleParticleType type, ClientLevel level, double x, double y, double z,
                                       double radius, double life, double style) {
            if (!ParticleFilter.allow(level, true)) {
                return null;
            }
            return new ShinraWaveParticle(level, x, y, z, radius, life, style, this.sprites);
        }
    }
}
