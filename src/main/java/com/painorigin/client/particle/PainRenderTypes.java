package com.painorigin.client.particle;

import com.mojang.blaze3d.systems.RenderSystem;
import com.mojang.blaze3d.vertex.BufferBuilder;
import com.mojang.blaze3d.vertex.DefaultVertexFormat;
import com.mojang.blaze3d.vertex.Tesselator;
import com.mojang.blaze3d.vertex.VertexFormat;
import com.painorigin.PainClientConfig;
import net.minecraft.client.Minecraft;
import net.minecraft.client.particle.ParticleRenderType;
import net.minecraft.client.renderer.texture.TextureAtlas;
import net.minecraft.client.renderer.texture.TextureManager;
import org.lwjgl.opengl.GL11;

/**
 * Render types of the six particles. Both draw the vanilla particle atlas with the vanilla particle
 * shader (Forge's ParticleEngine already selects the shader before calling {@code begin}).
 *
 * <ul>
 *   <li>{@link #glow()} - used by the bright white/blue sprites (shockwave ring, flash). Additive
 *       blending (SRC_ALPHA, ONE): a texel adds {@code rgb * alpha}, so a fully transparent texel adds
 *       exactly nothing and nothing can show up as a box around the sprite. Switchable to ordinary alpha
 *       blending with {@code particles.additiveBlend = false} in painorigin-client.toml.</li>
 *   <li>{@link #soft()} - used by the DARK sprites (violet spiral, Chibaku core, debris rocks, dark energy
 *       filaments). They must use ordinary alpha blending (SRC_ALPHA, ONE_MINUS_SRC_ALPHA): with additive
 *       blending a dark texel adds almost nothing and the sprite would be invisible.</li>
 * </ul>
 *
 * <p>Common to both: depth WRITES are off (a quad with transparent corners must never punch a rectangular
 * hole into the depth buffer - that is what would otherwise look like a square frame), depth TEST stays on
 * (terrain hides the particles), face culling is off (the shockwave ring is a flat horizontal quad seen
 * from above and below), and the atlas is switched to bilinear filtering while these batches are drawn and
 * restored right afterwards (the sprites are big smooth gradients; the transparent colour-bled margins
 * baked into the PNGs keep neighbouring atlas sprites from bleeding in).
 */
public final class PainRenderTypes {
    private static final ParticleRenderType ADDITIVE = new Type(true);
    private static final ParticleRenderType ALPHA = new Type(false);

    private PainRenderTypes() {}

    /** For the bright sprites: additive unless the player switched it off in the client config. */
    public static ParticleRenderType glow() {
        return PainClientConfig.ADDITIVE_BLEND.get() ? ADDITIVE : ALPHA;
    }

    /** For the dark sprites: always ordinary alpha blending. */
    public static ParticleRenderType soft() {
        return ALPHA;
    }

    private static final class Type implements ParticleRenderType {
        private final boolean additive;

        Type(boolean additive) {
            this.additive = additive;
        }

        @Override
        public void begin(BufferBuilder buffer, TextureManager textures) {
            RenderSystem.depthMask(false);
            RenderSystem.enableBlend();
            if (additive) {
                RenderSystem.blendFunc(GL11.GL_SRC_ALPHA, GL11.GL_ONE);
            } else {
                RenderSystem.defaultBlendFunc();
            }
            RenderSystem.disableCull();
            RenderSystem.setShaderTexture(0, TextureAtlas.LOCATION_PARTICLES);
            textures.getTexture(TextureAtlas.LOCATION_PARTICLES).setBlurMipmap(true, false);
            buffer.begin(VertexFormat.Mode.QUADS, DefaultVertexFormat.PARTICLE);
        }

        @Override
        public void end(Tesselator tesselator) {
            tesselator.end();
            Minecraft.getInstance().getTextureManager().getTexture(TextureAtlas.LOCATION_PARTICLES).restoreLastBlurMipmap();
            RenderSystem.enableCull();
            RenderSystem.defaultBlendFunc();
            RenderSystem.depthMask(true);
        }

        @Override
        public String toString() {
            return additive ? "painorigin:glow_additive" : "painorigin:soft_alpha";
        }
    }
}
