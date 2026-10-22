package com.painorigin;

import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;
import java.util.UUID;
import net.minecraft.core.particles.ParticleOptions;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.phys.Vec3;

/**
 * Server side of the particle effects.
 *
 * <p>Every particle is sent with {@code count = 0}; for such packets vanilla hands the three
 * "spread" values to the client as the particle's velocity. We use those three numbers as free
 * parameters (the client classes in {@code client.particle} decode them):
 *
 * <pre>
 *  shinra_tensei_wave   (a, b, c) = (max radius in blocks, lifetime in ticks, FxStyle)   horizontal ring
 *  shinra_tensei_burst  (a, b, c) = (visible radius,       lifetime in ticks, FxStyle)   camera-facing flash
 *  bansho_tenin_aura    (a, b, c) = velocity per tick; (0,0,0) = stationary flash        (lives 12 ticks)
 *  chibaku_tensei_core  (a, b, c) = (radius now, growth per tick, FxStyle)               (lives 6 ticks)
 *  chibaku_tensei_debris(a, b, c) = offset from the spawn point to where the piece flies to
 *  rinnegan_energy      (a, b, c) = velocity per tick
 * </pre>
 */
public final class Fx {
    private static final double TAU = Math.PI * 2.0;
    private static final RandomSource RANDOM = RandomSource.create();
    private static final List<Charge> CHARGES = new ArrayList<>();

    private static final class Charge {
        final UUID player;
        int remaining;

        Charge(UUID player, int remaining) {
            this.player = player;
            this.remaining = remaining;
        }
    }

    private Fx() {}

    // ------------------------------------------------------------------------------------------
    // low level
    // ------------------------------------------------------------------------------------------

    /** Sends one particle to every player within the configured range. */
    public static void send(ServerLevel level, ParticleOptions type, double x, double y, double z,
                            double a, double b, double c) {
        if (!PainConfig.PARTICLES_ENABLED.get()) {
            return;
        }
        double range = PainConfig.PARTICLE_RANGE.get();
        double range2 = range * range;
        boolean force = PainConfig.PARTICLES_OVERRIDE_LIMITER.get();
        for (ServerPlayer player : level.players()) {
            if (player.distanceToSqr(x, y, z) <= range2) {
                level.sendParticles(player, type, force, x, y, z, 0, a, b, c, 1.0);
            }
        }
    }

    /** Applies the {@code countMultiplier} config to a base count with unbiased random rounding. */
    public static int scaled(double base) {
        double want = base * PainConfig.PARTICLE_MULTIPLIER.get();
        int whole = (int) Math.floor(want);
        double fraction = want - whole;
        return whole + (RANDOM.nextDouble() < fraction ? 1 : 0);
    }

    // ------------------------------------------------------------------------------------------
    // Shinra Tensei / Massive Shinra Tensei
    // ------------------------------------------------------------------------------------------

    public static void shinra(ServerLevel level, Vec3 c, double radius, boolean massive) {
        int style = massive ? FxStyle.MASSIVE : FxStyle.NORMAL;
        double life = Mth.clamp(8.0 + radius * 0.8, 10.0, 34.0);
        send(level, ModParticles.SHINRA_TENSEI_WAVE.get(), c.x, c.y + 0.9, c.z, radius, life, style);
        if (massive) {
            send(level, ModParticles.SHINRA_TENSEI_WAVE.get(), c.x, c.y + 0.9, c.z, radius * 0.66, life * 0.85, style);
            send(level, ModParticles.SHINRA_TENSEI_WAVE.get(), c.x, c.y + 0.9, c.z, radius * 0.38, life * 0.7, style);
        }
        double size = Mth.clamp(radius * 0.3, 2.0, 8.0);
        send(level, ModParticles.SHINRA_TENSEI_BURST.get(), c.x, c.y + 1.0, c.z, size, massive ? 16.0 : 10.0, style);

        RandomSource rnd = level.getRandom();
        int streaks = scaled(massive ? 36.0 : 16.0);
        for (int i = 0; i < streaks; i++) {
            double angle = rnd.nextDouble() * TAU;
            double speed = (massive ? 0.9 : 0.55) + rnd.nextDouble() * 0.6;
            double vy = (rnd.nextDouble() - 0.4) * 0.1;
            send(level, ModParticles.RINNEGAN_ENERGY.get(),
                    c.x + Math.cos(angle) * 0.6, c.y + 0.4 + rnd.nextDouble() * 1.3, c.z + Math.sin(angle) * 0.6,
                    Math.cos(angle) * speed, vy, Math.sin(angle) * speed);
        }
    }

