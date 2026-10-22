package com.painorigin.client.particle;

import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.client.particle.Particle;
import net.minecraft.client.particle.ParticleProvider;
import net.minecraft.client.particle.SpriteSet;
import net.minecraft.core.particles.SimpleParticleType;
import net.minecraft.util.Mth;
import net.minecraft.world.phys.Vec3;

/**
 * {@code painorigin:chibaku_tensei_debris} - a SIMULATED rock fragment (never a block) that flies from its
 * spawn point to a target, on a swirling path that tightens toward the end.
 *
 * <p>Server parameters (a, b, c) = offset from the spawn point to the target. The flight time is derived
 * from the distance (about 22 ticks + 1.4 ticks per block, 22..90 ticks). The texture holds four rock
 * clusters in a 2x2 grid (64x64 px each, with a transparent margin), one of them is picked at random.
 * The same particle is used for the inbound debris and for the outward burst of the final collapse.
 */
public class ChibakuDebrisParticle extends PainParticle {
    private final double startX;
    private final double startY;
    private final double startZ;
    private final double offsetX;
    private final double offsetY;
    private final double offsetZ;
    /** Unit vectors perpendicular to the flight direction (swirl plane). */
    private final Vec3 sideU;
    private final Vec3 sideV;
    private final float swirlRadius;
    private final float swirlPhase;
    private final float swirlTurns;
    private final float baseSize;
    private final float spin;
    private final int frameX;
    private final int frameY;

    private ChibakuDebrisParticle(ClientLevel level, double x, double y, double z,
                                  double dx, double dy, double dz, SpriteSet sprites) {
        super(level, x, y, z, sprites);
        this.startX = x;
        this.startY = y;
        this.startZ = z;
        this.offsetX = dx;
        this.offsetY = dy;
        this.offsetZ = dz;
        double distance = Math.sqrt(dx * dx + dy * dy + dz * dz);
        this.lifetime = Mth.clamp((int) (22.0D + distance * 1.4D), 22, 90);

        Vec3 axis = distance > 1.0E-4D ? new Vec3(dx / distance, dy / distance, dz / distance) : new Vec3(0.0D, 1.0D, 0.0D);
        Vec3 helper = Math.abs(axis.y) > 0.95D ? new Vec3(1.0D, 0.0D, 0.0D) : new Vec3(0.0D, 1.0D, 0.0D);
        this.sideU = axis.cross(helper).normalize();
        this.sideV = axis.cross(this.sideU).normalize();

        this.swirlRadius = (float) Math.min(2.6D, 0.6D + distance * 0.08D) * (0.5F + this.random.nextFloat() * 0.8F);
        this.swirlPhase = this.random.nextFloat() * TAU;
        float turns = 0.6F + this.random.nextFloat() * 0.9F;
        this.swirlTurns = this.random.nextBoolean() ? turns : -turns;
        this.baseSize = 0.28F + this.random.nextFloat() * 0.30F;
        this.spin = (this.random.nextFloat() - 0.5F) * 0.35F;
        this.roll = this.random.nextFloat() * TAU;
        this.oRoll = this.roll;
        int frame = this.random.nextInt(4);
        this.frameX = frame & 1;
        this.frameY = frame >> 1;
    }

    @Override
    protected float alphaAt(float t) {
        return 0.95F * fade(t, 0.08F, 0.15F);
    }

    @Override
    protected float sizeAt(float t) {
        float shrink = t > 0.85F ? 1.0F - (t - 0.85F) / 0.15F * 0.5F : 1.0F;
        return this.baseSize * shrink;
    }

    @Override
    protected void onTick() {
        float t = Mth.clamp((float) this.age / (float) this.lifetime, 0.0F, 1.0F);
        float travelled = smoothstep(t);
        // the swirl is zero at both ends, so the piece leaves its source and reaches the target exactly
        float radius = this.swirlRadius * (float) Math.sin(Math.PI * t);
        float angle = this.swirlPhase + this.swirlTurns * TAU * t;
        double cos = Math.cos(angle) * radius;
        double sin = Math.sin(angle) * radius;
        this.setPos(
                this.startX + this.offsetX * travelled + this.sideU.x * cos + this.sideV.x * sin,
                this.startY + this.offsetY * travelled + this.sideU.y * cos + this.sideV.y * sin,
                this.startZ + this.offsetZ * travelled + this.sideU.z * cos + this.sideV.z * sin);
        this.roll += this.spin;
    }

    // The sprite is a 2x2 sheet of rock clusters: select one quarter of the sprite's UV rectangle.
    // (Declared public: widening the access of the inherited method is always legal.)
    @Override
    public float getU0() {
        return Mth.lerp(this.frameX * 0.5F, super.getU0(), super.getU1());
    }

    @Override
    public float getU1() {
        return Mth.lerp(this.frameX * 0.5F + 0.5F, super.getU0(), super.getU1());
    }

    @Override
    public float getV0() {
        return Mth.lerp(this.frameY * 0.5F, super.getV0(), super.getV1());
    }

    @Override
    public float getV1() {
        return Mth.lerp(this.frameY * 0.5F + 0.5F, super.getV0(), super.getV1());
    }

    public static class Provider implements ParticleProvider<SimpleParticleType> {
        private final SpriteSet sprites;

        public Provider(SpriteSet sprites) {
            this.sprites = sprites;
        }

        @Override
        public Particle createParticle(SimpleParticleType type, ClientLevel level, double x, double y, double z,
                                       double dx, double dy, double dz) {
            if (!ParticleFilter.allow(level, false)) {
                return null;
            }
            return new ChibakuDebrisParticle(level, x, y, z, dx, dy, dz, this.sprites);
        }
    }
}
