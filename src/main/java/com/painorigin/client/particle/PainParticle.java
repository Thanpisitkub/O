package com.painorigin.client.particle;

import com.mojang.blaze3d.vertex.VertexConsumer;
import com.painorigin.PainClientConfig;
import net.minecraft.client.Camera;
import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.client.particle.ParticleRenderType;
import net.minecraft.client.particle.SpriteSet;
import net.minecraft.client.particle.TextureSheetParticle;
import net.minecraft.util.Mth;
import net.minecraft.world.phys.Vec3;

/**
 * Common behaviour of the six particles: one transparent sprite, no physics, half-size and alpha computed
 * every frame from the normalised age {@code t} (0..1) so the animation is smooth between ticks, the
 * overall opacity from the client config, and no frustum culling (they are few and some are huge).
 *
 * <p>Sprites are drawn with the vanilla camera-facing quad ({@code SingleQuadParticle.render}); only the
 * flat shockwave ring replaces {@link #render} with its own horizontal quad.
 */
abstract class PainParticle extends TextureSheetParticle {
    protected static final float TAU = (float) (Math.PI * 2.0);

    /** The master opacity from painorigin-client.toml, read once when the particle is created. */
    protected final float opacity;

    protected PainParticle(ClientLevel level, double x, double y, double z, SpriteSet sprites) {
        super(level, x, y, z);
        this.pickSprite(sprites);
        this.hasPhysics = false;
        this.gravity = 0.0F;
        this.xd = 0.0D;
        this.yd = 0.0D;
        this.zd = 0.0D;
        this.lifetime = 20;
        double configured = PainClientConfig.PARTICLE_OPACITY.get();
        this.opacity = (float) Math.max(0.05D, Math.min(1.0D, configured));
    }

    /** Opacity at normalised age t (before the config opacity is applied). */
    protected abstract float alphaAt(float t);

    /** Half-size of the camera-facing quad at normalised age t (blocks). */
    protected abstract float sizeAt(float t);

    /** Bright sprites (ring, flash) use the additive render type, dark ones ordinary alpha blending. */
    protected boolean glows() {
        return false;
    }

    /** Per-tick movement / spin, called after the age was advanced. */
    protected void onTick() {
    }

    /**
     * Extra opacity factor that depends on where the camera is, so that a flash or a sphere that
     * surrounds the player's own camera never blanks the screen. Default: none.
     */
    protected float viewFade(float cameraDistance) {
        return 1.0F;
    }

    @Override
    public void tick() {
        this.xo = this.x;
        this.yo = this.y;
        this.zo = this.z;
        this.oRoll = this.roll;
        if (this.age++ >= this.lifetime) {
            this.remove();
            return;
        }
        this.onTick();
    }

    /** Normalised age at a render frame. */
    protected final float progress(float partialTick) {
        return Mth.clamp((this.age + partialTick) / (float) Math.max(1, this.lifetime), 0.0F, 1.0F);
    }

    /** Distance from the camera to the (interpolated) particle position. */
    protected final float cameraDistance(Camera camera, float partialTick) {
        Vec3 cam = camera.getPosition();
        double dx = Mth.lerp(partialTick, this.xo, this.x) - cam.x;
        double dy = Mth.lerp(partialTick, this.yo, this.y) - cam.y;
        double dz = Mth.lerp(partialTick, this.zo, this.z) - cam.z;
        return (float) Math.sqrt(dx * dx + dy * dy + dz * dz);
    }

    @Override
    public void render(VertexConsumer buffer, Camera camera, float partialTick) {
        float t = progress(partialTick);
        float a = alphaAt(t) * this.opacity * viewFade(cameraDistance(camera, partialTick));
        if (a <= 0.002F) {
            return;
        }
        this.alpha = Mth.clamp(a, 0.0F, 1.0F);
        this.quadSize = sizeAt(t);
        super.render(buffer, camera, partialTick);
    }

    @Override
    public ParticleRenderType getRenderType() {
        return glows() ? PainRenderTypes.glow() : PainRenderTypes.soft();
    }

    /** All six are self-lit: full-bright, unaffected by the world light level. */
    @Override
    protected int getLightColor(float partialTick) {
        return 0xF000F0;
    }

    /** Forge hook: never drop these by bounding box (they are few, and the big ones would pop out). */
    @Override
    public boolean shouldCull() {
        return false;
    }

    protected static float easeOutCubic(float t) {
        float u = 1.0F - t;
        return 1.0F - u * u * u;
    }

    protected static float smoothstep(float t) {
        return t * t * (3.0F - 2.0F * t);
    }

    /** Fade in over the first {@code in} fraction and out over the last {@code out} fraction. */
    protected static float fade(float t, float in, float out) {
        float a = in <= 0.0F ? 1.0F : Mth.clamp(t / in, 0.0F, 1.0F);
        float b = out <= 0.0F ? 1.0F : Mth.clamp((1.0F - t) / out, 0.0F, 1.0F);
        return a * b;
    }

    /** Linear 0..1 ramp of {@code value} between {@code from} and {@code to}. */
    protected static float ramp(float value, float from, float to) {
        return Mth.clamp((value - from) / (to - from), 0.0F, 1.0F);
    }
}