    /** Massive Shinra Tensei charge-up: a vortex of aura particles around the caster for {@code ticks} ticks. */
    public static void startCharge(ServerPlayer player, int ticks) {
        CHARGES.removeIf(charge -> charge.player.equals(player.getUUID()));
        CHARGES.add(new Charge(player.getUUID(), ticks));
    }

    /** Runs once per server tick (see CommonEvents). */
    public static void tick(MinecraftServer server) {
        if (CHARGES.isEmpty()) {
            return;
        }
        Iterator<Charge> it = CHARGES.iterator();
        while (it.hasNext()) {
            Charge charge = it.next();
            ServerPlayer player = server.getPlayerList().getPlayer(charge.player);
            charge.remaining--;
            if (player == null || !player.isAlive() || charge.remaining < 0) {
                it.remove();
                continue;
            }
            vortex((ServerLevel) player.level(), player.position().add(0.0, 1.0, 0.0), 5.0, scaled(2.0));
        }
    }

    /** Aura particles that start on a sphere around {@code center} and flow into it (they live 12 ticks). */
    public static void vortex(ServerLevel level, Vec3 center, double radius, int count) {
        RandomSource rnd = level.getRandom();
        for (int i = 0; i < count; i++) {
            double u = rnd.nextDouble() * 2.0 - 1.0;
            double theta = rnd.nextDouble() * TAU;
            double s = Math.sqrt(1.0 - u * u);
            double r = radius * (0.8 + rnd.nextDouble() * 0.4);
            double x = center.x + s * Math.cos(theta) * r;
            double y = center.y + u * r * 0.6;
            double z = center.z + s * Math.sin(theta) * r;
            send(level, ModParticles.BANSHO_TENIN_AURA.get(), x, y, z,
                    (center.x - x) / 12.0, (center.y - y) / 12.0, (center.z - z) / 12.0);
        }
    }

    // ------------------------------------------------------------------------------------------
    // Bansho Ten'in
    // ------------------------------------------------------------------------------------------

    /** One trail particle at a step of the pull ray, flowing back toward the caster. */
    public static void banshoTrail(ServerLevel level, Vec3 pos, Entity caster) {
        if (scaled(1.0) <= 0) {
            return;
        }
        Vec3 toCaster = caster.getEyePosition().subtract(pos);
        double length = toCaster.length();
        if (length < 0.8) {
            return;
        }
        double speed = Math.min(length / 12.0, 0.9);
        Vec3 velocity = toCaster.scale(speed / length);
        send(level, ModParticles.BANSHO_TENIN_AURA.get(), pos.x, pos.y, pos.z, velocity.x, velocity.y, velocity.z);
    }

    /** Flash on the creature that was grabbed. */
    public static void banshoHit(ServerLevel level, Entity target) {
        double x = target.getX();
        double y = target.getY() + target.getBbHeight() * 0.5;
        double z = target.getZ();
        send(level, ModParticles.BANSHO_TENIN_AURA.get(), x, y, z, 0.0, 0.0, 0.0);
        double size = Mth.clamp(target.getBbWidth() * 1.2 + 0.6, 1.0, 3.0);
        send(level, ModParticles.SHINRA_TENSEI_BURST.get(), x, y, z, size, 8.0, FxStyle.HIT);
    }

    // ------------------------------------------------------------------------------------------
    // Universal Defense / Rinnegan ambience
    // ------------------------------------------------------------------------------------------

    public static void defense(ServerLevel level, Entity entity) {
        double x = entity.getX();
        double y = entity.getY();
        double z = entity.getZ();
        send(level, ModParticles.SHINRA_TENSEI_BURST.get(), x, y + 1.0, z, 2.4, 9.0, FxStyle.DEFENSE);
        send(level, ModParticles.SHINRA_TENSEI_WAVE.get(), x, y + 0.9, z, 3.2, 10.0, FxStyle.DEFENSE);
        RandomSource rnd = level.getRandom();
        int n = scaled(10.0);
        for (int i = 0; i < n; i++) {
            double angle = rnd.nextDouble() * TAU;
            double speed = 0.2 + rnd.nextDouble() * 0.25;
            send(level, ModParticles.RINNEGAN_ENERGY.get(), x, y + 0.6 + rnd.nextDouble() * 1.0, z,
                    Math.cos(angle) * speed, (rnd.nextDouble() - 0.5) * 0.08, Math.sin(angle) * speed);
        }
    }

    public static void ambient(ServerLevel level, Entity entity) {
        if (!PainConfig.PARTICLES_AMBIENT.get()) {
            return;
        }
        RandomSource rnd = level.getRandom();
        int n = scaled(1.2);
        for (int i = 0; i < n; i++) {
            double angle = rnd.nextDouble() * TAU;
            double r = 0.7 + rnd.nextDouble() * 0.5;
            send(level, ModParticles.RINNEGAN_ENERGY.get(),
                    entity.getX() + Math.cos(angle) * r, entity.getY() + 0.2 + rnd.nextDouble() * 1.7,
                    entity.getZ() + Math.sin(angle) * r,
                    -Math.sin(angle) * 0.03, 0.025, Math.cos(angle) * 0.03);
        }
    }

    // ------------------------------------------------------------------------------------------
    // Chibaku Tensei
    // ------------------------------------------------------------------------------------------

    public static void chibakuCore(ServerLevel level, Vec3 core, double radius, double growthPerTick, int style) {
        send(level, ModParticles.CHIBAKU_TENSEI_CORE.get(), core.x, core.y, core.z, radius, growthPerTick, style);
    }

    /** Expanding ring that shows the size of the gravity field on the ground. */
    public static void pulse(ServerLevel level, Vec3 anchor, double radius) {
        send(level, ModParticles.SHINRA_TENSEI_WAVE.get(), anchor.x, anchor.y + 0.25, anchor.z, radius, 22.0, FxStyle.FIELD);
    }

    public static void burst(ServerLevel level, Vec3 pos, double size, double life, int style) {
        send(level, ModParticles.SHINRA_TENSEI_BURST.get(), pos.x, pos.y, pos.z, size, life, style);
    }

    /** One simulated debris piece that flies from (x, y, z) into the core. */
    public static void debris(ServerLevel level, double x, double y, double z, Vec3 core) {
        send(level, ModParticles.CHIBAKU_TENSEI_DEBRIS.get(), x, y, z, core.x - x, core.y - y, core.z - z);
    }

    public static void chibakuCollapse(ServerLevel level, Vec3 anchor, Vec3 core, double radius) {
        send(level, ModParticles.SHINRA_TENSEI_WAVE.get(), anchor.x, anchor.y + 0.4, anchor.z, radius, 26.0, FxStyle.COLLAPSE);
        send(level, ModParticles.SHINRA_TENSEI_WAVE.get(), core.x, core.y, core.z, radius * 0.8, 24.0, FxStyle.COLLAPSE);
        send(level, ModParticles.SHINRA_TENSEI_BURST.get(), core.x, core.y, core.z, 10.0, 22.0, FxStyle.COLLAPSE);
        send(level, ModParticles.CHIBAKU_TENSEI_CORE.get(), core.x, core.y, core.z, 4.0, 0.9, FxStyle.COLLAPSE);
        RandomSource rnd = level.getRandom();
        int pieces = scaled(24.0);
        for (int i = 0; i < pieces; i++) {
            double u = rnd.nextDouble() * 2.0 - 1.0;
            double theta = rnd.nextDouble() * TAU;
            double s = Math.sqrt(1.0 - u * u);
            double reach = 12.0 + rnd.nextDouble() * 10.0;
            send(level, ModParticles.CHIBAKU_TENSEI_DEBRIS.get(), core.x, core.y, core.z,
                    s * Math.cos(theta) * reach, u * reach * 0.7, s * Math.sin(theta) * reach);
        }
    }

    /** Forget scheduled effects (called when a world is closed). */
    public static void reset() {
        CHARGES.clear();
    }
}
